#!/usr/bin/env python3
"""
mirror_full.py
Create a *complete* local mirror of any page.
- Saves every asset exactly as-is (no URL rewriting).
- Re-creates the original folder structure under ./mirror_<sanitized_url>
- Serves perfectly from a local HTTP server.

usage:  python mirror_full.py https://www.instagram.com/accounts/login/
"""

import asyncio
import re
import sys
import pathlib
import urllib.parse
import traceback
from playwright.async_api import async_playwright


async def mirror(url: str) -> None:
    # 1. Prepare output folder
    slug = re.sub(r'[^\w._-]', '_', url.replace('://', '_'))
    root = pathlib.Path('mirror_' + slug)
    root.mkdir(exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # 2. Optional: log every request so the user sees progress
        def log_request(req):
            print("→", req.method, req.url)

        page.on("request", log_request)

        # 3. Intercept and save every response
        async def save_all(route):
            try:
                response = await route.fetch()
                body = await response.body()

                parsed = urllib.parse.urlparse(response.url)
                rel_path = parsed.path.lstrip('/') or "index.html"
                if rel_path.endswith('/'):
                    rel_path += "index.html"

                local_file = root / rel_path
                local_file.parent.mkdir(parents=True, exist_ok=True)
                local_file.write_bytes(body)

                # Let the browser continue
                await route.continue_()
            except Exception as exc:
                # Network-level errors (404, CORS, etc.) – keep going
                print("!!", exc)
                await route.continue_()

        await page.route("**/*", save_all)

        # 4. Navigate with a timeout so we never hang forever
        print("🚀  Loading", url)
        await page.goto(url, timeout=60_000)        # 60 s max
        await page.wait_for_load_state("domcontentloaded")
        print("✅  DOM ready")

        # 5. Small pause for late XHR/fetch
        await asyncio.sleep(3)

        await browser.close()
        print("✅  Mirror complete – serve with:")
        print(f"   python -m http.server 8000 --directory {root.absolute()}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Usage: python mirror_full.py <url>")
    asyncio.run(mirror(sys.argv[1]))
