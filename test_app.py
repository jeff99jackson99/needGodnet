#!/usr/bin/env python3
"""
Test script for Script Follower application
"""

import sys
import os
import json
from pathlib import Path

def test_imports():
    """Test if all required modules can be imported"""
    print("🧪 Testing imports...")
    
    try:
        import streamlit
        print("✅ Streamlit imported successfully")
    except ImportError as e:
        print(f"❌ Streamlit import failed: {e}")
        return False
    
    try:
        import speech_recognition
        print("✅ SpeechRecognition imported successfully")
    except ImportError as e:
        print(f"❌ SpeechRecognition import failed: {e}")
        return False
    
    try:
        import pyaudio
        print("✅ PyAudio imported successfully")
    except ImportError as e:
        print(f"❌ PyAudio import failed: {e}")
        return False
    
    try:
        import fuzzywuzzy
        print("✅ FuzzyWuzzy imported successfully")
    except ImportError as e:
        print(f"❌ FuzzyWuzzy import failed: {e}")
        return False
    
    try:
        import PyPDF2
        print("✅ PyPDF2 imported successfully")
    except ImportError as e:
        print(f"❌ PyPDF2 import failed: {e}")
        return False
    
    return True

def test_external_drive():
    """Test external drive access"""
    print("\n🧪 Testing external drive access...")
    
    external_drive = "/Volumes/ExternalJeff/script-follower"
    if not os.path.exists(external_drive):
        print(f"❌ External drive not found: {external_drive}")
        return False
    
    print(f"✅ External drive found: {external_drive}")
    
    # Test write access
    test_file = f"{external_drive}/test_write.txt"
    try:
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
        print("✅ Write access confirmed")
    except Exception as e:
        print(f"❌ Write access failed: {e}")
        return False
    
    return True

def test_directories():
    """Test if required directories exist"""
    print("\n🧪 Testing directory structure...")
    
    external_drive = "/Volumes/ExternalJeff/script-follower"
    required_dirs = ["logs", "data"]
    
    for dir_name in required_dirs:
        dir_path = f"{external_drive}/{dir_name}"
        if not os.path.exists(dir_path):
            print(f"❌ Directory not found: {dir_path}")
            return False
        print(f"✅ Directory found: {dir_path}")
    
    return True

def test_app_file():
    """Test if main app file exists and is valid"""
    print("\n🧪 Testing application file...")
    
    app_file = "app.py"
    if not os.path.exists(app_file):
        print(f"❌ Application file not found: {app_file}")
        return False
    
    print(f"✅ Application file found: {app_file}")
    
    # Try to compile the file
    try:
        with open(app_file, 'r') as f:
            compile(f.read(), app_file, 'exec')
        print("✅ Application file syntax is valid")
    except SyntaxError as e:
        print(f"❌ Application file syntax error: {e}")
        return False
    
    return True

def test_environment():
    """Test environment setup"""
    print("\n🧪 Testing environment setup...")
    
    env_file = ".env"
    if not os.path.exists(env_file):
        print("⚠️  Environment file not found, creating default...")
        with open(env_file, 'w') as f:
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
        print("✅ Environment file found")
    
    return True

def main():
    """Run all tests"""
    print("🎭 Script Follower - Test Suite")
    print("=" * 40)
    
    tests = [
        test_imports,
        test_external_drive,
        test_directories,
        test_app_file,
        test_environment
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        else:
            print("❌ Test failed!")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The application is ready to run.")
        print("\n🚀 To start the application, run:")
        print("   python run.py")
        print("   or")
        print("   ./deploy.sh")
    else:
        print("❌ Some tests failed. Please fix the issues before running the application.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
