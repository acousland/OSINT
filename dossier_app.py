#!/usr/bin/env python3
"""
OSINT Toolkit - Dossier Generator Entry Point
"""
import sys
import os
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

import streamlit as st
from osint_toolkit.ui.dossier_app import main as run_dossier_app

def main():
    """Main entry point for Dossier Generator."""
    run_dossier_app()

if __name__ == "__main__":
    main()
