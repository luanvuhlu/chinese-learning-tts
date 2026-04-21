#!/bin/bash

# Chinese TTS Video Generator - Unix/Linux/macOS Startup Script

echo ""
echo "========================================"
echo "Chinese TTS Video Generator"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    echo "Please install Python 3.13+ from https://www.python.org"
    exit 1
fi

# Check if FFmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    echo "Warning: FFmpeg is not installed"
    echo "Video generation will fail without FFmpeg"
    echo "On macOS: brew install ffmpeg"
    echo "On Ubuntu/Debian: sudo apt-get install ffmpeg"
    echo "On Fedora: sudo dnf install ffmpeg"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
else
    echo "Virtual environment not found. Creating one..."
    python3 -m venv .venv
    source .venv/bin/activate
    echo "Installing dependencies..."
    pip install -e .
fi

# Start the Flask application
echo ""
echo "Starting Flask application..."
echo ""
echo "========================================"
echo "Server is running at: http://localhost:5000"
echo "Press Ctrl+C to stop"
echo "========================================"
echo ""

python app.py
