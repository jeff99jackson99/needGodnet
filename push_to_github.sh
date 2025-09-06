#!/bin/bash

echo "🚀 Pushing Script Follower to GitHub"
echo "===================================="

# Check if we're in the right directory
if [ ! -f "app_cloud.py" ]; then
    echo "❌ app_cloud.py not found. Please run this script from the script-follower directory"
    exit 1
fi

echo "📋 To complete the deployment, please follow these steps:"
echo ""
echo "1. Go to https://github.com/new"
echo "2. Create a new repository named 'script-follower'"
echo "3. Make it public"
echo "4. Don't initialize with README"
echo "5. Copy the repository URL"
echo ""

read -p "Enter the GitHub repository URL (e.g., https://github.com/jeffjackson/script-follower.git): " REPO_URL

if [ -z "$REPO_URL" ]; then
    echo "❌ No repository URL provided. Exiting."
    exit 1
fi

echo "🔗 Adding remote origin..."
git remote add origin "$REPO_URL" 2>/dev/null || git remote set-url origin "$REPO_URL"

echo "📤 Pushing code to GitHub..."
git branch -M main
git push -u origin main

if [ $? -eq 0 ]; then
    echo "✅ Code pushed successfully!"
    echo ""
    echo "🌐 Next steps:"
    echo "1. Go to https://share.streamlit.io/"
    echo "2. Sign in with your GitHub account"
    echo "3. Click 'New app'"
    echo "4. Select your 'script-follower' repository"
    echo "5. Set main file path to 'app_cloud.py'"
    echo "6. Click 'Deploy!'"
    echo ""
    echo "🎉 Your app will be available at:"
    echo "https://YOUR_USERNAME-script-follower-app-XXXXXX.streamlit.app"
else
    echo "❌ Failed to push to GitHub. Please check your repository URL and try again."
    exit 1
fi
