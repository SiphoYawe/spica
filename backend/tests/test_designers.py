"""
Tests for Designer Agents

Tests all designer agents individually and parallel execution.
"""

import pytest
import asyncio
from typing import List

from app.agents.designers import (
    TriggerDesignerAgent,
    SwapDesignerAgent,
    StakeDesignerAgent,
    TransferDesignerAgent,
    create_trigger_designer,
    create_swap_designer,
    create_stake_designer,
    create_transfer_designer,
    design_workflow_nodes,
    NodeSpecification,
    NodePosition,
)

from app.models.workflow_models import (
    WorkflowSpec,
    PriceCondition,
    TimeCondition,
    SwapAction,
    StakeAction,
    TransferAction,
    WorkflowStep,
    TokenType,
)


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def price_trigger():
    """Price trigger condition fixture"""
    return PriceCondition(
        type="price",
        token=TokenType.GAS,
        operator="below",
        value=5.0
    )


@pytest.fixture
def time_trigger():
    """Time trigger condition fixture"""
    return TimeCondition(
        type="time",
        schedule="daily at 9am"
    )


@pytest.fixture
def swap_action():
    """Swap action fixture"""
    return SwapAction(
        type="swap",
        from_token=TokenType.GAS,
        to_token=TokenType.NEO,
        amount=10.0
    )


@pytest.fixture
def stake_action():
    """Stake action fixture"""
    return StakeAction(
        type="stake",
        token=TokenType.NEO,
        percentage=50.0
    )


@pytest.fixture
def transfer_action():
    """Transfer action fixture"""
    return TransferAction(
        type="transfer",
        token=TokenType.GAS,
        to_address="NNLi44dJNXtDNSBkofB48aTVYtb1zZrNEs",  # Valid Neo N3 testnet address
        amount=5.0
    )


@pytest.fixture
def simple_workflow(price_trigger, swap_action):
    """Simple workflow with one trigger and one action"""
    return WorkflowSpec(
        name="Test Workflow",
        description="Test workflow for designer tests",
        trigger=price_trigger,
        steps=[
            WorkflowStep(
                action=swap_action,
                description="Swap GAS to NEO"
            )
        ]
    )


@pytest.fixture
def multi_step_workflow(time_trigger, swap_action, stake_action, transfer_action):
    """Complex workflow with multiple actions"""
    return WorkflowSpec(
        name="Multi-Step Workflow",
        description="Test workflow with multiple actions",
        trigger=time_trigger,
        steps=[
            WorkflowStep(action=swap_action, description="Swap GAS to NEO"),
            WorkflowStep(action=stake_action, description="Stake NEO"),
            WorkflowStep(action=transfer_action, description="Transfer GAS"),
        ]
    )


# ============================================================================
# TriggerDesignerAgent Tests
# ============================================================================

class TestTriggerDesignerAgent:
    """Tests for TriggerDesignerAgent"""

    @pytest.mark.asyncio
    async def test_create_trigger_designer(self):
        """Test factory function creates agent correctly"""
        agent = create_trigger_designer()

        assert isinstance(agent, TriggerDesignerAgent)
        assert agent.name == "trigger_designer"
        assert agent.node_type == "trigger"
        assert agent.icon == "trigger"

    @pytest.mark.asyncio
    async def test_design_price_trigger_node(self, price_trigger):
        """Test designing a price trigger node"""
        agent = create_trigger_designer()

        node = await agent.design_node(
            component=price_trigger,
            node_id="trigger_1",
            position=NodePosition(x=100, y=200)
        )

        # Validate node structure
        assert isinstance(node, NodeSpecification)
        assert node.id == "trigger_1"
        assert node.type == "trigger"
        assert node.position.x == 100
        assert node.position.y == 200

        # Validate label contains key info
        assert "GAS" in node.label
        assert "price" in node.label.lower() or "$" in node.label
        assert "5" in node.label or "5.00" in node.label

        # Validate parameters
        assert node.parameters["type"] == "price"
        assert node.parameters["token"] == "GAS"
        assert node.parameters["operator"] == "below"
        assert node.parameters["value"] == 5.0

        # Validate data
        assert node.data.status == "pending"
        assert node.data.icon == "trigger"

    @pytest.mark.asyncio
    async def test_design_time_trigger_node(self, time_trigger):
        """Test designing a time trigger node"""
        agent = create_trigger_designer()

        node = await agent.design_node(
            component=time_trigger,
            node_id="trigger_2"
        )

        # Validate node structure
        assert node.id == "trigger_2"
        assert node.type == "trigger"

        # Validate label contains time info
        assert "daily" in node.label.lower() or "9" in node.label

        # Validate parameters
        assert node.parameters["type"] == "time"
        assert "schedule" in node.parameters

    @pytest.mark.asyncio
    async def test_price_label_formatting(self):
        """Test price label formatting for different operators"""
        agent = create_trigger_designer()

        # Test "below" operator
        below_trigger = PriceCondition(
            type="price",
            token=TokenType.NEO,
            operator="below",
            value=15.50
        )
        node = await agent.design_node(below_trigger, "t1")
        assert "NEO" in node.label
        assert "below" in node.label.lower()
        assert "15.50" in node.label

        # Test "above" operator
        above_trigger = PriceCondition(
            type="price",
            token=TokenType.GAS,
            operator="above",
            value=10.00
        )
        node = await agent.design_node(above_trigger, "t2")
        assert "above" in node.label.lower()
        assert "10.00" in node.label

    @pytest.mark.asyncio
    async def test_time_label_formatting(self):
        """Test time label formatting for different schedules"""
        agent = create_trigger_designer()

        # Test daily schedule
        daily = TimeCondition(type="time", schedule="daily at 9am")
        node = await agent.design_node(daily, "t1")
        assert "daily" in node.label.lower() or "9" in node.label

        # Test weekly schedule
        weekly = TimeCondition(type="time", schedule="every Monday at 10am")
        node = await agent.design_node(weekly, "t2")
        assert "monday" in node.label.lower() or "week" in node.label.lower()


# ============================================================================
# SwapDesignerAgent Tests
# ============================================================================

class TestSwapDesignerAgent:
    """Tests for SwapDesignerAgent"""

    @pytest.mark.asyncio
    async def test_create_swap_designer(self):
        """Test factory function creates agent correctly"""
        agent = create_swap_designer()

        assert isinstance(agent, SwapDesignerAgent)
        assert agent.name == "swap_designer"
        assert agent.node_type == "swap"
        assert agent.icon == "swap"

    @pytest.mark.asyncio
    async def test_design_swap_node_with_amount(self, swap_action):
        """Test designing a swap node with fixed amount"""
        agent = create_swap_designer()

        node = await agent.design_node(
            component=swap_action,
            node_id="swap_1",
            position=NodePosition(x=100, y=200)
        )

        # Validate structure
        assert node.id == "swap_1"
        assert node.type == "swap"
        assert node.position.x == 100

        # Validate label
        assert "GAS" in node.label
        assert "NEO" in node.label
        assert "10" in node.label  # Amount
        assert "→" in node.label or "->" in node.label  # Arrow

        # Validate parameters
        assert node.parameters["type"] == "swap"
        assert node.parameters["from_token"] == "GAS"
        assert node.parameters["to_token"] == "NEO"
        assert node.parameters["amount"] == 10.0

    @pytest.mark.asyncio
    async def test_design_swap_node_with_percentage(self):
        """Test designing a swap node with percentage"""
        agent = create_swap_designer()

        swap_action = SwapAction(
            type="swap",
            from_token=TokenType.NEO,
            to_token=TokenType.BNEO,
            percentage=75.0
        )

        node = await agent.design_node(swap_action, "swap_2")

        # Validate label contains percentage (can be 75% or 75.0%)
        assert "75" in node.label and "%" in node.label
        assert "NEO" in node.label
        assert "bNEO" in node.label

        # Validate parameters
        assert node.parameters["percentage"] == 75.0
        assert node.parameters["amount"] is None


# ============================================================================
# StakeDesignerAgent Tests
# ============================================================================

class TestStakeDesignerAgent:
    """Tests for StakeDesignerAgent"""

    @pytest.mark.asyncio
    async def test_create_stake_designer(self):
        """Test factory function creates agent correctly"""
        agent = create_stake_designer()

        assert isinstance(agent, StakeDesignerAgent)
        assert agent.name == "stake_designer"
        assert agent.node_type == "stake"
        assert agent.icon == "stake"

    @pytest.mark.asyncio
    async def test_design_stake_node_with_percentage(self, stake_action):
        """Test designing a stake node with percentage"""
        agent = create_stake_designer()

        node = await agent.design_node(
            component=stake_action,
            node_id="stake_1"
        )

        # Validate structure
        assert node.id == "stake_1"
        assert node.type == "stake"

        # Validate label
        assert "Stake" in node.label
        assert "NEO" in node.label
        assert "50" in node.label and "%" in node.label  # Can be 50% or 50.0%

        # Validate parameters
        assert node.parameters["type"] == "stake"
        assert node.parameters["token"] == "NEO"
        assert node.parameters["percentage"] == 50.0

    @pytest.mark.asyncio
    async def test_design_stake_node_with_amount(self):
        """Test designing a stake node with fixed amount"""
        agent = create_stake_designer()

        stake_action = StakeAction(
            type="stake",
            token=TokenType.GAS,
            amount=100.0
        )

        node = await agent.design_node(stake_action, "stake_2")

        # Validate label
        assert "100" in node.label
        assert "GAS" in node.label

        # Validate parameters
        assert node.parameters["amount"] == 100.0
        assert node.parameters["percentage"] is None


# ============================================================================
# TransferDesignerAgent Tests
# ============================================================================

class TestTransferDesignerAgent:
    """Tests for TransferDesignerAgent"""

    @pytest.mark.asyncio
    async def test_create_transfer_designer(self):
        """Test factory function creates agent correctly"""
        agent = create_transfer_designer()

        assert isinstance(agent, TransferDesignerAgent)
        assert agent.name == "transfer_designer"
        assert agent.node_type == "transfer"
        assert agent.icon == "transfer"

    @pytest.mark.asyncio
    async def test_design_transfer_node(self, transfer_action):
        """Test designing a transfer node"""
        agent = create_transfer_designer()

        node = await agent.design_node(
            component=transfer_action,
            node_id="transfer_1"
        )

        # Validate structure
        assert node.id == "transfer_1"
        assert node.type == "transfer"

        # Validate label
        assert "Transfer" in node.label
        assert "GAS" in node.label
        assert "5" in node.label  # Amount

        # Label should have shortened address
        assert "NNLi" in node.label or "NEs" in node.label

        # Validate parameters
        assert node.parameters["type"] == "transfer"
        assert node.parameters["token"] == "GAS"
        assert node.parameters["amount"] == 5.0
        assert len(node.parameters["to_address"]) == 34

    @pytest.mark.asyncio
    async def test_address_shortening(self):
        """Test that addresses are properly shortened in labels"""
        agent = create_transfer_designer()

        # Use a valid Neo N3 testnet address
        transfer_action = TransferAction(
            type="transfer",
            token=TokenType.NEO,
            to_address="NNLi44dJNXtDNSBkofB48aTVYtb1zZrNEs",
            percentage=25.0
        )

        node = await agent.design_node(transfer_action, "transfer_2")

        # Full address should be in parameters
        assert node.parameters["to_address"] == "NNLi44dJNXtDNSBkofB48aTVYtb1zZrNEs"

        # Shortened address should be in label (NNLi...NEs)
        assert "NNLi" in node.label
        assert "..." in node.label


# ============================================================================
# Parallel Execution Tests
# ============================================================================

class TestParallelExecution:
    """Tests for parallel workflow node design"""

    @pytest.mark.asyncio
    async def test_design_simple_workflow(self, simple_workflow):
        """Test designing a simple workflow with one action"""
        nodes = await design_workflow_nodes(simple_workflow)

        # Should have 2 nodes: trigger + 1 action
        assert len(nodes) == 2

        # First node should be trigger
        assert nodes[0].type == "trigger"
        assert nodes[0].id == "trigger_1"

        # Second node should be swap action
        assert nodes[1].type == "swap"
        assert nodes[1].id == "action_1"

        # Validate positions are set
        assert nodes[0].position.x >= 0
        assert nodes[0].position.y >= 0
        assert nodes[1].position.y > nodes[0].position.y  # Action below trigger

    @pytest.mark.asyncio
    async def test_design_multi_step_workflow(self, multi_step_workflow):
        """Test designing a complex workflow with multiple actions"""
        nodes = await design_workflow_nodes(multi_step_workflow)

        # Should have 4 nodes: trigger + 3 actions
        assert len(nodes) == 4

        # Validate node types
        assert nodes[0].type == "trigger"
        assert nodes[1].type == "swap"
        assert nodes[2].type == "stake"
        assert nodes[3].type == "transfer"

        # Validate IDs
        assert nodes[0].id == "trigger_1"
        assert nodes[1].id == "action_1"
        assert nodes[2].id == "action_2"
        assert nodes[3].id == "action_3"

        # Validate vertical layout (y increases)
        for i in range(len(nodes) - 1):
            assert nodes[i+1].position.y > nodes[i].position.y

    @pytest.mark.asyncio
    async def test_parallel_execution_uses_gather(self, multi_step_workflow, monkeypatch):
        """Test that parallel execution uses asyncio.gather"""
        import asyncio
        from unittest.mock import Mock, AsyncMock

        # Track whether asyncio.gather was called
        gather_called = False
        original_gather = asyncio.gather

        async def mock_gather(*tasks, **kwargs):
            nonlocal gather_called
            gather_called = True
            # Call original gather to maintain functionality
            return await original_gather(*tasks, **kwargs)

        # Patch asyncio.gather
        monkeypatch.setattr(asyncio, "gather", mock_gather)

        # Execute workflow node design
        nodes = await design_workflow_nodes(multi_step_workflow)

        # Verify asyncio.gather was used (parallel execution)
        assert gather_called, "design_workflow_nodes should use asyncio.gather for parallel execution"

        # Verify correct number of nodes created
        assert len(nodes) == 4  # 1 trigger + 3 actions

    @pytest.mark.asyncio
    async def test_node_spec_output_format(self, simple_workflow):
        """Test that node specs match expected React Flow format"""
        nodes = await design_workflow_nodes(simple_workflow)

        for node in nodes:
            # Validate required fields
            assert hasattr(node, 'id')
            assert hasattr(node, 'type')
            assert hasattr(node, 'label')
            assert hasattr(node, 'parameters')
            assert hasattr(node, 'position')
            assert hasattr(node, 'data')

            # Validate types
            assert isinstance(node.id, str)
            assert isinstance(node.type, str)
            assert isinstance(node.label, str)
            assert isinstance(node.parameters, dict)

            # Validate position
            assert hasattr(node.position, 'x')
            assert hasattr(node.position, 'y')
            assert isinstance(node.position.x, int)
            assert isinstance(node.position.y, int)

            # Validate data
            assert hasattr(node.data, 'label')
            assert hasattr(node.data, 'icon')
            assert hasattr(node.data, 'status')
            assert node.data.status == "pending"

    @pytest.mark.asyncio
    async def test_node_serialization(self, simple_workflow):
        """Test that nodes can be serialized to JSON"""
        nodes = await design_workflow_nodes(simple_workflow)

        # All nodes should be serializable via model_dump()
        for node in nodes:
            node_dict = node.model_dump()

            assert isinstance(node_dict, dict)
            assert "id" in node_dict
            assert "type" in node_dict
            assert "label" in node_dict
            assert "parameters" in node_dict
            assert "position" in node_dict
            assert "data" in node_dict


# ============================================================================
# Integration Tests
# ============================================================================

class TestDesignerIntegration:
    """Integration tests combining parser and designers"""

    @pytest.mark.asyncio
    async def test_end_to_end_workflow_design(self):
        """Test complete workflow: parse → design nodes"""
        from app.agents import create_workflow_parser

        # Parse a workflow from natural language
        parser = create_workflow_parser()
        parse_result = await parser.parse_workflow(
            "When GAS drops below $5, swap 10 GAS for NEO"
        )

        assert parse_result.success is True

        # Design nodes from parsed workflow
        nodes = await design_workflow_nodes(parse_result.workflow)

        # Validate complete output
        assert len(nodes) == 2  # Trigger + swap action
        assert nodes[0].type == "trigger"
        assert nodes[1].type == "swap"

        # Validate trigger node
        assert "GAS" in nodes[0].label
        assert "5" in nodes[0].label

        # Validate swap node
        assert "GAS" in nodes[1].label
        assert "NEO" in nodes[1].label
        assert "10" in nodes[1].label

    @pytest.mark.asyncio
    async def test_multi_step_end_to_end(self):
        """Test multi-step workflow: parse → design"""
        from app.agents import create_workflow_parser

        parser = create_workflow_parser()
        parse_result = await parser.parse_workflow(
            "Every Monday, swap 30% of my GAS to NEO and stake all of it"
        )

        assert parse_result.success is True

        nodes = await design_workflow_nodes(parse_result.workflow)

        # Should have trigger + 2 actions
        assert len(nodes) == 3
        assert nodes[0].type == "trigger"
        assert nodes[1].type == "swap"
        assert nodes[2].type == "stake"


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestErrorHandling:
    """Tests for error handling in designers"""

    @pytest.mark.asyncio
    async def test_invalid_position_type(self, swap_action):
        """Test handling of invalid position types"""
        agent = create_swap_designer()

        # Should work with None (default position)
        node = await agent.design_node(swap_action, "swap_1", position=None)
        assert node.position.x == 0
        assert node.position.y == 0

    @pytest.mark.asyncio
    async def test_empty_workflow(self):
        """Test that WorkflowSpec rejects empty steps (validation)"""
        from pydantic import ValidationError

        # WorkflowSpec requires min_length=1 for steps
        # This should fail validation
        with pytest.raises(ValidationError):
            WorkflowSpec(
                name="Empty Workflow",
                description="Test empty workflow",
                trigger=PriceCondition(
                    type="price",
                    token=TokenType.GAS,
                    operator="below",
                    value=5.0
                ),
                steps=[]
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
