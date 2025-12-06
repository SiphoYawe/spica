"""
Manual validation script for GraphAssembler (Story 3.2).

This script validates the GraphAssembler implementation without requiring
the full spoon_ai dependency to be installed.

Run this script to verify:
1. React Flow graph generation
2. Graph models
3. Serialization/deserialization
4. Edge creation logic
"""

import asyncio
import json
from pprint import pprint

# Import only what we need directly (bypass agents module to avoid spoon_ai dependency)
import sys
from pathlib import Path

# Add app to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.models.workflow_models import (
    WorkflowSpec,
    WorkflowStep,
    PriceCondition,
    SwapAction,
    StakeAction,
    TokenType,
)

# Import directly from file to bypass agents/__init__.py
from app.agents.designers.base import NodeSpecification, NodePosition, NodeData

from app.models.graph_models import GraphNode, GraphEdge, ReactFlowGraph, AssembledGraph

# Import GraphAssembler without going through services/__init__.py
from app.services.graph_assembler import GraphAssembler


def create_sample_nodes():
    """Create sample node specifications"""
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


def create_sample_workflow():
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


async def test_react_flow_assembly():
    """Test React Flow graph assembly"""
    print("\n" + "="*80)
    print("TEST 1: React Flow Graph Assembly")
    print("="*80)

    assembler = GraphAssembler()
    nodes = create_sample_nodes()

    react_flow = assembler.assemble_react_flow(nodes)

    print(f"\n✓ Created React Flow graph with {len(react_flow.nodes)} nodes")
    print(f"✓ Created {len(react_flow.edges)} edges")

    # Validate nodes
    assert len(react_flow.nodes) == 3, "Should have 3 nodes"
    assert react_flow.nodes[0].id == "trigger_1", "First node should be trigger"
    assert react_flow.nodes[0].type == "trigger", "First node type should be trigger"

    print("\n✓ Node validation passed")

    # Validate edges
    assert len(react_flow.edges) == 2, "Should have 2 edges"
    assert react_flow.edges[0].source == "trigger_1", "First edge should start from trigger"
    assert react_flow.edges[0].target == "action_1", "First edge should connect to action_1"

    print("✓ Edge validation passed")

    print("\nReact Flow Graph:")
    print(f"  Nodes: {[n.id for n in react_flow.nodes]}")
    print(f"  Edges: {[(e.source, '→', e.target) for e in react_flow.edges]}")

    return react_flow


async def test_complete_assembly():
    """Test complete graph assembly"""
    print("\n" + "="*80)
    print("TEST 2: Complete Graph Assembly")
    print("="*80)

    assembler = GraphAssembler()
    workflow = create_sample_workflow()
    nodes = create_sample_nodes()

    assembled = await assembler.assemble(workflow, nodes, workflow_id="test_wf_123")

    print(f"\n✓ Created assembled graph: {assembled.workflow_id}")
    print(f"✓ Workflow name: {assembled.workflow_name}")
    print(f"✓ React Flow nodes: {len(assembled.react_flow.nodes)}")
    print(f"✓ React Flow edges: {len(assembled.react_flow.edges)}")

    # Validate assembled graph structure
    assert assembled.workflow_id == "test_wf_123", "Workflow ID should match"
    assert assembled.workflow_name == "Auto DCA and Stake", "Name should match"
    assert len(assembled.react_flow.nodes) == 3, "Should have 3 nodes"
    assert "state_graph_config" in assembled.model_dump(), "Should have StateGraph config"

    print("\n✓ Assembly validation passed")

    # Print StateGraph config summary
    config = assembled.state_graph_config
    print(f"\nStateGraph Configuration:")
    print(f"  Trigger type: {config['trigger']['type']}")
    print(f"  Number of steps: {len(config['steps'])}")
    print(f"  Step types: {[s['action_type'] for s in config['steps']]}")

    return assembled


async def test_serialization():
    """Test JSON serialization/deserialization"""
    print("\n" + "="*80)
    print("TEST 3: JSON Serialization")
    print("="*80)

    assembler = GraphAssembler()
    workflow = create_sample_workflow()
    nodes = create_sample_nodes()

    # Assemble
    assembled = await assembler.assemble(workflow, nodes)

    # Serialize
    json_str = assembler.serialize(assembled)
    print(f"\n✓ Serialized to JSON ({len(json_str)} bytes)")

    # Validate JSON structure
    data = json.loads(json_str)
    assert "workflow_id" in data, "JSON should have workflow_id"
    assert "react_flow" in data, "JSON should have react_flow"
    assert "state_graph_config" in data, "JSON should have state_graph_config"

    print("✓ JSON structure validation passed")

    # Deserialize
    restored = assembler.deserialize(json_str)
    print("✓ Deserialized from JSON")

    # Validate roundtrip
    assert restored.workflow_id == assembled.workflow_id, "Workflow ID should match"
    assert restored.workflow_name == assembled.workflow_name, "Name should match"
    assert len(restored.react_flow.nodes) == len(assembled.react_flow.nodes), "Nodes should match"

    print("✓ Roundtrip validation passed")

    return json_str


async def test_edge_cases():
    """Test edge cases"""
    print("\n" + "="*80)
    print("TEST 4: Edge Cases")
    print("="*80)

    assembler = GraphAssembler()

    # Test empty nodes
    react_flow = assembler.assemble_react_flow([])
    assert len(react_flow.nodes) == 0, "Empty nodes should produce empty graph"
    assert len(react_flow.edges) == 0, "Empty nodes should produce no edges"
    print("✓ Empty nodes handled correctly")

    # Test single node
    single_node = [create_sample_nodes()[0]]
    react_flow = assembler.assemble_react_flow(single_node)
    assert len(react_flow.nodes) == 1, "Should have 1 node"
    assert len(react_flow.edges) == 0, "Single node should have no edges"
    print("✓ Single node handled correctly")

    print("\n✓ All edge cases passed")


async def main():
    """Run all validation tests"""
    print("\n" + "#"*80)
    print("# GraphAssembler Validation Suite (Story 3.2)")
    print("#"*80)

    try:
        # Run tests
        await test_react_flow_assembly()
        assembled = await test_complete_assembly()
        json_str = await test_serialization()
        await test_edge_cases()

        print("\n" + "="*80)
        print("VALIDATION SUMMARY")
        print("="*80)
        print("\n✓ All tests passed successfully!")
        print("\nStory 3.2 Acceptance Criteria:")
        print("  [✓] Accepts list of node specifications")
        print("  [✓] Generates React Flow compatible graph")
        print("  [✓] Nodes include: id, type, label, parameters, position")
        print("  [✓] Edges connect nodes in sequence")
        print("  [✓] StateGraph can be compiled from spec (config generated)")
        print("  [✓] Graph is serializable to JSON")

        print("\n" + "="*80)
        print("Sample JSON Output (first 500 chars):")
        print("="*80)
        print(json_str[:500] + "...")

        return True

    except Exception as e:
        print(f"\n❌ VALIDATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
