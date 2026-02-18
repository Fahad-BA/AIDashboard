#!/bin/bash
# AIDashboard Startup Script

echo "🚀 Starting AIDashboard..."
echo "📊 Real-time Agent Monitoring System"
echo "======================================="

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Check if required packages are installed
echo "📦 Checking dependencies..."
python3 -c "import quart, aiohttp, psutil, sqlite3" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "📦 Installing required packages..."
    pip3 install quart aiohttp psutil
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p /home/fahad/AIDB/static
mkdir -p /home/fahad/AIDB/static/img
mkdir -p /home/fahad/AIDB/templates

# Download default agent avatar
echo "🖼️ Downloading default avatar..."
if [ ! -f "/home/fahad/AIDB/static/img/default-agent.png" ]; then
    curl -s https://ui-avatars.com/api/?name=Agent&background=4a90e2&color=fff&format=png -o /home/fahad/AIDB/static/img/default-agent.png
fi

# Start the dashboard
echo "🎯 Starting AIDashboard..."
echo "📍 Dashboard URL: http://localhost:5000"
echo "🔄 Real-time updates enabled"
echo "⏹️  Press Ctrl+C to stop"
echo ""

cd /home/fahad/AIDB
python3 app.py