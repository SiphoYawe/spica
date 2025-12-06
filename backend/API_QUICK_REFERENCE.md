# Spica API Quick Reference

## Getting Started

### Start the Server
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

### View Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

---

## Health Check Endpoints

### Simple Health Check
**Use for:** Load balancers, quick status checks

```bash
curl http://localhost:8000/api/health
```

**Response:**
```json
{
  "status": "ok",
  "service": "Spica API",
  "version": "0.1.0",
  "timestamp": "2025-12-06T00:00:00.000000"
}
```

### Detailed Health Check
**Use for:** Monitoring dashboards, service status

```bash
curl http://localhost:8000/api/v1/health
```

**Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "services": {
    "api": {
      "status": "ok",
      "message": "API operational",
      "latency_ms": 2.1
    },
    "neo_rpc": {
      "status": "ok",
      "message": "Connected to Neo N3 testnet",
      "latency_ms": 150.5
    },
    "spoonos": {
      "status": "ok",
      "message": "SpoonOS agents ready",
      "latency_ms": 5.3
    }
  },
  "timestamp": "2025-12-06T00:00:00.000000"
}
```

---

## CORS Configuration

### Allowed Origins
- `http://localhost:5173` (Vite dev server)
- `http://localhost:3000` (Alternative dev)
- `http://frontend:5173` (Docker)

### Allowed Methods
- GET
- POST
- PUT
- DELETE
- OPTIONS

### Allowed Headers
- Content-Type
- Authorization
- Accept
- X-Requested-With
- **X-PAYMENT-REQUEST** (x402)
- **X-PAYMENT** (x402)
- **X-PAYMENT-SIGNATURE** (x402)

### Test CORS
```bash
curl -H "Origin: http://localhost:5173" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: X-PAYMENT" \
     -X OPTIONS \
     http://localhost:8000/api/health -v
```

---

## API Versioning

### Current Structure
```
/                     → Root service info
/health               → Legacy health (backward compat)
/api/health           → Simple health check
/api/v1/health        → Detailed health check (v1)
/api/v1/health/simple → Simple health check (v1)
```

### Using Versioned Endpoints
```bash
# v1 API
curl http://localhost:8000/api/v1/health

# Non-versioned (backward compatibility)
curl http://localhost:8000/api/health
```

---

## Response Models

### HealthCheckResponse
```json
{
  "status": "ok",
  "service": "Spica API",
  "version": "0.1.0",
  "timestamp": "2025-12-06T00:00:00.000000"
}
```

### DetailedHealthResponse
```json
{
  "status": "healthy|degraded|unhealthy",
  "version": "0.1.0",
  "services": {
    "service_name": {
      "status": "ok|degraded|down",
      "message": "Status message",
      "latency_ms": 123.45
    }
  },
  "timestamp": "2025-12-06T00:00:00.000000"
}
```

### ErrorResponse
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": "Additional details",
    "retry": true
  },
  "timestamp": "2025-12-06T00:00:00.000000"
}
```

---

## Testing

### Run All API Tests
```bash
cd backend
python -m pytest tests/test_api.py -v
```

### Run Specific Test Class
```bash
# Test CORS only
python -m pytest tests/test_api.py::TestCORSConfiguration -v

# Test health endpoints only
python -m pytest tests/test_api.py::TestHealthEndpoints -v

# Test OpenAPI docs
python -m pytest tests/test_api.py::TestOpenAPIDocumentation -v
```

### Run Single Test
```bash
python -m pytest tests/test_api.py::TestCORSConfiguration::test_cors_allows_x402_headers -v
```

---

## Common Use Cases

### Frontend Integration

**Check API Status:**
```javascript
const response = await fetch('http://localhost:8000/api/health');
const data = await response.json();
console.log(data.status); // "ok"
```

**With CORS Headers:**
```javascript
const response = await fetch('http://localhost:8000/api/v1/health', {
  method: 'GET',
  headers: {
    'Content-Type': 'application/json',
  },
  credentials: 'include'
});
```

### Load Balancer Health Check
```yaml
# Example: Docker Compose health check
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
  interval: 30s
  timeout: 10s
  retries: 3
```

### Monitoring Dashboard
```bash
# Get detailed service status
curl -s http://localhost:8000/api/v1/health | jq '.services'
```

---

## Status Codes

| Code | Meaning | When |
|------|---------|------|
| 200 | OK | Request successful |
| 404 | Not Found | Endpoint doesn't exist |
| 405 | Method Not Allowed | Wrong HTTP method |
| 503 | Service Unavailable | Service unhealthy |

---

## Next Steps

After Story 1.4, the API is ready for:

1. **Workflow Endpoints** - `/api/v1/workflows`
2. **Parse Endpoint** - `/api/v1/parse`
3. **Deploy Endpoint** - `/api/v1/workflows/{id}/deploy` (with x402)
4. **Execute Endpoint** - `/api/v1/workflows/{id}/execute`

See `docs/architecture.md` for complete API design.

---

## Troubleshooting

### Server won't start
```bash
# Check if port 8000 is in use
lsof -i :8000

# Try different port
uvicorn app.main:app --port 8001
```

### CORS errors in browser
1. Check origin is in allowed list (main.py)
2. Verify headers are allowed
3. Check browser console for specific error

### Tests failing
```bash
# Install dependencies
pip install -r requirements.txt

# Clear cache
pytest --cache-clear

# Verbose output
pytest tests/test_api.py -vv
```

---

**For full API documentation, visit:** http://localhost:8000/docs
