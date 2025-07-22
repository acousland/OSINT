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

# Core exports
from .core.mapper import HighSpeedWebMapper
from .core.scraper import HighSpeedScraper  
from .core.dossier import DossierGenerator, CompanyDossier

__all__ = [
    "HighSpeedWebMapper",
    "HighSpeedScraper", 
    "DossierGenerator",
    "CompanyDossier"
]
