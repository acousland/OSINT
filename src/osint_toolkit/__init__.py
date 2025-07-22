"""
OSINT Toolkit - A comprehensive intelligence gathering and analysis framework.

This package provides tools for:
- Website mapping and content discovery
- High-speed content scraping 
- AI-powered business intelligence dossier generation
- Interactive web interfaces for OSINT operations

Main Components:
- core: Core business logic and data models
- ui: Streamlit-based user interfaces
- utils: Utility functions and helpers
"""

__version__ = "1.0.0"
__author__ = "OSINT Toolkit Team"

# Core exports - In-Memory Pipeline
from .core.in_memory_mapper import InMemoryWebMapper
from .core.in_memory_scraper import InMemoryScraper  
from .core.in_memory_dossier import InMemoryDossierGenerator

__all__ = [
    "InMemoryWebMapper",
    "InMemoryScraper", 
    "InMemoryDossierGenerator"
]
