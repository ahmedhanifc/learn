# O’Reilly book exporter plan

- **Goal:** Export *ROS 2 from Scratch* (`9781835881408`) into chapter Markdown files and one combined `book.md` for AI indexing.
- **Tools:** Use Python, [Playwright](https://playwright.dev/python/docs/auth) for browser access, Beautiful Soup for cleanup, and [Markdownify](https://github.com/matthewwithanm/python-markdownify) for conversion.
- **Login:** Open a dedicated browser for university login, then save its cookies and browser storage locally. Support importing cookies. Keep authentication files out of Git and logs.
- **First check:** Export one chapter through your library proxy. Confirm login reuse, content loading, and extraction before exporting everything.
- **Find pages:** Collect all table-of-contents links in order, including front matter and appendices. Remove duplicates and stay within this book.
- **Save content:** Remove reader controls; preserve headings, code indentation, tables, and links. Download images and rewrite their paths.
- **Track progress:** Record chapter titles, source URLs, order, and completion in `manifest.json`. Save safely, resume interruptions, and retry temporary failures with delays. Stop for expired login or access blocks.
- **Check results:** Compare output against the contents list; reject empty pages and login screens. Test missing chapters, code formatting, images, and resume behavior.
- **Deliver:** Provide `login`, `export`, and `verify` commands with setup instructions. Keep AI indexing separate.
