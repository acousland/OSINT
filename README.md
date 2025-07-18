# OSINT Web Scraper & PDF Downloader

A comprehensive Open Source Intelligence (OSINT) tool for website mapping, URL discovery, and automated PDF generation/downloading. This application provides both command-line and web interface options for crawling websites and extracting information.

## Features

- **Website Mapping**: Recursively crawl websites to discover all internal links
- **PDF Generation**: Convert web pages to PDF format for offline analysis
- **PDF Download**: Automatically download existing PDF files from discovered URLs
- **Streamlit Web UI**: User-friendly web interface for easy operation
- **Concurrent Processing**: Multi-threaded PDF downloading for improved performance
- **Organized Output**: Automatic folder structure creation based on domain names

## Installation

### Prerequisites

- Python 3.7+
- wkhtmltopdf (required for PDF generation)

### Install wkhtmltopdf

**macOS:**
```bash
brew install wkhtmltopdf
```

**Ubuntu/Debian:**
```bash
sudo apt-get install wkhtmltopdf
```

**Windows:**
Download from: https://wkhtmltopdf.org/downloads.html

### Python Dependencies

1. Clone the repository:
```bash
git clone <repository-url>
cd OSINT
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

## Usage

### Web Interface (Recommended)

Launch the Streamlit web interface:

```bash
streamlit run app.py
```

This will open a web browser with an intuitive interface where you can:
- Enter the target URL
- Set the maximum crawling depth
- Run mapping and scraping operations with visual progress indicators
- View the location where files are saved

### Command Line Interface

#### Basic Usage

Edit the `OSintel.py` file to set your target URL and parameters:

```python
START_URL = "https://example.com"
MAX_DEPTH = 1000

ms.map(START_URL, MAX_DEPTH)  # Map the website
sc.scrape(START_URL)          # Download/generate PDFs
```

Then run:
```bash
python OSintel.py
```

#### Individual Components

**Map a website only:**
```python
import mapStructure as ms
ms.map("https://example.com", max_depth=100)
```

**Scrape PDFs only (requires existing mapping):**
```python
import scrape as sc
sc.scrape("https://example.com")
```

## How It Works

### 1. Website Mapping (`mapStructure.py`)

- Starts from a given URL and recursively discovers all internal links
- Respects the specified maximum depth to prevent infinite crawling
- Uses fake user agents to avoid basic bot detection
- Saves all discovered URLs to `visited_urls.txt`
- Only processes internal links (same domain)

### 2. PDF Scraping (`scrape.py`)

- Reads the list of URLs from the mapping phase
- For each URL:
  - If it's already a PDF file: downloads it directly
  - If it's a web page: converts it to PDF using wkhtmltopdf
- Uses multi-threading (up to 10 concurrent workers) for faster processing
- Handles errors gracefully and continues with remaining URLs

### Output Structure

```
downloads/
└── domain.com/
    ├── visited_urls.txt    # List of all discovered URLs
    └── pdfs/              # Generated and downloaded PDFs
        ├── page1.pdf
        ├── document.pdf
        └── index.pdf
```

## Configuration

### Key Parameters

- **START_URL**: The initial URL to begin crawling
- **MAX_DEPTH**: Maximum depth for recursive crawling (default: 1000)
- **MAX_WORKERS**: Number of concurrent threads for PDF downloading (default: 10)

### Customization

You can modify the following in the source files:

- **User Agents**: The tool uses `fake_useragent` library for rotation
- **Request Headers**: Customize in the download functions
- **File Naming**: Modify the filename generation logic in `scrape.py`
- **Crawling Rules**: Adjust the `is_internal_link()` function for different crawling behaviors

## Dependencies

- `streamlit`: Web interface framework
- `fake_useragent`: User agent rotation for web requests
- `lxml`: HTML parsing and link extraction
- `requests`: HTTP client for web requests
- `pdfkit`: Python wrapper for wkhtmltopdf

## Troubleshooting

### Common Issues

1. **"wkhtmltopdf not found"**
   - Ensure wkhtmltopdf is installed and in your system PATH
   - On macOS: `brew install wkhtmltopdf`

2. **Permission Errors**
   - Check write permissions in the downloads directory
   - Run with appropriate user permissions

3. **SSL Certificate Errors**
   - Some sites may have SSL issues; the tool handles these gracefully
   - Check console output for specific error messages

4. **Memory Issues with Large Sites**
   - Reduce MAX_DEPTH for very large websites
   - Monitor system resources during operation

### Performance Tips

- Start with smaller MAX_DEPTH values for initial testing
- Use the web interface for better progress tracking
- Monitor disk space when scraping large websites
- Consider the target website's robots.txt and rate limiting

## Legal and Ethical Considerations

- Always respect robots.txt files
- Be mindful of website terms of service
- Use reasonable delays to avoid overwhelming target servers
- Only scrape websites you have permission to access
- This tool is intended for legitimate security research and OSINT purposes

## Contributing

Feel free to submit issues, feature requests, or pull requests to improve this tool.

## License

See LICENSE file for details.