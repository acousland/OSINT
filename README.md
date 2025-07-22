# OSINT Toolkit

A comprehensive Open Source Intelligence (OSINT)   │           └── setup.py         # 🔧 API setup utilities
├── tests/                       # 🧪 Test suite
├── docs/                        # 📚 Documentation
│   ├── ARCHITECTURE.md         # 🏗️ Architecture guide
│   └── USAGE.md                # 📖 Usage documentation
├── streamlined_app.py          # ⚡ Main application entry pointts/                       # 🧪 Test suite
├── docs/                        # 📚 Documentation├── dossiers/                    # 📋 Generated intelligence reports (git-ignored)─ utils/               # 🛠️ Utility modules
           ├── config.py        # ⚙️ Configuration management
           └── setup.py         # 🔧 API setup utilities
├── tests/                       # 🧪 Test suite
├── config/                      # ⚙️ Configuration filesrm combining high-speed website mapping, content scraping, and AI-powered company dossier generation in a unified interface.

## 🚀 Quick Start

### Streamlined Pipeline
```bash
./run.sh
```
**All-in-one in-memory workflow:** Map → Scrape → Analyze → Download Results
- No file system clutter
- Faster processing  
- Download only final results

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
├── src/                          # 📦 Source code
│   └── osint_toolkit/           # 🏠 Main package
│       ├── core/                # ⚙️ Core business logic
│       │   ├── in_memory_mapper.py     # 🗺️ In-memory website mapping
│       │   ├── in_memory_scraper.py    # 📄 In-memory content scraping
│       │   └── in_memory_dossier.py    # 🤖 In-memory dossier generation
│       ├── ui/                  # 🎨 User interfaces
│       │   └── streamlined_app.py      # ⚡ Streamlined application UI
│       └── utils/               # 🛠️ Utility modules
│           ├── config.py        # ⚙️ Configuration management
│           └── setup.py         # 🔧 API setup utilities
├── tests/                       # 🧪 Test suite
├── docs/                        # 📚 Documentation
│   └── ARCHITECTURE.md         # 🏗️ Architecture guide
├── dossiers/                    # � Generated intelligence reports (git-ignored)
├── downloads/                   # 📥 Scraped content storage
├── streamlined_app.py          # ⚡ Main application entry point
├── run.sh                       # 🚀 Application launcher script
├── requirements.txt            # 📦 Python dependencies
└── .env.example                # ⚙️ Configuration template
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

## 💻 Usage

### 🚀 Launch the Streamlined Pipeline
```bash
./run.sh
```

The application will start and provide:
- **Interactive interface** for URL input and configuration
- **Real-time progress tracking** during all phases
- **Download options** for final JSON and HTML reports

## 📊 Output Structure

### Generated Reports
The streamlined pipeline generates intelligence reports that are downloaded directly:
- **`company_dossier.json`** - Structured data for further processing
- **`company_dossier.html`** - Formatted report for presentation

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

#### Quick Start with Main Application

Use the integrated main application (recommended):

```bash
# Start the main OSINT toolkit
./run.sh

# Or directly:
streamlit run main.py
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
- **💾 In-Memory Processing**: No file I/O overhead for optimal performance

### 🔧 In-Memory Content Processing

- **⚡ Zero File I/O**: All processing done in memory for maximum speed
- **📄 Multi-format Support**: HTML pages and PDF documents processed directly
- **🧠 Intelligent Chunking**: Semantic text processing for AI analysis
- **📊 Real-time Progress**: Live updates during all pipeline stages
- **� Streamlined Workflow**: Map → Scrape → Analyze → Download in one session

## ⚙️ Configuration

The streamlined pipeline uses environment variables for configuration:

```bash
# Copy .env.example to .env and configure:
OPENAI_API_KEY=your_openai_api_key_here
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
MAX_CONTEXT_TOKENS=4000
MAX_CLUSTERS=8
```

## 🛠️ Dependencies

Core dependencies for the streamlined pipeline:
- `streamlit`: Modern web interface
- `openai`: AI-powered analysis (or alternative LLM providers)
- `aiohttp`: Async HTTP client for high-speed requests
- `beautifulsoup4`: HTML parsing and content extraction
- `pypdf`: PDF text extraction
- `fake_useragent`: User agent rotation

## 🐛 Troubleshooting

### Common Issues

1. **"OpenAI API Key not found"**
   - Ensure you've copied `.env.example` to `.env`
   - Add your OpenAI API key to the `.env` file

2. **Memory Issues with Large Websites**
   - Reduce crawling depth in the web interface
   - Process fewer documents at once
   - Monitor system memory usage

3. **SSL Certificate Errors**
   - The tool handles SSL issues gracefully
   - Check console output for specific error messages

4. **Rate Limiting**
   - Reduce concurrent request settings if needed
   - Use respectful crawling delays

### Performance Tips

- Start with smaller crawling depths for testing
- Use the web interface for real-time progress monitoring
- The in-memory approach is significantly faster than file-based alternatives
- Results are only saved when you download them

## 🔒 Legal and Ethical Considerations

- Always respect robots.txt files
- Be mindful of website terms of service
- Use reasonable delays to avoid overwhelming target servers
- Only scrape websites you have permission to access
- This tool is intended for legitimate security research and OSINT purposes

## 🤝 Contributing

Feel free to submit issues, feature requests, or pull requests to improve this tool.

## 📄 License

See LICENSE file for details.