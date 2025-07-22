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
    "dossier")
        echo "📋 Starting AI-Powered Dossier Generator..."
        streamlit run dossier_app.py
        ;;
    *)
        echo "🚀 Starting OSINT Toolkit (Main Application)..."
        streamlit run app.py
        ;;
esac