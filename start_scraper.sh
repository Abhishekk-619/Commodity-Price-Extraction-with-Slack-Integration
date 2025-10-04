#!/bin/bash

# Linux Chicken Scraper Startup Script
# This script sets up the environment and runs the scraper

echo "🐧 Starting Linux Chicken Price Scraper..."

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to start virtual display
start_virtual_display() {
    echo "🖥️ Setting up virtual display..."
    
    # Kill any existing Xvfb processes
    pkill -f Xvfb || true
    
    # Start virtual display
    export DISPLAY=:99
    Xvfb :99 -screen 0 1920x1080x24 -ac +extension GLX +render -noreset &
    XVFB_PID=$!
    
    # Wait for display to start
    sleep 3
    
    echo "✅ Virtual display started (PID: $XVFB_PID)"
    return $XVFB_PID
}

# Function to cleanup
cleanup() {
    echo "🧹 Cleaning up..."
    if [ ! -z "$XVFB_PID" ]; then
        kill $XVFB_PID 2>/dev/null || true
        echo "✅ Virtual display stopped"
    fi
}

# Set trap for cleanup on exit
trap cleanup EXIT

# Check prerequisites
echo "🔍 Checking prerequisites..."

if ! command_exists python3; then
    echo "❌ Python3 not found. Please install Python3."
    exit 1
fi

if ! command_exists Xvfb; then
    echo "❌ Xvfb not found. Installing..."
    if command_exists apt-get; then
        sudo apt-get update && sudo apt-get install -y xvfb
    elif command_exists yum; then
        sudo yum install -y xorg-x11-server-Xvfb
    else
        echo "❌ Cannot install Xvfb automatically. Please install manually."
        exit 1
    fi
fi

# Check Python packages
echo "🐍 Checking Python packages..."
python3 -c "import playwright" 2>/dev/null || {
    echo "❌ Playwright not found. Installing..."
    pip3 install playwright pymongo
    playwright install chromium
    playwright install-deps chromium
}

# Start virtual display
start_virtual_display
XVFB_PID=$?

# Set environment variables
export DISPLAY=:99
export PYTHONUNBUFFERED=1

# Run the scraper
echo "🚀 Starting chicken price scraper..."
python3 linux_chicken_scraper.py

# Check exit code
if [ $? -eq 0 ]; then
    echo "✅ Scraper completed successfully!"
else
    echo "❌ Scraper failed with exit code $?"
fi

echo "🏁 Script finished."
