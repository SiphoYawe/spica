# Payment Service Documentation

## Overview

The Payment Service implements x402 protocol integration for workflow monetization in the Spica platform. It calculates pricing based on workflow complexity and generates x402-compatible payment requests.

## Story 4.1: Payment Service ✅

**Status**: Implementation Complete

**Implementation Files**:
- `/spica/backend/app/models/payment_models.py` - Payment data models
- `/spica/backend/app/services/payment_service.py` - Payment service logic
- `/spica/backend/app/config.py` - Configuration with `spica_demo_mode`
- `/spica/backend/tests/test_payment_service.py` - Comprehensive unit tests (31 passed)

---

## Pricing Model

### Workflow Complexity Tiers

| Complexity | Price (USDC) | Criteria |
|------------|--------------|----------|
| **SIMPLE** | $0.01 | 1-2 steps, no trigger (theoretical, all workflows require triggers) |
| **TRIGGERED** | $0.02 | Any workflow with time/price trigger, < 3 steps |
| **COMPLEX** | $0.05 | 3+ steps (regardless of trigger type) |

### Complexity Calculation Logic

```python
def calculate_complexity(workflow: WorkflowSpec) -> WorkflowComplexity:
    num_steps = len(workflow.steps)

    # 3+ steps = COMPLEX
    if num_steps >= 3:
        return WorkflowComplexity.COMPLEX

    # Has trigger = TRIGGERED (all workflows have triggers per model)
    if workflow.trigger:
        return WorkflowComplexity.TRIGGERED

    # 1-2 steps without trigger = SIMPLE
    return WorkflowComplexity.SIMPLE
```

---

## Usage Examples

### Basic Payment Request Creation

```python
from app.services import get_payment_service
from app.models import WorkflowSpec

# Get service instance
payment_service = get_payment_service()

# Create payment request for a workflow
workflow = WorkflowSpec(...)  # Your workflow
payment_request = payment_service.create_payment_request(workflow)

print(f"Workflow ID: {payment_request.workflow_id}")
print(f"Complexity: {payment_request.complexity}")
print(f"Price: ${payment_request.amount_usdc} USDC")
print(f"Memo: {payment_request.memo}")
```

### Generate x402 Payment Request

```python
# Generate x402 protocol-compatible payment request
x402_request = await payment_service.generate_x402_payment_request(workflow)

# Returns dict with x402 PaymentRequirements structure:
# {
#     "scheme": "exact",
#     "network": "base-sepolia",
#     "max_amount_required": "20000",  # atomic units
#     "resource": "workflow://wf_abc123",
#     "description": "Execute workflow: Auto DCA into NEO",
#     "pay_to": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
#     "extra": {
#         "currency": "USDC",
#         "memo": "Spica workflow execution: wf_abc123",
#         "metadata": {
#             "workflow_id": "wf_abc123",
#             "complexity": "triggered",
#             "service": "Spica Workflow Builder"
#         }
#     }
# }
```

### Custom Workflow ID

```python
# Use custom workflow ID
custom_id = "wf_custom_123"
payment_request = payment_service.create_payment_request(
    workflow,
    workflow_id=custom_id
)
```

### Payment Verification (Future)

```python
# Verify payment header from client
result = await payment_service.verify_payment(payment_header)

if result.is_valid:
    print(f"Payment verified from: {result.payer}")
    print(f"Workflow ID: {result.workflow_id}")
else:
    print(f"Payment invalid: {result.error_reason}")
```

---

## Configuration

### Environment Variables

Add to your `.env` file:

```bash
# x402 Payment Configuration
X402_RECEIVER_ADDRESS=0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb  # Your Ethereum address
X402_NETWORK=base-sepolia  # Payment network
X402_DEFAULT_ASSET=USDC  # Payment token
X402_FACILITATOR_URL=https://x402.org/facilitator  # Optional: x402 facilitator service

# Demo Mode (Story 4.5)
SPICA_DEMO_MODE=false  # Set to true to bypass payments in demo
```

### Configuration in Code

The payment service automatically reads from `app.config.settings`:

```python
from app.config import settings

# Access configuration
print(settings.x402_receiver_address)  # Receiver address
print(settings.x402_network)  # base-sepolia
print(settings.x402_default_asset)  # USDC
print(settings.spica_demo_mode)  # Demo mode flag
```

---

## Models

### WorkflowComplexity

```python
from app.models import WorkflowComplexity

complexity = WorkflowComplexity.SIMPLE     # $0.01
complexity = WorkflowComplexity.TRIGGERED  # $0.02
complexity = WorkflowComplexity.COMPLEX    # $0.05
```

### PaymentRequestData

```python
from app.models import PaymentRequestData

payment_data = PaymentRequestData(
    workflow_id="wf_abc123",
    complexity=WorkflowComplexity.TRIGGERED,
    amount_usdc=Decimal("0.02"),
    currency="USDC",
    memo="Spica workflow execution: wf_abc123",
    resource="workflow://wf_abc123",
    description="Execute workflow: Auto DCA into NEO",
    network="base-sepolia",
    receiver_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
)
```

### PaymentVerificationResult

```python
from app.models import PaymentVerificationResult

result = PaymentVerificationResult(
    is_valid=True,
    workflow_id="wf_abc123",
    payer="0x123...",
    transaction="0xabc...",
    error_reason=None
)
```

---

## x402 Integration

### SpoonOS Integration

The payment service integrates with SpoonOS `X402PaymentService` when available:

```python
# Automatically initialized if spoon_ai is available
from spoon_ai.payments import X402PaymentService, X402Settings

# Service detects and uses SpoonOS if installed
payment_service._x402_available  # True if SpoonOS available
payment_service._x402_service    # SpoonOS X402PaymentService instance
```

### Fallback Implementation

When SpoonOS is not available, the service provides a fallback implementation:

```python
# Generates compatible x402 payment request structure
# Converts USDC to atomic units (6 decimals)
# Includes all required x402 fields
```

---

## Testing

### Run All Tests

```bash
cd /spica/backend
python -m pytest tests/test_payment_service.py -v
```

### Test Coverage

The test suite includes:
- ✅ Pricing configuration and defaults
- ✅ Complexity calculation for all workflow types
- ✅ Price calculation with custom pricing
- ✅ Workflow ID generation and uniqueness
- ✅ Payment request creation
- ✅ x402 payment request generation (fallback)
- ✅ x402 payment request generation (with SpoonOS - skipped if unavailable)
- ✅ Payment verification (mocked)
- ✅ Service singleton pattern
- ✅ Model validation
- ✅ Integration scenarios

**Results**: 31 passed, 1 skipped (SpoonOS integration test)

---

## Acceptance Criteria ✅

| Criterion | Status | Implementation |
|-----------|--------|----------------|
| Calculate price based on workflow complexity | ✅ | `calculate_complexity()`, `calculate_price()` |
| Simple: 0.01 USDC | ✅ | `WorkflowPricing.SIMPLE_PRICE = 0.01` |
| Triggered: 0.02 USDC | ✅ | `WorkflowPricing.TRIGGERED_PRICE = 0.02` |
| Complex: 0.05 USDC | ✅ | `WorkflowPricing.COMPLEX_PRICE = 0.05` |
| Generate x402 payment request JSON | ✅ | `generate_x402_payment_request()` |
| Include workflow_id in memo | ✅ | `memo = "Spica workflow execution: {workflow_id}"` |
| Service reads from environment variables | ✅ | Uses `settings.x402_*` from config |

---

## Future Enhancements

1. **Payment Verification** - Full implementation with x402 facilitator
2. **Payment Settlement** - Automatic settlement via x402 protocol
3. **Payment History** - Track and store payment records
4. **Dynamic Pricing** - Adjust pricing based on market conditions
5. **Multi-Currency Support** - Support for tokens beyond USDC
6. **Webhook Integration** - Payment status webhooks
7. **Refund Handling** - Refund failed workflow executions

---

## Architecture Notes

### Design Principles

1. **Graceful Degradation** - Works with or without SpoonOS
2. **Environment-Based Config** - All settings from environment variables
3. **Testability** - Comprehensive unit test coverage
4. **Extensibility** - Easy to add new complexity tiers or pricing models
5. **Type Safety** - Full Pydantic model validation

### Integration Points

- **Workflow Models** - Uses `WorkflowSpec` for complexity analysis
- **Config System** - Reads from `app.config.settings`
- **SpoonOS** - Optional integration with `X402PaymentService`
- **x402 Protocol** - Compatible with x402 payment standard

---

## Support

For issues or questions:
1. Check test suite for usage examples
2. Review SpoonOS x402 documentation in `/spoon-core/spoon_ai/payments/`
3. Verify environment configuration in `.env`
4. Enable demo mode for testing without payments

---

**Implementation Date**: December 6, 2024
**Story**: 4.1 - Payment Service
**Status**: ✅ Complete - All acceptance criteria met
