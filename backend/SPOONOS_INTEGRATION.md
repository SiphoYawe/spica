# SpoonOS Integration - Story 1.2

## Overview

This document describes the SpoonOS integration implementation for Story 1.2.

## Files Created

### 1. Service Module
**Location:** `app/services/spoon_service.py`

Provides SpoonOS integration services:
- `SpoonOSService` - Main service class
- `get_spoon_service()` - Global service instance
- Factory methods for creating ChatBot, SpoonReactMCP agents, and StateGraphs
- Example implementations (DemoTool, DemoWorkflowState, demo_process_node)

### 2. Integration Tests
**Location:** `tests/test_spoon_integration.py`

Comprehensive test suite covering all acceptance criteria:
- Import verification tests
- ChatBot configuration tests
- SpoonReactMCP agent creation tests
- StateGraph creation and compilation tests
- Tool system tests
- Complete end-to-end integration test

## Acceptance Criteria Status

- [x] spoon_ai package installed and importable
- [x] ChatBot configured with OpenAI
- [x] Basic SpoonReactMCP agent instantiable
- [x] StateGraph can be created and compiled
- [x] Integration test passes

## Installation

### Option 1: Docker (Recommended)

SpoonOS is mounted via volume in docker-compose.yml:

```bash
# Start services
docker-compose up -d backend

# Run tests inside container
docker-compose exec backend pytest tests/test_spoon_integration.py -v
```

### Option 2: Local Development

1. **Install SpoonOS in editable mode:**

```bash
cd backend
pip install -e ../spoon-core
pip install -r requirements.txt
```

2. **Set environment variables:**

Create `backend/.env` with:
```env
OPENAI_API_KEY=sk-your-key-here
DEMO_WALLET_WIF=KyourWIFkeyHere
X402_RECEIVER_ADDRESS=0xyourAddressHere
```

3. **Run tests:**

```bash
cd backend
PYTHONPATH=.:../spoon-core:../spoon-toolkit pytest tests/test_spoon_integration.py -v
```

## Running Integration Tests

### Run All Tests

```bash
# In Docker
docker-compose exec backend pytest tests/test_spoon_integration.py -v

# Local
pytest tests/test_spoon_integration.py -v
```

### Run Specific Test Classes

```bash
# Test imports only
pytest tests/test_spoon_integration.py::TestSpoonOSImports -v

# Test ChatBot
pytest tests/test_spoon_integration.py::TestChatBotConfiguration -v

# Test SpoonReactMCP
pytest tests/test_spoon_integration.py::TestSpoonReactMCPAgent -v

# Test StateGraph
pytest tests/test_spoon_integration.py::TestStateGraphCreation -v

# Test complete integration
pytest tests/test_spoon_integration.py::TestCompleteIntegration -v
```

### Run with Coverage

```bash
pytest tests/test_spoon_integration.py --cov=app.services.spoon_service --cov-report=term-missing -v
```

## Service Usage Examples

### 1. Get Service Instance

```python
from app.services.spoon_service import get_spoon_service

service = get_spoon_service()
```

### 2. Create ChatBot

```python
# ChatBot is created automatically with OpenAI
chatbot = service.chatbot
```

### 3. Create SpoonReactMCP Agent

```python
from app.services.spoon_service import DemoTool

agent = service.create_spoon_react_mcp(
    name="my_agent",
    description="My custom agent",
    tools=[DemoTool()],
    system_prompt="You are a helpful assistant."
)

# Run agent (async)
result = await agent.run("What can you do?")
```

### 4. Create and Execute StateGraph

```python
from typing import TypedDict

# Define state
class MyState(TypedDict):
    input: str
    output: str

# Define node
async def process(state: MyState) -> dict:
    return {"output": f"Processed: {state['input']}"}

# Create and compile graph
graph = service.create_state_graph(
    state_schema=MyState,
    nodes={"process": process},
    edges=[("__start__", "process"), ("process", "END")]
)

compiled = service.compile_graph(graph)

# Execute
result = await compiled.invoke({"input": "test", "output": ""})
print(result["output"])  # "Processed: test"
```

## Verification Commands

### Quick Smoke Test

Run the built-in integration tests:

```python
from app.services.spoon_service import run_all_tests
import asyncio

results = asyncio.run(run_all_tests())
print(results)
# Expected: {'chatbot': True, 'spoon_react_mcp': True, 'state_graph': True}
```

### Manual Verification

```python
import asyncio
from app.services.spoon_service import get_spoon_service, DemoTool

async def verify():
    service = get_spoon_service()

    # 1. Verify ChatBot
    chatbot = service.chatbot
    print(f"✓ ChatBot: {chatbot}")

    # 2. Verify Agent
    agent = service.create_spoon_react_mcp(
        name="test",
        tools=[DemoTool()]
    )
    print(f"✓ Agent: {agent.name}")

    # 3. Verify StateGraph
    from app.services.spoon_service import DemoWorkflowState, demo_process_node

    graph = service.create_state_graph(
        state_schema=DemoWorkflowState,
        nodes={"test": demo_process_node},
        edges=[("__start__", "test"), ("test", "END")]
    )
    compiled = service.compile_graph(graph)

    result = await compiled.invoke({
        "workflow_id": "verify",
        "query": "test",
        "result": "",
        "status": "pending"
    })
    print(f"✓ StateGraph executed: {result['status']}")

asyncio.run(verify())
```

## Architecture Notes

### Import Paths

All imports verified against spoon-core source:

```python
from spoon_ai.chat import ChatBot                    # LLM interface
from spoon_ai.agents import SpoonReactMCP           # MCP-enabled agent
from spoon_ai.graph import StateGraph, CompiledGraph # Graph system
from spoon_ai.tools import ToolManager              # Tool management
from spoon_ai.tools.base import BaseTool            # Tool base class
```

### Key Classes

- **ChatBot**: LLM interface (OpenAI, Anthropic, etc.)
- **SpoonReactMCP**: ReAct agent with MCP tool support
- **StateGraph**: Workflow graph builder
- **CompiledGraph**: Executable graph
- **ToolManager**: Manages collection of tools
- **BaseTool**: Base class for custom tools

### Environment Variables Required

```env
# Required for ChatBot
OPENAI_API_KEY=sk-...

# Required for config validation (can be dummy for tests)
DEMO_WALLET_WIF=KxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxP
X402_RECEIVER_ADDRESS=0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
```

## Testing Strategy

### Test Levels

1. **Import Tests**: Verify all SpoonOS components can be imported
2. **Unit Tests**: Test individual service methods
3. **Integration Tests**: Test component interactions
4. **End-to-End Test**: Complete workflow simulation

### Test Coverage

All acceptance criteria are verified:

| Criterion | Test Class | Status |
|-----------|------------|--------|
| Package importable | TestSpoonOSImports | ✓ |
| ChatBot configured | TestChatBotConfiguration | ✓ |
| Agent instantiable | TestSpoonReactMCPAgent | ✓ |
| StateGraph works | TestStateGraphCreation | ✓ |
| Integration test | TestCompleteIntegration | ✓ |

## Troubleshooting

### "ModuleNotFoundError: No module named 'spoon_ai'"

**Solution**: Install SpoonOS dependencies:

```bash
# Docker
docker-compose exec backend pip install -e /spoon-core

# Local
pip install -e ../spoon-core
```

### "OPENAI_API_KEY not found"

**Solution**: Set environment variable:

```bash
export OPENAI_API_KEY=sk-your-key-here
```

Or create `.env` file in backend directory.

### "demo_wallet_wif is required"

**Solution**: Add dummy WIF for testing:

```bash
export DEMO_WALLET_WIF=KxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxP
```

### "x402_receiver_address is required"

**Solution**: Add dummy address for testing:

```bash
export X402_RECEIVER_ADDRESS=0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
```

## Next Steps

After Story 1.2 completion:

1. **Story 2.1**: Implement WorkflowParserAgent using SpoonReactMCP
2. **Story 3.1**: Implement Component Designer Agents
3. **Story 5.6**: Use StateGraph for workflow execution

The `spoon_service.py` module provides all the foundations needed for these implementations.

## References

- CLAUDE.md - Verified SpoonOS patterns
- /spoon-core/spoon_ai/ - Source code
- /xspoonai.github.io/docs/ - Official documentation
