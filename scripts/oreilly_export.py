import argparse
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path
from urllib.parse import quote, urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup
from markdownify import markdownify
from playwright.sync_api import Error as PlaywrightError, sync_playwright


ROOT = Path(__file__).resolve().parent
STATE = ROOT / ".auth/state.json"
BOOK_URL = "https://learning-oreilly-com.udstlibrary.idm.oclc.org/library/view/ros-2-from/9781835881408/"


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_bytes(data.encode("utf-8") if isinstance(data, str) else data)
    temporary.replace(path)


def save_json(path, data):
    write(path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def book_address(url):
    parts = urlsplit(url)
    match = re.fullmatch(r"(/library/view/[^/]+/([^/]+)/).*", parts.path)
    if parts.scheme not in {"https", "http"} or not parts.netloc or not match:
        raise ValueError("Use the book's /library/view/title/book-id/ URL.")
    origin = urlunsplit((parts.scheme, parts.netloc, "", "", ""))
    return origin, origin + match[1], match[2]


def proxy_url(url, base, origin):
    parts = urlsplit(urljoin(base, url))
    if parts.hostname in {"learning.oreilly.com", "www.oreilly.com", "api.oreilly.com"}:
        proxy = urlsplit(origin)
        parts = parts._replace(scheme=proxy.scheme, netloc=proxy.netloc)
    if parts.scheme not in {"https", "http"}:
        raise ValueError("Unsupported content URL.")
    return urlunsplit(parts)


def fetch(request, url, kind):
    for attempt in range(3):
        try:
            response = request.get(url, timeout=30000)
        except PlaywrightError:
            if attempt == 2:
                raise ValueError("Network request failed after three attempts.") from None
            time.sleep(2 ** attempt)
            continue
        status = response.status
        if status in {401, 403, 429}:
            response.dispose()
            raise ValueError(f"Access stopped (HTTP {status}). Check login or wait before retrying.")
        if 500 <= status < 600 and attempt < 2:
            response.dispose()
            time.sleep(2 ** attempt)
            continue
        try:
            if not response.ok:
                raise ValueError(f"Request failed (HTTP {status}) at {urlsplit(url).path}; the book API may have changed.")
            if re.search(r"/(login|signin|sso|authorize|access-denied)(/|$)", urlsplit(response.url).path, re.I):
                raise ValueError("Redirected to login or an access block. Run login again.")
            mime = response.headers.get("content-type", "").split(";")[0].lower()
            if kind == "json":
                if "json" not in mime:
                    raise ValueError("Expected book metadata; received a login page or unsupported API response.")
                return response.json()
            if kind == "image":
                if not mime.startswith("image/"):
                    raise ValueError("An image request returned a login page or non-image response.")
                return response.body(), mime
            if mime not in {"text/html", "application/xhtml+xml"}:
                raise ValueError("Expected chapter HTML; received an unsupported response.")
            return response.text()
        finally:
            response.dispose()


def discover(request, book_url):
    origin, base, book_id = book_address(book_url)
    api = f"{origin}/api/v2/epubs/urn:orm:book:{quote(book_id, safe='')}/"
    info = fetch(request, api, "json")
    spine = proxy_url(info["spine"], api, origin)
    files = proxy_url(info["files"], api, origin)
    toc_url = proxy_url(info["table_of_contents"], api, origin)
    if spine != api + "spine/" or files != api + "files/" or toc_url != api + "table-of-contents/":
        raise ValueError("Book metadata points outside the expected book endpoints.")
    chapters, visited = [], set()
    next_url = spine
    expected = None
    while next_url:
        next_url = proxy_url(next_url, spine, origin)
        if next_url.split("?", 1)[0] != spine or next_url in visited:
            raise ValueError("Unexpected or repeated chapter-list URL.")
        visited.add(next_url)
        data = fetch(request, next_url, "json")
        if not isinstance(data, dict) or not isinstance(data.get("results"), list):
            raise ValueError("Unsupported chapter-list format.")
        expected = data["count"] if expected is None else expected
        chapters.extend(data["results"])
        next_url = data.get("next")
    if not chapters or len(chapters) != expected:
        raise ValueError("The chapter list is empty or incomplete.")
    references = [c["reference_id"] for c in chapters]
    if len(set(references)) != len(references):
        raise ValueError("The chapter list contains duplicate files.")
    toc = fetch(request, toc_url, "json")
    if not isinstance(toc, list) or not toc:
        raise ValueError("The table of contents is empty or unsupported.")

    def check_toc(entries):
        for entry in entries:
            if entry["reference_id"] not in references:
                raise ValueError("A contents entry is missing from the chapter list.")
            check_toc(entry.get("children") or [])

    check_toc(toc)
    result = []
    for i, chapter in enumerate(chapters, 1):
        reference = chapter["reference_id"]
        if not reference.startswith(book_id + "-/"):
            raise ValueError("Chapter reference points outside this book.")
        filename = reference[len(book_id) + 2:]
        if filename.startswith("/") or ".." in Path(filename).parts or urlsplit(filename).scheme:
            raise ValueError("Unexpected chapter filename.")
        content = urljoin(files, quote(filename, safe="/"))
        result.append({
            "order": i, "title": chapter["title"], "filename": filename,
            "source_url": urljoin(base, quote(filename, safe="/")),
            "content_url": content, "asset_base": content,
            "file": f"{i:03d}.md", "complete": False,
        })
    return {"book_id": book_id, "title": info["title"], "source_url": base,
            "expected_chapters": expected, "toc": toc, "chapters": result}


def convert(html, chapter, request, output, origin):
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    if soup.select_one('input[type="password"], .paywall, #challenge-form') or re.search(
        r"sign in|log in|login|access denied|verify you are human|just a moment", title, re.I
    ):
        raise ValueError("Received a login or access-block page instead of a chapter.")
    root = soup.select_one("#sbo-rt-content") or soup.body or soup
    for element in root.select("script, style, nav, button, form, noscript"):
        element.decompose()
    for svg in root.select("svg"):
        if svg.select_one("image"):
            for image in svg.select("image"):
                image.name = "img"
                image["src"] = image.get("href") or image.get("xlink:href", "")
            svg.unwrap()
    if not root.get_text(strip=True) and not root.select_one("img[src]"):
        raise ValueError("The chapter is empty.")
    assets = []
    for img in root.select("img"):
        src = img.get("data-src") or img.get("src")
        if not src:
            raise ValueError("An image has no source URL.")
        url = proxy_url(src, chapter["asset_base"], origin)
        content, mime = fetch(request, url, "image")
        extension = {"image/jpeg": "jpg", "image/svg+xml": "svg"}.get(mime, mime.split("/")[1])
        if not re.fullmatch(r"[a-z0-9]+", extension):
            raise ValueError("Unsupported image format.")
        local = "images/" + hashlib.sha256(content).hexdigest()[:20] + "." + extension
        write(output / local, content)
        assets.append({"file": local, "sha256": hashlib.sha256(content).hexdigest()})
        img["src"] = local
    for link in root.select("a[href]"):
        href = link["href"]
        if urlsplit(href).scheme in {"", "http", "https"}:
            link["href"] = urljoin(chapter["source_url"], href)
        elif urlsplit(href).scheme != "mailto":
            del link["href"]
    body = markdownify(str(root), heading_style="ATX", bullets="-", strip_pre=None,
                       keep_inline_images_in=["td", "th", "h1", "h2", "h3"])
    if not body.strip():
        raise ValueError("Markdown conversion produced no content.")
    metadata = {"title": chapter["title"], "source_url": chapter["source_url"], "order": chapter["order"]}
    front = "---\n" + "\n".join(f"{key}: {json.dumps(value, ensure_ascii=False)}" for key, value in metadata.items()) + "\n---\n\n"
    return front + body.strip() + "\n", assets


def valid_file(output, record):
    path = output / record["file"]
    return path.is_file() and path.stat().st_size > 0 and hashlib.sha256(path.read_bytes()).hexdigest() == record.get("sha256")


def chapter_complete(output, chapter):
    return chapter.get("complete") and valid_file(output, chapter) and all(
        valid_file(output, asset) for asset in chapter.get("images", [])
    )


def combined(manifest, output):
    text = f"# {manifest['title']}\n\nSource: {manifest['source_url']}\n"
    for chapter in manifest["chapters"]:
        body = (output / chapter["file"]).read_text(encoding="utf-8").split("\n---\n", 1)[1].strip()
        text += f"\n---\n\n## {chapter['title']}\n\nSource: {chapter['source_url']}\n\n{body}\n"
    return text


def export(request, book_url, output, limit):
    manifest = discover(request, book_url)
    path = output / "manifest.json"
    if path.exists():
        old = json.loads(path.read_text(encoding="utf-8"))
        if old["source_url"] != manifest["source_url"]:
            raise ValueError("The output folder belongs to a different book or host.")
        previous = {c["source_url"]: c for c in old["chapters"]}
        for chapter in manifest["chapters"]:
            saved = previous.get(chapter["source_url"])
            if saved and all(saved.get(k) == chapter[k] for k in ("file", "title", "content_url")) and chapter_complete(output, saved):
                chapter.update({k: saved[k] for k in ("complete", "sha256", "images")})
    save_json(path, manifest)
    if not all(chapter_complete(output, c) for c in manifest["chapters"]):
        (output / "book.md").unlink(missing_ok=True)
    count = 0
    for chapter in manifest["chapters"]:
        if chapter_complete(output, chapter):
            continue
        if limit is not None and count >= limit:
            break
        print(f"Exporting chapter file {chapter['order']}/{manifest['expected_chapters']}", flush=True)
        html = fetch(request, chapter["content_url"], "html")
        markdown, images = convert(html, chapter, request, output, book_address(book_url)[0])
        write(output / chapter["file"], markdown)
        chapter.update(complete=True, images=images, sha256=hashlib.sha256(markdown.encode("utf-8")).hexdigest())
        save_json(path, manifest)
        count += 1
        time.sleep(1)
    complete = sum(bool(chapter_complete(output, c)) for c in manifest["chapters"])
    if complete == manifest["expected_chapters"]:
        write(output / "book.md", combined(manifest, output))
        print(f"Complete: {complete} chapter files and book.md in {output}")
    else:
        print(f"Partial export: {complete}/{manifest['expected_chapters']}. Rerun without --limit to finish.")


def verify(output):
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    chapters = manifest["chapters"]
    if not chapters or len(chapters) != manifest["expected_chapters"]:
        raise ValueError("The manifest has an incomplete chapter list.")
    missing = [str(c["order"]) for c in chapters if not chapter_complete(output, c)]
    if missing:
        raise ValueError("Missing or changed chapters/images: " + ", ".join(missing))
    book = output / "book.md"
    if not book.is_file() or book.read_text(encoding="utf-8") != combined(manifest, output):
        raise ValueError("book.md is missing or outdated. Rerun export to rebuild it.")
    print(f"Verified {len(chapters)} chapter files, their images, and book.md against the saved manifest.")


def login(playwright, book_url, cookies):
    STATE.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    STATE.parent.chmod(0o700)
    if cookies:
        state = json.loads(cookies.read_text(encoding="utf-8"))
        if isinstance(state, list):
            clean = []
            for cookie in state:
                item = {k: cookie[k] for k in ("name", "value", "domain", "path", "secure", "httpOnly", "expires") if k in cookie}
                item.setdefault("path", "/")
                if not cookie.get("session") and "expirationDate" in cookie:
                    item["expires"] = cookie["expirationDate"]
                item["sameSite"] = {"strict": "Strict", "lax": "Lax", "none": "None", "no_restriction": "None"}.get(str(cookie.get("sameSite")).lower(), "Lax")
                clean.append(item)
            state = {"cookies": clean, "origins": []}
        if not isinstance(state, dict) or not isinstance(state.get("cookies"), list):
            raise ValueError("Use a browser cookie JSON array or Playwright storage-state JSON.")
        save_json(STATE, state)
    else:
        browser = playwright.chromium.launch(channel="chrome", headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto(book_url, wait_until="domcontentloaded", timeout=60000)
        input("Log in and open a readable chapter in the browser, then press Enter here: ")
        save_json(STATE, context.storage_state(indexed_db=True))
        browser.close()
    STATE.chmod(0o600)
    print("Saved login locally. Run export --limit 1 to check access and formatting.")


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description="Export an accessible O'Reilly book to Markdown.")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("login", "export", "verify"):
        command = commands.add_parser(name)
        if name != "verify":
            command.add_argument("--book-url", default=BOOK_URL)
        if name != "login":
            command.add_argument("--out", type=Path, default=ROOT / "output/9781835881408")
        if name == "login":
            command.add_argument("--cookies", type=Path, help="Local cookie JSON array or Playwright storage-state JSON")
        if name == "export":
            command.add_argument("--limit", type=int, help="Maximum new chapter files this run (1 for a trial)")
    args = parser.parse_args()
    if args.command == "export" and args.limit is not None and args.limit < 1:
        parser.error("--limit must be positive")
    try:
        if args.command == "verify":
            verify(args.out)
            return
        book_address(args.book_url)
        with sync_playwright() as playwright:
            if args.command == "login":
                login(playwright, args.book_url, args.cookies)
            else:
                if not STATE.exists():
                    raise ValueError("No saved login. Run the login command first.")
                request = playwright.request.new_context(storage_state=str(STATE))
                try:
                    export(request, args.book_url, args.out, args.limit)
                finally:
                    request.dispose()
    except (ValueError, OSError) as error:
        print(f"Stopped: {error}", file=sys.stderr)
        sys.exit(1)
    except (KeyError, TypeError):
        print("Stopped: unsupported metadata or saved state format; the API may have changed.", file=sys.stderr)
        sys.exit(1)
    except PlaywrightError:
        print("Stopped: browser or request failed. Check Chrome installation, network, and saved login.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
