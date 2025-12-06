#!/bin/bash

# Spica Quick Start Script
# Starts both frontend and backend in development mode

set -e

echo "═══════════════════════════════════════════════════════════════"
echo "  🚀 SPICA - AI-Powered DeFi Workflow Builder"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found"
    echo ""
    echo "Please copy .env.example to .env and configure it:"
    echo "  cp .env.example .env"
    echo "  nano .env"
    echo ""
    exit 1
fi

echo "✅ Environment configuration found"
echo ""

# Check if Docker is available
if command -v docker-compose &> /dev/null || command -v docker &> /dev/null; then
    echo "🐳 Docker detected - using Docker Compose"
    echo ""
    echo "Starting services..."
    docker-compose up --build
else
    echo "📦 Docker not detected - starting local development servers"
    echo ""
    echo "This will start backend and frontend in separate terminal windows"
    echo "Press Ctrl+C in each window to stop"
    echo ""

    # Start backend in new terminal
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        osascript -e 'tell app "Terminal" to do script "cd \"'"$(pwd)"'/backend\" && ./run.sh"'
        echo "✅ Backend starting in new terminal window"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        if command -v gnome-terminal &> /dev/null; then
            gnome-terminal -- bash -c "cd $(pwd)/backend && ./run.sh; exec bash"
        elif command -v xterm &> /dev/null; then
            xterm -e "cd $(pwd)/backend && ./run.sh" &
        else
            echo "Please start backend manually: cd backend && ./run.sh"
        fi
        echo "✅ Backend starting in new terminal window"
    else
        echo "Please start backend manually: cd backend && ./run.sh"
    fi

    # Wait a moment
    sleep 2

    # Start frontend in new terminal
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        osascript -e 'tell app "Terminal" to do script "cd \"'"$(pwd)"'/frontend\" && ./run.sh"'
        echo "✅ Frontend starting in new terminal window"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        if command -v gnome-terminal &> /dev/null; then
            gnome-terminal -- bash -c "cd $(pwd)/frontend && ./run.sh; exec bash"
        elif command -v xterm &> /dev/null; then
            xterm -e "cd $(pwd)/frontend && ./run.sh" &
        else
            echo "Please start frontend manually: cd frontend && ./run.sh"
        fi
        echo "✅ Frontend starting in new terminal window"
    else
        echo "Please start frontend manually: cd frontend && ./run.sh"
    fi

    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "  Services starting..."
    echo "═══════════════════════════════════════════════════════════════"
    echo ""
    echo "  Frontend:  http://localhost:5173"
    echo "  Backend:   http://localhost:8000"
    echo "  API Docs:  http://localhost:8000/docs"
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
fi
