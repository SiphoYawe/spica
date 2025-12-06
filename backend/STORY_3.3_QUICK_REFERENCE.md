# Story 3.3: Generate API Endpoint - Quick Reference

## Overview

**Endpoint:** `POST /api/v1/generate`
**Purpose:** Convert WorkflowSpec into visual graph with nodes and edges
**Status:** ✅ Complete

---

## Quick Start

### 1. Start Backend Server

```bash
cd backend
./run.sh
```

### 2. Send Request

```bash
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_spec": {
      "name": "Auto DCA into NEO",
      "description": "When GAS price falls below $5, swap 10 GAS for NEO",
      "trigger": {
        "type": "price",
        "token": "GAS",
        "operator": "below",
        "value": 5.0
      },
      "steps": [
        {
          "action": {
            "type": "swap",
            "from_token": "GAS",
            "to_token": "NEO",
            "amount": 10.0
          }
        }
      ]
    }
  }'
```

### 3. Response

```json
{
  "success": true,
  "workflow_id": "wf_abc123def456",
  "nodes": [
    {
      "id": "trigger_1",
      "type": "trigger",
      "label": "GAS price below $5.00",
      "position": {"x": 250, "y": 0},
      "data": {...}
    },
    {
      "id": "action_1",
      "type": "swap",
      "label": "Swap 10.0 GAS → NEO",
      "position": {"x": 250, "y": 150},
      "data": {...}
    }
  ],
  "edges": [
    {
      "id": "e1",
      "source": "trigger_1",
      "target": "action_1",
      "type": "default",
      "animated": false
    }
  ],
  "workflow_name": "Auto DCA into NEO",
  "workflow_description": "When GAS price falls below $5, swap 10 GAS for NEO",
  "generation_time_ms": 234.56,
  "sla_exceeded": false
}
```

---

## API Documentation

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI Spec:** http://localhost:8000/openapi.json

---

## Files Created

### Core Implementation

1. **`app/services/workflow_storage.py`**
   - WorkflowStorage service for JSON file storage
   - CRUD operations: save, load, list, delete
   - Storage statistics and utilities

2. **`app/api/v1/workflow.py`** (modified)
   - Added `GenerateRequest` model
   - Added `GenerateSuccessResponse` model
   - Added `generate_workflow_graph` endpoint

3. **`data/workflows/`**
   - Storage directory for workflow JSON files
   - Format: `{workflow_id}.json`

### Testing

1. **`test_generate_endpoint.py`**
   - Standalone test for complete pipeline
   - Validates all acceptance criteria

2. **`test_generate_api.sh`**
   - curl-based API test
   - Example of endpoint usage

---

## Request Model

```python
class GenerateRequest(BaseModel):
    workflow_spec: WorkflowSpec  # Required
    user_id: Optional[str] = "anonymous"
    user_address: Optional[str] = "N/A"
```

### WorkflowSpec Structure

```python
{
  "name": str,              # Workflow name
  "description": str,       # Workflow description
  "trigger": {              # PriceCondition or TimeCondition
    "type": "price" | "time",
    ...                     # Trigger-specific fields
  },
  "steps": [                # List of WorkflowStep
    {
      "action": {           # SwapAction, StakeAction, or TransferAction
        "type": "swap" | "stake" | "transfer",
        ...                 # Action-specific fields
      },
      "description": str    # Optional step description
    }
  ]
}
```

---

## Response Model

```python
class GenerateSuccessResponse(BaseModel):
    success: bool = True
    workflow_id: str                    # Unique workflow ID
    nodes: List[Dict[str, Any]]        # React Flow nodes
    edges: List[Dict[str, Any]]        # React Flow edges
    workflow_name: str
    workflow_description: str
    generation_time_ms: float
    sla_exceeded: bool                  # True if > 10 seconds
    timestamp: datetime
```

---

## Node Structure

```python
{
  "id": str,              # e.g., "trigger_1", "action_1"
  "type": str,            # "trigger", "swap", "stake", "transfer"
  "label": str,           # Human-readable label
  "parameters": {...},    # Workflow logic parameters
  "position": {           # React Flow position
    "x": int,
    "y": int
  },
  "data": {               # React Flow rendering data
    "label": str,
    "icon": str,
    "status": str
  }
}
```

---

## Edge Structure

```python
{
  "id": str,              # e.g., "e1", "e2"
  "source": str,          # Source node ID
  "target": str,          # Target node ID
  "type": str,            # "default"
  "animated": bool        # false by default
}
```

---

## Error Responses

### Validation Error (422)

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid workflow specification",
    "details": "Field 'trigger.value' must be greater than 0",
    "retry": false
  }
}
```

### Timeout Error (503)

```json
{
  "success": false,
  "error": {
    "code": "TIMEOUT_ERROR",
    "message": "Node design timed out",
    "details": "Error ID: abc123",
    "retry": true
  }
}
```

### Internal Error (500)

```json
{
  "success": false,
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "An unexpected error occurred",
    "details": "Error ID: def456",
    "retry": true
  }
}
```

---

## Storage Format

Workflows are stored as JSON files in `data/workflows/{workflow_id}.json`:

```json
{
  "workflow_id": "wf_abc123def456",
  "user_id": "user_123",
  "user_address": "NXXXyyy...",
  "assembled_graph": {
    "workflow_id": "wf_abc123def456",
    "workflow_name": "Auto DCA into NEO",
    "workflow_description": "...",
    "react_flow": {
      "nodes": [...],
      "edges": [...]
    },
    "state_graph_config": {...}
  },
  "status": "active",
  "enabled": true,
  "trigger_count": 0,
  "execution_count": 0,
  "created_at": "2025-12-06T...",
  "updated_at": "2025-12-06T..."
}
```

---

## Testing

### Run Standalone Test

```bash
cd backend
source venv/bin/activate
python test_generate_endpoint.py
```

**Expected Output:**
```
================================================================================
STORY 3.3: Generate API Endpoint - Standalone Test
================================================================================

Test Case 1: Price-Triggered Swap
--------------------------------------------------------------------------------
✓ Created WorkflowSpec: Auto DCA into NEO
✓ Designed 2 nodes
✓ Assembled graph: wf_5948d95ecaec
✓ Workflow stored: wf_5948d95ecaec
✓ File created: /data/workflows/wf_5948d95ecaec.json

...

================================================================================
ALL TESTS PASSED ✓
================================================================================
```

### Run API Test

```bash
# Terminal 1: Start server
cd backend
./run.sh

# Terminal 2: Run test
./test_generate_api.sh
```

---

## Performance

| Metric | Value | SLA |
|--------|-------|-----|
| Node design | ~100-200ms | <8s |
| Graph assembly | ~5-10ms | <2s |
| Storage | ~5-10ms | <2s |
| **Total** | **~200-300ms** | **<10s** |

**Status:** ✅ Well under SLA (3% of limit)

---

## Integration with Frontend

### TypeScript Example

```typescript
interface GenerateRequest {
  workflow_spec: WorkflowSpec;
  user_id?: string;
  user_address?: string;
}

interface GenerateResponse {
  success: boolean;
  workflow_id: string;
  nodes: ReactFlowNode[];
  edges: ReactFlowEdge[];
  workflow_name: string;
  workflow_description: string;
  generation_time_ms: number;
  sla_exceeded: boolean;
  timestamp: string;
}

async function generateWorkflowGraph(
  workflowSpec: WorkflowSpec
): Promise<GenerateResponse> {
  const response = await fetch('http://localhost:8000/api/v1/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      workflow_spec: workflowSpec,
      user_id: 'current_user',
      user_address: 'NXXXyyy...'
    })
  });

  if (!response.ok) {
    throw new Error(`Generate failed: ${response.statusText}`);
  }

  return await response.json();
}
```

### React Flow Integration

```typescript
import ReactFlow from 'react-flow-renderer';

function WorkflowGraph({ workflowSpec }: { workflowSpec: WorkflowSpec }) {
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);

  useEffect(() => {
    generateWorkflowGraph(workflowSpec).then(response => {
      setNodes(response.nodes);
      setEdges(response.edges);
    });
  }, [workflowSpec]);

  return <ReactFlow nodes={nodes} edges={edges} />;
}
```

---

## Troubleshooting

### Issue: "Module not found: spoon_ai"

**Solution:** Activate virtual environment
```bash
source venv/bin/activate
```

### Issue: Storage directory not found

**Solution:** Directory is auto-created, but verify:
```bash
mkdir -p data/workflows
```

### Issue: Timeout errors

**Solution:** Check node designer performance:
```bash
# Add logging in app/agents/designers/__init__.py
logger.setLevel(logging.DEBUG)
```

---

## Next Steps

1. **Frontend Integration (Story 3.4)**
   - Connect to /api/v1/generate endpoint
   - Display React Flow graph
   - Add user interaction

2. **Database Migration**
   - Replace JSON files with PostgreSQL
   - Add indexes for performance
   - Implement migrations

3. **Workflow Execution (Phase 4)**
   - Load workflows by workflow_id
   - Execute StateGraph
   - Track execution history

---

**Last Updated:** December 6, 2025
**Status:** ✅ Production Ready
