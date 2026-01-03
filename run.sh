#!/bin/bash

echo "============================================"
echo "WebRTC Video Streaming Server"
echo "============================================"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.8+ from https://python.org"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "============================================"
echo "Starting server on http://localhost:5000"
echo "Open this URL in multiple browser tabs to test"
echo "Press Ctrl+C to stop the server"
echo "============================================"
echo ""

# Run the server
python app.py
