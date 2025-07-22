from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os
import sys

def mirror(url):
    slug = url.replace('://', '_').replace('/', '_')
    folder = f'mirror_{slug}'
    os.makedirs(folder, exist_ok=True)

    options = Options()
    options.headless = True
    driver = webdriver.Chrome(options=options)
    driver.get(url)

    # Save HTML
    with open(os.path.join(folder, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(driver.page_source)

    # Save screenshot
    driver.save_screenshot(os.path.join(folder, 'screenshot.png'))

    print(f'✅ Done – open {folder}/index.html')
    driver.quit()

if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit('Usage: python mirror_selenium.py <url>')
    mirror(sys.argv[1])
