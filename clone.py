#!/usr/bin/env python3
"""
Developed by: https://github.com/zebbern
"""

import os
import requests
from urllib.parse import urljoin, urlparse, unquote
import re

class CleanFirefoxDownloader:
    def __init__(self, url):
        self.url = url
        self.session = requests.Session()
        
        # Firefox headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })
        
        # Set up folder structure: sites/domain_name/
        parsed_url = urlparse(url)
        domain_name = parsed_url.netloc.replace('www.', '').replace('.', '_')
        
        self.site_folder = os.path.join("sites", domain_name)
        self.html_filename = f"{domain_name}.htm"
        self.assets_folder_name = f"{domain_name}_files"
        self.html_path = os.path.join(self.site_folder, self.html_filename)
        self.assets_folder = os.path.join(self.site_folder, self.assets_folder_name)
        
        # Track downloads
        self.downloaded_assets = {}
        self.url_mapping = {}
        
    def _get_filename_from_url(self, url):
        """Get safe filename from URL"""
        parsed = urlparse(url)
        filename = os.path.basename(parsed.path) or 'index.html'
        filename = unquote(filename)
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # Handle duplicates
        if filename in self.downloaded_assets.values():
            name, ext = os.path.splitext(filename)
            counter = len([v for v in self.downloaded_assets.values() if v.startswith(name)])
            filename = f"{name}_{counter}{ext}"
        
        return filename
    
    def _download_asset(self, url):
        """Download asset silently"""
        if url in self.url_mapping:
            return self.url_mapping[url]
            
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            local_filename = self._get_filename_from_url(url)
            local_path = os.path.join(self.assets_folder, local_filename)
            
            os.makedirs(self.assets_folder, exist_ok=True)
            
            with open(local_path, 'wb') as f:
                f.write(response.content)
            
            self.downloaded_assets[url] = local_filename
            self.url_mapping[url] = local_filename
            return local_filename
            
        except:
            return None
    
    def _download_css_and_process(self, css_url):
        """Download CSS and process its internal URLs"""
        try:
            response = self.session.get(css_url, timeout=30)
            response.raise_for_status()
            css_content = response.text
            
            # Process @import statements
            import_pattern = r'@import\s+(?:url\()?["\']?([^"\')\s]+)["\']?\)?[^;]*;'
            def replace_import(match):
                import_url = match.group(1)
                if import_url.startswith('data:'):
                    return match.group(0)
                absolute_url = urljoin(css_url, import_url)
                local_filename = self._download_css_and_process(absolute_url)
                if local_filename:
                    return match.group(0).replace(import_url, local_filename)
                return match.group(0)
            
            css_content = re.sub(import_pattern, replace_import, css_content)
            
            # Process url() statements  
            url_pattern = r'url\s*\(\s*["\']?([^"\')\s]+)["\']?\s*\)'
            def replace_url(match):
                url = match.group(1)
                if url.startswith('data:'):
                    return match.group(0)
                absolute_url = urljoin(css_url, url)
                local_filename = self._download_asset(absolute_url)
                if local_filename:
                    return match.group(0).replace(url, local_filename)
                return match.group(0)
            
            css_content = re.sub(url_pattern, replace_url, css_content)
            
            # Save processed CSS
            local_filename = self._get_filename_from_url(css_url)
            local_path = os.path.join(self.assets_folder, local_filename)
            
            with open(local_path, 'w', encoding='utf-8') as f:
                f.write(css_content)
                
            self.url_mapping[css_url] = local_filename
            return local_filename
            
        except:
            return None
    
    def download(self):
        """Download webpage silently"""
        try:
            # Create site folder
            os.makedirs(self.site_folder, exist_ok=True)
            
            # Download main HTML
            response = self.session.get(self.url, timeout=30)
            response.raise_for_status()
            html_content = response.text
            
            # Process CSS links
            css_pattern = r'<link[^>]+rel=["\']stylesheet["\'][^>]*href=["\']([^"\']+)["\'][^>]*>'
            def process_css_link(match):
                full_link = match.group(0)
                css_url = match.group(1)
                
                if css_url.startswith(('http://', 'https://')):
                    absolute_url = css_url
                else:
                    absolute_url = urljoin(self.url, css_url)
                
                local_filename = self._download_css_and_process(absolute_url)
                if local_filename:
                    new_href = f"{self.assets_folder_name}/{local_filename}"
                    return full_link.replace(css_url, new_href)
                return full_link
            
            html_content = re.sub(css_pattern, process_css_link, html_content, flags=re.IGNORECASE)
            
            # Process images
            img_pattern = r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>'
            def process_img(match):
                full_img = match.group(0)
                img_url = match.group(1)
                
                if img_url.startswith('data:'):
                    return full_img
                    
                if img_url.startswith(('http://', 'https://')):
                    absolute_url = img_url
                else:
                    absolute_url = urljoin(self.url, img_url)
                
                local_filename = self._download_asset(absolute_url)
                if local_filename:
                    new_src = f"{self.assets_folder_name}/{local_filename}"
                    return full_img.replace(img_url, new_src)
                return full_img
            
            html_content = re.sub(img_pattern, process_img, html_content, flags=re.IGNORECASE)
            
            # Process scripts
            script_pattern = r'<script[^>]+src=["\']([^"\']+)["\'][^>]*>'
            def process_script(match):
                full_script = match.group(0)
                script_url = match.group(1)
                
                if script_url.startswith(('http://', 'https://')):
                    absolute_url = script_url
                else:
                    absolute_url = urljoin(self.url, script_url)
                
                local_filename = self._download_asset(absolute_url)
                if local_filename:
                    new_src = f"{self.assets_folder_name}/{local_filename}"
                    return full_script.replace(script_url, new_src)
                return full_script
            
            html_content = re.sub(script_pattern, process_script, html_content, flags=re.IGNORECASE)
            
            # Process other links (icons, manifests, etc.)
            link_pattern = r'<link[^>]+href=["\']([^"\']+)["\'][^>]*>'
            def process_link(match):
                full_link = match.group(0)
                link_url = match.group(1)
                
                if ('stylesheet' in full_link.lower() or 
                    link_url.startswith(('mailto:', 'tel:', '#', 'javascript:')) or
                    'dns-prefetch' in full_link or 'preconnect' in full_link):
                    return full_link
                
                if any(rel in full_link.lower() for rel in ['icon', 'manifest', 'apple-touch']):
                    if link_url.startswith(('http://', 'https://')):
                        absolute_url = link_url
                    else:
                        absolute_url = urljoin(self.url, link_url)
                    
                    local_filename = self._download_asset(absolute_url)
                    if local_filename:
                        new_href = f"{self.assets_folder_name}/{local_filename}"
                        return full_link.replace(link_url, new_href)
                
                return full_link
            
            html_content = re.sub(link_pattern, process_link, html_content, flags=re.IGNORECASE)
            
            # Save HTML file
            with open(self.html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return True
            
        except Exception as e:
            print(f"Error: {e}")
            return False

def main():
    url = input("Enter URL: ").strip()
    
    if not url:
        print("No URL provided!")
        return
    
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    print("Downloading...")
    
    downloader = CleanFirefoxDownloader(url)
    success = downloader.download()
    
    if success:
        print(f"✅ Saved to: {downloader.site_folder}")
    else:
        print("❌ Download failed")

if __name__ == "__main__":
    main()