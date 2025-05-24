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
python clone.py
```

**Example:**
```
Enter URL: github.com/login
Downloading...
✅ Saved to: sites/github_com
```

## Output Structure

Downloaded sites are organized as follows:
```
sites/
└── github_com/
    ├── github_com.htm          # Main HTML file
    └── github_com_files/        # Assets folder
        ├── style.css
        ├── script.js
        ├── logo.png
        └── favicon.ico
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
