#!/bin/bash

# Spica Backend Development Server
# Quick start script for local development

set -e

echo "🚀 Starting Spica Backend..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "✅ Activating virtual environment..."
source venv/bin/activate

# Install dependencies
if [ ! -f "venv/.deps_installed" ]; then
    echo "📥 Installing dependencies..."
    pip install -r requirements.txt
    touch venv/.deps_installed
else
    echo "✅ Dependencies already installed"
fi

# Set PYTHONPATH for SpoonOS
export PYTHONPATH="${PYTHONPATH}:$(pwd)/../spoon-core:$(pwd)/../spoon-toolkit"

# Load environment variables
if [ -f "../.env" ]; then
    echo "✅ Loading environment variables from .env"
    export $(cat ../.env | grep -v '^#' | xargs)
else
    echo "⚠️  Warning: .env file not found. Copy .env.example to .env"
fi

# Run the development server
echo "🌐 Starting FastAPI server on http://localhost:8000"
echo "📝 API docs available at http://localhost:8000/docs"
echo ""
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
