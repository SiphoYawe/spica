# Designer Agents Module

Specialized AI agents for designing workflow node specifications from parsed WorkflowSpec components.

## Overview

The designer agents module provides four specialized agents that transform workflow components into React Flow-compatible node specifications. These agents run in parallel for optimal performance when designing complete workflows.

## Architecture

```
WorkflowSpec (from parser)
    │
    ├─→ TriggerDesignerAgent    → trigger node spec
    ├─→ SwapDesignerAgent        → swap node spec
    ├─→ StakeDesignerAgent       → stake node spec
    └─→ TransferDesignerAgent    → transfer node spec
         │
         └─→ Complete React Flow graph
```

## Designer Agents

### BaseDesignerAgent

Abstract base class providing:
- Common node specification structure
- Position management for React Flow
- Standardized output format
- Helper methods for formatting

All designer agents extend `SpoonReactMCP` and implement the `design_node()` method.

### TriggerDesignerAgent

**Purpose:** Design trigger nodes for price and time conditions

**Node Type:** `trigger`

**Handles:**
- Price triggers (GAS/NEO/bNEO price monitoring)
- Time triggers (cron schedules, natural language)

**Example Output:**
```python
NodeSpecification(
    id="trigger_1",
    type="trigger",
    label="GAS price below $5.00",
    parameters={
        "type": "price",
        "token": "GAS",
        "operator": "below",
        "value": 5.0
    },
    position={"x": 250, "y": 0},
    data={"label": "...", "icon": "trigger", "status": "pending"}
)
```

### SwapDesignerAgent

**Purpose:** Design swap action nodes for Flamingo token swaps

**Node Type:** `swap`

**Handles:**
- Token swaps (GAS ↔ NEO ↔ bNEO)
- Fixed amounts or percentage-based swaps

**Example Output:**
```python
NodeSpecification(
    id="action_1",
    type="swap",
    label="Swap 10.0 GAS → NEO",
    parameters={
        "type": "swap",
        "from_token": "GAS",
        "to_token": "NEO",
        "amount": 10.0
    },
    position={"x": 250, "y": 150},
    data={"label": "...", "icon": "swap", "status": "pending"}
)
```

### StakeDesignerAgent

**Purpose:** Design stake action nodes for Flamingo staking

**Node Type:** `stake`

**Handles:**
- Token staking (GAS, NEO, bNEO)
- Fixed amounts or percentage-based staking

**Example Output:**
```python
NodeSpecification(
    id="action_2",
    type="stake",
    label="Stake 50.0% NEO",
    parameters={
        "type": "stake",
        "token": "NEO",
        "percentage": 50.0
    },
    position={"x": 250, "y": 300},
    data={"label": "...", "icon": "stake", "status": "pending"}
)
```

### TransferDesignerAgent

**Purpose:** Design transfer action nodes for NEP-17 token transfers

**Node Type:** `transfer`

**Handles:**
- NEP-17 token transfers
- Address shortening for display (Nabc...xyz)
- Fixed amounts or percentage-based transfers

**Example Output:**
```python
NodeSpecification(
    id="action_3",
    type="transfer",
    label="Transfer 5.0 GAS to NNLi...NEs",
    parameters={
        "type": "transfer",
        "token": "GAS",
        "to_address": "NNLi44dJNXtDNSBkofB48aTVYtb1zZrNEs",
        "amount": 5.0
    },
    position={"x": 250, "y": 450},
    data={"label": "...", "icon": "transfer", "status": "pending"}
)
```

## Parallel Execution

The `design_workflow_nodes()` function orchestrates parallel execution of all designer agents using `asyncio.gather()`.

### Benefits

1. **Speed:** All nodes designed simultaneously
2. **Efficiency:** Maximum utilization of async capabilities
3. **Scalability:** Handles complex multi-step workflows efficiently

### Usage

```python
from app.agents.designers import design_workflow_nodes
from app.agents import create_workflow_parser

# Parse workflow from natural language
parser = create_workflow_parser()
result = await parser.parse_workflow(
    "When GAS drops below $5, swap 10 GAS for NEO and stake it"
)

# Design all nodes in parallel
nodes = await design_workflow_nodes(result.workflow)

# nodes[0] = trigger node
# nodes[1] = swap node
# nodes[2] = stake node
```

## Node Specification Format

All designer agents return `NodeSpecification` objects with this structure:

```python
class NodeSpecification(BaseModel):
    id: str                    # Unique identifier (e.g., "trigger_1")
    type: str                  # Node type ("trigger", "swap", "stake", "transfer")
    label: str                 # Human-readable label
    parameters: Dict[str, Any] # Action/trigger specific parameters
    position: NodePosition     # {x: int, y: int} for React Flow
    data: NodeData            # {label, icon, status} for React Flow
```

### Position Layout

Nodes are positioned vertically with automatic spacing:

- **Trigger:** x=250, y=0
- **Action 1:** x=250, y=150
- **Action 2:** x=250, y=300
- **Action 3:** x=250, y=450
- etc.

This creates a clean vertical flow from trigger → actions.

## React Flow Integration

Convert node specifications to React Flow format:

```python
from app.agents.designers import workflow_to_react_flow

# Get nodes from designers
nodes = await design_workflow_nodes(workflow_spec)

# Convert to React Flow format
react_flow_data = workflow_to_react_flow(nodes)

# Returns:
# {
#   "nodes": [...],  # Node specifications
#   "edges": [...]   # Connections between nodes
# }
```

## Factory Functions

Each designer has a factory function for easy instantiation:

```python
from app.agents.designers import (
    create_trigger_designer,
    create_swap_designer,
    create_stake_designer,
    create_transfer_designer
)

# Create individual designers
trigger_designer = create_trigger_designer()
swap_designer = create_swap_designer()

# Optional: Share LLM instance across agents
from spoon_ai.chat import ChatBot

llm = ChatBot(llm_provider="openai")
trigger_designer = create_trigger_designer(llm=llm)
swap_designer = create_swap_designer(llm=llm)
```

## Testing

Comprehensive tests available in `/tests/test_designers.py`:

```bash
# Run all designer tests
pytest tests/test_designers.py -v

# Run specific test class
pytest tests/test_designers.py::TestTriggerDesignerAgent -v

# Run parallel execution tests
pytest tests/test_designers.py::TestParallelExecution -v
```

## Integration Example

Complete workflow: Parse → Design → React Flow

```python
from app.agents import create_workflow_parser
from app.agents.designers import design_workflow_nodes, workflow_to_react_flow

async def create_workflow_graph(user_input: str):
    # Step 1: Parse natural language
    parser = create_workflow_parser()
    parse_result = await parser.parse_workflow(user_input)

    if not parse_result.success:
        return {"error": parse_result.error}

    # Step 2: Design nodes in parallel
    nodes = await design_workflow_nodes(parse_result.workflow)

    # Step 3: Convert to React Flow format
    graph = workflow_to_react_flow(nodes)

    return {
        "workflow": parse_result.workflow.model_dump(),
        "graph": graph
    }

# Example usage
result = await create_workflow_graph(
    "When GAS drops below $5, swap 10 GAS for NEO"
)
```

## Performance

Parallel execution provides significant performance benefits:

- **Sequential:** ~4-6 seconds for 4-node workflow
- **Parallel:** ~1-2 seconds for 4-node workflow
- **Speedup:** 2-3x faster for multi-step workflows

## Error Handling

All designer agents include robust error handling:

1. **Input Validation:** Pydantic models validate all inputs
2. **Type Checking:** Strong typing with Python type hints
3. **Graceful Degradation:** Fallbacks for missing/invalid data
4. **Logging:** Comprehensive logging for debugging

## Extending

To add a new designer agent:

1. Create new file in `app/agents/designers/`
2. Extend `BaseDesignerAgent`
3. Implement `design_node()` method
4. Add factory function
5. Export from `__init__.py`
6. Add tests to `test_designers.py`

Example:

```python
from .base import BaseDesignerAgent, NodeSpecification

class MyDesignerAgent(BaseDesignerAgent):
    name = "my_designer"
    node_type = "my_type"
    icon = "my_icon"

    async def design_node(self, component, node_id, position=None):
        label = f"My custom label: {component.field}"
        parameters = component.model_dump()
        return self._create_node_spec(node_id, label, parameters, position)
```

## Dependencies

- **SpoonOS:** `SpoonReactMCP` base agent class
- **Pydantic:** Data validation and serialization
- **asyncio:** Parallel execution
- **app.models.workflow_models:** Workflow specifications

## License

Part of the Spica project - see project LICENSE
