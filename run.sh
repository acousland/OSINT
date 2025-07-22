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

# Start the Streamlined OSINT Pipeline
echo "⚡ Starting Streamlined OSINT Pipeline (In-Memory)..."
streamlit run streamlined_app.py