#!/bin/bash

echo "🎭 Script Follower - Deployment Script"
echo "======================================"

# Check if external drive is mounted
if [ ! -d "/Volumes/ExternalJeff" ]; then
    echo "❌ External drive not found at /Volumes/ExternalJeff"
    echo "Please ensure the external drive is connected and mounted"
    exit 1
fi

echo "✅ External drive found"

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "❌ app.py not found. Please run this script from the script-follower directory"
    exit 1
fi

echo "✅ Application files found"

# Install requirements if needed
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

echo "🔧 Activating virtual environment..."
source venv/bin/activate

echo "📦 Installing requirements..."
pip install -r requirements.txt

echo "🌐 Starting Streamlit application..."
echo "📱 The app will be available at:"
echo "   - Local: http://localhost:8501"
echo "   - Network: http://$(ifconfig | grep 'inet ' | grep -v '127.0.0.1' | awk '{print $2}' | head -1):8501"
echo ""
echo "Press Ctrl+C to stop the application"
echo ""

# Run the application
python run.py
