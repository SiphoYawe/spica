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

## Project Structure

```
spica/
├── frontend/              # Next.js 16 + TypeScript frontend
│   ├── src/
│   │   ├── app/           # Next.js App Router pages
│   │   │   ├── layout.tsx # Root layout with providers
│   │   │   ├── page.tsx   # Main workflow builder page
│   │   │   └── globals.css# Tailwind CSS styles
│   │   ├── components/
│   │   │   ├── layout/    # App layout components
│   │   │   ├── ui/        # shadcn/ui components
│   │   │   └── workflow/  # Workflow-specific components
│   │   ├── stores/        # Zustand state stores
│   │   ├── api/           # API client
│   │   ├── hooks/         # Custom React hooks
│   │   └── lib/           # Utility functions
│   ├── Dockerfile         # Frontend container
│   └── package.json
│
├── backend/               # FastAPI + SpoonOS backend
│   ├── app/
│   │   ├── main.py        # FastAPI application
│   │   ├── config.py      # Configuration
│   │   ├── api/           # API routes
│   │   ├── agents/        # SpoonOS agents
│   │   ├── services/      # Business logic
│   │   ├── models/        # Data models
│   │   └── utils/         # Utilities
│   ├── tests/             # Backend test suite
│   ├── Dockerfile         # Backend container
│   └── requirements.txt
│
├── spoon-core/            # SpoonOS framework (bundled)
├── spoon-toolkit/         # SpoonOS toolkits (bundled)
│
├── docker-compose.yml     # Multi-container orchestration
├── .env.example           # Environment variables template
└── README.md              # This file
```

## Getting Testnet Tokens

### Neo N3 Testnet (GAS & NEO)
1. Visit https://neoxwish.ngd.network/
2. Create or import a wallet
3. Request GAS and NEO tokens
4. Export your private key in WIF format for `DEMO_WALLET_WIF`

### Base Sepolia (ETH)
1. Visit https://www.alchemy.com/faucets/base-sepolia
2. Enter your Ethereum address
3. Receive testnet ETH for gas fees

### Base Sepolia USDC (for x402 payments)
- Use a Base Sepolia faucet or bridge to get testnet USDC
- Needed to pay for workflow deployments via x402

## API Documentation

Once the backend is running, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/parse` | POST | Parse natural language to workflow spec |
| `/api/generate` | POST | Generate graph from workflow spec |
| `/api/workflows` | GET | List all workflows |
| `/api/workflows/{id}/deploy` | POST | Deploy workflow (x402 protected) |
| `/api/workflows/{id}/execute` | POST | Manually trigger workflow |
| `/health` | GET | Health check |

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

## Testing

### Backend Tests

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_parser.py -v
```

### Frontend

```bash
cd frontend

# Run linting
npm run lint

# Build for production
npm run build
```

## Troubleshooting

### Docker Issues

**Problem:** Containers won't start
```bash
# Check container logs
docker-compose logs backend
docker-compose logs frontend

# Rebuild from scratch
docker-compose down -v
docker-compose up --build
```

**Problem:** Port already in use
```bash
# Find and kill process using port 8000
lsof -ti:8000 | xargs kill -9

# Or change ports in docker-compose.yml
```

### Backend Issues

**Problem:** SpoonOS import errors
```bash
# Verify PYTHONPATH includes SpoonOS directories
echo $PYTHONPATH

# Should include paths to spoon-core and spoon-toolkit
export PYTHONPATH="${PYTHONPATH}:/path/to/spoon-core:/path/to/spoon-toolkit"
```

**Problem:** Neo RPC connection fails
```bash
# Test RPC endpoint
curl https://testnet1.neo.coz.io:443 \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"getversion","params":[],"id":1}'

# Try fallback endpoint in .env
NEO_TESTNET_RPC=https://testnet2.neo.coz.io:443
```

### Frontend Issues

**Problem:** API calls fail with CORS error
- Ensure backend is running and accessible
- Check CORS configuration in `backend/app/main.py`
- Verify `NEXT_PUBLIC_API_URL` in `.env.local` matches backend URL

## Development Workflow

### Making Changes

1. **Frontend changes** - Next.js with Turbopack hot reload activates automatically
2. **Backend changes** - Uvicorn auto-reloads on file changes
3. **Both use Docker volumes** for live code updates

### Adding Dependencies

**Backend:**
```bash
# Add to requirements.txt
echo "new-package==1.0.0" >> backend/requirements.txt

# Rebuild backend container
docker-compose up --build backend
```

**Frontend:**
```bash
# Install package
cd frontend
npm install new-package

# Rebuild frontend container
docker-compose up --build frontend
```

### Adding shadcn/ui Components

```bash
cd frontend

# Add a new shadcn/ui component
npx shadcn@latest add <component-name>

# Example: add a calendar component
npx shadcn@latest add calendar
```

## Production Deployment

### Build for Production

```bash
# Build optimized images
docker-compose -f docker-compose.prod.yml build

# Deploy to your server
# (Configure docker-compose.prod.yml with production settings)
```

### Environment Variables for Production

Update `.env` with production values:
- Use **mainnet** RPC endpoints (when ready)
- Secure API keys using secrets management
- Enable HTTPS and proper CORS origins
- Set `DEBUG=false`

## Contributing

This is a hackathon project. Contributions welcome!

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License - See LICENSE file for details

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
