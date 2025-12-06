# Spica Backend Tests

This directory contains all tests for the Spica backend.

## Test Organization

- `test_neo_integration.py` - Neo N3 blockchain integration tests (Story 1.3)

## Running Tests

### Prerequisites

1. Install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

2. Configure environment:
```bash
cp ../.env.example ../.env
# Edit .env with your actual values
```

### Run All Tests

```bash
cd backend
pytest tests/ -v
```

### Run Specific Test File

```bash
# Neo integration tests
pytest tests/test_neo_integration.py -v

# With output
pytest tests/test_neo_integration.py -v -s
```

### Run Specific Test

```bash
# Story 1.3 acceptance criteria verification
pytest tests/test_neo_integration.py::test_story_1_3_acceptance_criteria -v -s
```

### Run by Test Class

```bash
# Connection tests only
pytest tests/test_neo_integration.py::TestNeoServiceConnection -v

# Balance tests only
pytest tests/test_neo_integration.py::TestNeoServiceBalances -v
```

## Test Coverage

To generate test coverage report:

```bash
pytest tests/ --cov=app --cov-report=html
open htmlcov/index.html
```

## Story 1.3 Verification

To verify all acceptance criteria for Story 1.3: Neo N3 Connection:

```bash
pytest tests/test_neo_integration.py::test_story_1_3_acceptance_criteria -v -s
```

This test verifies:
- ✓ neo3 library installed
- ✓ RPC client connects to testnet
- ✓ Can query demo wallet balance
- ✓ Can fetch current block height
- ✓ Connection timeout handling works

## Test Output Example

```
✓ Criterion 1: Neo libraries importable
  - neo_service module imported successfully
  - httpx for RPC calls available

✓ Criterion 2: RPC client connects to testnet
  - Connected: True
  - RPC URL: https://testnet1.neo.coz.io:443
  - Version: /NEO-GO:0.112.0/

✓ Criterion 3: Can query wallet balance
  - Address: NXsG3zwpwcfvBiA3bNMx6mWZGEro9ZqTqM
  - GAS balance: 0
  - NEO balance: 0

✓ Criterion 4: Can fetch current block height
  - Current height: 11673747

✓ Criterion 5: Connection timeout handling works
  - Timeout handled correctly: NeoConnectionError
```

## Debugging Tests

### Run with extra verbosity

```bash
pytest tests/test_neo_integration.py -vv -s
```

### Run specific test with debugging

```bash
pytest tests/test_neo_integration.py::TestNeoServiceConnection::test_connect_testnet_success -vv -s --pdb
```

### See print statements

```bash
pytest tests/ -v -s
```

## Notes

- Neo integration tests connect to the live Neo N3 testnet
- Tests may take a few seconds due to network calls
- Ensure you have internet connectivity
- Some tests verify error handling (timeout, invalid RPC, etc.)
- All tests are designed to work with or without a funded demo wallet
