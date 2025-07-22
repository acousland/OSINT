# OSINT Toolkit - Usage Guide

## Quick Start (UI Only)

The OSINT Toolkit is designed for interactive use through Streamlit web interfaces. All functionality is accessible through two main applications:

### 🚀 Main Application
```bash
./run.sh
```
**Features:**
- Website mapping and structure discovery
- High-speed content scraping
- Real-time progress tracking
- Interactive result exploration

### 📋 Dossier Generator
```bash
./run.sh dossier
```
**Features:**
- AI-powered business intelligence analysis
- 9-section business proforma generation
- Multi-format document processing (PDF + HTML)
- JSON and HTML export options

## Typical Workflow

1. **Map a website** using the main application to discover structure
2. **Scrape content** to download HTML pages and PDFs
3. **Generate dossier** using the collected content for AI analysis

## Configuration

1. **API Setup**: Required for dossier generation
   - Copy `.env.example` to `.env`
   - Add your OpenAI API key: `OPENAI_API_KEY=your_key_here`

2. **Dependencies**: Automatically handled by `run.sh`
   - Virtual environment creation
   - Package installation from `requirements.txt`

## Data Storage

- **Downloads**: Scraped content stored in `downloads/`
- **Dossiers**: Generated reports saved in `dossiers/`
- **Configuration**: Settings in `.env` file

## Architecture

The toolkit follows a clean, modular architecture:

- **Core Logic**: `src/osint_toolkit/core/` - Business logic
- **UI Components**: `src/osint_toolkit/ui/` - Streamlit interfaces  
- **Utilities**: `src/osint_toolkit/utils/` - Configuration and setup
- **Entry Points**: `app.py` and `dossier_app.py` - Clean launchers

This structure ensures maintainability, scalability, and ease of use through web interfaces.
