# OSINT Toolkit Architecture

## Project Structure

```
OSINT/
├── src/                          # Source code
│   └── osint_toolkit/           # Main package
│       ├── __init__.py          # Package initialization
│       ├── core/                # Core business logic
│       │   ├── __init__.py
│       │   ├── mapper.py        # Website mapping engine
│       │   ├── scraper.py       # Content scraping engine
│       │   └── dossier.py       # AI-powered dossier generation
│       ├── ui/                  # User interfaces
│       │   ├── __init__.py
│       │   ├── main_app.py      # Main Streamlit application
│       │   └── dossier_app.py   # Dossier generator UI
│       └── utils/               # Utility modules
│           ├── __init__.py
│           ├── config.py        # Configuration management
│           └── setup.py         # API setup utilities
├── tests/                       # Test suite
├── config/                      # Configuration files
├── docs/                        # Documentation
├── dossiers/                    # Generated intelligence reports (git-ignored)
├── downloads/                   # Scraped content storage
├── app.py                       # Main application entry point
├── dossier_app.py              # Dossier app entry point
└── run.sh                       # Unified launcher script
```

## Architecture Principles

### 1. **Separation of Concerns**
- **Core Logic**: Business logic separated from UI concerns
- **UI Layer**: Clean separation between different interfaces
- **Utilities**: Shared functionality in dedicated modules

### 2. **Modular Design**
- **Mapper**: Website structure discovery and URL mapping
- **Scraper**: High-performance content extraction
- **Dossier**: AI-powered business intelligence analysis

### 3. **Configuration Management**
- Centralized configuration in `config.py`
- Environment variable support via `.env`
- Path management for data directories

### 4. **Entry Points**
- **app.py**: Main application (mapping + scraping)
- **dossier_app.py**: Dedicated dossier generation interface
- **run.sh**: Shell script launcher with multiple modes

## Component Overview

### Core Modules

#### `core/mapper.py` - HighSpeedWebMapper
- Asynchronous website mapping
- Multiple speed modes (Turbo, Fast, Respectful)
- Comprehensive URL discovery and structure analysis

#### `core/scraper.py` - HighSpeedScraper  
- High-performance content extraction
- PDF and HTML processing
- Concurrent download management

#### `core/dossier.py` - DossierGenerator
- AI-powered business intelligence analysis
- 9-section business proforma generation
- JSON and HTML export formats

### UI Modules

#### `ui/main_app.py`
- Streamlit-based main interface
- Website mapping and scraping workflows
- Real-time progress tracking and results display

#### `ui/dossier_app.py`
- Dedicated dossier generation interface
- File upload and processing
- Interactive dossier customization

### Utility Modules

#### `utils/config.py`
- Centralized configuration management
- Environment variable handling
- Path resolution and directory management

#### `utils/setup.py`
- API key configuration
- Environment setup utilities
- Configuration validation

## Benefits of New Structure

1. **Maintainability**: Clear separation makes code easier to maintain
2. **Scalability**: Modular design supports adding new features
3. **Testability**: Isolated components are easier to test
4. **Reusability**: Core modules can be used independently
5. **Professional**: Standard Python package structure
6. **Documentation**: Clear organization aids understanding
