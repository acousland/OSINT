#!/usr/bin/env python3
"""
Migration script to help transition to the new project structure.
This script sets up the Python path and validates the new structure.
"""
import sys
import os
from pathlib import Path

def setup_python_path():
    """Add src directory to Python path."""
    project_root = Path(__file__).parent
    src_path = project_root / "src"
    
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
        print(f"✅ Added {src_path} to Python path")
    
    return src_path

def validate_structure():
    """Validate that the new structure is properly set up."""
    project_root = Path(__file__).parent
    
    required_paths = [
        "src/osint_toolkit/__init__.py",
        "src/osint_toolkit/core/__init__.py", 
        "src/osint_toolkit/core/mapper.py",
        "src/osint_toolkit/core/scraper.py",
        "src/osint_toolkit/core/dossier.py",
        "src/osint_toolkit/ui/__init__.py",
        "src/osint_toolkit/ui/main_app.py",
        "src/osint_toolkit/ui/dossier_app.py",
        "src/osint_toolkit/utils/__init__.py",
        "src/osint_toolkit/utils/config.py",
        "src/osint_toolkit/utils/setup.py",
        "app.py",
        "dossier_app.py",
    ]
    
    missing = []
    for path_str in required_paths:
        path = project_root / path_str
        if not path.exists():
            missing.append(path_str)
    
    if missing:
        print("❌ Missing required files:")
        for item in missing:
            print(f"   - {item}")
        return False
    else:
        print("✅ All required files present")
        return True

def test_imports():
    """Test that the new imports work correctly."""
    try:
        setup_python_path()
        
        # Test core imports
        from osint_toolkit.core.mapper import HighSpeedWebMapper
        from osint_toolkit.core.scraper import HighSpeedScraper
        from osint_toolkit.core.dossier import DossierGenerator, CompanyDossier
        from osint_toolkit.utils.config import config
        
        print("✅ Core imports successful")
        print(f"✅ Configuration loaded: {config.BASE_DIR}")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    """Main migration validation function."""
    print("🚀 OSINT Toolkit - New Structure Validation")
    print("=" * 50)
    
    # Check structure
    if not validate_structure():
        print("\n❌ Structure validation failed!")
        return 1
    
    # Test imports  
    if not test_imports():
        print("\n❌ Import validation failed!")
        return 1
    
    print("\n🎉 Migration validation completed successfully!")
    print("\nYou can now use:")
    print("  ./run.sh          - Main OSINT application")
    print("  ./run.sh dossier  - Dossier generator")
    print("  python app.py     - Direct Python execution")
    
    return 0

if __name__ == "__main__":
    exit(main())
