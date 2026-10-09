import base64
import io
import json
import tempfile
import threading
import unittest
from collections import Counter
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

from playwright.sync_api import sync_playwright

import oreilly_export as exporter


class ExportTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.hits = Counter()
        cls.routes = {}

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                cls.hits[self.path] += 1
                if self.headers.get("Cookie") != "session=test-only":
                    status, mime, body = 403, "text/plain", b"Login required"
                else:
                    status, mime, body = cls.routes.get(self.path, (404, "text/plain", b"Missing"))
                self.send_response(status)
                self.send_header("Content-Type", mime)
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args):
                pass

        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.origin = f"http://127.0.0.1:{cls.server.server_port}"
        cls.book_url = cls.origin + "/library/view/test/123/"
        cls.api = "/api/v2/epubs/urn:orm:book:123/"
        cls.files = cls.api + "files/"
        cls.playwright = sync_playwright().start()

    @classmethod
    def tearDownClass(cls):
        cls.playwright.stop()
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def setUp(self):
        self.hits.clear()
        self.routes.clear()
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.output = Path(self.temp.name)
        self.request = self.playwright.request.new_context(storage_state={
            "cookies": [{"name": "session", "value": "test-only", "domain": "127.0.0.1", "path": "/", "expires": -1, "httpOnly": True, "secure": False, "sameSite": "Lax"}],
            "origins": [],
        })
        self.addCleanup(self.request.dispose)
        self.addCleanup(patch.stopall)
        patch.object(exporter.time, "sleep").start()
        patch("sys.stdout", new=io.StringIO()).start()
        self.json(self.api, {"title": "Test book", "spine": self.origin + self.api + "spine/",
                             "files": self.origin + self.files, "table_of_contents": self.origin + self.api + "table-of-contents/"})
        self.chapters = [{"title": title, "reference_id": "123-/" + name}
                         for title, name in [("Preface", "preface.xhtml"), ("Chapter 1", "ch1.xhtml")]]
        self.json(self.api + "spine/", {"count": 2, "results": self.chapters[:1], "next": "?page=2"})
        self.json(self.api + "spine/?page=2", {"count": 2, "results": self.chapters[1:], "next": None})
        self.json(self.api + "table-of-contents/", [
            {"title": "Preface", "reference_id": "123-/preface.xhtml", "children": []},
            {"title": "Chapter 1", "reference_id": "123-/ch1.xhtml", "children": [
                {"title": "Code", "reference_id": "123-/ch1.xhtml", "fragment": "code", "children": []}]}])
        self.html("preface.xhtml", "<html><body><h1>Preface</h1><p>Welcome.</p></body></html>")
        self.html("ch1.xhtml", '''<html><body><nav>Reader controls</nav><div id="sbo-rt-content">
        <h1>Chapter 1</h1><pre><code>def hello():\n    print("hello")\n</code></pre>
        <table><tr><th>Name</th><th>Value</th></tr><tr><td>Speed</td><td>2</td></tr></table>
        <a href="preface.xhtml#start">Preface</a><img src="robot.png" alt="Robot">
        </div></body></html>''')
        self.routes[self.files + "robot.png"] = (200, "image/png", base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a3ZkAAAAASUVORK5CYII="))

    def json(self, path, value):
        self.routes[path] = (200, "application/json", json.dumps(value).encode())

    def html(self, filename, text):
        self.routes[self.files + filename] = (200, "text/html", text.encode())

    def run_export(self, limit=None):
        exporter.export(self.request, self.book_url, self.output, limit)

    def test_current_epub_api_without_legacy_routes(self):
        self.run_export(limit=1)
        self.assertEqual(self.hits["/api/v1/book/123/"], 0)
        self.assertEqual(self.hits[self.api + "spine/?page=2"], 1)
        manifest = json.loads((self.output / "manifest.json").read_text())
        self.assertEqual([c["filename"] for c in manifest["chapters"]], ["preface.xhtml", "ch1.xhtml"])
        self.assertTrue((self.output / "001.md").is_file())

    def test_trial_resume_formatting_and_repair(self):
        self.run_export(limit=1)
        self.assertTrue((self.output / "001.md").exists())
        self.assertFalse((self.output / "book.md").exists())
        with self.assertRaisesRegex(ValueError, "Missing or changed"):
            exporter.verify(self.output)
        self.run_export()
        exporter.verify(self.output)
        chapter = (self.output / "002.md").read_text()
        self.assertIn('def hello():\n    print("hello")', chapter)
        self.assertIn("```", chapter)
        self.assertIn("| Speed | 2 |", chapter)
        self.assertIn(self.book_url + "preface.xhtml#start", chapter)
        self.assertIn("![Robot](images/", chapter)
        self.assertNotIn("Reader controls", chapter)
        book = (self.output / "book.md").read_text()
        self.assertLess(book.index("## Preface"), book.index("## Chapter 1"))
        self.assertNotIn("order:", book)
        self.assertEqual(self.hits[self.files + "preface.xhtml"], 1)
        self.run_export()
        self.assertEqual(self.hits[self.files + "ch1.xhtml"], 1)
        image = next((self.output / "images").iterdir())
        image.unlink()
        with self.assertRaisesRegex(ValueError, "Missing or changed"):
            exporter.verify(self.output)
        self.run_export()
        self.assertEqual(self.hits[self.files + "ch1.xhtml"], 2)
        (self.output / "001.md").write_text("corrupt")
        with self.assertRaises(ValueError):
            exporter.verify(self.output)
        self.run_export()
        exporter.verify(self.output)
        (self.output / "book.md").write_text("outdated")
        with self.assertRaisesRegex(ValueError, "outdated"):
            exporter.verify(self.output)

    def test_missing_chapter_and_toc_entries(self):
        self.json(self.api + "spine/?page=2", {"count": 2, "results": [], "next": None})
        with self.assertRaisesRegex(ValueError, "incomplete"):
            self.run_export()
        self.json(self.api + "spine/?page=2", {"count": 2, "results": self.chapters[1:], "next": None})
        self.json(self.api + "table-of-contents/", [{"reference_id": "123-/missing.xhtml"}])
        with self.assertRaisesRegex(ValueError, "contents entry"):
            self.run_export()

    def test_reject_login_and_access_blocks(self):
        self.html("preface.xhtml", '<html><title>Sign in</title><body><input type="password"></body></html>')
        with self.assertRaisesRegex(ValueError, "login"):
            self.run_export()
        self.assertFalse((self.output / "001.md").exists())
        for status in (401, 403, 429):
            with self.subTest(status=status):
                self.routes[self.api] = (status, "text/html", b"Blocked")
                before = self.hits[self.api]
                with self.assertRaisesRegex(ValueError, str(status)):
                    self.run_export()
                self.assertEqual(self.hits[self.api] - before, 1)

    def test_reject_bad_images_empty_chapters_and_pagination_loops(self):
        self.routes[self.files + "robot.png"] = (200, "text/html", b"Please log in")
        with self.assertRaisesRegex(ValueError, "non-image"):
            self.run_export()
        self.assertFalse((self.output / "002.md").exists())
        self.html("ch1.xhtml", "<html><body><script>loader()</script></body></html>")
        with self.assertRaisesRegex(ValueError, "empty"):
            self.run_export()
        self.json(self.api + "spine/?page=2", {"count": 2, "results": self.chapters[1:], "next": "?page=2"})
        with self.assertRaisesRegex(ValueError, "repeated"):
            self.run_export()

    def test_server_errors_retry_then_stop(self):
        self.routes[self.api] = (503, "text/plain", b"Temporary failure")
        with self.assertRaisesRegex(ValueError, "503"):
            self.run_export()
        self.assertEqual(self.hits[self.api], 3)

    def test_import_cookies_and_proxy_mapping(self):
        cookie_file = self.output / "cookies.json"
        cookie_file.write_text(json.dumps([{"name": "session", "value": "test-only", "domain": "127.0.0.1", "path": "/", "sameSite": "no_restriction", "expirationDate": 2000000000}]))
        state_file = self.output / ".auth/state.json"
        with patch.object(exporter, "STATE", state_file):
            exporter.login(self.playwright, self.book_url, cookie_file)
        state = json.loads(state_file.read_text())
        self.assertEqual(state["cookies"][0]["sameSite"], "None")
        self.assertEqual(state["cookies"][0]["expires"], 2000000000)
        self.assertEqual(state_file.stat().st_mode & 0o777, 0o600)
        self.assertEqual(state_file.parent.stat().st_mode & 0o777, 0o700)
        self.assertEqual(exporter.proxy_url("https://learning.oreilly.com" + self.api, self.book_url, self.origin), self.origin + self.api)


if __name__ == "__main__":
    unittest.main()
