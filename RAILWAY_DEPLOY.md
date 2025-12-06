# Railway Deployment Guide for Spica

This guide covers deploying Spica (backend + frontend) to Railway.

## Prerequisites

- Railway account at [railway.app](https://railway.app)
- GitHub repository with Spica code pushed
- Required API keys (see Environment Variables section)

---

## Quick Deploy Steps

### 1. Create Railway Project

1. Go to [railway.app/new](https://railway.app/new)
2. Click **"Deploy from GitHub repo"**
3. Select your Spica repository
4. Railway will create a new project

### 2. Deploy Backend Service

1. In your Railway project, click **"+ New"** → **"GitHub Repo"**
2. Select your Spica repository
3. **Configure the service:**
   - **Name**: `backend`
   - **Root Directory**: Leave empty (use repo root)
   - **Build Command**: Leave empty
   - **Dockerfile Path**: `Dockerfile.backend`

4. **Add Environment Variables** (click on the service → Variables tab):
   ```
   # Required
   OPENAI_API_KEY=sk-your-openai-key
   DEMO_WALLET_WIF=your-neo-wallet-wif

   # Optional (has defaults)
   NEO_TESTNET_RPC=https://testnet1.neo.coz.io:443
   NEO_TESTNET_RPC_FALLBACK=https://testnet2.neo.coz.io:443
   NEO_RPC_TIMEOUT=60

   # x402 Payments (optional for demo mode)
   X402_RECEIVER_ADDRESS=0x-your-ethereum-address
   X402_FACILITATOR_URL=https://x402-facilitator.example.com
   X402_NETWORK=base-sepolia
   X402_DEFAULT_ASSET=USDC

   # Production settings
   ENVIRONMENT=production
   DEBUG=false
   SPICA_DEMO_MODE=true
   ```

5. Click **Deploy**
6. Once deployed, note the generated URL (e.g., `https://backend-xxx.railway.app`)

### 3. Deploy Frontend Service

1. Click **"+ New"** → **"GitHub Repo"** again
2. Select the same Spica repository
3. **Configure the service:**
   - **Name**: `frontend`
   - **Root Directory**: Leave empty (use repo root)
   - **Dockerfile Path**: `Dockerfile.frontend`

4. **Add Environment Variables:**
   ```
   # Point to your backend URL from step 2
   NEXT_PUBLIC_API_URL=https://backend-xxx.railway.app
   ```

5. Click **Deploy**

### 4. Configure Networking

Both services will automatically get public URLs. You can customize domains:

1. Click on each service → **Settings** → **Networking**
2. Generate domain or add custom domain
3. Update `NEXT_PUBLIC_API_URL` in frontend if backend URL changes

---

## Environment Variables Reference

### Backend (Required)

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key for LLM | `sk-...` |
| `DEMO_WALLET_WIF` | Neo N3 wallet private key (WIF format) | `KxDg...` or `Lx...` |

### Backend (Optional)

| Variable | Default | Description |
|----------|---------|-------------|
| `NEO_TESTNET_RPC` | `https://testnet1.neo.coz.io:443` | Primary Neo testnet RPC |
| `NEO_TESTNET_RPC_FALLBACK` | `https://testnet2.neo.coz.io:443` | Fallback RPC |
| `NEO_RPC_TIMEOUT` | `60` | RPC timeout in seconds |
| `ENVIRONMENT` | `development` | Set to `production` |
| `DEBUG` | `true` | Set to `false` for production |
| `SPICA_DEMO_MODE` | `false` | Enable to bypass x402 payments |
| `COINGECKO_API_KEY` | - | Optional for price data |

### Backend (x402 Payments)

| Variable | Default | Description |
|----------|---------|-------------|
| `X402_RECEIVER_ADDRESS` | - | Ethereum address for payments |
| `X402_FACILITATOR_URL` | - | x402 facilitator service URL |
| `X402_NETWORK` | `base-sepolia` | Network (base-sepolia, base) |
| `X402_DEFAULT_ASSET` | `USDC` | Payment asset |

### Frontend

| Variable | Description | Example |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | `https://backend-xxx.railway.app` |

---

## Dockerfile Structure

The deployment uses two root-level Dockerfiles:

```
spica/
├── Dockerfile.backend    # Backend + SpoonOS dependencies
├── Dockerfile.frontend   # Next.js production build
├── .dockerignore         # Exclude unnecessary files
├── backend/              # FastAPI application
├── frontend/             # Next.js application
├── spoon-core/           # SpoonOS framework
└── spoon-toolkit/        # SpoonOS toolkits
```

### Why Root-Level Dockerfiles?

The backend requires SpoonOS dependencies (`spoon-core/` and `spoon-toolkit/`) which are at the repository root. Building from root allows copying these into the Docker image.

---

## Health Checks

Both services include health checks:

- **Backend**: `GET /health` returns `{"status": "healthy"}`
- **Frontend**: `GET /` returns the app page

Railway automatically monitors these endpoints.

---

## Troubleshooting

### Backend fails to start

1. Check logs in Railway dashboard
2. Verify all required environment variables are set
3. Ensure `OPENAI_API_KEY` is valid
4. Check `DEMO_WALLET_WIF` is in correct WIF format (starts with K or L, 52 chars)

### Frontend can't connect to backend

1. Verify `NEXT_PUBLIC_API_URL` is set correctly
2. Ensure backend is fully deployed and healthy
3. Check CORS - backend allows Railway domains

### SpoonOS import errors

1. Verify `Dockerfile.backend` is being used (not `backend/Dockerfile.prod`)
2. Check that `PYTHONPATH` includes SpoonOS directories

### Build times are slow

1. Railway caches Docker layers - subsequent builds are faster
2. Consider using Railway's build cache settings

---

## Updating Deployments

Railway auto-deploys on git push. To manually redeploy:

1. Go to service → **Deployments** tab
2. Click **"Redeploy"** or trigger via `git push`

---

## Cost Estimation

Railway pricing (as of 2024):
- **Free tier**: $5 credit/month, enough for testing
- **Pro plan**: $20/month, includes more resources

Spica resource usage:
- Backend: ~256-512MB RAM, low CPU
- Frontend: ~128-256MB RAM, minimal CPU

---

## Alternative: Railway CLI

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link to project
railway link

# Deploy backend
railway up --service backend

# Deploy frontend
railway up --service frontend
```

---

## Support

- Railway docs: https://docs.railway.app
- Spica issues: Check project repository
