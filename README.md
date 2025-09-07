# 🎭 Real-Time Script Follower

A Streamlit application that listens to speech in real-time and matches it against scripts stored in GitHub to provide instant responses.

## Features

- 🎤 **Real-time speech recognition** using Google's speech API
- 📁 **GitHub integration** - load scripts directly from your repository
- ⚡ **Fast fuzzy matching** for script lines with configurable confidence
- 🎯 **Live response display** with real-time updates
- 💾 **External drive storage** for logs and data
- 🔧 **Configurable settings** for optimal performance
- 📱 **Web interface** accessible from any device on your network
- ✝️ **Enhanced Evangelism Script Follower** with intelligent conversation flow
- 🧠 **Context-aware matching** with conversation history tracking
- 🐳 **Docker support** for easy deployment
- 🚀 **CI/CD pipeline** with GitHub Actions
- 🧪 **Comprehensive test suite** with pytest

## Quick Start

### Prerequisites

- Python 3.11+
- External drive mounted at `/Volumes/ExternalJeff/`
- Microphone access
- Internet connection (for Google Speech Recognition)

### Installation & Setup

1. **Clone or download this repository to your external drive:**
   ```bash
   cd /Volumes/ExternalJeff/
   git clone https://github.com/jeffjackson/script-follower.git
   cd script-follower
   ```

2. **Setup the project:**
   ```bash
   make setup
   ```

3. **Run the application:**
   ```bash
   # Main app
   make main
   
   # Enhanced evangelism app
   make evangelism-enhanced
   
   # Original evangelism app
   make evangelism
   
   # Cloud app
   make cloud
   ```

4. **Access the app:**
   - Local: `http://localhost:8501`
   - Network: `http://[your-ip]:8501`

## How It Works

### 1. Script Loading
- **GitHub Integration**: Load scripts directly from your GitHub repository
- **File Upload**: Upload PDF files as fallback
- **Local Storage**: Cached scripts stored on external drive

### 2. Speech Recognition
- Uses Google's speech recognition API for real-time audio processing
- Processes audio in 3-second chunks for optimal speed
- Adjustable confidence thresholds for matching accuracy

### 3. Script Matching
- **Fuzzy String Matching**: Compares spoken words against script lines
- **Keyword Extraction**: Identifies important terms for better matching
- **Real-time Processing**: Instant response as you speak

### 4. Data Storage
- **Logs**: All interactions saved to external drive
- **Scripts**: Parsed scripts cached locally
- **Configurations**: Settings persisted across sessions

## GitHub Integration

### Setting Up GitHub Repository

1. **Create a new repository** on GitHub
2. **Upload your script files** (PDF, TXT, MD formats supported)
3. **Configure the app** with your repository details:
   - GitHub Owner: Your username
   - Repository Name: Your repo name
   - GitHub Token: (Optional) For private repositories

### Supported File Formats

- **PDF**: Automatically parsed and processed
- **TXT**: Plain text scripts
- **MD**: Markdown formatted scripts

## Configuration

### Environment Variables

Create a `.env` file with your settings:

```env
# External Drive Configuration
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
GITHUB_OWNER=your-username
GITHUB_REPO=your-repo-name
GITHUB_TOKEN=your-github-token
```

### Settings in the App

- **Confidence Threshold**: Adjust matching sensitivity (0-100%)
- **Response Delay**: Control response timing (50-500ms)
- **GitHub Settings**: Configure repository access

## Usage

### Loading Scripts

1. **From GitHub**:
   - Enter your GitHub repository details
   - Click "Refresh GitHub Files"
   - Select and load your script

2. **Upload File**:
   - Use the file uploader for local PDFs
   - Files are automatically processed and cached

### Running the App

1. **Start Listening**: Click the microphone button
2. **Speak**: Say lines from your script
3. **View Responses**: See instant matches and responses
4. **Monitor Logs**: Track all interactions

## App Variants

### 🎭 Main App (`app.py`)
- General-purpose script follower
- GitHub integration for script loading
- File upload support
- Real-time speech recognition

### ✝️ Evangelism App (`app_evangelism.py`)
- Specialized for evangelism conversations
- 39-question conversation flow
- Intelligent response matching
- Script guidance system

### ✝️ Enhanced Evangelism App (`app_evangelism_enhanced.py`)
- **NEW**: Advanced conversation flow management
- **NEW**: Context-aware matching with conversation history
- **NEW**: Enhanced keyword extraction and response patterns
- **NEW**: Intelligent analysis for better question routing
- **NEW**: Person name and belief tracking
- **NEW**: Improved UI with conversation context display

### ☁️ Cloud App (`app_cloud.py`)
- Optimized for cloud deployment
- Reduced external dependencies
- Container-ready configuration

## File Structure

```
script-follower/
├── app.py                        # Main Streamlit application
├── app_evangelism.py             # Original evangelism app
├── app_evangelism_enhanced.py    # Enhanced evangelism app
├── app_cloud.py                  # Cloud-optimized app
├── run.py                        # Application launcher
├── requirements.txt              # Python dependencies
├── pyproject.toml               # Project configuration
├── Makefile                     # Build and run commands
├── Dockerfile                   # Docker configuration
├── docker-compose.yml           # Docker Compose setup
├── .dockerignore               # Docker ignore rules
├── .pre-commit-config.yaml     # Pre-commit hooks
├── .github/workflows/          # CI/CD pipelines
│   ├── ci.yml                  # Continuous integration
│   └── release.yml             # Release automation
├── .vscode/                    # VS Code configuration
│   ├── tasks.json              # VS Code tasks
│   └── launch.json             # Debug configuration
├── tests/                      # Test suite
│   └── test_evangelism_enhanced.py
├── streamlit_config.toml       # Streamlit configuration
├── README.md                   # This file
├── .env.example                # Environment template
├── .gitignore                  # Git ignore rules
├── logs/                       # Interaction logs (external drive)
└── data/                       # Cached scripts (external drive)
```

## Troubleshooting

### Common Issues

1. **External Drive Not Found**
   - Ensure drive is mounted at `/Volumes/ExternalJeff/`
   - Check drive permissions

2. **Audio Issues**
   - Verify microphone access in system preferences
   - Close other audio applications

3. **GitHub Connection**
   - Check repository name and owner
   - Verify GitHub token for private repos
   - Ensure internet connection

4. **Performance Issues**
   - Adjust confidence threshold
   - Close unnecessary applications
   - Check available disk space

### Logs

- **Application Logs**: `logs/script_follower.log`
- **Interaction Logs**: `logs/interactions_YYYYMMDD.jsonl`
- **Error Logs**: Check terminal output

## Development

### Available Commands

```bash
# Setup and installation
make setup              # Install dependencies and setup environment
make install-dev        # Install development dependencies

# Running applications
make dev                # Run development server
make main               # Run main app
make evangelism         # Run original evangelism app
make evangelism-enhanced # Run enhanced evangelism app
make cloud              # Run cloud app

# Development tools
make test               # Run test suite
make lint               # Run linting checks
make fmt                # Format code
make clean              # Clean up temporary files

# Docker
make docker/build       # Build Docker image
make docker/run         # Run Docker container

# Deployment
make deploy             # Deploy to cloud
make check-drive        # Check external drive status
```

### Running in Development Mode

```bash
# Install development dependencies
make install-dev

# Run with auto-reload
make dev
```

### Testing

```bash
# Run all tests
make test

# Run specific test file
python -m pytest tests/test_evangelism_enhanced.py -v

# Run with coverage
python -m pytest tests/ --cov=. --cov-report=html
```

### Docker Development

```bash
# Build and run with Docker Compose
docker-compose up --build

# Run development version with hot reload
docker-compose --profile dev up --build
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
- Check the troubleshooting section
- Review the logs
- Create an issue on GitHub

---

**Note**: This application requires an external drive for optimal performance and data storage. Ensure your external drive is properly mounted before running the application.
