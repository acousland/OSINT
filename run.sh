#!/bin/bash

# Check if virtual environment exists, if not create it
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "Virtual environment created."
fi

# Activate the virtual environment
source venv/bin/activate

# Install requirements if needed
if [ -f "requirements.txt" ]; then
    echo "Installing/updating requirements..."
    pip install -r requirements.txt
fi

# Check command line argument for which app to run
case "$1" in
    "map"|"mapping")
        echo "🚀 Starting High-Speed OSINT Mapping Tool..."
        streamlit run app.py
        ;;
    "scrape"|"scraping") 
        echo "📄 Starting OSINT Scraping Tool..."
        streamlit run app.py
        ;;
    "dossier")
        echo "📋 Starting AI-Powered Dossier Generator..."
        streamlit run dossier_ui.py
        ;;
    "legacy")
        echo "Starting Legacy OSINT App..."
        streamlit run app.py
        ;;
    "setup"|"api")
        echo "Starting API Key Setup..."
        python setup_api.py
        ;;
    "check")
        echo "Checking API Configuration..."
        python setup_api.py check
        ;;
    *)
        echo "Starting OSINT Toolkit (Main Application)..."
        streamlit run main.py
        ;;
esac