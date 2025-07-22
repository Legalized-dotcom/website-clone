#!/usr/bin/env python3
"""
Developed by: https://github.com/zebbern
Works for most tasks
"""

import asyncio, re, sys, pathlib, urllib.parse
from playwright.async_api import async_playwright


def fix_real_links(html: str, base_url: str) -> str:
    """
    Rewrite only the <a href="..."> that are actual navigation links
    and would otherwise become file:// when opened locally.
    """

    base = urllib.parse.urlparse(base_url)._replace(params='', query='', fragment='').geturl()

    def _abs(match):
        pre, q, url, post = match.group(1, 2, 3, 4)

        # Skip absolute URLs, mailto:, javascript:, fragments, etc.
        if re.match(r'^(https?://|mailto:|javascript:|#)', url, re.I):
            return match.group(0)

        abs_url = urllib.parse.urljoin(base, url)
        return f'{pre}{q}{abs_url}{q}{post}'

    # Only touch <a … href="…">
    return re.sub(r'(<a\b[^>]*\bhref=)(["\']?)([^"\'\s>]+)\2([^>]*>)', _abs, html, flags=re.I)


async def mirror(url: str):
    slug = re.sub(r'[^\w._-]', '_', url.replace('://', '_'))
    folder = pathlib.Path('mirror_' + slug)
    folder.mkdir(exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, wait_until='domcontentloaded')
        await page.wait_for_load_state('networkidle')
        await page.wait_for_timeout(500)  # short cushion for late JS

        html = await page.content()
        html = fix_real_links(html, url)

        (folder / 'index.html').write_text(html, encoding='utf-8')

        # Keep downloading assets so the page still looks right
        await page.route('**/*', lambda route: route.continue_())
        await page.wait_for_load_state('networkidle')

        await page.screenshot(path=folder / 'screenshot.png', full_page=True)
        await browser.close()

    print(f'✅  Clean mirror ready – open {folder.absolute()}/index.html')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit('Usage: python mirror_clean.py <url>')
    asyncio.run(mirror(sys.argv[1]))
