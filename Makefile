# Script Follower - Real-Time Speech Recognition
# Makefile for project management

.PHONY: help setup dev test lint fmt clean docker/build docker/run deploy

# Default target
help:
	@echo "🎭 Script Follower - Available Commands:"
	@echo ""
	@echo "Setup & Development:"
	@echo "  setup     - Install dependencies and setup environment"
	@echo "  dev       - Run development server"
	@echo "  test      - Run tests"
	@echo "  lint      - Run linting checks"
	@echo "  fmt       - Format code"
	@echo ""
	@echo "Docker:"
	@echo "  docker/build - Build Docker image"
	@echo "  docker/run   - Run Docker container"
	@echo ""
	@echo "Deployment:"
	@echo "  deploy    - Deploy to cloud"
	@echo ""
	@echo "Maintenance:"
	@echo "  clean     - Clean up temporary files"

# Setup environment
setup:
	@echo "🔧 Setting up Script Follower..."
	python -m venv venv
	. venv/bin/activate && pip install --upgrade pip
	. venv/bin/activate && pip install -r requirements.txt
	@echo "✅ Setup complete! Run 'make dev' to start development"

# Development server
dev:
	@echo "🎭 Starting Script Follower development server..."
	. venv/bin/activate && python run.py

# Run tests
test:
	@echo "🧪 Running tests..."
	. venv/bin/activate && python -m pytest tests/ -v

# Lint code
lint:
	@echo "🔍 Running linting checks..."
	. venv/bin/activate && ruff check .
	. venv/bin/activate && mypy .

# Format code
fmt:
	@echo "✨ Formatting code..."
	. venv/bin/activate && black .
	. venv/bin/activate && ruff check --fix .

# Clean up
clean:
	@echo "🧹 Cleaning up..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/

# Docker build
docker/build:
	@echo "🐳 Building Docker image..."
	docker build -t script-follower:latest .

# Docker run
docker/run:
	@echo "🐳 Running Docker container..."
	docker run -p 8501:8501 --env-file .env script-follower:latest

# Deploy to cloud
deploy:
	@echo "☁️ Deploying to cloud..."
	./deploy.sh

# Install development dependencies
install-dev:
	@echo "📦 Installing development dependencies..."
	. venv/bin/activate && pip install -e ".[dev]"

# Check external drive
check-drive:
	@echo "💾 Checking external drive..."
	@if [ -d "/Volumes/ExternalJeff/script-follower" ]; then \
		echo "✅ External drive found: /Volumes/ExternalJeff/script-follower"; \
	else \
		echo "❌ External drive not found: /Volumes/ExternalJeff/script-follower"; \
		echo "Please ensure the external drive is connected and accessible"; \
	fi

# Run evangelism app specifically
evangelism:
	@echo "✝️ Starting Evangelism Script Follower..."
	. venv/bin/activate && streamlit run app_evangelism.py --server.port 8501 --server.address 0.0.0.0

# Run enhanced evangelism app
evangelism-enhanced:
	@echo "✝️ Starting Enhanced Evangelism Script Follower..."
	. venv/bin/activate && streamlit run app_evangelism_enhanced.py --server.port 8501 --server.address 0.0.0.0

# Run main app
main:
	@echo "🎭 Starting Main Script Follower..."
	. venv/bin/activate && streamlit run app.py --server.port 8501 --server.address 0.0.0.0

# Run cloud app
cloud:
	@echo "☁️ Starting Cloud Script Follower..."
	. venv/bin/activate && streamlit run app_cloud.py --server.port 8501 --server.address 0.0.0.0
