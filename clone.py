#!/usr/bin/env python3
"""
mirror_offline.py
Fully-offline mirror of a web page.
Usage:  python mirror_offline.py https://example.com
Creates ./mirror_<sanitized_url>/index.html  (+ assets/)
"""
import os
import sys
import re
import json
import mimetypes
from urllib.parse import urljoin, urlparse
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

HEADERS = {'User-Agent': 'Mozilla/5.0 (mirror script)'}

def mirror(url: str):
    slug = url.replace('://', '_').replace('/', '_')
    root_dir = f'mirror_{slug}'
    assets_dir = os.path.join(root_dir, 'assets')
    os.makedirs(assets_dir, exist_ok=True)

    # --- Selenium session ----------------------------------------------------
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--log-level=3')
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

    driver = webdriver.Chrome(options=options)
    driver.get(url)
    driver.implicitly_wait(3)

    # -------------------------------------------------------------------------
    # 1. Collect URLs from Chrome performance log
    resource_urls = set()
    for entry in driver.get_log('performance'):
        try:
            msg = json.loads(entry['message'])['message']
            if msg.get('method') == 'Network.requestWillBeSent':
                req_url = msg.get('params', {}).get('request', {}).get('url', '')
                if req_url.startswith('http'):
                    resource_urls.add(req_url)
        except Exception:
            continue

    # 2. Also scrape final DOM for <img src>, <link href>, etc.
    html = driver.page_source
    for attr in re.findall(
        r'(?:src|href|poster|action|data-src)\s*=\s*["\'](.*?)["\']',
        html,
        flags=re.I
    ):
        abs_url = urljoin(url, attr)
        if abs_url.startswith('http'):
            resource_urls.add(abs_url)

    # 3. JS-side performance entries (XHR/fetch that happened after load)
    entries = driver.execute_script(
        'return window.performance.getEntriesByType("resource").map(e=>e.name)'
    )
    for u in entries:
        if u.startswith('http'):
            resource_urls.add(u)

    # -------------------------------------------------------------------------
    # Download each resource and remember local path
    url_to_local = {}
    for remote_url in sorted(resource_urls):
        parsed = urlparse(remote_url)
        path = parsed.path.lstrip('/') or 'index'
        local_path = os.path.join(assets_dir, parsed.netloc, path)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)

        # Add extension if missing
        try:
            ctype = requests.head(
                remote_url, headers=HEADERS, allow_redirects=True, timeout=10
            ).headers.get('content-type', '').split(';')[0]
            ext = mimetypes.guess_extension(ctype) or ''
            if not local_path.lower().endswith(ext.lower()):
                local_path += ext
        except Exception:
            pass

        if os.path.exists(local_path):
            url_to_local[remote_url] = os.path.relpath(
                local_path, root_dir
            ).replace(os.sep, '/')
            continue

        print('⬇', remote_url)
        try:
            r = requests.get(remote_url, headers=HEADERS, stream=True, timeout=20)
            r.raise_for_status()
            with open(local_path, 'wb') as f:
                for chunk in r.iter_content(8192):
                    f.write(chunk)
            url_to_local[remote_url] = os.path.relpath(
                local_path, root_dir
            ).replace(os.sep, '/')
        except Exception as e:
            print('⚠ skip', remote_url, e)

    # -------------------------------------------------------------------------
    # Rewrite HTML
    def replace_url(match):
        orig = match.group(2)
        abs_url = urljoin(url, orig)
        local = url_to_local.get(abs_url, orig)
        return match.group(1) + local + match.group(3)

    html = re.sub(
        r'(\b(?:src|href|poster|action)\s*=\s*["\'])(.*?)(["\'])',
        replace_url,
        html,
        flags=re.I,
    )
    html = re.sub(
        r'(?i)(url\(["\']?)(.*?)["\']?\)',
        lambda m: 'url('
        + url_to_local.get(urljoin(url, m.group(2)), m.group(2))
        + ')',
        html,
    )

    with open(os.path.join(root_dir, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(html)

    driver.save_screenshot(os.path.join(root_dir, 'screenshot.png'))
    driver.quit()
    print(f'✅ Offline mirror ready:  {root_dir}/index.html')

# -----------------------------------------------------------------------------

if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit('Usage: python mirror_offline.py <url>')
    mirror(sys.argv[1])
