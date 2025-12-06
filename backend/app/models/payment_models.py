"""
Payment models for x402 workflow monetization.

Defines pricing models and payment request structures for workflow execution.
"""

from decimal import Decimal
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class PaymentErrorCode(str, Enum):
    """
    Standardized error codes for payment verification failures.

    All error codes follow the pattern: PAYMENT_<SPECIFIC_ERROR>
    """
    PAYMENT_MISSING = "PAYMENT_MISSING"
    PAYMENT_EXPIRED = "PAYMENT_EXPIRED"
    PAYMENT_DECODE_FAILED = "PAYMENT_DECODE_FAILED"
    PAYMENT_INVALID_VERSION = "PAYMENT_INVALID_VERSION"
    PAYMENT_MISSING_PAYLOAD = "PAYMENT_MISSING_PAYLOAD"
    PAYMENT_MISSING_AUTHORIZATION = "PAYMENT_MISSING_AUTHORIZATION"
    PAYMENT_MISSING_SIGNATURE = "PAYMENT_MISSING_SIGNATURE"
    PAYMENT_MISSING_EXPIRY = "PAYMENT_MISSING_EXPIRY"
    PAYMENT_MISSING_AMOUNT = "PAYMENT_MISSING_AMOUNT"
    PAYMENT_SIGNATURE_INVALID = "PAYMENT_SIGNATURE_INVALID"
    PAYMENT_AMOUNT_MISMATCH = "PAYMENT_AMOUNT_MISMATCH"
    PAYMENT_INVALID_TIMESTAMP = "PAYMENT_INVALID_TIMESTAMP"
    PAYMENT_INVALID_AMOUNT = "PAYMENT_INVALID_AMOUNT"
    PAYMENT_SERVICE_UNAVAILABLE = "PAYMENT_SERVICE_UNAVAILABLE"
    PAYMENT_VERIFICATION_ERROR = "PAYMENT_VERIFICATION_ERROR"


class WorkflowComplexity(str, Enum):
    """
    Workflow complexity levels for pricing calculation.

    - SIMPLE: Single-step workflows without triggers
    - TRIGGERED: Workflows with time or price triggers
    - COMPLEX: Multi-step workflows (3+ steps)
    """
    SIMPLE = "simple"
    TRIGGERED = "triggered"
    COMPLEX = "complex"


class WorkflowPricing(BaseModel):
    """Pricing configuration for workflow execution"""

    # Pricing in USDC
    SIMPLE_PRICE: Decimal = Field(
        default=Decimal("0.01"),
        description="Price for simple workflows (1-2 steps, no trigger)"
    )
    TRIGGERED_PRICE: Decimal = Field(
        default=Decimal("0.02"),
        description="Price for triggered workflows (any steps with trigger)"
    )
    COMPLEX_PRICE: Decimal = Field(
        default=Decimal("0.05"),
        description="Price for complex workflows (3+ steps)"
    )

    def get_price(self, complexity: WorkflowComplexity) -> Decimal:
        """Get price for a given complexity level"""
        price_map = {
            WorkflowComplexity.SIMPLE: self.SIMPLE_PRICE,
            WorkflowComplexity.TRIGGERED: self.TRIGGERED_PRICE,
            WorkflowComplexity.COMPLEX: self.COMPLEX_PRICE,
        }
        return price_map[complexity]


class PaymentRequestData(BaseModel):
    """
    Payment request data for workflow execution.

    This model represents the payment information sent to clients
    for x402 payment processing.
    """
    workflow_id: str = Field(..., description="Unique workflow identifier")
    complexity: WorkflowComplexity = Field(..., description="Workflow complexity level")
    amount_usdc: Decimal = Field(..., description="Payment amount in USDC")
    currency: str = Field(default="USDC", description="Payment currency")
    memo: str = Field(..., description="Payment memo including workflow_id")
    resource: str = Field(..., description="Resource being paid for")
    description: str = Field(..., description="Human-readable payment description")

    # x402 protocol fields
    network: str = Field(default="base-sepolia", description="Payment network")
    receiver_address: str = Field(..., description="Payment receiver address")

    class Config:
        json_schema_extra = {
            "example": {
                "workflow_id": "wf_abc123",
                "complexity": "simple",
                "amount_usdc": "0.01",
                "currency": "USDC",
                "memo": "Spica workflow execution: wf_abc123",
                "resource": "workflow://wf_abc123",
                "description": "Execute workflow: Auto DCA into NEO",
                "network": "base-sepolia",
                "receiver_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
            }
        }


class PaymentPayload(BaseModel):
    """
    Decoded x402 payment payload from X-PAYMENT header.

    The X-PAYMENT header contains base64-encoded JSON with this structure.
    """
    x402Version: int = Field(..., description="x402 protocol version (should be 1)")
    scheme: str = Field(..., description="Payment scheme (e.g., 'exact')")
    network: str = Field(..., description="Blockchain network (e.g., 'base-sepolia')")
    payload: Dict[str, Any] = Field(..., description="Payment signature and authorization")

    class Config:
        json_schema_extra = {
            "example": {
                "x402Version": 1,
                "scheme": "exact",
                "network": "base-sepolia",
                "payload": {
                    "signature": "0xabcd1234...",
                    "authorization": {
                        "from": "0xpayer...",
                        "to": "0xreceiver...",
                        "value": "20000",
                        "validAfter": "1701936000",
                        "validBefore": "1701936120",
                        "nonce": "0x..."
                    }
                }
            }
        }


class PaymentVerificationResult(BaseModel):
    """Result of payment verification"""
    is_valid: bool = Field(..., description="Whether payment is valid")
    workflow_id: Optional[str] = Field(None, description="Workflow ID from payment memo")
    payer: Optional[str] = Field(None, description="Payer address")
    transaction: Optional[str] = Field(None, description="Transaction hash")
    error_reason: Optional[str] = Field(None, description="Error reason if invalid")
    error_code: Optional[PaymentErrorCode] = Field(None, description="Standardized error code for categorization")
