<p align="center">
  <img src="frontend/public/spica-logo.svg" alt="Spica Logo" width="400" />
</p>

# Spica - AI-Powered DeFi Workflow Builder for Neo N3

Spica is an intelligent workflow automation platform for Neo N3 blockchain, powered by SpoonOS AI agents and secured by the x402 payment protocol.

## Features

- **Natural Language Workflow Creation** - Describe DeFi strategies in plain English
- **Neo N3 Integration** - Execute swaps, staking, and transfers on Neo testnet
- **x402 Payments** - Pay-per-deployment using USDC on Base Sepolia
- **Visual Workflow Builder** - See and edit your workflows as interactive graphs
- **Real-time Execution** - Monitor triggers and execute actions automatically

## Tech Stack

### Frontend

- **Next.js 16** with React 19 and TypeScript
- **Tailwind CSS v4** for styling
- **shadcn/ui** component library
- **ReactFlow** for graph visualization
- **Zustand** for state management

### Backend

- **FastAPI** with Python 3.11+
- **SpoonOS** for AI agent orchestration
- **Neo3** Python libraries for blockchain interaction
- **x402 Protocol** for payment integration

### Blockchain

- **Neo N3 Testnet** for DeFi operations
- **Base Sepolia** for x402 USDC payments

## Prerequisites

Before you begin, ensure you have the following installed:

- **Docker** & **Docker Compose** (recommended for easy setup)
- **Python 3.11+** (if running without Docker)
- **Node.js 20+** (if running without Docker)
- **Git** for cloning the repository

## Quick Start (Docker - Recommended)

### 1. Clone the Repository

```bash
git clone https://github.com/SiphoYawe/spica.git
cd spica
```

### 2. Set Up Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and fill in your API keys and wallet addresses
nano .env  # or use your preferred editor
```

**Required environment variables:**

- `OPENAI_API_KEY` - Get from https://platform.openai.com/api-keys
- `DEMO_WALLET_WIF` - Generate testnet wallet at https://neoxwish.ngd.network/
- `X402_RECEIVER_ADDRESS` - Your Ethereum address for receiving payments

### 3. Start the Application

```bash
# Build and start all services
docker-compose up --build

# Or run in detached mode
docker-compose up -d
```

The application will be available at:

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs

### 4. Verify Installation

```bash
# Check backend health
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","services":{"api":"ok"}}
```

## Development Setup (Without Docker)

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp ../.env.example ../.env
# Edit .env with your values

# Add SpoonOS to Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/../spoon-core:$(pwd)/../spoon-toolkit"

# Run development server with hot reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at http://localhost:8000

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server (with Turbopack)
npm run dev
```

Frontend will be available at http://localhost:3000

## API Documentation

Once the backend is running, visit:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Key Endpoints

| Endpoint                      | Method | Description                             |
| ----------------------------- | ------ | --------------------------------------- |
| `/api/parse`                  | POST   | Parse natural language to workflow spec |
| `/api/generate`               | POST   | Generate graph from workflow spec       |
| `/api/workflows`              | GET    | List all workflows                      |
| `/api/workflows/{id}/deploy`  | POST   | Deploy workflow (x402 protected)        |
| `/api/workflows/{id}/execute` | POST   | Manually trigger workflow               |
| `/health`                     | GET    | Health check                            |

## Usage Example

### 1. Create a Workflow

```bash
# Parse natural language to workflow spec
curl -X POST http://localhost:8000/api/parse \
  -H "Content-Type: application/json" \
  -d '{
    "input": "When GAS price drops below $5, swap 50 GAS to bNEO on Flamingo"
  }'
```

### 2. Generate Graph Visualization

```bash
# Convert workflow spec to graph
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_spec": { ... }
  }'
```

### 3. Deploy Workflow (requires x402 payment)

```bash
# First request returns 402 with payment details
curl -X POST http://localhost:8000/api/workflows/workflow_123/deploy

# Send payment and retry with X-PAYMENT header
curl -X POST http://localhost:8000/api/workflows/workflow_123/deploy \
  -H "X-PAYMENT: {payment_proof}"
```

## Contributing

This is a hackathon project. Contributions welcome!

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Support

- **Documentation:** https://xspoonai.github.io/
- **Neo N3 Docs:** https://docs.neo.org/
- **x402 Protocol:** https://x402.org/

## Acknowledgments

- **SpoonOS** - AI agent framework
- **Neo N3** - Blockchain platform
- **x402 Protocol** - Payment standard
- **ReactFlow** - Graph visualization
- **shadcn/ui** - UI component library

---

**Built for the Agentic Hackathon with SpoonOS and Neo at Encode Hub**
