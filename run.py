#!/usr/bin/env python3
"""
Script Follower - Real-time speech recognition script follower
Run this script to start the Streamlit application
"""

import subprocess
import sys
import os
from pathlib import Path

def check_external_drive():
    """Check if external drive is available"""
    external_drive = "/Volumes/ExternalJeff/script-follower"
    if not os.path.exists(external_drive):
        print(f"❌ External drive not found: {external_drive}")
        print("Please ensure the external drive is connected and accessible")
        return False
    print(f"✅ External drive found: {external_drive}")
    return True

def install_requirements():
    """Install required packages"""
    print("📦 Installing requirements...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Requirements installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing requirements: {e}")
        return False

def setup_environment():
    """Setup environment variables"""
    env_file = Path(".env")
    if not env_file.exists():
        print("🔧 Creating environment file...")
        with open(".env", "w") as f:
            f.write("""# External Drive Configuration
EXTERNAL_DRIVE_PATH=/Volumes/ExternalJeff/script-follower
LOG_PATH=/Volumes/ExternalJeff/script-follower/logs
DATA_PATH=/Volumes/ExternalJeff/script-follower/data

# Streamlit Configuration
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Speech Recognition Settings
SPEECH_CONFIDENCE_THRESHOLD=60
SPEECH_RESPONSE_DELAY=0.1

# GitHub Configuration
GITHUB_OWNER=jeffjackson
GITHUB_REPO=script-follower
GITHUB_TOKEN=
""")
        print("✅ Environment file created")
    else:
        print("✅ Environment file already exists")

def run_streamlit():
    """Run the Streamlit app"""
    print("🎭 Starting Script Follower...")
    print("🌐 The app will be available at: http://localhost:8501")
    print("📱 For network access, use: http://[your-ip]:8501")
    print("\nPress Ctrl+C to stop the application")
    
    try:
        # Set environment variables
        os.environ['STREAMLIT_SERVER_PORT'] = '8501'
        os.environ['STREAMLIT_SERVER_ADDRESS'] = '0.0.0.0'
        
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.port", "8501",
            "--server.address", "0.0.0.0",
            "--server.headless", "true"
        ])
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except Exception as e:
        print(f"❌ Error running application: {e}")

def main():
    print("🎭 Script Follower - Real-time Speech Recognition")
    print("=" * 50)
    
    # Check external drive
    if not check_external_drive():
        return
    
    # Setup environment
    setup_environment()
    
    # Install requirements
    if not install_requirements():
        return
    
    # Run the application
    run_streamlit()

if __name__ == "__main__":
    main()
