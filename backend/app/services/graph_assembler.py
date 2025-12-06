"""
Graph Assembler Service - Combines node specifications into executable graphs.

This service implements Story 3.2 and provides:
1. React Flow graph generation from node specifications
2. SpoonOS StateGraph creation for workflow execution
3. Graph serialization to JSON for storage

The GraphAssembler bridges the gap between:
- Designer agents (Story 3.1) that create node specifications
- Execution engine that runs workflows using StateGraph
"""

import logging
import uuid
import asyncio
from typing import List, Dict, Any, Callable, Awaitable, Optional
from datetime import datetime, timezone

try:
    from spoon_ai.graph import StateGraph
    from spoon_ai.graph.engine import END  # Import END constant
    SPOON_AI_AVAILABLE = True
except ImportError:
    SPOON_AI_AVAILABLE = False
    END = "__end__"  # Fallback constant
    logger = logging.getLogger(__name__)
    logger.warning("spoon_ai package not available - StateGraph functionality will be limited")

from app.models.workflow_models import WorkflowSpec, WorkflowAction, SwapAction, StakeAction, TransferAction
from app.models.graph_models import (
    WorkflowState,
    GraphNode,
    GraphEdge,
    ReactFlowGraph,
    AssembledGraph,
    NodeFunctionConfig,
    NodePosition,
)
from app.agents.designers.base import NodeSpecification

logger = logging.getLogger(__name__)


# ============================================================================
# GraphAssembler Service
# ============================================================================

class GraphAssembler:
    """
    Assembles workflow graphs from node specifications.

    This service combines node specifications from designer agents into:
    1. React Flow graphs for frontend visualization
    2. SpoonOS StateGraph instances for execution
    3. JSON-serializable graph configurations for storage

    Usage:
        ```python
        from app.agents.designers import design_workflow_nodes
        from app.services.graph_assembler import GraphAssembler

        # Design nodes
        nodes = await design_workflow_nodes(workflow_spec)

        # Assemble graph
        assembler = GraphAssembler()
        assembled = await assembler.assemble(workflow_spec, nodes)

        # Use assembled graph
        print(assembled.react_flow)  # For frontend
        state_graph = await assembler.assemble_state_graph(workflow_spec)  # For execution
        ```
    """

    def __init__(self):
        """Initialize the graph assembler."""
        logger.info("GraphAssembler initialized")

    # ========================================================================
    # React Flow Graph Assembly
    # ========================================================================

    def assemble_react_flow(self, nodes: List[NodeSpecification]) -> ReactFlowGraph:
        """
        Assemble React Flow graph from node specifications.

        Args:
            nodes: List of node specifications from designer agents

        Returns:
            ReactFlowGraph with nodes and edges for visualization

        Example:
            ```python
            nodes = await design_workflow_nodes(workflow_spec)
            react_flow = assembler.assemble_react_flow(nodes)
            ```
        """
        logger.info(f"Assembling React Flow graph from {len(nodes)} nodes")

        # Convert NodeSpecification to GraphNode
        graph_nodes = [
            GraphNode(
                id=node.id,
                type=node.type,
                label=node.label,
                parameters=node.parameters,
                position=NodePosition(x=node.position.x, y=node.position.y),
                data=node.data.model_dump()
            )
            for node in nodes
        ]

        # Create edges connecting nodes sequentially
        edges = self._create_edges(graph_nodes)

        react_flow = ReactFlowGraph(nodes=graph_nodes, edges=edges)

        logger.info(f"Created React Flow graph with {len(graph_nodes)} nodes and {len(edges)} edges")

        return react_flow

    def _create_edges(self, nodes: List[GraphNode]) -> List[GraphEdge]:
        """
        Create sequential edges between nodes.

        Edge ID Generation:
        - Uses sequential numbering: e1, e2, e3, etc.
        - Simple, deterministic, and human-readable
        - Format: "e{index+1}" where index is 0-based loop counter
        - Example: For 3 nodes, creates edges "e1" (0→1) and "e2" (1→2)

        Alternative approaches considered:
        - UUID-based: More unique but harder to debug
        - Hash-based: Not deterministic, makes testing difficult
        - Source-target concat: Works but less readable (e.g., "trigger_1-action_1")

        Sequential numbering chosen for simplicity and debuggability in MVP.
        Future enhancement: Consider UUID for distributed/concurrent scenarios.

        Args:
            nodes: List of graph nodes

        Returns:
            List of edges connecting nodes in sequence
        """
        edges = []

        for i in range(len(nodes) - 1):
            edge = GraphEdge(
                id=f"e{i+1}",  # Sequential ID: e1, e2, e3...
                source=nodes[i].id,
                target=nodes[i+1].id,
                type="default",
                animated=False
            )
            edges.append(edge)

        return edges

    # ========================================================================
    # StateGraph Assembly
    # ========================================================================

    async def assemble_state_graph(self, workflow_spec: WorkflowSpec):
        """
        Assemble executable SpoonOS StateGraph from workflow specification.

        This creates a StateGraph with:
        - Trigger evaluation node
        - Action execution nodes (swap/stake/transfer)
        - Error handling and state management

        Args:
            workflow_spec: Parsed workflow specification

        Returns:
            StateGraph instance ready for compilation and execution

        Raises:
            ImportError: If spoon_ai package is not available

        Example:
            ```python
            state_graph = await assembler.assemble_state_graph(workflow_spec)
            compiled = state_graph.compile()
            result = await compiled.invoke({
                "workflow_id": "wf_123",
                "user_address": "NXXXyyy...",
                ...
            })
            ```
        """
        if not SPOON_AI_AVAILABLE:
            raise ImportError(
                "spoon_ai package is not installed. "
                "Please install it to use StateGraph functionality: "
                "pip install -e /path/to/spoon-core"
            )

        logger.info(f"Assembling StateGraph for workflow: {workflow_spec.name}")

        # Initialize StateGraph with WorkflowState
        graph = StateGraph(WorkflowState)

        # ====================================================================
        # Create trigger evaluation node
        # ====================================================================

        trigger_func = self._create_trigger_node(workflow_spec.trigger)
        graph.add_node("evaluate_trigger", trigger_func)

        # ====================================================================
        # Create action execution nodes
        # ====================================================================

        for i, step in enumerate(workflow_spec.steps):
            node_id = f"action_{i}"
            action_func = self._create_action_node(step.action, i)
            graph.add_node(node_id, action_func)

        # ====================================================================
        # Define graph edges (workflow flow)
        # ====================================================================

        # Set entry point
        graph.set_entry_point("evaluate_trigger")

        # Trigger -> First action
        if workflow_spec.steps:
            graph.add_edge("evaluate_trigger", "action_0")

            # Connect actions sequentially
            for i in range(len(workflow_spec.steps) - 1):
                graph.add_edge(f"action_{i}", f"action_{i+1}")

            # Last action -> END
            graph.add_edge(f"action_{len(workflow_spec.steps) - 1}", END)
        else:
            # No actions, go straight to end
            graph.add_edge("evaluate_trigger", END)

        logger.info(f"StateGraph created with {len(workflow_spec.steps) + 1} nodes")

        return graph

    # ========================================================================
    # Node Function Creators
    # ========================================================================

    def _create_trigger_node(self, trigger) -> Callable[[WorkflowState], Awaitable[Dict[str, Any]]]:
        """
        Create trigger evaluation node function.

        Args:
            trigger: PriceCondition or TimeCondition

        Returns:
            Async function for StateGraph node
        """
        trigger_type = trigger.type

        async def evaluate_trigger(state: WorkflowState) -> Dict[str, Any]:
            """
            Evaluate trigger condition.

            For now, this is a placeholder that logs the trigger check.
            In production, this would:
            - For price triggers: Check current price against condition
            - For time triggers: Validate schedule and timing

            Returns:
                State updates
            """
            logger.info(f"Evaluating {trigger_type} trigger")

            # Update state
            # Type-safe metadata merge
            existing_metadata = state.get("metadata", {})
            if not isinstance(existing_metadata, dict):
                existing_metadata = {}

            return {
                "workflow_status": "running",
                "metadata": {
                    **existing_metadata,
                    "trigger_evaluated_at": datetime.now(timezone.utc).isoformat(),
                    "trigger_type": trigger_type,
                }
            }

        return evaluate_trigger

    def _create_action_node(
        self,
        action: WorkflowAction,
        step_index: int
    ) -> Callable[[WorkflowState], Awaitable[Dict[str, Any]]]:
        """
        Create action execution node function.

        Args:
            action: SwapAction, StakeAction, or TransferAction
            step_index: Index of this step in the workflow

        Returns:
            Async function for StateGraph node
        """
        action_type = action.type

        async def execute_action(state: WorkflowState) -> Dict[str, Any]:
            """
            Execute workflow action.

            For now, this is a placeholder that logs the action.
            In production, this would:
            - For swap: Call Flamingo DEX smart contract
            - For stake: Call Flamingo staking contract
            - For transfer: Execute NEP-17 transfer

            Returns:
                State updates
            """
            logger.info(f"Executing {action_type} action (step {step_index})")

            # Simulate action execution
            result = {
                "step": step_index,
                "action_type": action_type,
                "status": "completed",
                "executed_at": datetime.now(timezone.utc).isoformat(),
            }

            # Add action-specific details
            if isinstance(action, SwapAction):
                result["details"] = {
                    "from_token": action.from_token,
                    "to_token": action.to_token,
                    "amount": action.amount,
                    "percentage": action.percentage,
                }
            elif isinstance(action, StakeAction):
                result["details"] = {
                    "token": action.token,
                    "amount": action.amount,
                    "percentage": action.percentage,
                }
            elif isinstance(action, TransferAction):
                result["details"] = {
                    "token": action.token,
                    "to_address": action.to_address,
                    "amount": action.amount,
                    "percentage": action.percentage,
                }

            # Update state with mutation-safe patterns
            # Create new lists instead of mutating existing ones
            completed_steps = state.get("completed_steps", [])
            step_results = state.get("step_results", [])

            # Validate types before mutation
            if not isinstance(completed_steps, list):
                completed_steps = []
            if not isinstance(step_results, list):
                step_results = []

            # Use list copying to avoid mutation
            new_completed_steps = [*completed_steps, step_index]
            new_step_results = [*step_results, result]

            return {
                "current_step": step_index + 1,
                "completed_steps": new_completed_steps,
                "step_results": new_step_results,
                "workflow_status": "running" if step_index < state["total_steps"] - 1 else "completed",
            }

        return execute_action

    # ========================================================================
    # Complete Assembly
    # ========================================================================

    async def assemble(
        self,
        workflow_spec: WorkflowSpec,
        nodes: List[NodeSpecification],
        workflow_id: Optional[str] = None
    ) -> AssembledGraph:
        """
        Assemble complete graph with both React Flow and StateGraph.

        This is the primary method that creates a complete assembled graph
        ready for visualization, execution, and storage.

        Args:
            workflow_spec: Parsed workflow specification
            nodes: Node specifications from designer agents
            workflow_id: Optional workflow ID (generates UUID if not provided)

        Returns:
            AssembledGraph with complete graph data

        Example:
            ```python
            # Complete workflow assembly pipeline
            workflow = await parser.parse_workflow("Swap GAS when price drops")
            nodes = await design_workflow_nodes(workflow.workflow)
            assembled = await assembler.assemble(workflow.workflow, nodes)

            # Now you have:
            # - assembled.react_flow -> for frontend visualization
            # - assembled.state_graph_config -> for execution engine
            # - assembled.model_dump_json() -> for database storage
            ```
        """
        if workflow_id is None:
            workflow_id = f"wf_{uuid.uuid4().hex[:12]}"

        logger.info(f"Assembling complete graph for workflow: {workflow_id}")

        # Assemble React Flow graph
        react_flow = self.assemble_react_flow(nodes)

        # Create StateGraph configuration (serializable representation)
        # Note: We store configuration, not the actual StateGraph object
        # The execution engine will reconstruct the StateGraph from this config
        state_graph_config = {
            "trigger": {
                "type": workflow_spec.trigger.type,
                "params": workflow_spec.trigger.model_dump(),
            },
            "steps": [
                {
                    "action_type": step.action.type,
                    "params": step.action.model_dump(),
                    "description": step.description,
                }
                for step in workflow_spec.steps
            ],
            "node_count": len(nodes),
            "initial_state": {
                "workflow_id": workflow_id,
                "trigger_type": workflow_spec.trigger.type,
                "trigger_params": workflow_spec.trigger.model_dump(),
                "current_step": 0,
                "total_steps": len(workflow_spec.steps),
                "completed_steps": [],
                "step_results": [],
                "workflow_status": "pending",
                "error": None,
                "metadata": {
                    "workflow_name": workflow_spec.name,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                },
            }
        }

        # Create assembled graph
        assembled = AssembledGraph(
            workflow_id=workflow_id,
            workflow_name=workflow_spec.name,
            workflow_description=workflow_spec.description,
            react_flow=react_flow,
            state_graph_config=state_graph_config,
        )

        logger.info(f"Successfully assembled graph {workflow_id}")

        return assembled

    # ========================================================================
    # Serialization
    # ========================================================================

    def serialize(self, assembled: AssembledGraph) -> str:
        """
        Serialize assembled graph to JSON.

        Args:
            assembled: Assembled graph

        Returns:
            JSON string

        Example:
            ```python
            assembled = await assembler.assemble(workflow_spec, nodes)
            json_str = assembler.serialize(assembled)
            # Store in database or file
            ```
        """
        return assembled.model_dump_json(indent=2)

    def deserialize(self, json_str: str) -> AssembledGraph:
        """
        Deserialize JSON to assembled graph.

        Args:
            json_str: JSON string

        Returns:
            AssembledGraph instance

        Example:
            ```python
            # Load from database or file
            json_str = load_from_db(workflow_id)
            assembled = assembler.deserialize(json_str)
            ```
        """
        return AssembledGraph.model_validate_json(json_str)


# ============================================================================
# Singleton Instance (Thread-Safe)
# ============================================================================

_graph_assembler: Optional[GraphAssembler] = None
_graph_assembler_lock = asyncio.Lock()


async def get_graph_assembler() -> GraphAssembler:
    """
    Get the global GraphAssembler instance (thread-safe singleton pattern).

    This function uses asyncio.Lock to ensure thread-safe singleton creation
    in async contexts.

    Returns:
        GraphAssembler instance
    """
    global _graph_assembler

    if _graph_assembler is None:
        async with _graph_assembler_lock:
            # Double-check pattern to avoid race condition
            if _graph_assembler is None:
                _graph_assembler = GraphAssembler()

    return _graph_assembler


def get_graph_assembler_sync() -> GraphAssembler:
    """
    Get the global GraphAssembler instance (synchronous, non-thread-safe).

    Use this only in synchronous contexts. For async contexts, use
    get_graph_assembler() instead.

    Returns:
        GraphAssembler instance
    """
    global _graph_assembler

    if _graph_assembler is None:
        _graph_assembler = GraphAssembler()

    return _graph_assembler
