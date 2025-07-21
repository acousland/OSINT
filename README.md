# OSINT Toolkit

A comprehensive Open Source Intelligence (OSINT) platform combining high-speed website mapping, content scraping, and AI-powered company dossier generation in a unified interface.

## 🚀 Quick Start

### Unified Application (Recommended)
```bash
./run.sh
```
This launches the main OSINT Toolkit with all tools integrated in one interface.

### Individual Tools
```bash
./run.sh legacy      # Original mapping/scraping interface
./run.sh dossier     # Standalone dossier generator
```

## 🛠️ Core Features

### 🗺️ High-Speed Website Mapping
- **🚀 Concurrent Processing**: 50-100 concurrent requests for maximum speed
- **⚡ Speed Modes**: Respectful (30 req/s), Fast (50 req/s), Turbo (100 req/s)
- **📊 Performance Metrics**: Real-time speed monitoring and statistics
- **🎯 Smart Discovery**: Recursive crawling to find all internal links and resources
- **📄 Resource Identification**: Automatic detection of PDF files and documents
- **⚙️ Configurable Depth**: Control crawling scope and thoroughness
- **🤖 Respectful Crawling**: Honor robots.txt and implement rate limiting

### 📄 High-Speed Content Scraping & Download
- **🚀 Concurrent Downloads**: 20-50 concurrent requests for maximum speed  
- **⚡ Speed Modes**: Normal (20 req/s), Fast (30 req/s), Turbo (50 req/s)
- **📊 Performance Metrics**: Real-time download speed and success tracking
- **📄 Multi-format Support**: HTML pages, PDF documents, and metadata
- **💾 Smart Organization**: Automatic folder structure by domain and content type
- **🔍 Content Analysis**: Extract text content and metadata for AI processing
- **🛡️ Error Handling**: Robust async error management and retry logic

### 📋 AI-Powered Dossier Generation
- **Multi-format Analysis**: Process both PDFs and HTML content for comprehensive intelligence
- **Hierarchical Analysis**: Process hundreds of documents using semantic chunking
- **Context Management**: Respect AI model token limits with intelligent batching
- **Comprehensive Reports**: Generate executive summaries, financial highlights, personnel info
- **Multiple Sources**: Support both scraped content and custom document collections
- **Export Options**: JSON for data processing, HTML for presentation

## 🎯 Typical OSINT Workflow

1. **🗺️ Map Website** → Discover structure and identify all accessible content
2. **📄 Scrape Content** → Download HTML pages, PDFs and extract intelligence data  
3. **📋 Generate Dossier** → Create comprehensive AI-powered analysis from all collected content

## 📁 Project Structure

```
OSINT/
├── main.py              # 🏠 Unified application entry point
├── app.py               # 🗺️ Legacy mapping/scraping interface  
├── dossier_ui.py        # 📋 Standalone dossier generator
├── dossier_generator.py # 🤖 Core AI dossier generation logic
├── cli_dossier.py       # 💻 Command-line dossier tool
├── mapStructure.py      # 🗺️ Website mapping functionality
├── scrape.py            # 📄 High-speed content scraping functionality
├── run.sh              # 🚀 Unified launcher script
├── requirements.txt    # 📦 Python dependencies
├── .env.example        # ⚙️ Configuration template
└── dossiers/           # 📊 Generated intelligence reports
```

## ⚙️ Installation & Setup

### Prerequisites
- Python 3.7+
- wkhtmltopdf (for PDF generation)
- AI API key (OpenAI, Anthropic, etc. - for dossier generation)

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

### Setup Instructions

1. **Clone and setup:**
```bash
git clone <repository-url>
cd OSINT
chmod +x run.sh
```

2. **Automatic setup (recommended):**
```bash
./run.sh  # Creates venv and installs all dependencies automatically
```

3. **Manual setup (alternative):**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

4. **Configure AI API (for dossier generation):**
```bash
cp .env.example .env
# Edit .env file with your API keys
```

## 💻 Usage Options

### 🏠 Unified Interface (Recommended)
```bash
./run.sh
```
- Navigate between all tools in one application
- Integrated workflow from mapping to dossier generation
- Modern, intuitive interface

### 🗺️ Legacy Tools
```bash
./run.sh legacy    # Original mapping/scraping interface
./run.sh mapping   # Direct to mapping tool
./run.sh scraping  # Direct to scraping tool
```

### 📋 Dossier Tools
```bash
./run.sh dossier   # Standalone dossier generator UI

# Command-line dossier generation:
python cli_dossier.py --company-domain www.example.com
python cli_dossier.py --pdf-directory /path/to/pdfs --company-name "Company Name"
```

## 📊 Output Structure

### Generated Files
```
OSINT/
├── downloads/           # Scraped content
│   └── www.company.com/
│       ├── visited_urls.txt
│       ├── html_pages/  # Downloaded HTML content
│       └── pdfs/        # Downloaded PDF files
├── dossiers/           # Generated intelligence reports
│   ├── company_dossier.json
│   └── company_dossier.html
└── logs/               # Application logs
```

### Dossier Report Sections
- **Executive Summary**: High-level company overview
- **Business Overview**: Operations, business model, services
- **Financial Highlights**: Revenue, profits, key financial metrics
- **Key Personnel**: Leadership team and important contacts
- **Locations**: Office locations, facilities, geographic presence
- **Products & Services**: Offerings, solutions, capabilities
- **Source Attribution**: All analyzed documents tracked

## 🤖 AI-Powered Intelligence Analysis

### Technical Approach
- **Semantic Chunking**: Documents split into meaningful segments
- **Vector Embeddings**: Content similarity analysis using sentence transformers
- **Topic Clustering**: Related content grouped using K-means clustering
- **Hierarchical Summarization**: Multi-level analysis respecting context windows
- **Targeted Extraction**: Semantic search for specific information types

### Supported AI Providers
- OpenAI (GPT-3.5, GPT-4)
- Anthropic Claude (easily configurable)
- Other providers via simple API modification

### Context Window Management
- Intelligent chunking to respect 4K-32K token limits
- Hierarchical processing: chunks → clusters → summaries → final report
- Semantic search to find relevant content across hundreds of documents
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

# High-speed mapping with different modes
ms.fast_map("https://example.com", max_depth=100)      # Balanced speed (50 concurrent)
ms.turbo_map("https://example.com", max_depth=100)     # Maximum speed (100 concurrent) 
ms.map("https://example.com", max_depth=100)           # Custom settings
```

**Scrape PDFs only (requires existing mapping):**
```python
import scrape as sc
sc.scrape("https://example.com")
```

## How It Works

### 1. High-Speed Website Mapping (`mapStructure.py`)

- **🚀 Concurrent Architecture**: Uses async/await with aiohttp for parallel processing
- **⚡ Speed Modes**: 
  - `fast_map()`: 30 concurrent requests (balanced)
  - `turbo_map()`: 100 concurrent requests (aggressive)
  - `map()`: Custom concurrent settings
- **📊 Real-time Metrics**: Tracks URLs/second, total time, and progress
- **🎯 Smart Discovery**: Recursively finds all internal links up to specified depth
- **🤖 Respectful Crawling**: Configurable delays and user agent rotation
- **💾 Efficient Storage**: Batch writes for better I/O performance

### 2. High-Speed Content Scraping (`scrape.py`)

- **🚀 Async Architecture**: Uses aiohttp and asyncio for concurrent processing
- **📄 Multi-format Support**: Downloads HTML pages, PDF files, and extracts metadata
- **⚡ Speed Modes**: 
  - `fast_scrape()`: 30 concurrent requests (recommended)
  - `turbo_scrape()`: 50 concurrent requests (aggressive)
  - `scrape()`: Custom concurrent settings
- **📊 Performance Tracking**: Real-time metrics and download statistics
- **🛡️ Error Handling**: Robust async error management and retry logic
- **💾 Smart Organization**: Separate folders for HTML content and PDF files

### Output Structure

```
downloads/
└── domain.com/
    ├── visited_urls.txt    # List of all discovered URLs
    ├── html_pages/         # Downloaded HTML content
    │   ├── page1.html
    │   ├── page1_metadata.json
    │   └── index.html
    └── pdfs/              # Direct PDF downloads
        ├── document.pdf
        └── report.pdf
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