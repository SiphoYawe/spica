# Spica - AI-Powered DeFi Workflow Builder for Neo N3

Spica is an intelligent workflow automation platform for Neo N3 blockchain, powered by SpoonOS AI agents and secured by the x402 payment protocol.

## Features

- 🤖 **Natural Language Workflow Creation** - Describe DeFi strategies in plain English
- 🔗 **Neo N3 Integration** - Execute swaps, staking, and transfers on Neo testnet
- 💳 **x402 Payments** - Pay-per-deployment using USDC on Base Sepolia
- 📊 **Visual Workflow Builder** - See and edit your workflows as interactive graphs
- ⚡ **Real-time Execution** - Monitor triggers and execute actions automatically

## Tech Stack

### Frontend
- **React 18** with TypeScript
- **Vite** for fast development and building
- **React Flow** for graph visualization (to be added)

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
- **Frontend:** http://localhost:5173
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

# Run development server
npm run dev
```

Frontend will be available at http://localhost:5173

## Project Structure

```
spica/
├── frontend/              # React + TypeScript frontend
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── contexts/      # React contexts for state
│   │   ├── hooks/         # Custom React hooks
│   │   ├── api/           # API client
│   │   ├── types/         # TypeScript types
│   │   └── App.tsx        # Main app component
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

### Frontend Tests

```bash
cd frontend

# Run tests
npm test

# Run with coverage
npm run test:coverage
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
- Verify `VITE_API_URL` in `.env` matches backend URL

## Development Workflow

### Making Changes

1. **Frontend changes** - Vite hot reload activates automatically
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
- **React Flow** - Graph visualization

---

**Built for the Neo N3 + SpoonOS Hackathon**

Happy building! 🚀
