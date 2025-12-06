"""
Tests for GraphAssembler service (Story 3.2).

This test suite validates:
1. React Flow graph generation from node specifications
2. StateGraph compilation and structure
3. JSON serialization/deserialization
4. Edge creation logic
5. Complete assembly pipeline
"""

import pytest
import json
from typing import List

from app.services.graph_assembler import GraphAssembler, get_graph_assembler_sync, SPOON_AI_AVAILABLE
from app.models.workflow_models import (
    WorkflowSpec,
    WorkflowStep,
    PriceCondition,
    TimeCondition,
    SwapAction,
    StakeAction,
    TransferAction,
    TokenType,
)
from app.models.graph_models import (
    WorkflowState,
    GraphNode,
    GraphEdge,
    ReactFlowGraph,
    AssembledGraph,
)
from app.agents.designers.base import NodeSpecification, NodeData, NodePosition


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def assembler():
    """Create GraphAssembler instance"""
    return GraphAssembler()


@pytest.fixture
def sample_nodes() -> List[NodeSpecification]:
    """Create sample node specifications for testing"""
    return [
        NodeSpecification(
            id="trigger_1",
            type="trigger",
            label="When GAS price below $5.00",
            parameters={
                "type": "price",
                "token": "GAS",
                "operator": "below",
                "value": 5.0,
            },
            position=NodePosition(x=250, y=0),
            data=NodeData(
                label="When GAS price below $5.00",
                icon="clock",
                status="pending"
            )
        ),
        NodeSpecification(
            id="action_1",
            type="swap",
            label="Swap 10 GAS → NEO",
            parameters={
                "type": "swap",
                "from_token": "GAS",
                "to_token": "NEO",
                "amount": 10.0,
            },
            position=NodePosition(x=250, y=150),
            data=NodeData(
                label="Swap 10 GAS → NEO",
                icon="swap",
                status="pending"
            )
        ),
        NodeSpecification(
            id="action_2",
            type="stake",
            label="Stake 50% NEO",
            parameters={
                "type": "stake",
                "token": "NEO",
                "percentage": 50.0,
            },
            position=NodePosition(x=250, y=300),
            data=NodeData(
                label="Stake 50% NEO",
                icon="stake",
                status="pending"
            )
        ),
    ]


@pytest.fixture
def sample_workflow_spec() -> WorkflowSpec:
    """Create sample workflow specification"""
    return WorkflowSpec(
        name="Auto DCA and Stake",
        description="When GAS price drops, swap to NEO and stake",
        trigger=PriceCondition(
            type="price",
            token=TokenType.GAS,
            operator="below",
            value=5.0
        ),
        steps=[
            WorkflowStep(
                action=SwapAction(
                    type="swap",
                    from_token=TokenType.GAS,
                    to_token=TokenType.NEO,
                    amount=10.0
                ),
                description="Swap 10 GAS to NEO"
            ),
            WorkflowStep(
                action=StakeAction(
                    type="stake",
                    token=TokenType.NEO,
                    percentage=50.0
                ),
                description="Stake 50% of NEO"
            ),
        ]
    )


@pytest.fixture
def time_workflow_spec() -> WorkflowSpec:
    """Create time-based workflow specification"""
    return WorkflowSpec(
        name="Daily Transfer",
        description="Transfer GAS daily at 9am",
        trigger=TimeCondition(
            type="time",
            schedule="daily at 9am"
        ),
        steps=[
            WorkflowStep(
                action=TransferAction(
                    type="transfer",
                    token=TokenType.GAS,
                    to_address="NNLi44dJNXtDNSBkofB48aTVYtb1zZrNEs",  # Valid Neo N3 testnet address
                    amount=5.0
                ),
                description="Transfer 5 GAS"
            ),
        ]
    )


# ============================================================================
# React Flow Graph Tests
# ============================================================================

def test_assemble_react_flow_creates_nodes(assembler, sample_nodes):
    """Test that React Flow graph correctly converts NodeSpecification to GraphNode"""
    react_flow = assembler.assemble_react_flow(sample_nodes)

    assert isinstance(react_flow, ReactFlowGraph)
    assert len(react_flow.nodes) == 3

    # Validate first node (trigger)
    trigger_node = react_flow.nodes[0]
    assert trigger_node.id == "trigger_1"
    assert trigger_node.type == "trigger"
    assert trigger_node.label == "When GAS price below $5.00"
    assert trigger_node.parameters["type"] == "price"
    assert trigger_node.position.x == 250
    assert trigger_node.position.y == 0

    # Validate second node (swap action)
    swap_node = react_flow.nodes[1]
    assert swap_node.id == "action_1"
    assert swap_node.type == "swap"
    assert swap_node.parameters["from_token"] == "GAS"
    assert swap_node.parameters["to_token"] == "NEO"


def test_assemble_react_flow_creates_edges(assembler, sample_nodes):
    """Test that edges are created sequentially between nodes"""
    react_flow = assembler.assemble_react_flow(sample_nodes)

    assert len(react_flow.edges) == 2  # 3 nodes = 2 edges

    # Validate edge 1: trigger -> action_1
    edge1 = react_flow.edges[0]
    assert edge1.id == "e1"
    assert edge1.source == "trigger_1"
    assert edge1.target == "action_1"
    assert edge1.type == "default"
    assert edge1.animated is False

    # Validate edge 2: action_1 -> action_2
    edge2 = react_flow.edges[1]
    assert edge2.id == "e2"
    assert edge2.source == "action_1"
    assert edge2.target == "action_2"


def test_assemble_react_flow_single_node(assembler):
    """Test React Flow graph with single node (no edges)"""
    single_node = [
        NodeSpecification(
            id="trigger_1",
            type="trigger",
            label="Daily trigger",
            parameters={"type": "time"},
            position=NodePosition(x=0, y=0),
            data=NodeData(label="Daily trigger", icon="clock", status="pending")
        )
    ]

    react_flow = assembler.assemble_react_flow(single_node)

    assert len(react_flow.nodes) == 1
    assert len(react_flow.edges) == 0  # No edges with single node


def test_assemble_react_flow_preserves_positions(assembler, sample_nodes):
    """Test that node positions are preserved from NodeSpecification"""
    react_flow = assembler.assemble_react_flow(sample_nodes)

    assert react_flow.nodes[0].position.x == 250
    assert react_flow.nodes[0].position.y == 0
    assert react_flow.nodes[1].position.x == 250
    assert react_flow.nodes[1].position.y == 150
    assert react_flow.nodes[2].position.x == 250
    assert react_flow.nodes[2].position.y == 300


# ============================================================================
# StateGraph Assembly Tests
# ============================================================================

@pytest.mark.skipif(not SPOON_AI_AVAILABLE, reason="spoon_ai package not installed")
@pytest.mark.asyncio
async def test_assemble_state_graph_creates_graph(assembler, sample_workflow_spec):
    """Test that StateGraph is created from workflow specification"""
    state_graph = await assembler.assemble_state_graph(sample_workflow_spec)

    # StateGraph should be created (we can't easily inspect internal structure)
    assert state_graph is not None
    assert hasattr(state_graph, "compile")


@pytest.mark.skipif(not SPOON_AI_AVAILABLE, reason="spoon_ai package not installed")
@pytest.mark.asyncio
async def test_assemble_state_graph_compiles_successfully(assembler, sample_workflow_spec):
    """Test that assembled StateGraph can be compiled"""
    state_graph = await assembler.assemble_state_graph(sample_workflow_spec)

    # Should compile without errors
    compiled = state_graph.compile()
    assert compiled is not None


@pytest.mark.skipif(not SPOON_AI_AVAILABLE, reason="spoon_ai package not installed")
@pytest.mark.asyncio
async def test_state_graph_trigger_node_execution(assembler, sample_workflow_spec):
    """Test that trigger node can be executed"""
    state_graph = await assembler.assemble_state_graph(sample_workflow_spec)
    compiled = state_graph.compile()

    # Create initial state
    initial_state = {
        "workflow_id": "test_wf_123",
        "user_address": "NXXXwj3Rd4qJErvdGGUY5JqbMhJmGHs4Xy",
        "trigger_type": "price",
        "trigger_params": {"token": "GAS", "operator": "below", "value": 5.0},
        "current_step": 0,
        "total_steps": 2,
        "completed_steps": [],
        "step_results": [],
        "workflow_status": "pending",
        "error": None,
        "metadata": {},
    }

    # Execute graph
    result = await compiled.invoke(initial_state)

    # Verify execution completed
    assert result["workflow_status"] == "completed"
    # Verify at least 2 steps completed (may include trigger step)
    assert len(result["completed_steps"]) >= 2
    assert len(result["step_results"]) >= 2


@pytest.mark.skipif(not SPOON_AI_AVAILABLE, reason="spoon_ai package not installed")
@pytest.mark.asyncio
async def test_state_graph_action_nodes_execution(assembler, sample_workflow_spec):
    """Test that action nodes execute and update state correctly"""
    state_graph = await assembler.assemble_state_graph(sample_workflow_spec)
    compiled = state_graph.compile()

    initial_state = {
        "workflow_id": "test_wf_456",
        "user_address": "NXXXwj3Rd4qJErvdGGUY5JqbMhJmGHs4Xy",
        "trigger_type": "price",
        "trigger_params": {},
        "current_step": 0,
        "total_steps": 2,
        "completed_steps": [],
        "step_results": [],
        "workflow_status": "pending",
        "error": None,
        "metadata": {},
    }

    result = await compiled.invoke(initial_state)

    # Verify action results - there should be at least 2 step results
    assert len(result["step_results"]) >= 2

    # Find swap action result (may not be first due to node ordering)
    swap_results = [r for r in result["step_results"] if r.get("action_type") == "swap"]
    assert len(swap_results) >= 1
    swap_result = swap_results[0]
    assert swap_result["status"] == "completed"
    assert str(swap_result["details"]["from_token"]) in ["GAS", "TokenType.GAS"]
    assert str(swap_result["details"]["to_token"]) in ["NEO", "TokenType.NEO"]

    # Find stake action result
    stake_results = [r for r in result["step_results"] if r.get("action_type") == "stake"]
    assert len(stake_results) >= 1
    stake_result = stake_results[0]
    assert stake_result["status"] == "completed"
    assert str(stake_result["details"]["token"]) in ["NEO", "TokenType.NEO"]
    assert stake_result["details"]["percentage"] == 50.0


@pytest.mark.skipif(not SPOON_AI_AVAILABLE, reason="spoon_ai package not installed")
@pytest.mark.asyncio
async def test_state_graph_time_trigger(assembler, time_workflow_spec):
    """Test StateGraph with time-based trigger"""
    state_graph = await assembler.assemble_state_graph(time_workflow_spec)
    compiled = state_graph.compile()

    initial_state = {
        "workflow_id": "test_wf_time",
        "user_address": "NXXXwj3Rd4qJErvdGGUY5JqbMhJmGHs4Xy",
        "trigger_type": "time",
        "trigger_params": {"schedule": "daily at 9am"},
        "current_step": 0,
        "total_steps": 1,
        "completed_steps": [],
        "step_results": [],
        "workflow_status": "pending",
        "error": None,
        "metadata": {},
    }

    result = await compiled.invoke(initial_state)

    # Verify execution
    assert result["workflow_status"] == "completed"
    assert result["step_results"][0]["action_type"] == "transfer"


# ============================================================================
# Complete Assembly Tests
# ============================================================================

@pytest.mark.asyncio
async def test_assemble_creates_complete_graph(assembler, sample_workflow_spec, sample_nodes):
    """Test that assemble() creates complete AssembledGraph"""
    assembled = await assembler.assemble(sample_workflow_spec, sample_nodes)

    assert isinstance(assembled, AssembledGraph)
    assert assembled.workflow_id.startswith("wf_")
    assert assembled.workflow_name == "Auto DCA and Stake"
    assert assembled.workflow_description == "When GAS price drops, swap to NEO and stake"
    assert assembled.version == "1.0"


@pytest.mark.asyncio
async def test_assemble_includes_react_flow(assembler, sample_workflow_spec, sample_nodes):
    """Test that assembled graph includes React Flow data"""
    assembled = await assembler.assemble(sample_workflow_spec, sample_nodes)

    assert isinstance(assembled.react_flow, ReactFlowGraph)
    assert len(assembled.react_flow.nodes) == 3
    assert len(assembled.react_flow.edges) == 2


@pytest.mark.asyncio
async def test_assemble_includes_state_graph_config(assembler, sample_workflow_spec, sample_nodes):
    """Test that assembled graph includes StateGraph configuration"""
    assembled = await assembler.assemble(sample_workflow_spec, sample_nodes)

    config = assembled.state_graph_config

    assert "trigger" in config
    assert config["trigger"]["type"] == "price"
    assert "steps" in config
    assert len(config["steps"]) == 2
    assert config["steps"][0]["action_type"] == "swap"
    assert config["steps"][1]["action_type"] == "stake"


@pytest.mark.asyncio
async def test_assemble_custom_workflow_id(assembler, sample_workflow_spec, sample_nodes):
    """Test that custom workflow ID is used when provided"""
    custom_id = "custom_workflow_123"
    assembled = await assembler.assemble(sample_workflow_spec, sample_nodes, workflow_id=custom_id)

    assert assembled.workflow_id == custom_id
    assert assembled.state_graph_config["initial_state"]["workflow_id"] == custom_id


# ============================================================================
# Serialization Tests
# ============================================================================

@pytest.mark.asyncio
async def test_serialize_to_json(assembler, sample_workflow_spec, sample_nodes):
    """Test that assembled graph can be serialized to JSON"""
    assembled = await assembler.assemble(sample_workflow_spec, sample_nodes)
    json_str = assembler.serialize(assembled)

    assert isinstance(json_str, str)
    assert len(json_str) > 0

    # Verify valid JSON
    data = json.loads(json_str)
    assert data["workflow_name"] == "Auto DCA and Stake"
    assert "react_flow" in data
    assert "state_graph_config" in data


@pytest.mark.asyncio
async def test_deserialize_from_json(assembler, sample_workflow_spec, sample_nodes):
    """Test that JSON can be deserialized back to AssembledGraph"""
    assembled = await assembler.assemble(sample_workflow_spec, sample_nodes)
    json_str = assembler.serialize(assembled)

    # Deserialize
    deserialized = assembler.deserialize(json_str)

    assert isinstance(deserialized, AssembledGraph)
    assert deserialized.workflow_id == assembled.workflow_id
    assert deserialized.workflow_name == assembled.workflow_name
    assert len(deserialized.react_flow.nodes) == len(assembled.react_flow.nodes)


@pytest.mark.asyncio
async def test_serialization_roundtrip(assembler, sample_workflow_spec, sample_nodes):
    """Test complete serialization/deserialization roundtrip"""
    original = await assembler.assemble(sample_workflow_spec, sample_nodes)

    # Serialize
    json_str = assembler.serialize(original)

    # Deserialize
    restored = assembler.deserialize(json_str)

    # Verify data integrity
    assert restored.workflow_id == original.workflow_id
    assert restored.workflow_name == original.workflow_name
    assert restored.workflow_description == original.workflow_description
    assert len(restored.react_flow.nodes) == len(original.react_flow.nodes)
    assert len(restored.react_flow.edges) == len(original.react_flow.edges)
    assert restored.state_graph_config == original.state_graph_config


# ============================================================================
# Singleton Tests
# ============================================================================

def test_get_graph_assembler_singleton():
    """Test that get_graph_assembler_sync returns singleton instance"""
    assembler1 = get_graph_assembler_sync()
    assembler2 = get_graph_assembler_sync()

    assert assembler1 is assembler2  # Same instance


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================

def test_assemble_react_flow_empty_nodes(assembler):
    """Test React Flow assembly with empty node list"""
    react_flow = assembler.assemble_react_flow([])

    assert len(react_flow.nodes) == 0
    assert len(react_flow.edges) == 0


def test_empty_workflow_validation():
    """Test that WorkflowSpec rejects empty steps (Pydantic validation)"""
    from pydantic import ValidationError

    # WorkflowSpec requires min_length=1 for steps
    with pytest.raises(ValidationError):
        WorkflowSpec(
            name="Empty Workflow",
            description="Workflow with no actions",
            trigger=PriceCondition(
                type="price",
                token=TokenType.GAS,
                operator="below",
                value=5.0
            ),
            steps=[]  # This should fail validation
        )


@pytest.mark.skipif(not SPOON_AI_AVAILABLE, reason="spoon_ai package not installed")
@pytest.mark.asyncio
async def test_assemble_with_malformed_state(assembler, sample_workflow_spec):
    """Test that assembly handles malformed state gracefully"""
    # Create a workflow with deliberately bad state types
    # The type validation we added should handle this
    state_graph = await assembler.assemble_state_graph(sample_workflow_spec)
    compiled = state_graph.compile()

    # Initial state with wrong types for metadata and lists
    malformed_state = {
        "workflow_id": "malformed_wf",
        "user_address": "NNLi44dJNXtDNSBkofB48aTVYtb1zZrNEs",
        "trigger_type": "price",
        "trigger_params": {},
        "current_step": 0,
        "total_steps": 2,
        "completed_steps": "not_a_list",  # Wrong type
        "step_results": None,  # Wrong type
        "workflow_status": "pending",
        "error": None,
        "metadata": "not_a_dict",  # Wrong type
    }

    # Should not crash due to type validation
    result = await compiled.invoke(malformed_state)

    # Verify execution completed despite malformed input
    assert result["workflow_status"] == "completed"
    # Type validation should have converted to proper lists
    assert isinstance(result["completed_steps"], list)
    assert isinstance(result["step_results"], list)
    assert isinstance(result["metadata"], dict)


@pytest.mark.skipif(not SPOON_AI_AVAILABLE, reason="spoon_ai package not installed")
@pytest.mark.asyncio
async def test_assemble_single_step_workflow(assembler):
    """Test assembly with single-step workflow"""
    workflow = WorkflowSpec(
        name="Simple Swap",
        description="Just swap GAS to NEO",
        trigger=PriceCondition(
            type="price",
            token=TokenType.GAS,
            operator="below",
            value=5.0
        ),
        steps=[
            WorkflowStep(
                action=SwapAction(
                    type="swap",
                    from_token=TokenType.GAS,
                    to_token=TokenType.NEO,
                    amount=10.0
                )
            )
        ]
    )

    state_graph = await assembler.assemble_state_graph(workflow)
    compiled = state_graph.compile()

    initial_state = {
        "workflow_id": "single_step",
        "user_address": "NXXXwj3Rd4qJErvdGGUY5JqbMhJmGHs4Xy",
        "trigger_type": "price",
        "trigger_params": {},
        "current_step": 0,
        "total_steps": 1,
        "completed_steps": [],
        "step_results": [],
        "workflow_status": "pending",
        "error": None,
        "metadata": {},
    }

    result = await compiled.invoke(initial_state)

    assert result["workflow_status"] == "completed"
    assert len(result["step_results"]) == 1


# ============================================================================
# Integration Tests
# ============================================================================

@pytest.mark.skipif(not SPOON_AI_AVAILABLE, reason="spoon_ai package not installed")
@pytest.mark.asyncio
async def test_full_workflow_pipeline(assembler, sample_workflow_spec, sample_nodes):
    """Test complete workflow: assemble -> serialize -> deserialize -> verify"""
    # Step 1: Assemble
    assembled = await assembler.assemble(sample_workflow_spec, sample_nodes)

    # Step 2: Serialize
    json_str = assembler.serialize(assembled)

    # Step 3: Store (simulate database storage)
    stored_json = json_str  # In real app, this would be saved to DB

    # Step 4: Load (simulate database retrieval)
    loaded_json = stored_json

    # Step 5: Deserialize
    restored = assembler.deserialize(loaded_json)

    # Step 6: Verify we can still create StateGraph from restored config
    state_graph = await assembler.assemble_state_graph(sample_workflow_spec)
    compiled = state_graph.compile()

    # Step 7: Execute workflow
    initial_state = restored.state_graph_config["initial_state"]
    initial_state["user_address"] = "NXXXwj3Rd4qJErvdGGUY5JqbMhJmGHs4Xy"

    result = await compiled.invoke(initial_state)

    # Verify successful execution
    assert result["workflow_status"] == "completed"
    assert result["workflow_id"] == restored.workflow_id
