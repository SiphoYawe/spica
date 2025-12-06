# Spica Backend Services

This directory contains all business logic services for the Spica application.

## Services

### Neo Service (`neo_service.py`)

Neo N3 blockchain integration service.

**Capabilities:**
- Connect to Neo N3 testnet/mainnet via RPC
- Query blockchain state (block height, balances)
- Validate Neo addresses
- Fetch blocks and transactions
- Automatic failover to backup RPC

**Usage:**

```python
from app.services.neo_service import get_neo_service

# Get global service instance
neo = get_neo_service()

# Connect to testnet
await neo.connect_testnet()

# Get current block height
height = await neo.get_block_height()

# Query balance
balance = await neo.get_balance("NXsG3zwpwcfvBiA3bNMx6mWZGEro9ZqTqM")
print(f"GAS: {balance.gas_balance}")

# Close when done
await neo.close()
```

**Configuration:**

Set these environment variables:
- `NEO_TESTNET_RPC` - Primary RPC endpoint
- `NEO_TESTNET_RPC_FALLBACK` - Backup RPC endpoint
- `NEO_RPC_TIMEOUT` - Request timeout (seconds)

### SpoonOS Service (`spoon_service.py`)

SpoonOS AI agent framework integration.

*(To be implemented in future stories)*

### Payment Service

x402 payment protocol integration.

*(To be implemented in future stories)*

### Price Service

Token price data from CoinGecko.

*(To be implemented in future stories)*

## Service Patterns

### Singleton Pattern

Services use the singleton pattern for global state management:

```python
from app.services.neo_service import get_neo_service, close_neo_service

# Get instance (creates if doesn't exist)
service = get_neo_service()

# Close and cleanup
await close_neo_service()
```

### Error Handling

All services use custom exceptions for better error handling:

```python
from app.services.neo_service import NeoConnectionError, NeoRPCError

try:
    await neo.connect_testnet()
except NeoConnectionError as e:
    # Handle connection failures
    logger.error(f"Neo network unavailable: {e}")
except NeoRPCError as e:
    # Handle RPC errors
    logger.error(f"RPC error: {e}")
```

### Async/Await

All services are async-first for better performance:

```python
# Correct
result = await neo.get_block_height()

# Incorrect - will not work
result = neo.get_block_height()  # Missing await
```

## Testing

Each service has corresponding integration tests in `/backend/tests/`:

```bash
# Test Neo service
pytest tests/test_neo_integration.py -v

# Test all services
pytest tests/ -v
```

## Adding New Services

1. Create service file in this directory
2. Implement service class with async methods
3. Add singleton getter function
4. Create corresponding tests
5. Update this README

Example:

```python
# app/services/my_service.py

class MyService:
    async def do_something(self):
        # Implementation
        pass

_my_service = None

def get_my_service() -> MyService:
    global _my_service
    if _my_service is None:
        _my_service = MyService()
    return _my_service
```
