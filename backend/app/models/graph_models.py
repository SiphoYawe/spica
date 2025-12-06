"""
Graph models for workflow graph assembly and execution.

This module defines the models used by GraphAssembler to create executable
StateGraph workflows and React Flow visualizations.
"""

from typing import TypedDict, Dict, Any, List, Optional, Literal, TYPE_CHECKING
from pydantic import BaseModel, Field
from datetime import datetime, timezone

if TYPE_CHECKING:
    from app.models.workflow_models import WorkflowSpec


# ============================================================================
# StateGraph Workflow State (for SpoonOS StateGraph execution)
# ============================================================================

class WorkflowState(TypedDict):
    """
    TypedDict state for SpoonOS StateGraph execution.

    This state is passed between nodes during workflow execution.
    Each node receives this state and returns updates to merge.

    State Fields:
    - workflow_id: Unique identifier for the workflow instance
    - user_address: User's Neo N3 address for transaction execution
    - trigger_type: Type of trigger (price/time)
    - trigger_params: Parameters for the trigger condition
    - current_step: Current step being executed (0-indexed)
    - total_steps: Total number of action steps
    - completed_steps: List of completed step indices
    - step_results: Results from each completed step
    - workflow_status: Current status of workflow execution
    - error: Error message if any step fails
    - metadata: Additional execution metadata
    """
    workflow_id: str
    user_address: str
    trigger_type: str  # "price" or "time"
    trigger_params: Dict[str, Any]
    current_step: int
    total_steps: int
    completed_steps: List[int]
    step_results: List[Dict[str, Any]]
    workflow_status: str  # "pending", "running", "completed", "failed"
    error: Optional[str]
    metadata: Dict[str, Any]


# ============================================================================
# React Flow Graph Models
# ============================================================================

# NodePosition is used for React Flow layout
# We define it here to avoid circular imports with base.py


class NodePosition(BaseModel):
    """Position for React Flow node layout"""
    x: int = 0
    y: int = 0


class GraphNode(BaseModel):
    """
    React Flow node specification.

    Note: 'parameters' contains the structured workflow logic (tokens, amounts, conditions)
          while 'data' contains React Flow-specific rendering metadata (labels, icons, status).
          Both fields serve different purposes and are intentionally separate.
    """
    id: str = Field(..., description="Unique node identifier")
    type: str = Field(..., description="Node type (trigger/swap/stake/transfer)")
    label: str = Field(..., description="Human-readable label")
    parameters: Dict[str, Any] = Field(..., description="Node-specific workflow parameters (tokens, amounts, etc.)")
    position: NodePosition = Field(..., description="Node position for layout")
    data: Dict[str, Any] = Field(..., description="React Flow rendering metadata (label, icon, status)")


class GraphEdge(BaseModel):
    """React Flow edge specification"""
    id: str = Field(..., description="Unique edge identifier")
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    type: str = Field(default="default", description="Edge type")
    animated: bool = Field(default=False, description="Whether edge is animated")


class ReactFlowGraph(BaseModel):
    """Complete React Flow graph structure"""
    nodes: List[GraphNode] = Field(..., description="List of nodes")
    edges: List[GraphEdge] = Field(..., description="List of edges")


# ============================================================================
# Assembled Graph Model
# ============================================================================

class AssembledGraph(BaseModel):
    """
    Complete assembled graph with both React Flow and StateGraph representations.

    This is the primary output from GraphAssembler.assemble() and contains
    everything needed to:
    1. Visualize the workflow in the frontend (react_flow)
    2. Execute the workflow with SpoonOS (state_graph_config)
    3. Store the workflow in the database (serializable to JSON)
    """
    workflow_id: str = Field(..., description="Unique workflow identifier")
    workflow_name: str = Field(..., description="User-friendly workflow name")
    workflow_description: str = Field(..., description="Workflow description")

    # Original workflow specification
    workflow_spec: Any = Field(..., description="Original WorkflowSpec used to create this graph")

    # React Flow visualization
    react_flow: ReactFlowGraph = Field(..., description="React Flow graph data")

    # StateGraph configuration (serializable representation)
    state_graph_config: Dict[str, Any] = Field(
        ...,
        description="StateGraph configuration for execution"
    )

    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    version: str = Field(default="1.0", description="Graph schema version")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# ============================================================================
# Stored Workflow Model (for persistence)
# ============================================================================

class StoredWorkflow(BaseModel):
    """
    Workflow stored in database with execution state.

    This model extends AssembledGraph with runtime execution state
    and user ownership information.
    """
    # Core workflow data
    workflow_id: str = Field(..., description="Unique workflow identifier")
    user_id: str = Field(..., description="Owner user ID")
    user_address: str = Field(..., description="User's Neo N3 address")

    # Workflow specification
    assembled_graph: AssembledGraph = Field(..., description="The assembled graph")

    # Execution state
    status: Literal["active", "paused", "completed", "failed"] = Field(
        default="active",
        description="Current workflow status"
    )
    enabled: bool = Field(default=True, description="Whether workflow is enabled")
    trigger_count: int = Field(default=0, description="Number of times triggered")
    execution_count: int = Field(default=0, description="Number of successful executions")
    last_triggered_at: Optional[datetime] = Field(None, description="Last trigger timestamp")
    last_executed_at: Optional[datetime] = Field(None, description="Last execution timestamp")
    last_error: Optional[str] = Field(None, description="Last error message if any")

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# ============================================================================
# Node Function Metadata (for StateGraph node creation)
# ============================================================================

class NodeFunctionConfig(BaseModel):
    """
    Configuration for creating StateGraph node functions.

    This model defines the metadata needed to generate executable
    node functions for different workflow actions.
    """
    node_id: str = Field(..., description="Node identifier")
    node_type: str = Field(..., description="Node type (trigger/swap/stake/transfer)")
    function_name: str = Field(..., description="Generated function name")
    parameters: Dict[str, Any] = Field(..., description="Node parameters")

    # Execution metadata
    contract_hash: Optional[str] = Field(None, description="Smart contract hash if applicable")
    method_name: Optional[str] = Field(None, description="Contract method to call")
    requires_signature: bool = Field(default=True, description="Whether transaction needs signing")
