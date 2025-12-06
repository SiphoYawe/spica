"""
Unit tests for payment service functionality.

Tests cover:
- Workflow complexity calculation
- Payment pricing calculation
- Payment request generation
- x402 integration (with mocking)
"""

import pytest
import time
from decimal import Decimal
from unittest.mock import Mock, patch, AsyncMock

from app.models.payment_models import (
    WorkflowComplexity,
    WorkflowPricing,
    PaymentRequestData,
    PaymentVerificationResult,
)
from app.models.workflow_models import (
    WorkflowSpec,
    WorkflowStep,
    PriceCondition,
    TimeCondition,
    SwapAction,
    StakeAction,
    TokenType,
)
from app.services.payment_service import PaymentService, get_payment_service


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def payment_service():
    """Create a fresh PaymentService instance for testing"""
    return PaymentService()


@pytest.fixture
def custom_pricing():
    """Custom pricing configuration for testing"""
    return WorkflowPricing(
        SIMPLE_PRICE=Decimal("0.05"),
        TRIGGERED_PRICE=Decimal("0.10"),
        COMPLEX_PRICE=Decimal("0.20"),
    )


@pytest.fixture
def simple_workflow():
    """Simple workflow: 1 step with trigger"""
    return WorkflowSpec(
        name="Simple Swap",
        description="Swap GAS to NEO when price is low",
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


@pytest.fixture
def triggered_workflow():
    """Triggered workflow: 2 steps with time trigger"""
    return WorkflowSpec(
        name="Daily Rebalance",
        description="Daily portfolio rebalance",
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
                )
            ),
            WorkflowStep(
                action=StakeAction(
                    type="stake",
                    token=TokenType.NEO,
                    percentage=50.0
                )
            )
        ]
    )


@pytest.fixture
def complex_workflow():
    """Complex workflow: 3+ steps"""
    return WorkflowSpec(
        name="Complex Strategy",
        description="Multi-step portfolio strategy",
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
                    percentage=30.0
                )
            ),
            WorkflowStep(
                action=StakeAction(
                    type="stake",
                    token=TokenType.NEO,
                    percentage=50.0
                )
            ),
            WorkflowStep(
                action=SwapAction(
                    type="swap",
                    from_token=TokenType.GAS,
                    to_token=TokenType.BNEO,
                    percentage=20.0
                )
            )
        ]
    )


# ============================================================================
# Test Pricing Configuration
# ============================================================================

class TestWorkflowPricing:
    """Test pricing configuration and calculation"""

    def test_default_pricing(self):
        """Test default pricing values"""
        pricing = WorkflowPricing()
        assert pricing.SIMPLE_PRICE == Decimal("0.01")
        assert pricing.TRIGGERED_PRICE == Decimal("0.02")
        assert pricing.COMPLEX_PRICE == Decimal("0.05")

    def test_custom_pricing(self, custom_pricing):
        """Test custom pricing values"""
        assert custom_pricing.SIMPLE_PRICE == Decimal("0.05")
        assert custom_pricing.TRIGGERED_PRICE == Decimal("0.10")
        assert custom_pricing.COMPLEX_PRICE == Decimal("0.20")

    def test_get_price_simple(self):
        """Test getting price for simple complexity"""
        pricing = WorkflowPricing()
        price = pricing.get_price(WorkflowComplexity.SIMPLE)
        assert price == Decimal("0.01")

    def test_get_price_triggered(self):
        """Test getting price for triggered complexity"""
        pricing = WorkflowPricing()
        price = pricing.get_price(WorkflowComplexity.TRIGGERED)
        assert price == Decimal("0.02")

    def test_get_price_complex(self):
        """Test getting price for complex complexity"""
        pricing = WorkflowPricing()
        price = pricing.get_price(WorkflowComplexity.COMPLEX)
        assert price == Decimal("0.05")


# ============================================================================
# Test Complexity Calculation
# ============================================================================

class TestComplexityCalculation:
    """Test workflow complexity calculation"""

    def test_simple_workflow_complexity(self, payment_service, simple_workflow):
        """Test complexity for simple workflow (1 step with trigger)"""
        complexity = payment_service.calculate_complexity(simple_workflow)
        # 1 step with trigger = TRIGGERED
        assert complexity == WorkflowComplexity.TRIGGERED

    def test_triggered_workflow_complexity(self, payment_service, triggered_workflow):
        """Test complexity for triggered workflow (2 steps with trigger)"""
        complexity = payment_service.calculate_complexity(triggered_workflow)
        # 2 steps with trigger = TRIGGERED
        assert complexity == WorkflowComplexity.TRIGGERED

    def test_complex_workflow_complexity(self, payment_service, complex_workflow):
        """Test complexity for complex workflow (3+ steps)"""
        complexity = payment_service.calculate_complexity(complex_workflow)
        # 3+ steps = COMPLEX
        assert complexity == WorkflowComplexity.COMPLEX

    def test_complexity_rules(self, payment_service):
        """Test complexity calculation rules comprehensively"""
        # Rule: 3+ steps = COMPLEX (regardless of trigger)
        complex_spec = WorkflowSpec(
            name="Test",
            description="Test",
            trigger=TimeCondition(type="time", schedule="daily"),
            steps=[
                WorkflowStep(action=SwapAction(
                    type="swap",
                    from_token=TokenType.GAS,
                    to_token=TokenType.NEO,
                    amount=10.0
                )) for _ in range(3)
            ]
        )
        assert payment_service.calculate_complexity(complex_spec) == WorkflowComplexity.COMPLEX


# ============================================================================
# Test Price Calculation
# ============================================================================

class TestPriceCalculation:
    """Test payment price calculation"""

    def test_calculate_price_simple(self, payment_service, simple_workflow):
        """Test price calculation for simple workflow"""
        price = payment_service.calculate_price(simple_workflow)
        # Simple workflow with trigger = TRIGGERED = 0.02 USDC
        assert price == Decimal("0.02")

    def test_calculate_price_triggered(self, payment_service, triggered_workflow):
        """Test price calculation for triggered workflow"""
        price = payment_service.calculate_price(triggered_workflow)
        # Triggered workflow = 0.02 USDC
        assert price == Decimal("0.02")

    def test_calculate_price_complex(self, payment_service, complex_workflow):
        """Test price calculation for complex workflow"""
        price = payment_service.calculate_price(complex_workflow)
        # Complex workflow = 0.05 USDC
        assert price == Decimal("0.05")

    def test_calculate_price_custom_pricing(self, custom_pricing, simple_workflow):
        """Test price calculation with custom pricing"""
        service = PaymentService(pricing=custom_pricing)
        price = service.calculate_price(simple_workflow)
        # Simple workflow with custom pricing
        assert price == Decimal("0.10")  # TRIGGERED price


# ============================================================================
# Test Workflow ID Generation
# ============================================================================

class TestWorkflowIDGeneration:
    """Test workflow ID generation"""

    def test_generate_workflow_id_format(self, payment_service):
        """Test workflow ID format"""
        workflow_id = payment_service.generate_workflow_id()
        assert workflow_id.startswith("wf_")
        assert len(workflow_id) == 15  # "wf_" + 12 hex chars

    def test_generate_workflow_id_uniqueness(self, payment_service):
        """Test that generated IDs are unique"""
        ids = [payment_service.generate_workflow_id() for _ in range(100)]
        assert len(ids) == len(set(ids))  # All unique


# ============================================================================
# Test Payment Request Creation
# ============================================================================

class TestPaymentRequestCreation:
    """Test payment request generation"""

    def test_create_payment_request_simple(self, payment_service, simple_workflow):
        """Test creating payment request for simple workflow"""
        request = payment_service.create_payment_request(simple_workflow)

        assert isinstance(request, PaymentRequestData)
        assert request.workflow_id.startswith("wf_")
        assert request.complexity == WorkflowComplexity.TRIGGERED
        assert request.amount_usdc == Decimal("0.02")
        assert request.currency == "USDC"
        assert request.workflow_id in request.memo
        assert "Spica workflow execution" in request.memo
        assert request.resource == f"workflow://{request.workflow_id}"
        assert request.description == f"Execute workflow: {simple_workflow.name}"
        assert request.network == "base-sepolia"
        assert request.receiver_address  # Should be set from config

    def test_create_payment_request_custom_id(self, payment_service, simple_workflow):
        """Test creating payment request with custom workflow ID"""
        custom_id = "wf_custom123"
        request = payment_service.create_payment_request(simple_workflow, workflow_id=custom_id)

        assert request.workflow_id == custom_id
        assert custom_id in request.memo
        assert request.resource == f"workflow://{custom_id}"

    def test_create_payment_request_complex(self, payment_service, complex_workflow):
        """Test creating payment request for complex workflow"""
        request = payment_service.create_payment_request(complex_workflow)

        assert request.complexity == WorkflowComplexity.COMPLEX
        assert request.amount_usdc == Decimal("0.05")


# ============================================================================
# Test x402 Payment Request Generation
# ============================================================================

class TestX402PaymentRequestGeneration:
    """Test x402 protocol payment request generation"""

    @pytest.mark.asyncio
    async def test_generate_x402_request_fallback(self, payment_service, simple_workflow):
        """Test x402 request generation with fallback (no SpoonOS)"""
        # Ensure fallback is used
        payment_service._x402_available = False
        payment_service._x402_service = None

        request = await payment_service.generate_x402_payment_request(simple_workflow)

        assert isinstance(request, dict)
        assert request["scheme"] == "exact"
        assert request["network"] == "base-sepolia"
        assert "max_amount_required" in request
        assert request["resource"].startswith("workflow://")
        assert "extra" in request
        assert "memo" in request["extra"]
        assert "metadata" in request["extra"]
        assert request["extra"]["metadata"]["service"] == "Spica Workflow Builder"

    @pytest.mark.asyncio
    async def test_generate_x402_request_atomic_units(self, payment_service, simple_workflow):
        """Test x402 request converts USDC to atomic units correctly"""
        payment_service._x402_available = False

        request = await payment_service.generate_x402_payment_request(simple_workflow)

        # 0.02 USDC = 20000 atomic units (6 decimals)
        assert request["max_amount_required"] == "20000"

    @pytest.mark.asyncio
    async def test_generate_x402_request_custom_id(self, payment_service, simple_workflow):
        """Test x402 request with custom workflow ID"""
        payment_service._x402_available = False

        custom_id = "wf_test456"
        request = await payment_service.generate_x402_payment_request(
            simple_workflow,
            workflow_id=custom_id
        )

        assert request["extra"]["metadata"]["workflow_id"] == custom_id
        assert custom_id in request["extra"]["memo"]

    @pytest.mark.asyncio
    async def test_generate_x402_request_with_spoonos(self, payment_service, simple_workflow):
        """Test x402 request generation with SpoonOS service (mocked)"""
        # Skip if spoon_ai is not available
        try:
            import spoon_ai.payments
        except ImportError:
            pytest.skip("spoon_ai not available in test environment")

        # Mock SpoonOS x402 service
        mock_service = Mock()
        mock_requirements = Mock()
        mock_requirements.model_dump = Mock(return_value={
            "scheme": "exact",
            "network": "base-sepolia",
            "max_amount_required": "20000",
            "resource": "workflow://wf_test",
            "description": "Test workflow",
            "pay_to": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
        })
        mock_service.build_payment_requirements = Mock(return_value=mock_requirements)

        payment_service._x402_available = True
        payment_service._x402_service = mock_service

        # Mock the X402PaymentRequest import inside the method
        with patch('spoon_ai.payments.X402PaymentRequest') as mock_request_class:
            request = await payment_service.generate_x402_payment_request(simple_workflow)

            assert isinstance(request, dict)
            assert request["scheme"] == "exact"
            mock_service.build_payment_requirements.assert_called_once()


# ============================================================================
# Test Payment Verification
# ============================================================================

class TestPaymentVerification:
    """Test payment verification functionality"""

    @pytest.mark.asyncio
    async def test_verify_payment_no_service(self, payment_service):
        """Test payment verification without x402 service (should reject without crypto verification)"""
        payment_service._x402_available = False

        # Create a valid payment header structure (base64 encoded JSON)
        import base64
        import json
        payment_data = {
            "x402Version": 1,
            "scheme": "exact",
            "network": "base-sepolia",
            "payload": {
                "signature": "0xmocksignature",
                "authorization": {
                    "from": "0x1234567890abcdef",
                    "to": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
                    "value": "10000",
                    "validBefore": str(int(time.time()) + 3600),
                    "validAfter": str(int(time.time()) - 60),
                    "nonce": "0x123"
                }
            }
        }
        payment_header = base64.b64encode(json.dumps(payment_data).encode()).decode()

        result = await payment_service.verify_payment(payment_header)

        assert isinstance(result, PaymentVerificationResult)
        assert result.is_valid is False
        # With the security fix, payments are rejected when x402 service is unavailable
        assert "service unavailable" in result.error_reason.lower() or "verification required" in result.error_reason.lower()

    @pytest.mark.asyncio
    async def test_verify_payment_with_service_success(self, payment_service):
        """Test successful payment verification with x402 service"""
        import base64
        import json

        # Create a valid payment header structure
        payment_data = {
            "x402Version": 1,
            "scheme": "exact",
            "network": "base-sepolia",
            "payload": {
                "signature": "0xmocksignature",
                "authorization": {
                    "from": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
                    "to": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
                    "value": "10000",
                    "validBefore": str(int(time.time()) + 3600),
                    "validAfter": str(int(time.time()) - 60),
                    "nonce": "0x123"
                }
            }
        }
        payment_header = base64.b64encode(json.dumps(payment_data).encode()).decode()

        # Mock x402 service
        mock_service = AsyncMock()
        mock_verify_result = Mock()
        mock_verify_result.is_valid = True
        mock_verify_result.payer = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
        mock_verify_result.invalid_reason = None
        mock_service.verify_payment = AsyncMock(return_value=mock_verify_result)

        payment_service._x402_available = True
        payment_service._x402_service = mock_service

        result = await payment_service.verify_payment(payment_header)

        assert result.is_valid is True
        assert result.payer == "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
        assert result.error_reason is None

    @pytest.mark.asyncio
    async def test_verify_payment_with_service_failure(self, payment_service):
        """Test failed payment verification with x402 service"""
        import base64
        import json

        # Create a valid payment header structure
        payment_data = {
            "x402Version": 1,
            "scheme": "exact",
            "network": "base-sepolia",
            "payload": {
                "signature": "0xmocksignature",
                "authorization": {
                    "from": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
                    "to": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
                    "value": "10000",
                    "validBefore": str(int(time.time()) + 3600),
                    "validAfter": str(int(time.time()) - 60),
                    "nonce": "0x123"
                }
            }
        }
        payment_header = base64.b64encode(json.dumps(payment_data).encode()).decode()

        # Mock x402 service
        mock_service = AsyncMock()
        mock_verify_result = Mock()
        mock_verify_result.is_valid = False
        mock_verify_result.payer = None
        mock_verify_result.invalid_reason = "Insufficient funds"
        mock_service.verify_payment = AsyncMock(return_value=mock_verify_result)

        payment_service._x402_available = True
        payment_service._x402_service = mock_service

        result = await payment_service.verify_payment(payment_header)

        assert result.is_valid is False
        assert result.error_reason == "Insufficient funds"

    @pytest.mark.asyncio
    async def test_verify_payment_exception_handling(self, payment_service):
        """Test payment verification exception handling"""
        import base64
        import json

        # Create a valid payment header structure
        payment_data = {
            "x402Version": 1,
            "scheme": "exact",
            "network": "base-sepolia",
            "payload": {
                "signature": "0xmocksignature",
                "authorization": {
                    "from": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
                    "to": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
                    "value": "10000",
                    "validBefore": str(int(time.time()) + 3600),
                    "validAfter": str(int(time.time()) - 60),
                    "nonce": "0x123"
                }
            }
        }
        payment_header = base64.b64encode(json.dumps(payment_data).encode()).decode()

        # Mock x402 service that throws exception
        mock_service = AsyncMock()
        mock_service.verify_payment = AsyncMock(side_effect=Exception("Network error"))

        payment_service._x402_available = True
        payment_service._x402_service = mock_service

        result = await payment_service.verify_payment(payment_header)

        assert result.is_valid is False
        assert "Network error" in result.error_reason


# ============================================================================
# Test Service Singleton
# ============================================================================

class TestServiceSingleton:
    """Test payment service singleton pattern"""

    def test_get_payment_service_singleton(self):
        """Test that get_payment_service returns singleton"""
        service1 = get_payment_service()
        service2 = get_payment_service()

        assert service1 is service2

    def test_get_payment_service_returns_payment_service(self):
        """Test that singleton returns PaymentService instance"""
        service = get_payment_service()
        assert isinstance(service, PaymentService)


# ============================================================================
# Test Payment Models
# ============================================================================

class TestPaymentModels:
    """Test payment model validation and serialization"""

    def test_payment_request_data_validation(self):
        """Test PaymentRequestData validation"""
        data = PaymentRequestData(
            workflow_id="wf_test123",
            complexity=WorkflowComplexity.SIMPLE,
            amount_usdc=Decimal("0.01"),
            memo="Test memo: wf_test123",
            resource="workflow://wf_test123",
            description="Test workflow",
            receiver_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
        )

        assert data.workflow_id == "wf_test123"
        assert data.complexity == WorkflowComplexity.SIMPLE
        assert data.amount_usdc == Decimal("0.01")
        assert data.currency == "USDC"  # Default value

    def test_payment_verification_result_validation(self):
        """Test PaymentVerificationResult validation"""
        result = PaymentVerificationResult(
            is_valid=True,
            workflow_id="wf_test123",
            payer="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
            transaction="0xabc123"
        )

        assert result.is_valid is True
        assert result.workflow_id == "wf_test123"
        assert result.error_reason is None


# ============================================================================
# Test Integration Scenarios
# ============================================================================

class TestIntegrationScenarios:
    """Test end-to-end integration scenarios"""

    @pytest.mark.asyncio
    async def test_full_payment_flow(self, payment_service, simple_workflow):
        """Test complete payment flow from workflow to x402 request"""
        # Step 1: Calculate complexity
        complexity = payment_service.calculate_complexity(simple_workflow)
        assert complexity in [WorkflowComplexity.SIMPLE, WorkflowComplexity.TRIGGERED, WorkflowComplexity.COMPLEX]

        # Step 2: Calculate price
        price = payment_service.calculate_price(simple_workflow)
        assert price > 0

        # Step 3: Create payment request
        payment_request = payment_service.create_payment_request(simple_workflow)
        assert payment_request.amount_usdc == price
        assert payment_request.complexity == complexity

        # Step 4: Generate x402 request
        payment_service._x402_available = False  # Use fallback
        x402_request = await payment_service.generate_x402_payment_request(simple_workflow)
        assert "max_amount_required" in x402_request
        assert x402_request["extra"]["metadata"]["workflow_id"]

    def test_different_workflow_types_pricing(self, payment_service):
        """Test that different workflow types get correct pricing"""
        workflows = {
            "simple_triggered": WorkflowSpec(
                name="Test",
                description="Test",
                trigger=TimeCondition(type="time", schedule="daily"),
                steps=[WorkflowStep(action=SwapAction(
                    type="swap",
                    from_token=TokenType.GAS,
                    to_token=TokenType.NEO,
                    amount=10.0
                ))]
            ),
            "complex": WorkflowSpec(
                name="Test",
                description="Test",
                trigger=TimeCondition(type="time", schedule="daily"),
                steps=[WorkflowStep(action=SwapAction(
                    type="swap",
                    from_token=TokenType.GAS,
                    to_token=TokenType.NEO,
                    amount=10.0
                )) for _ in range(3)]
            ),
        }

        # Triggered workflow (1 step)
        price1 = payment_service.calculate_price(workflows["simple_triggered"])
        assert price1 == Decimal("0.02")

        # Complex workflow (3 steps)
        price2 = payment_service.calculate_price(workflows["complex"])
        assert price2 == Decimal("0.05")

        # Verify pricing hierarchy
        assert price2 > price1
