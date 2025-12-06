"""
Unit tests for Workflow Models

Tests the Pydantic models for workflow specification without requiring SpoonOS.
"""

import pytest
from pydantic import ValidationError

from app.models.workflow_models import (
    WorkflowSpec,
    WorkflowStep,
    ParserSuccess,
    ParserError,
    TokenType,
    ActionType,
    TriggerType,
    PriceCondition,
    TimeCondition,
    SwapAction,
    StakeAction,
    TransferAction,
    EXAMPLE_WORKFLOWS,
)


# ============================================================================
# Test Enums
# ============================================================================

def test_token_type_enum():
    """
    Test TokenType enum contains exactly the three supported Neo N3 tokens.
    This ensures we only support the tokens available in our workflow system.
    """
    assert TokenType.GAS == "GAS"
    assert TokenType.NEO == "NEO"
    assert TokenType.BNEO == "bNEO"
    assert len(TokenType) == 3


def test_action_type_enum():
    """
    Test ActionType enum contains exactly the three supported DeFi actions.
    This validates that only swap, stake, and transfer operations are allowed.
    """
    assert ActionType.SWAP == "swap"
    assert ActionType.STAKE == "stake"
    assert ActionType.TRANSFER == "transfer"
    assert len(ActionType) == 3


def test_trigger_type_enum():
    """
    Test TriggerType enum contains exactly the two supported trigger mechanisms.
    This ensures workflows can only be triggered by price conditions or time schedules.
    """
    assert TriggerType.PRICE == "price"
    assert TriggerType.TIME == "time"
    assert len(TriggerType) == 2


# ============================================================================
# Test Trigger Conditions
# ============================================================================

def test_price_condition_valid():
    """
    Test creating a valid price-based trigger condition.
    This validates that price conditions can be created with valid token, operator, and value.
    """
    condition = PriceCondition(
        type="price",
        token=TokenType.GAS,
        operator="below",
        value=5.0
    )
    assert condition.token == TokenType.GAS
    assert condition.operator == "below"
    assert condition.value == 5.0


def test_price_condition_negative_value():
    """
    Test that negative price values are rejected by validation.
    This prevents invalid workflows with nonsensical negative price triggers.
    """
    with pytest.raises(ValidationError, match="greater than 0"):
        PriceCondition(
            type="price",
            token=TokenType.GAS,
            operator="below",
            value=-5.0
        )


def test_price_condition_zero_value():
    """
    Test that zero price values are rejected by validation.
    This ensures price triggers are meaningful (price must be > 0).
    """
    with pytest.raises(ValidationError):
        PriceCondition(
            type="price",
            token=TokenType.GAS,
            operator="below",
            value=0.0
        )


def test_time_condition_valid():
    """
    Test creating a valid time-based trigger condition.
    This validates that time conditions accept natural language schedules.
    """
    condition = TimeCondition(
        type="time",
        schedule="daily at 9am"
    )
    assert condition.schedule == "daily at 9am"


def test_time_condition_empty_schedule():
    """
    Test that empty schedule strings are rejected by validation.
    This ensures every time trigger has a meaningful schedule definition.
    """
    with pytest.raises(ValidationError, match="Schedule cannot be empty"):
        TimeCondition(
            type="time",
            schedule=""
        )


def test_time_condition_whitespace_schedule():
    """
    Test that whitespace-only schedule strings are rejected.
    This prevents users from submitting invalid schedules that appear non-empty.
    """
    with pytest.raises(ValidationError, match="Schedule cannot be empty"):
        TimeCondition(
            type="time",
            schedule="   "
        )


# ============================================================================
# Test Actions
# ============================================================================

def test_swap_action_valid():
    """
    Test creating a valid token swap action with fixed amount.
    This validates the core swap functionality with explicit token amounts.
    """
    action = SwapAction(
        type="swap",
        from_token=TokenType.GAS,
        to_token=TokenType.NEO,
        amount=10.0
    )
    assert action.from_token == TokenType.GAS
    assert action.to_token == TokenType.NEO
    assert action.amount == 10.0
    assert action.percentage is None


def test_swap_action_with_percentage():
    """
    Test creating a swap action with percentage-based amounts.
    This validates that users can swap a percentage of their balance instead of fixed amounts.
    """
    action = SwapAction(
        type="swap",
        from_token=TokenType.GAS,
        to_token=TokenType.BNEO,
        percentage=50.0
    )
    assert action.percentage == 50.0
    assert action.amount is None


def test_swap_action_same_token_invalid():
    """
    Test that swapping a token to itself is rejected.
    This prevents nonsensical operations like swapping GAS to GAS.
    """
    with pytest.raises(ValidationError, match="Cannot swap a token to itself"):
        SwapAction(
            type="swap",
            from_token=TokenType.GAS,
            to_token=TokenType.GAS,
            amount=10.0
        )


def test_swap_action_both_amount_and_percentage_invalid():
    """
    Test that specifying both amount and percentage is rejected.
    This enforces mutual exclusivity - users must choose one or the other.
    """
    with pytest.raises(ValidationError, match="Cannot specify both amount and percentage"):
        SwapAction(
            type="swap",
            from_token=TokenType.GAS,
            to_token=TokenType.NEO,
            amount=10.0,
            percentage=50.0
        )


def test_swap_action_neither_amount_nor_percentage_invalid():
    """
    Test that omitting both amount and percentage is rejected.
    This ensures every swap has a defined quantity to execute.
    """
    with pytest.raises(ValidationError, match="Must specify either amount or percentage"):
        SwapAction(
            type="swap",
            from_token=TokenType.GAS,
            to_token=TokenType.NEO
        )


def test_stake_action_valid():
    """
    Test creating a valid staking action with fixed amount.
    This validates that tokens can be staked with explicit amounts.
    """
    action = StakeAction(
        type="stake",
        token=TokenType.NEO,
        amount=100.0
    )
    assert action.token == TokenType.NEO
    assert action.amount == 100.0


def test_stake_action_with_percentage():
    """
    Test creating a staking action with percentage-based amounts.
    This allows users to stake a percentage of their token balance.
    """
    action = StakeAction(
        type="stake",
        token=TokenType.NEO,
        percentage=75.0
    )
    assert action.percentage == 75.0
    assert action.amount is None


def test_stake_action_both_amount_and_percentage_invalid():
    """
    Test that specifying both amount and percentage for staking is rejected.
    This enforces the mutual exclusivity constraint on stake amounts.
    """
    with pytest.raises(ValidationError, match="Cannot specify both amount and percentage"):
        StakeAction(
            type="stake",
            token=TokenType.NEO,
            amount=100.0,
            percentage=50.0
        )


def test_transfer_action_valid():
    """
    Test creating a valid token transfer action.
    This validates that tokens can be transferred to a valid Neo N3 address.
    """
    # Use a real valid Neo N3 address (from Neo documentation)
    action = TransferAction(
        type="transfer",
        token=TokenType.GAS,
        to_address="NNLi44dJNXtDNSBkofB48aTVYtb1zZrNEs",
        amount=5.0
    )
    assert action.token == TokenType.GAS
    assert action.to_address == "NNLi44dJNXtDNSBkofB48aTVYtb1zZrNEs"
    assert action.amount == 5.0


def test_transfer_action_invalid_address_not_starting_with_n():
    """
    Test that addresses not starting with 'N' are rejected.
    This enforces Neo N3's address format requirement (all addresses start with 'N').
    """
    with pytest.raises(ValidationError, match="Invalid Neo N3 address"):
        TransferAction(
            type="transfer",
            token=TokenType.GAS,
            to_address="Aabc123def456ghi789jkl012mno345pqr",
            amount=5.0
        )


def test_transfer_action_invalid_address_length():
    """
    Test that addresses with incorrect length are rejected.
    Neo N3 addresses must be exactly 34 characters long.
    """
    with pytest.raises(ValidationError, match="Invalid Neo N3 address"):
        TransferAction(
            type="transfer",
            token=TokenType.GAS,
            to_address="Nabc123",  # Too short
            amount=5.0
        )


def test_transfer_action_empty_address():
    """
    Test that empty addresses are rejected by validation.
    This prevents transfers without a valid recipient address.
    """
    with pytest.raises(ValidationError, match="Address cannot be empty"):
        TransferAction(
            type="transfer",
            token=TokenType.GAS,
            to_address="",
            amount=5.0
        )


# ============================================================================
# Test WorkflowSpec
# ============================================================================

def test_workflow_spec_valid():
    """Test creating valid WorkflowSpec"""
    spec = WorkflowSpec(
        name="Test Workflow",
        description="A test workflow for DeFi automation",
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
            )
        ]
    )

    assert spec.name == "Test Workflow"
    assert spec.description == "A test workflow for DeFi automation"
    assert isinstance(spec.trigger, PriceCondition)
    assert len(spec.steps) == 1
    assert isinstance(spec.steps[0].action, SwapAction)


def test_workflow_spec_multi_step():
    """Test creating WorkflowSpec with multiple steps"""
    spec = WorkflowSpec(
        name="Multi-Step Workflow",
        description="A workflow with multiple actions",
        trigger=TimeCondition(
            type="time",
            schedule="daily at 9am"
        ),
        steps=[
            WorkflowStep(
                action=SwapAction(
                    type="swap",
                    from_token=TokenType.GAS,
                    to_token=TokenType.NEO,
                    percentage=30.0
                ),
                description="Swap 30% of GAS to NEO"
            ),
            WorkflowStep(
                action=StakeAction(
                    type="stake",
                    token=TokenType.NEO,
                    percentage=100.0
                ),
                description="Stake all NEO"
            )
        ]
    )

    assert len(spec.steps) == 2
    assert isinstance(spec.steps[0].action, SwapAction)
    assert isinstance(spec.steps[1].action, StakeAction)


def test_workflow_spec_empty_steps_invalid():
    """Test that WorkflowSpec with no steps is invalid"""
    with pytest.raises(ValidationError):
        WorkflowSpec(
            name="Invalid Workflow",
            description="This workflow has no steps",
            trigger=PriceCondition(
                type="price",
                token=TokenType.GAS,
                operator="below",
                value=5.0
            ),
            steps=[]
        )


def test_workflow_spec_empty_name_invalid():
    """Test that WorkflowSpec with empty name is invalid"""
    with pytest.raises(ValidationError, match="Workflow name cannot be empty"):
        WorkflowSpec(
            name="",
            description="Valid description",
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
                    description="Test"
                )
            ]
        )


# ============================================================================
# Test Parser Response Models
# ============================================================================

def test_parser_success():
    """Test creating ParserSuccess response"""
    workflow = WorkflowSpec(
        name="Test",
        description="Test workflow",
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
                description="Test"
            )
        ]
    )

    response = ParserSuccess(
        success=True,
        workflow=workflow,
        confidence=0.95
    )

    assert response.success is True
    assert isinstance(response.workflow, WorkflowSpec)
    assert response.confidence == 0.95


def test_parser_error():
    """Test creating ParserError response"""
    response = ParserError(
        success=False,
        error="The workflow description is too vague",
        suggestions=[
            "Specify which token to monitor",
            "Define the action to take"
        ]
    )

    assert response.success is False
    assert "vague" in response.error
    assert len(response.suggestions) == 2


# ============================================================================
# Test Example Workflows
# ============================================================================

def test_example_workflows_exist():
    """Test that example workflows are provided"""
    assert isinstance(EXAMPLE_WORKFLOWS, dict)
    assert len(EXAMPLE_WORKFLOWS) > 0


def test_example_workflows_valid():
    """Test that all example workflows are valid"""
    for name, workflow in EXAMPLE_WORKFLOWS.items():
        assert isinstance(workflow, WorkflowSpec)
        assert workflow.name
        assert workflow.description
        assert workflow.trigger
        assert len(workflow.steps) > 0


def test_example_price_swap_workflow():
    """Test the price_swap example workflow"""
    workflow = EXAMPLE_WORKFLOWS["price_swap"]

    assert isinstance(workflow, WorkflowSpec)
    assert isinstance(workflow.trigger, PriceCondition)
    assert workflow.trigger.token == TokenType.GAS
    assert workflow.trigger.operator == "below"
    assert workflow.trigger.value == 5.0

    assert len(workflow.steps) == 1
    assert isinstance(workflow.steps[0].action, SwapAction)
    assert workflow.steps[0].action.from_token == TokenType.GAS
    assert workflow.steps[0].action.to_token == TokenType.NEO


def test_example_time_stake_workflow():
    """Test the time_stake example workflow"""
    workflow = EXAMPLE_WORKFLOWS["time_stake"]

    assert isinstance(workflow, WorkflowSpec)
    assert isinstance(workflow.trigger, TimeCondition)
    assert "daily" in workflow.trigger.schedule.lower()

    assert len(workflow.steps) == 1
    assert isinstance(workflow.steps[0].action, StakeAction)
    assert workflow.steps[0].action.token == TokenType.NEO
    assert workflow.steps[0].action.percentage == 50.0


def test_example_multi_step_workflow():
    """Test the multi_step example workflow"""
    workflow = EXAMPLE_WORKFLOWS["multi_step"]

    assert isinstance(workflow, WorkflowSpec)
    assert isinstance(workflow.trigger, TimeCondition)

    assert len(workflow.steps) == 2
    assert isinstance(workflow.steps[0].action, SwapAction)
    assert isinstance(workflow.steps[1].action, StakeAction)


# ============================================================================
# Test Model Serialization
# ============================================================================

def test_workflow_spec_serialization():
    """Test that WorkflowSpec can be serialized to dict"""
    spec = WorkflowSpec(
        name="Test",
        description="Test workflow",
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
                description="Test"
            )
        ]
    )

    # Serialize to dict
    spec_dict = spec.model_dump()

    assert isinstance(spec_dict, dict)
    assert spec_dict["name"] == "Test"
    assert spec_dict["trigger"]["type"] == "price"
    assert spec_dict["steps"][0]["action"]["type"] == "swap"


def test_workflow_spec_json_round_trip():
    """Test that WorkflowSpec can be serialized to JSON and back"""
    spec = WorkflowSpec(
        name="Test",
        description="Test workflow",
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
                description="Test"
            )
        ]
    )

    # Serialize to JSON string
    json_str = spec.model_dump_json()
    assert isinstance(json_str, str)

    # Deserialize back
    import json
    spec_dict = json.loads(json_str)
    spec_restored = WorkflowSpec(**spec_dict)

    assert spec_restored.name == spec.name
    assert spec_restored.trigger.value == spec.trigger.value
    assert spec_restored.steps[0].action.amount == spec.steps[0].action.amount
