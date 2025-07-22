#!/usr/bin/env python3
"""
OSINT Toolkit - Streamlined Application Entry Point
In-memory pipeline: Map → Scrape → Analyze → Download Results
"""
import sys
import os
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

import streamlit as st
from osint_toolkit.ui.streamlined_app import main as run_streamlined_app

def main():
    """Main entry point for Streamlined OSINT Application."""
    run_streamlined_app()

if __name__ == "__main__":
    main()
