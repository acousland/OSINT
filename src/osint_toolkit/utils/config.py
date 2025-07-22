"""
Configuration management for OSINT Toolkit.
"""
import os
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

class Config:
    """Central configuration management for OSINT Toolkit."""
    
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Base paths
        self.BASE_DIR = Path(__file__).parent.parent.parent.parent
        self.SRC_DIR = self.BASE_DIR / "src"
        self.DATA_DIR = self.BASE_DIR / "downloads"
        self.DOSSIER_DIR = self.BASE_DIR / "dossiers"
        self.TEST_DIR = self.BASE_DIR / "tests"
        
        # Ensure directories exist
        self.DATA_DIR.mkdir(exist_ok=True)
        self.DOSSIER_DIR.mkdir(exist_ok=True)
        
        # API Configuration
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        self.OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")
        
        # Scraping Configuration
        self.MAX_CONCURRENT_REQUESTS = int(os.getenv("MAX_CONCURRENT_REQUESTS", "10"))
        self.REQUEST_DELAY = float(os.getenv("REQUEST_DELAY", "1.0"))
        self.MAX_DEPTH = int(os.getenv("MAX_DEPTH", "3"))
        
        # UI Configuration
        self.STREAMLIT_PORT = int(os.getenv("STREAMLIT_PORT", "8501"))
        
    def get_data_path(self, filename: str) -> Path:
        """Get path for data file."""
        return self.DATA_DIR / filename
    
    def get_dossier_path(self, filename: str) -> Path:
        """Get path for dossier file."""
        return self.DOSSIER_DIR / filename
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "base_dir": str(self.BASE_DIR),
            "data_dir": str(self.DATA_DIR),
            "dossier_dir": str(self.DOSSIER_DIR),
            "max_concurrent_requests": self.MAX_CONCURRENT_REQUESTS,
            "request_delay": self.REQUEST_DELAY,
            "max_depth": self.MAX_DEPTH,
            "openai_model": self.OPENAI_MODEL,
            "streamlit_port": self.STREAMLIT_PORT,
        }

# Global config instance
config = Config()
