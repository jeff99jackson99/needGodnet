#!/bin/bash

echo "🎭 Script Follower - GitHub Setup"
echo "================================="

echo "📋 To complete the setup, please follow these steps:"
echo ""
echo "1. Go to https://github.com/new"
echo "2. Create a new repository named 'script-follower'"
echo "3. Make it public"
echo "4. Don't initialize with README (we already have one)"
echo "5. Copy the repository URL"
echo ""

read -p "Enter the GitHub repository URL (e.g., https://github.com/jeffjackson/script-follower.git): " REPO_URL

if [ -z "$REPO_URL" ]; then
    echo "❌ No repository URL provided. Exiting."
    exit 1
fi

echo "🔗 Adding remote origin..."
git remote add origin "$REPO_URL"

echo "📤 Pushing code to GitHub..."
git branch -M main
git push -u origin main

echo "✅ Setup complete!"
echo "🌐 Your repository is now available at: $REPO_URL"
echo ""
echo "🚀 To run the application:"
echo "   python run.py"
echo ""
echo "📱 Access the app at: http://localhost:8501"
