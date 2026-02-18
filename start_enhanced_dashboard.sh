#!/bin/bash
# Enhanced AIDashboard Startup Script with Task Distribution

echo "🚀 Starting Enhanced AIDashboard with Task Distribution..."
echo "📊 Real-time Agent Monitoring & Task Distribution System"
echo "=========================================================="

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Initialize task system
echo "🔧 Initializing task distribution system..."
cd /home/fahad/AIDB
python3 agent_task_system.py init

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment and install dependencies
echo "📦 Installing dependencies..."
source venv/bin/activate
pip install -r requirements.txt 2>/dev/null || pip install quart aiohttp psutil

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

# Start the enhanced dashboard
echo "🎯 Starting Enhanced AIDashboard..."
echo "📍 Dashboard URL: http://localhost:5000"
echo "🔄 Real-time updates enabled"
echo "👥 Task distribution active"
echo "📊 Each agent will work on their assigned tasks"
echo "⏹️  Press Ctrl+C to stop"
echo ""

python3 enhanced_dashboard.py