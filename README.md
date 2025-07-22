## Website Cloner

- Complete webpage download including all assets
- Preserves original HTML structure and formatting
- Downloads CSS files and processes internal references
- Handles images, scripts, and other linked resources
- Organized folder structure: `sites/domain_name/`
- Clean console interface with minimal output
- Firefox-compatible headers for accurate downloads

## Installation

1. Clone this repository:
```bash
git clone https://github.com/zebbern/website-clone
cd website-clone
```

## Usage

Run the script and enter the URL when prompted:

```bash
python clone.py https://example.com/login
```

Then host the folder
```
python -m http.server 8000

¤¤ Example: python -m http.server 8000 --directory /mirror_https_github.com_login/

then go to http://localhost:8000/ in browser to see page
```

## How It Works

1. Downloads the main HTML page while preserving exact structure
2. Parses HTML using regex to find resource links
3. Downloads all CSS stylesheets and processes internal URLs
4. Downloads images, JavaScript files, and other assets
5. Updates all links to point to local files
6. Saves everything in an organized folder structure

## Use Cases

- Web archival and research
- Offline browsing and documentation
- Website backup and preservation
- Web development reference
- Educational purposes

## Requirements

- Python 3.6+
- requests library
- Internet connection for downloading

## Technical Details

- Uses Firefox-compatible user agent and headers
- Processes CSS @import statements and url() references
- Handles relative and absolute URLs correctly
- Maintains original HTML formatting and structure
- Silent operation with minimal console output

## Disclaimer

This tool is intended for legitimate purposes such as web archival, research, and backup. Users are responsible for respecting website terms of service and copyright laws when using this tool.
