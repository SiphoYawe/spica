"""
Unit tests for deploy endpoint with x402 payment integration.

Tests cover:
- 402 response without payment
- X-PAYMENT-REQUEST header format
- Valid payment returns 200
- Invalid payment returns 402
- Workflow not found handling
- Demo mode bypass
"""

import base64
import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from decimal import Decimal

from fastapi import status
from fastapi.testclient import TestClient

from app.main import app
from app.models.payment_models import (
    WorkflowComplexity,
    PaymentRequestData,
    PaymentVerificationResult,
    PaymentErrorCode,
)
from app.models.workflow_models import (
    WorkflowSpec,
    WorkflowStep,
    PriceCondition,
    SwapAction,
    TokenType,
)
from app.models.graph_models import (
    AssembledGraph,
    ReactFlowGraph,
    GraphNode,
    GraphEdge,
    NodePosition,
    StoredWorkflow,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def client():
    """Create a FastAPI TestClient"""
    return TestClient(app)


@pytest.fixture
def sample_workflow_spec():
    """Sample workflow specification for testing"""
    return WorkflowSpec(
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


@pytest.fixture
def sample_assembled_graph(sample_workflow_spec):
    """Sample assembled graph for testing"""
    return AssembledGraph(
        workflow_id="wf_test123456",
        workflow_name="Auto DCA into NEO",
        workflow_description="When GAS price falls below $5, automatically swap 10 GAS for NEO",
        workflow_spec=sample_workflow_spec,
        react_flow=ReactFlowGraph(
            nodes=[
                GraphNode(
                    id="trigger_1",
                    type="trigger",
                    label="GAS Below $5.00",
                    position=NodePosition(x=250, y=0),
                    parameters={
                        "token": "GAS",
                        "operator": "below",
                        "value": 5.0
                    },
                    data={
                        "label": "GAS Below $5.00",
                        "type": "price",
                        "icon": "dollar-sign"
                    }
                ),
                GraphNode(
                    id="action_1",
                    type="swap",
                    label="Swap 10.0 GAS → NEO",
                    position=NodePosition(x=250, y=150),
                    parameters={
                        "from_token": "GAS",
                        "to_token": "NEO",
                        "amount": 10.0
                    },
                    data={
                        "label": "Swap 10.0 GAS → NEO",
                        "type": "swap",
                        "icon": "repeat"
                    }
                )
            ],
            edges=[
                GraphEdge(
                    id="e1",
                    source="trigger_1",
                    target="action_1",
                    type="default",
                    animated=False
                )
            ]
        ),
        state_graph_config={"nodes": [], "edges": []}
    )


@pytest.fixture
def sample_stored_workflow(sample_assembled_graph):
    """Sample stored workflow for testing"""
    return StoredWorkflow(
        workflow_id="wf_test123456",
        user_id="test_user",
        user_address="NTest123",
        assembled_graph=sample_assembled_graph,
        status="paused",  # Use a valid status
        enabled=False,
        trigger_count=0,
        execution_count=0,
    )


@pytest.fixture
def sample_payment_request():
    """Sample x402 payment request"""
    return {
        "x402Version": 1,
        "accepts": [{
            "scheme": "exact",
            "network": "base-sepolia",
            "max_amount_required": "20000",
            "resource": "workflow://wf_test123456",
            "description": "Execute workflow: Auto DCA into NEO",
            "mime_type": "application/json",
            "pay_to": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
            "max_timeout_seconds": 120,
            "asset": "0xa063B8d5ada3bE64A24Df594F96aB75F0fb78160",
            "extra": {
                "currency": "USDC",
                "memo": "Spica workflow execution: wf_test123456",
                "metadata": {
                    "workflow_id": "wf_test123456",
                    "complexity": "triggered",
                    "service": "Spica Workflow Builder"
                }
            }
        }]
    }


# ============================================================================
# Test 402 Response Without Payment
# ============================================================================

@pytest.mark.asyncio
async def test_deploy_without_payment_returns_402(client, sample_stored_workflow, sample_payment_request):
    """
    Test: POST /workflows/{id}/deploy without X-PAYMENT header returns 402.

    Acceptance Criteria:
    - POST /api/workflows/{id}/deploy without X-PAYMENT header returns 402
    """
    workflow_id = "wf_test123456"

    # Mock workflow storage to return a stored workflow
    with patch('app.api.v1.deploy.get_workflow_storage') as mock_storage:
        mock_storage_instance = MagicMock()
        mock_storage_instance.load_workflow = AsyncMock(return_value=sample_stored_workflow)
        mock_storage.return_value = mock_storage_instance

        # Mock payment service to generate payment request
        with patch('app.api.v1.deploy.get_payment_service') as mock_payment_service:
            mock_payment_service_instance = MagicMock()
            mock_payment_service_instance.generate_x402_payment_request = AsyncMock(
                return_value=sample_payment_request["accepts"][0]
            )
            mock_payment_service.return_value = mock_payment_service_instance

            # Mock demo mode to be disabled
            with patch('app.api.v1.deploy.settings') as mock_settings:
                mock_settings.spica_demo_mode = False

                # Make request without X-PAYMENT header
                response = client.post(f"/api/v1/workflows/{workflow_id}/deploy")

                # Assert 402 status
                assert response.status_code == status.HTTP_402_PAYMENT_REQUIRED

                # Assert response structure
                data = response.json()
                assert data["success"] is False
                assert "error" in data
                assert data["error"]["code"] == "PAYMENT_REQUIRED"


# ============================================================================
# Test X-PAYMENT-REQUEST Header Format
# ============================================================================

@pytest.mark.asyncio
async def test_402_response_includes_payment_request_header(client, sample_stored_workflow, sample_payment_request):
    """
    Test: 402 response includes X-PAYMENT-REQUEST header with correct format.

    Acceptance Criteria:
    - Response includes X-PAYMENT-REQUEST header
    - Header contains payment amount, recipient, memo
    """
    workflow_id = "wf_test123456"

    # Mock workflow storage
    with patch('app.api.v1.deploy.get_workflow_storage') as mock_storage:
        mock_storage_instance = MagicMock()
        mock_storage_instance.load_workflow = AsyncMock(return_value=sample_stored_workflow)
        mock_storage.return_value = mock_storage_instance

        # Mock payment service
        with patch('app.api.v1.deploy.get_payment_service') as mock_payment_service:
            mock_payment_service_instance = MagicMock()
            mock_payment_service_instance.generate_x402_payment_request = AsyncMock(
                return_value=sample_payment_request["accepts"][0]
            )
            mock_payment_service.return_value = mock_payment_service_instance

            # Mock demo mode disabled
            with patch('app.api.v1.deploy.settings') as mock_settings:
                mock_settings.spica_demo_mode = False

                # Make request without payment
                response = client.post(f"/api/v1/workflows/{workflow_id}/deploy")

                # Assert 402 status
                assert response.status_code == status.HTTP_402_PAYMENT_REQUIRED

                # Assert X-PAYMENT-REQUEST header exists
                assert "x-payment-request" in response.headers

                # Decode and parse payment request
                payment_header = response.headers["x-payment-request"]
                decoded = base64.b64decode(payment_header).decode()
                payment_data = json.loads(decoded)

                # Verify x402 format
                assert "x402Version" in payment_data
                assert payment_data["x402Version"] == 1
                assert "accepts" in payment_data
                assert len(payment_data["accepts"]) > 0

                # Verify payment details
                accept = payment_data["accepts"][0]
                assert "max_amount_required" in accept
                assert "pay_to" in accept
                assert "resource" in accept
                assert accept["resource"] == f"workflow://{workflow_id}"

                # Verify extra metadata
                if "extra" in accept:
                    assert "memo" in accept["extra"]
                    assert workflow_id in accept["extra"]["memo"]


# ============================================================================
# Test Valid Payment Returns 200
# ============================================================================

@pytest.mark.asyncio
async def test_deploy_with_valid_payment_returns_200(client, sample_stored_workflow):
    """
    Test: POST /workflows/{id}/deploy with valid X-PAYMENT header returns 200.

    Acceptance Criteria:
    - With valid X-PAYMENT header, returns 200
    """
    workflow_id = "wf_test123456"

    # Mock workflow storage
    with patch('app.api.v1.deploy.get_workflow_storage') as mock_storage:
        mock_storage_instance = MagicMock()
        mock_storage_instance.load_workflow = AsyncMock(return_value=sample_stored_workflow)

        # Create updated workflow
        updated_workflow = sample_stored_workflow.model_copy(deep=True)
        updated_workflow.status = "active"
        updated_workflow.enabled = True

        mock_storage_instance.update_workflow = AsyncMock(return_value=updated_workflow)
        mock_storage.return_value = mock_storage_instance

        # Mock payment verification in the deploy endpoint (not middleware)
        with patch('app.api.v1.deploy.get_payment_service') as mock_payment_service:
            mock_payment_service_instance = MagicMock()
            mock_payment_service_instance.verify_payment = AsyncMock(
                return_value=PaymentVerificationResult(
                    is_valid=True,
                    workflow_id=workflow_id,
                    payer="0x1234567890abcdef",
                    transaction="0xabcdef1234567890",
                    error_reason=None
                )
            )
            mock_payment_service_instance.calculate_price = MagicMock(return_value=Decimal("0.02"))
            mock_payment_service.return_value = mock_payment_service_instance

            # Mock demo mode disabled
            with patch('app.api.v1.deploy.settings') as mock_deploy_settings:
                mock_deploy_settings.spica_demo_mode = False

                with patch('app.middleware.payment_middleware.settings') as mock_middleware_settings:
                    mock_middleware_settings.spica_demo_mode = False

                    # Make request with valid payment header
                    valid_payment = base64.b64encode(b'{"proof": "valid_payment"}').decode()
                    response = client.post(
                        f"/api/v1/workflows/{workflow_id}/deploy",
                        headers={"X-PAYMENT": valid_payment}
                    )

                    # Assert 200 status
                    assert response.status_code == status.HTTP_200_OK

                    # Assert response structure
                    data = response.json()
                    assert data["success"] is True
                    assert data["workflow_id"] == workflow_id
                    assert data["status"] == "active"
                    assert "message" in data


# ============================================================================
# Test Invalid Payment Returns 402
# ============================================================================

@pytest.mark.asyncio
async def test_deploy_with_invalid_payment_returns_402(client, sample_stored_workflow, sample_payment_request):
    """
    Test: POST /workflows/{id}/deploy with invalid X-PAYMENT header returns 402.

    Acceptance Criteria:
    - Invalid payment header returns 402 again
    """
    workflow_id = "wf_test123456"

    # Mock workflow storage
    with patch('app.api.v1.deploy.get_workflow_storage') as mock_storage:
        mock_storage_instance = MagicMock()
        mock_storage_instance.load_workflow = AsyncMock(return_value=sample_stored_workflow)
        mock_storage.return_value = mock_storage_instance

        # Mock payment service for 402 response (verification happens in endpoint now)
        with patch('app.api.v1.deploy.get_payment_service') as mock_payment_service:
            mock_payment_service_instance = MagicMock()
            # Mock verification to return invalid
            mock_payment_service_instance.verify_payment = AsyncMock(
                return_value=PaymentVerificationResult(
                    is_valid=False,
                    error_reason="Invalid payment signature",
                    error_code=PaymentErrorCode.PAYMENT_SIGNATURE_INVALID
                )
            )
            mock_payment_service_instance.calculate_price = MagicMock(return_value=Decimal("0.02"))
            mock_payment_service_instance.generate_x402_payment_request = AsyncMock(
                return_value=sample_payment_request["accepts"][0]
            )
            mock_payment_service.return_value = mock_payment_service_instance

            # Mock demo mode disabled
            with patch('app.api.v1.deploy.settings') as mock_settings:
                mock_settings.spica_demo_mode = False

                # Mock middleware settings
                with patch('app.middleware.payment_middleware.settings') as mock_middleware_settings:
                    mock_middleware_settings.spica_demo_mode = False

                    # Make request with invalid payment header
                    invalid_payment = base64.b64encode(b'{"proof": "invalid_payment"}').decode()
                    response = client.post(
                        f"/api/v1/workflows/{workflow_id}/deploy",
                        headers={"X-PAYMENT": invalid_payment}
                    )

                    # Assert 402 status
                    assert response.status_code == status.HTTP_402_PAYMENT_REQUIRED

                    # Assert X-PAYMENT-REQUEST header exists
                    assert "x-payment-request" in response.headers


# ============================================================================
# Test Workflow Not Found
# ============================================================================

@pytest.mark.asyncio
async def test_deploy_workflow_not_found(client):
    """
    Test: POST /workflows/{id}/deploy with non-existent workflow returns 404.
    """
    workflow_id = "wf_nonexistent"

    # Mock workflow storage to raise FileNotFoundError
    with patch('app.api.v1.deploy.get_workflow_storage') as mock_storage:
        mock_storage_instance = MagicMock()
        mock_storage_instance.load_workflow = AsyncMock(
            side_effect=FileNotFoundError(f"Workflow {workflow_id} does not exist")
        )
        mock_storage.return_value = mock_storage_instance

        # Make request
        response = client.post(f"/api/v1/workflows/{workflow_id}/deploy")

        # Assert 404 status
        assert response.status_code == status.HTTP_404_NOT_FOUND

        # Assert error response
        data = response.json()
        # FastAPI wraps the detail in a 'detail' key
        detail = data.get("detail", data)
        assert detail["success"] is False
        assert detail["error"]["code"] == "WORKFLOW_NOT_FOUND"


# ============================================================================
# Test Invalid Workflow ID Format
# ============================================================================

@pytest.mark.asyncio
async def test_deploy_invalid_workflow_id_format(client):
    """
    Test: POST /workflows/{id}/deploy with invalid workflow_id format returns 404.
    """
    workflow_id = "../../../etc/passwd"  # Path traversal attempt

    # Mock workflow storage to raise ValueError
    with patch('app.api.v1.deploy.get_workflow_storage') as mock_storage:
        mock_storage_instance = MagicMock()
        mock_storage_instance.load_workflow = AsyncMock(
            side_effect=ValueError("Invalid workflow_id format")
        )
        mock_storage.return_value = mock_storage_instance

        # Make request
        response = client.post(f"/api/v1/workflows/{workflow_id}/deploy")

        # Assert 404 status (invalid ID treated as not found)
        assert response.status_code == status.HTTP_404_NOT_FOUND


# ============================================================================
# Test Demo Mode Bypass
# ============================================================================

@pytest.mark.asyncio
async def test_deploy_demo_mode_bypasses_payment(client, sample_stored_workflow):
    """
    Test: Demo mode bypasses payment verification and deploys successfully.
    """
    workflow_id = "wf_test123456"

    # Mock workflow storage
    with patch('app.api.v1.deploy.get_workflow_storage') as mock_storage:
        mock_storage_instance = MagicMock()
        mock_storage_instance.load_workflow = AsyncMock(return_value=sample_stored_workflow)

        # Create updated workflow
        updated_workflow = sample_stored_workflow.model_copy(deep=True)
        updated_workflow.status = "active"
        updated_workflow.enabled = True

        mock_storage_instance.update_workflow = AsyncMock(return_value=updated_workflow)
        mock_storage.return_value = mock_storage_instance

        # Mock demo mode enabled
        with patch('app.api.v1.deploy.settings') as mock_deploy_settings:
            mock_deploy_settings.spica_demo_mode = True

            with patch('app.middleware.payment_middleware.settings') as mock_middleware_settings:
                mock_middleware_settings.spica_demo_mode = True

                # Make request WITHOUT payment header
                response = client.post(f"/api/v1/workflows/{workflow_id}/deploy")

                # Assert 200 status (payment bypassed)
                assert response.status_code == status.HTTP_200_OK

                # Assert successful deployment
                data = response.json()
                assert data["success"] is True
                assert data["workflow_id"] == workflow_id
                assert data["status"] == "active"


# ============================================================================
# Test Payment Request Contains Required Fields
# ============================================================================

@pytest.mark.asyncio
async def test_payment_request_contains_required_fields(client, sample_stored_workflow):
    """
    Test: X-PAYMENT-REQUEST header contains all required x402 fields.
    """
    workflow_id = "wf_test123456"

    # Mock workflow storage
    with patch('app.api.v1.deploy.get_workflow_storage') as mock_storage:
        mock_storage_instance = MagicMock()
        mock_storage_instance.load_workflow = AsyncMock(return_value=sample_stored_workflow)
        mock_storage.return_value = mock_storage_instance

        # Mock payment service with detailed payment request
        with patch('app.api.v1.deploy.get_payment_service') as mock_payment_service:
            mock_payment_service_instance = MagicMock()
            mock_payment_service_instance.generate_x402_payment_request = AsyncMock(
                return_value={
                    "scheme": "exact",
                    "network": "base-sepolia",
                    "max_amount_required": "20000",
                    "resource": f"workflow://{workflow_id}",
                    "description": "Execute workflow: Auto DCA into NEO",
                    "pay_to": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
                    "asset": "0xa063B8d5ada3bE64A24Df594F96aB75F0fb78160",
                    "extra": {
                        "currency": "USDC",
                        "memo": f"Spica workflow execution: {workflow_id}",
                        "metadata": {
                            "workflow_id": workflow_id,
                            "complexity": "triggered"
                        }
                    }
                }
            )
            mock_payment_service.return_value = mock_payment_service_instance

            # Mock demo mode disabled
            with patch('app.api.v1.deploy.settings') as mock_settings:
                mock_settings.spica_demo_mode = False

                # Make request without payment
                response = client.post(f"/api/v1/workflows/{workflow_id}/deploy")

                # Decode payment request
                payment_header = response.headers["x-payment-request"]
                decoded = base64.b64decode(payment_header).decode()
                payment_data = json.loads(decoded)

                # Verify required x402 fields
                assert "x402Version" in payment_data
                assert "accepts" in payment_data

                accept = payment_data["accepts"][0]
                required_fields = [
                    "scheme", "network", "max_amount_required",
                    "resource", "description", "pay_to"
                ]

                for field in required_fields:
                    assert field in accept, f"Missing required field: {field}"

                # Verify memo in extra
                assert "extra" in accept
                assert "memo" in accept["extra"]
                assert workflow_id in accept["extra"]["memo"]
