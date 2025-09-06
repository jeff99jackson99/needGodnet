# 🚀 Streamlit Cloud Deployment Guide

## Step 1: Create GitHub Repository

1. Go to [GitHub](https://github.com/new)
2. Create a new repository named `script-follower`
3. Make it public
4. Don't initialize with README (we already have one)

## Step 2: Push Your Code

```bash
# Add remote origin (replace with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/script-follower.git

# Push to GitHub
git branch -M main
git push -u origin main
```

## Step 3: Deploy to Streamlit Cloud

1. Go to [Streamlit Cloud](https://share.streamlit.io/)
2. Sign in with your GitHub account
3. Click "New app"
4. Select your `script-follower` repository
5. Set the main file path to `app_cloud.py`
6. Click "Deploy!"

## Step 4: Configure Your App

Once deployed, you can:

1. **Load Scripts from GitHub**: Upload your script files to the repository
2. **Test Matching**: Use the text input to test script matching
3. **Configure Settings**: Adjust confidence thresholds and other settings

## Features Available in Cloud Version

- ✅ GitHub script loading
- ✅ PDF file upload
- ✅ Text-based script matching
- ✅ Real-time matching testing
- ✅ Script preview and statistics
- ✅ Logging and interaction tracking

## Note

The cloud version doesn't include real-time speech recognition due to browser limitations, but you can:
- Upload scripts from GitHub
- Test matching by typing text
- View script previews and statistics
- Use all the script analysis features

## Your App Will Be Available At

`https://YOUR_USERNAME-script-follower-app-XXXXXX.streamlit.app`

Replace `YOUR_USERNAME` with your GitHub username and `XXXXXX` with the random ID Streamlit assigns.
