# O'Reilly → Markdown

Exports chapter files, images, source metadata, and a combined `book.md`. Defaults to *ROS 2 from Scratch* through your university proxy.

From this repository:

```bash
python3 -m venv scripts/.venv
scripts/.venv/bin/pip install -r scripts/requirements.txt
scripts/.venv/bin/python scripts/oreilly_export.py login
scripts/.venv/bin/python scripts/oreilly_export.py export --limit 1
# Inspect scripts/output/9781835881408/001.md, then continue:
scripts/.venv/bin/python scripts/oreilly_export.py export
scripts/.venv/bin/python scripts/oreilly_export.py verify
```

Requires installed Google Chrome, network access, and your book login. Sign in yourself in the opened browser. Alternatively, use `login --cookies scripts/.auth/cookies.json` with a cookie JSON array or Playwright storage-state JSON. Include university proxy cookies. Authentication stays in `.auth/`, excluded from Git; keep imported cookies there too.

Use `--book-url URL` on login/export and `--out DIRECTORY` on export/verify for another book. Rerunning resumes checked files. `book.md` is written only after every chapter succeeds. Verification checks saved contents, files, and image hashes; it does not prove the online edition is unchanged. AI indexing is separate.

Uses the reader's `/api/v2/epubs/` metadata, paginated spine (reading order), and table of contents with [Playwright authentication](https://playwright.dev/python/docs/auth). The old `/api/v1/book/` route returns 404 for this book. Login/access blocks stop the export. Cookie-only import may be insufficient for some SSO sessions.

Source limitation: some code blocks in this book (confirmed in Chapter 4) already lack line breaks in O'Reilly's reader and HTML. The export preserves that source; it cannot recover missing formatting.

Local checks: `scripts/.venv/bin/python -m unittest discover -s scripts -p 'test_*.py' -v` (uses a temporary localhost server and fake book content).
