#!/bin/bash

# Spica Frontend Development Server
# Quick start script for local development

set -e

echo "🚀 Starting Spica Frontend..."

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
else
    echo "✅ Dependencies already installed"
fi

# Load environment variables
if [ -f "../.env" ]; then
    echo "✅ Loading environment variables from .env"
    export $(cat ../.env | grep '^VITE_' | xargs)
else
    echo "⚠️  Warning: .env file not found. Using default API URL"
fi

# Run the development server
echo "🌐 Starting Vite dev server on http://localhost:5173"
echo ""
npm run dev
