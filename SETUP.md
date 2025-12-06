# Spica Setup Guide

Complete setup instructions for getting Spica running on your machine.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Option 1: Docker Setup (Recommended)](#option-1-docker-setup-recommended)
- [Option 2: Local Development Setup](#option-2-local-development-setup)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Required

- **Git** - Version control
  - [Download Git](https://git-scm.com/downloads)
  - Verify: `git --version`

- **Docker & Docker Compose** (for Docker setup)
  - [Download Docker Desktop](https://www.docker.com/products/docker-desktop/)
  - Verify: `docker --version` and `docker-compose --version`

**OR**

- **Python 3.11+** (for local setup)
  - [Download Python](https://www.python.org/downloads/)
  - Verify: `python3 --version`

- **Node.js 20+** (for local setup)
  - [Download Node.js](https://nodejs.org/)
  - Verify: `node --version`

### API Keys & Testnet Setup

1. **OpenAI API Key** (Required)
   - Sign up at [OpenAI Platform](https://platform.openai.com/)
   - Create API key at [API Keys page](https://platform.openai.com/api-keys)
   - Cost: ~$0.01-0.10 per workflow for testing

2. **Neo N3 Testnet Wallet** (Required)
   - Visit [Neo Faucet](https://neoxwish.ngd.network/)
   - Create a new wallet or import existing
   - Save your **WIF private key** (starts with 'K' or 'L')
   - Request testnet GAS and NEO tokens

3. **Base Sepolia Wallet** (Required for x402)
   - Use MetaMask or any Ethereum wallet
   - Switch network to Base Sepolia
   - Get testnet ETH from [Alchemy Faucet](https://www.alchemy.com/faucets/base-sepolia)
   - Note your Ethereum address for receiving payments

---

## Option 1: Docker Setup (Recommended)

### Step 1: Clone Repository

```bash
git clone https://github.com/yourusername/spica.git
cd spica
```

### Step 2: Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your actual values
nano .env  # or use your preferred editor
```

**Required values in .env:**

```bash
# LLM
OPENAI_API_KEY=sk-proj-your-actual-key-here

# Neo N3
NEO_TESTNET_RPC=https://testnet1.neo.coz.io:443
DEMO_WALLET_WIF=your-testnet-wif-key-here

# x402
X402_FACILITATOR_URL=https://x402.org/facilitator
X402_RECEIVER_ADDRESS=0xYourEthereumAddress
X402_NETWORK=base-sepolia
```

### Step 3: Start Services

```bash
# Build and start all services
docker-compose up --build

# Or run in detached mode (background)
docker-compose up -d
```

**Wait for services to start** (~30-60 seconds for first build)

### Step 4: Verify

Open in your browser:
- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

You should see the Spica dashboard with backend status showing "OK".

### Step 5: Stop Services

```bash
# Stop services
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v
```

---

## Option 2: Local Development Setup

### Backend Setup

#### Step 1: Create Virtual Environment

```bash
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

#### Step 3: Configure SpoonOS Path

```bash
# Add SpoonOS to Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/../spoon-core:$(pwd)/../spoon-toolkit"

# On Windows PowerShell:
# $env:PYTHONPATH="$env:PYTHONPATH;$PWD\..\spoon-core;$PWD\..\spoon-toolkit"
```

#### Step 4: Set Environment Variables

```bash
# From project root
cd ..
cp .env.example .env
nano .env  # Edit with your values

# Source the environment (Linux/Mac)
export $(cat .env | grep -v '^#' | xargs)

# On Windows, manually set each variable or use dotenv
```

#### Step 5: Run Backend

```bash
cd backend

# Using the run script (recommended)
./run.sh

# Or manually
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: http://localhost:8000

### Frontend Setup

#### Step 1: Install Dependencies

```bash
cd frontend
npm install
```

#### Step 2: Run Frontend

```bash
# Using the run script (recommended)
./run.sh

# Or manually
npm run dev
```

Frontend will be available at: http://localhost:5173

---

## Verification

### 1. Check Backend Health

```bash
curl http://localhost:8000/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "services": {
    "api": "ok"
  }
}
```

### 2. Check Frontend Connection

Open http://localhost:5173 in your browser. You should see:
- Spica dashboard
- Backend status: "OK"
- Version number displayed

### 3. Check API Documentation

Open http://localhost:8000/docs - you should see Swagger UI with available endpoints.

### 4. Test Hot Reload

**Backend:**
1. Edit `backend/app/main.py`
2. Add a comment or change the version string
3. Save the file
4. Check terminal - should see "Application startup complete"

**Frontend:**
1. Edit `frontend/src/App.tsx`
2. Change the header text
3. Save the file
4. Browser should auto-refresh with changes

---

## Troubleshooting

### Docker Issues

**Problem:** `docker-compose: command not found`

```bash
# Install Docker Desktop
# OR use docker compose (without hyphen) on newer versions
docker compose up --build
```

**Problem:** Port already in use

```bash
# Check what's using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or change port in docker-compose.yml
```

**Problem:** Containers won't start

```bash
# View logs
docker-compose logs backend
docker-compose logs frontend

# Rebuild from scratch
docker-compose down -v
docker-compose build --no-cache
docker-compose up
```

### Backend Issues

**Problem:** `ModuleNotFoundError: No module named 'spoon_ai'`

```bash
# Ensure SpoonOS is in PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/../spoon-core:$(pwd)/../spoon-toolkit"

# Verify spoon-core exists
ls ../spoon-core/spoon_ai/

# If missing, you need to clone/add SpoonOS source code
```

**Problem:** `uvicorn: command not found`

```bash
# Activate virtual environment
source venv/bin/activate

# Reinstall requirements
pip install -r requirements.txt
```

**Problem:** Neo RPC connection fails

```bash
# Test RPC endpoint
curl -X POST https://testnet1.neo.coz.io:443 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"getversion","params":[],"id":1}'

# If fails, try fallback in .env
NEO_TESTNET_RPC=https://testnet2.neo.coz.io:443
```

### Frontend Issues

**Problem:** `npm: command not found`

```bash
# Install Node.js from https://nodejs.org/
# Verify installation
node --version
npm --version
```

**Problem:** CORS errors in browser console

- Ensure backend is running on port 8000
- Check CORS settings in `backend/app/main.py`
- Verify `VITE_API_URL` in `.env` matches backend URL

**Problem:** Backend status shows "disconnected"

1. Verify backend is running: `curl http://localhost:8000/`
2. Check browser console for errors
3. Ensure ports match in frontend and backend

### Environment Variable Issues

**Problem:** API keys not being read

```bash
# Verify .env file exists
cat .env

# Check for typos in variable names
# Check for spaces around = sign (should be KEY=value, not KEY = value)

# Reload environment
export $(cat .env | grep -v '^#' | xargs)
```

**Problem:** WIF key format error

- WIF keys start with 'K' or 'L'
- Ensure no extra spaces or quotes
- Get from Neo wallet export/private key view

---

## Quick Reference Commands

### Docker

```bash
# Start services
docker-compose up

# Start in background
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Rebuild specific service
docker-compose up --build backend

# Clean restart
docker-compose down -v && docker-compose up --build
```

### Local Development

```bash
# Backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload

# Frontend
cd frontend
npm run dev

# Run tests
cd backend
pytest -v
```

---

## Next Steps

Once setup is complete:

1. ✅ Verify both frontend and backend are running
2. ✅ Check API documentation at http://localhost:8000/docs
3. ✅ Test hot reload by making small changes
4. ✅ Review the architecture document: `docs/architecture.md`
5. ✅ Ready to start feature development!

---

## Additional Resources

- [Architecture Document](docs/architecture.md) - System design and patterns
- [API Documentation](http://localhost:8000/docs) - Interactive API explorer
- [SpoonOS Documentation](https://xspoonai.github.io/) - AI agent framework
- [Neo N3 Documentation](https://docs.neo.org/) - Blockchain platform
- [x402 Protocol](https://x402.org/) - Payment standard

---

**Need Help?**

Check the main [README.md](README.md) or review logs for error messages.
