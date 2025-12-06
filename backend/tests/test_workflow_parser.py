"""
Unit tests for WorkflowParserAgent

Tests the natural language workflow parsing functionality.
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch

from app.agents.workflow_parser import (
    WorkflowParserAgent,
    create_workflow_parser,
    WORKFLOW_PARSER_SYSTEM_PROMPT,
    MAX_INPUT_LENGTH,
)
from app.models.workflow_models import (
    WorkflowSpec,
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
    WorkflowStep,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_llm():
    """Create a mock ChatBot"""
    llm = MagicMock()
    llm.chat = AsyncMock()
    return llm


@pytest.fixture
def parser_agent(mock_llm):
    """Create a WorkflowParserAgent with mocked LLM"""
    with patch('app.agents.workflow_parser.SpoonReactMCP.__init__', return_value=None):
        agent = WorkflowParserAgent(llm=mock_llm)
        agent.llm = mock_llm
        agent.run = AsyncMock()
        return agent


# ============================================================================
# Test Agent Initialization
# ============================================================================

def test_agent_name():
    """Test that agent has correct name"""
    with patch('app.agents.workflow_parser.SpoonReactMCP.__init__', return_value=None):
        agent = WorkflowParserAgent()
        assert agent.name == "workflow_parser"


def test_agent_description():
    """Test that agent has descriptive description"""
    with patch('app.agents.workflow_parser.SpoonReactMCP.__init__', return_value=None):
        agent = WorkflowParserAgent()
        assert "workflow" in agent.description.lower()
        assert "parse" in agent.description.lower()


def test_agent_system_prompt():
    """Test that agent has comprehensive system prompt"""
    with patch('app.agents.workflow_parser.SpoonReactMCP.__init__', return_value=None):
        agent = WorkflowParserAgent()
        assert agent.system_prompt == WORKFLOW_PARSER_SYSTEM_PROMPT
        assert "GAS" in agent.system_prompt
        assert "NEO" in agent.system_prompt
        assert "bNEO" in agent.system_prompt
        assert "swap" in agent.system_prompt
        assert "stake" in agent.system_prompt
        assert "transfer" in agent.system_prompt
        assert "price" in agent.system_prompt
        assert "time" in agent.system_prompt


def test_factory_function():
    """Test that factory function creates agent correctly"""
    with patch('app.agents.workflow_parser.WorkflowParserAgent') as MockAgent:
        llm = MagicMock()
        agent = create_workflow_parser(llm=llm)
        MockAgent.assert_called_once_with(llm=llm)


# ============================================================================
# Test Static Helper Methods
# ============================================================================

def test_get_supported_tokens():
    """Test getting list of supported tokens"""
    tokens = WorkflowParserAgent.get_supported_tokens()
    assert "GAS" in tokens
    assert "NEO" in tokens
    assert "bNEO" in tokens
    assert len(tokens) == 3


def test_get_supported_actions():
    """Test getting list of supported actions"""
    actions = WorkflowParserAgent.get_supported_actions()
    assert "swap" in actions
    assert "stake" in actions
    assert "transfer" in actions
    assert len(actions) == 3


def test_get_supported_triggers():
    """Test getting list of supported triggers"""
    triggers = WorkflowParserAgent.get_supported_triggers()
    assert "price" in triggers
    assert "time" in triggers
    assert len(triggers) == 2


def test_get_example_workflows():
    """Test getting example workflow specifications"""
    examples = WorkflowParserAgent.get_example_workflows()
    assert isinstance(examples, dict)
    assert len(examples) > 0
    # Check that examples are serialized (dict, not WorkflowSpec objects)
    for example in examples.values():
        assert isinstance(example, dict)
        assert "name" in example
        assert "trigger" in example
        assert "steps" in example


# ============================================================================
# Test JSON Response Parsing
# ============================================================================

def test_parse_json_response_clean(parser_agent):
    """Test parsing clean JSON response"""
    json_str = '{"success": true, "workflow": {}}'
    result = parser_agent._parse_json_response(json_str)
    assert result["success"] is True


def test_parse_json_response_with_markdown(parser_agent):
    """Test parsing JSON wrapped in markdown code blocks"""
    json_str = '''```json
{"success": true, "workflow": {}}
```'''
    result = parser_agent._parse_json_response(json_str)
    assert result["success"] is True


def test_parse_json_response_with_whitespace(parser_agent):
    """Test parsing JSON with extra whitespace"""
    json_str = '''

    {"success": true, "workflow": {}}

    '''
    result = parser_agent._parse_json_response(json_str)
    assert result["success"] is True


def test_parse_json_response_invalid(parser_agent):
    """Test that invalid JSON raises error"""
    json_str = "not valid json"
    with pytest.raises(json.JSONDecodeError):
        parser_agent._parse_json_response(json_str)


# ============================================================================
# Test Successful Workflow Parsing
# ============================================================================

@pytest.mark.asyncio
async def test_parse_simple_swap(parser_agent):
    """Test parsing simple swap workflow"""
    user_input = "When GAS drops below $5, swap 10 GAS for NEO"

    # Mock the agent's run method to return a valid response
    parser_agent.run.return_value = json.dumps({
        "success": True,
        "workflow": {
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
                    },
                    "description": "Swap 10 GAS to NEO"
                }
            ]
        },
        "confidence": 0.98
    })

    result = await parser_agent.parse_workflow(user_input)

    assert isinstance(result, ParserSuccess)
    assert result.success is True
    assert isinstance(result.workflow, WorkflowSpec)
    assert result.workflow.name == "Auto DCA into NEO"
    assert result.confidence >= 0.9

    # Validate trigger
    assert isinstance(result.workflow.trigger, PriceCondition)
    assert result.workflow.trigger.token == TokenType.GAS
    assert result.workflow.trigger.operator == "below"
    assert result.workflow.trigger.value == 5.0

    # Validate steps
    assert len(result.workflow.steps) == 1
    assert isinstance(result.workflow.steps[0].action, SwapAction)
    assert result.workflow.steps[0].action.from_token == TokenType.GAS
    assert result.workflow.steps[0].action.to_token == TokenType.NEO
    assert result.workflow.steps[0].action.amount == 10.0


@pytest.mark.asyncio
async def test_parse_time_stake(parser_agent):
    """Test parsing time-based staking workflow"""
    user_input = "Stake 50% of my NEO every day at 9 AM"

    parser_agent.run.return_value = json.dumps({
        "success": True,
        "workflow": {
            "name": "Daily NEO Staking",
            "description": "Stake 50% of NEO balance daily at 9 AM",
            "trigger": {
                "type": "time",
                "schedule": "daily at 9am"
            },
            "steps": [
                {
                    "action": {
                        "type": "stake",
                        "token": "NEO",
                        "percentage": 50.0
                    },
                    "description": "Stake 50% of NEO balance"
                }
            ]
        },
        "confidence": 0.99
    })

    result = await parser_agent.parse_workflow(user_input)

    assert isinstance(result, ParserSuccess)
    assert result.success is True

    # Validate trigger
    assert isinstance(result.workflow.trigger, TimeCondition)
    assert result.workflow.trigger.schedule == "daily at 9am"

    # Validate steps
    assert len(result.workflow.steps) == 1
    assert isinstance(result.workflow.steps[0].action, StakeAction)
    assert result.workflow.steps[0].action.token == TokenType.NEO
    assert result.workflow.steps[0].action.percentage == 50.0


@pytest.mark.asyncio
async def test_parse_multi_step(parser_agent):
    """Test parsing multi-step workflow"""
    user_input = "Every Monday, swap 30% of my GAS to NEO and stake all of it"

    parser_agent.run.return_value = json.dumps({
        "success": True,
        "workflow": {
            "name": "Weekly Portfolio Rebalance",
            "description": "Every Monday, swap 30% of GAS to NEO and stake it",
            "trigger": {
                "type": "time",
                "schedule": "every Monday at 10am"
            },
            "steps": [
                {
                    "action": {
                        "type": "swap",
                        "from_token": "GAS",
                        "to_token": "NEO",
                        "percentage": 30.0
                    },
                    "description": "Swap 30% of GAS to NEO"
                },
                {
                    "action": {
                        "type": "stake",
                        "token": "NEO",
                        "percentage": 100.0
                    },
                    "description": "Stake all NEO"
                }
            ]
        },
        "confidence": 0.95
    })

    result = await parser_agent.parse_workflow(user_input)

    assert isinstance(result, ParserSuccess)
    assert len(result.workflow.steps) == 2
    assert isinstance(result.workflow.steps[0].action, SwapAction)
    assert isinstance(result.workflow.steps[1].action, StakeAction)


@pytest.mark.asyncio
async def test_parse_transfer(parser_agent):
    """Test parsing transfer workflow"""
    user_input = "Send 5 GAS to NNLi44dJNXtDNSBkofB48aTVYtb1zZrNEs every Friday"

    parser_agent.run.return_value = json.dumps({
        "success": True,
        "workflow": {
            "name": "Weekly GAS Transfer",
            "description": "Transfer 5 GAS to specified address every Friday",
            "trigger": {
                "type": "time",
                "schedule": "every Friday at 12pm"
            },
            "steps": [
                {
                    "action": {
                        "type": "transfer",
                        "token": "GAS",
                        "to_address": "NNLi44dJNXtDNSBkofB48aTVYtb1zZrNEs",
                        "amount": 5.0
                    },
                    "description": "Transfer 5 GAS"
                }
            ]
        },
        "confidence": 0.92
    })

    result = await parser_agent.parse_workflow(user_input)

    assert isinstance(result, ParserSuccess)
    assert isinstance(result.workflow.steps[0].action, TransferAction)
    assert result.workflow.steps[0].action.token == TokenType.GAS
    assert result.workflow.steps[0].action.amount == 5.0
    assert result.workflow.steps[0].action.to_address.startswith("N")


# ============================================================================
# Test Error Handling
# ============================================================================

@pytest.mark.asyncio
async def test_parse_ambiguous_input(parser_agent):
    """Test handling of ambiguous input"""
    user_input = "Do something with my tokens when the price is good"

    parser_agent.run.return_value = json.dumps({
        "success": False,
        "error": "The workflow description is too vague to parse accurately",
        "suggestions": [
            "Specify which token you want to monitor (GAS, NEO, or bNEO)",
            "Define what 'good price' means",
            "Specify the action you want (swap, stake, or transfer)"
        ]
    })

    result = await parser_agent.parse_workflow(user_input)

    assert isinstance(result, ParserError)
    assert result.success is False
    assert len(result.error) > 0
    assert len(result.suggestions) > 0


@pytest.mark.asyncio
async def test_parse_unsupported_token(parser_agent):
    """Test handling of unsupported token"""
    user_input = "Swap my Bitcoin for NEO when it's below $30k"

    parser_agent.run.return_value = json.dumps({
        "success": False,
        "error": "Unsupported token 'Bitcoin'",
        "suggestions": [
            "Use one of the supported tokens: GAS, NEO, or bNEO"
        ]
    })

    result = await parser_agent.parse_workflow(user_input)

    assert isinstance(result, ParserError)
    assert result.success is False
    assert "token" in result.error.lower() or "Bitcoin" in result.error


@pytest.mark.asyncio
async def test_parse_invalid_json_response(parser_agent):
    """
    Test handling when agent returns invalid JSON.
    This validates graceful error handling for malformed LLM responses.
    """
    user_input = "Test input"

    parser_agent.run.return_value = "This is not JSON at all"

    result = await parser_agent.parse_workflow(user_input)

    assert isinstance(result, ParserError)
    assert result.success is False
    assert "JSON" in result.error or "json" in result.error


@pytest.mark.asyncio
async def test_parse_workflow_validation_error(parser_agent):
    """
    Test handling of Pydantic validation errors.
    This ensures validation errors are caught and returned as ParserError.
    """
    # Invalid workflow - missing required 'steps' field
    invalid_response = {
        "success": True,
        "workflow": {
            "name": "Invalid",
            "description": "Missing steps",
            "trigger": {
                "type": "price",
                "token": "GAS",
                "operator": "below",
                "value": 5.0
            }
            # Missing 'steps' field
        },
        "confidence": 0.8
    }

    parser_agent.run.return_value = json.dumps(invalid_response)

    result = await parser_agent.parse_workflow("Test input")

    assert isinstance(result, ParserError)
    assert result.success is False
    assert "validation" in result.error.lower() or "invalid" in result.error.lower()


@pytest.mark.asyncio
async def test_parse_exception_handling(parser_agent):
    """Test handling when agent raises exception"""
    user_input = "Test input"

    parser_agent.run.side_effect = Exception("Something went wrong")

    result = await parser_agent.parse_workflow(user_input)

    assert isinstance(result, ParserError)
    assert result.success is False
    assert len(result.suggestions) > 0


# ============================================================================
# Test Workflow Model Validation
# ============================================================================

def test_workflow_spec_valid():
    """Test creating valid WorkflowSpec"""
    spec = WorkflowSpec(
        name="Test Workflow",
        description="A test workflow",
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
                description="Test swap"
            )
        ]
    )

    assert spec.name == "Test Workflow"
    assert len(spec.steps) == 1


def test_swap_action_same_token_invalid():
    """Test that swapping token to itself is invalid"""
    with pytest.raises(ValueError, match="Cannot swap a token to itself"):
        SwapAction(
            type="swap",
            from_token=TokenType.GAS,
            to_token=TokenType.GAS,
            amount=10.0
        )


def test_swap_action_both_amount_and_percentage_invalid():
    """Test that specifying both amount and percentage is invalid"""
    with pytest.raises(ValueError, match="Cannot specify both amount and percentage"):
        SwapAction(
            type="swap",
            from_token=TokenType.GAS,
            to_token=TokenType.NEO,
            amount=10.0,
            percentage=50.0
        )


def test_swap_action_neither_amount_nor_percentage_invalid():
    """Test that not specifying amount or percentage is invalid"""
    with pytest.raises(ValueError, match="Must specify either amount or percentage"):
        SwapAction(
            type="swap",
            from_token=TokenType.GAS,
            to_token=TokenType.NEO
        )


def test_transfer_action_invalid_address():
    """Test that invalid Neo address is rejected"""
    with pytest.raises(ValueError, match="Invalid Neo N3 address"):
        TransferAction(
            type="transfer",
            token=TokenType.GAS,
            to_address="NInvalidAddressWithWrongChecksum1",
            amount=5.0
        )


def test_price_condition_negative_value():
    """Test that negative price is rejected"""
    with pytest.raises(ValueError, match="Price value must be greater than 0"):
        PriceCondition(
            type="price",
            token=TokenType.GAS,
            operator="below",
            value=-5.0
        )


# ============================================================================
# Integration Test (Simulated)
# ============================================================================

@pytest.mark.asyncio
async def test_end_to_end_parsing_flow(parser_agent):
    """Test complete parsing flow with realistic scenario"""
    user_input = "When NEO goes above $15, swap 50% of my GAS for bNEO and stake it all"

    # Simulate realistic agent response
    parser_agent.run.return_value = '''```json
{
  "success": true,
  "workflow": {
    "name": "NEO Bull Run Strategy",
    "description": "When NEO price rises above $15, convert half of GAS holdings to bNEO and stake everything",
    "trigger": {
      "type": "price",
      "token": "NEO",
      "operator": "above",
      "value": 15.0
    },
    "steps": [
      {
        "action": {
          "type": "swap",
          "from_token": "GAS",
          "to_token": "bNEO",
          "percentage": 50.0
        },
        "description": "Swap 50% of GAS to bNEO"
      },
      {
        "action": {
          "type": "stake",
          "token": "bNEO",
          "percentage": 100.0
        },
        "description": "Stake all bNEO"
      }
    ]
  },
  "confidence": 0.94
}
```'''

    result = await parser_agent.parse_workflow(user_input)

    # Verify success
    assert isinstance(result, ParserSuccess)
    assert result.success is True
    assert result.confidence > 0.9

    # Verify workflow structure
    workflow = result.workflow
    assert "NEO" in workflow.name or "Bull" in workflow.name
    assert isinstance(workflow.trigger, PriceCondition)
    assert workflow.trigger.token == TokenType.NEO
    assert workflow.trigger.operator == "above"
    assert workflow.trigger.value == 15.0

    # Verify steps
    assert len(workflow.steps) == 2

    # Step 1: Swap
    step1 = workflow.steps[0]
    assert isinstance(step1.action, SwapAction)
    assert step1.action.from_token == TokenType.GAS
    assert step1.action.to_token == TokenType.BNEO
    assert step1.action.percentage == 50.0

    # Step 2: Stake
    step2 = workflow.steps[1]
    assert isinstance(step2.action, StakeAction)
    assert step2.action.token == TokenType.BNEO
    assert step2.action.percentage == 100.0

    # Verify can serialize back to JSON
    workflow_dict = workflow.model_dump()
    assert isinstance(workflow_dict, dict)
    assert "name" in workflow_dict
    assert "trigger" in workflow_dict
    assert "steps" in workflow_dict


# ============================================================================
# Test Edge Cases
# ============================================================================

@pytest.mark.asyncio
async def test_parse_empty_input(parser_agent):
    """
    Test handling of empty input string.
    This validates that empty inputs are rejected before calling the LLM.
    """
    result = await parser_agent.parse_workflow("")

    assert isinstance(result, ParserError)
    assert result.success is False
    assert "empty" in result.error.lower()


@pytest.mark.asyncio
async def test_parse_whitespace_only_input(parser_agent):
    """
    Test handling of whitespace-only input.
    This ensures whitespace inputs are treated as empty.
    """
    result = await parser_agent.parse_workflow("   \n\t   ")

    assert isinstance(result, ParserError)
    assert result.success is False
    assert "empty" in result.error.lower()


@pytest.mark.asyncio
async def test_parse_very_long_input(parser_agent):
    """
    Test handling of input exceeding MAX_INPUT_LENGTH.
    This validates the DoS protection mechanism.
    """
    long_input = "x" * (MAX_INPUT_LENGTH + 1)

    result = await parser_agent.parse_workflow(long_input)

    # Should reject before calling LLM
    assert isinstance(result, ParserError)
    assert result.success is False
    assert "too long" in result.error.lower()
    assert str(MAX_INPUT_LENGTH) in result.error


def test_system_prompt_completeness():
    """
    Test that system prompt covers all requirements.
    This validates the LLM has comprehensive instructions for parsing.
    """
    prompt = WORKFLOW_PARSER_SYSTEM_PROMPT

    # Check for all supported tokens
    assert "GAS" in prompt
    assert "NEO" in prompt
    assert "bNEO" in prompt

    # Check for all supported actions
    assert "swap" in prompt
    assert "stake" in prompt
    assert "transfer" in prompt

    # Check for all supported triggers
    assert "price" in prompt
    assert "time" in prompt

    # Check for examples
    assert "Example" in prompt or "example" in prompt

    # Check for error handling guidance
    assert "error" in prompt or "Error" in prompt
    assert "suggestions" in prompt or "Suggestions" in prompt

    # Check for JSON format specification
    assert "JSON" in prompt or "json" in prompt

    # Check for security rules (Issue #7)
    assert "security" in prompt.lower() or "NEVER execute" in prompt or "IGNORE" in prompt


def test_system_prompt_has_security_protection():
    """
    Test that system prompt includes prompt injection protection.
    This validates Issue #7 fix for security rules.
    """
    prompt = WORKFLOW_PARSER_SYSTEM_PROMPT

    # Check for security-related instructions
    security_keywords = ["NEVER execute", "IGNORE", "security", "injection", "override"]
    has_security = any(keyword.lower() in prompt.lower() for keyword in security_keywords)
    assert has_security, "System prompt should include security protection rules"
