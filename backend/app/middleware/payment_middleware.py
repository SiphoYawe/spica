"""
Payment middleware for x402 protocol integration.

This middleware handles:
- 402 Payment Required responses
- X-PAYMENT-REQUEST header generation
- X-PAYMENT header verification
- Payment dependency injection
"""

import base64
import json
import logging
from typing import Optional

from fastapi import Header, HTTPException, status
from fastapi.responses import JSONResponse

from app.services.payment_service import get_payment_service
from app.models.payment_models import PaymentVerificationResult
from app.config import settings

logger = logging.getLogger(__name__)


# ============================================================================
# Payment Exception
# ============================================================================

class PaymentRequired(HTTPException):
    """
    Exception for 402 Payment Required responses.

    This exception is raised when a request requires payment but none was provided,
    or the provided payment is invalid.

    The exception handler will automatically add the X-PAYMENT-REQUEST header
    with the payment requirements in x402 format.
    """

    def __init__(
        self,
        payment_request: dict,
        detail: str = "Payment required",
        headers: Optional[dict] = None
    ):
        """
        Initialize PaymentRequired exception.

        Args:
            payment_request: x402 payment request structure
            detail: Error detail message
            headers: Optional additional headers
        """
        self.payment_request = payment_request

        # Encode payment request as base64 JSON (x402 spec)
        payment_json = json.dumps(payment_request)
        payment_b64 = base64.b64encode(payment_json.encode()).decode()

        # Build response headers
        response_headers = {
            "X-PAYMENT-REQUEST": payment_b64,
        }
        if headers:
            response_headers.update(headers)

        super().__init__(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=detail,
            headers=response_headers
        )


# ============================================================================
# Payment Dependency
# ============================================================================

async def require_payment(
    x_payment: Optional[str] = Header(None, alias="X-PAYMENT"),
) -> Optional[str]:
    """
    FastAPI dependency for x402 payment header extraction.

    This dependency extracts the X-PAYMENT header and returns it for the endpoint
    to verify. The endpoint performs full verification with amount and workflow_id
    to avoid TOCTOU vulnerabilities.

    Args:
        x_payment: X-PAYMENT header value (base64 encoded payment proof)

    Returns:
        Optional[str]: The X-PAYMENT header value, or None if missing

    Usage:
        ```python
        @router.post("/deploy")
        async def deploy(
            payment_header: Optional[str] = Depends(require_payment)
        ):
            # Endpoint verifies payment with amount and workflow_id
            pass
        ```
    """
    # Check if demo mode is enabled (bypass payments)
    if settings.spica_demo_mode:
        logger.info("Demo mode enabled - bypassing payment verification")
        return "demo-mode"

    # Return the header value (or None) for endpoint to verify
    if not x_payment:
        logger.debug("No X-PAYMENT header provided")
    else:
        logger.debug("X-PAYMENT header extracted")

    return x_payment


# ============================================================================
# Utility Functions
# ============================================================================

def create_402_response(payment_request: dict, detail: str = "Payment required") -> JSONResponse:
    """
    Create a 402 Payment Required response with X-PAYMENT-REQUEST header.

    Args:
        payment_request: x402 payment request structure
        detail: Error detail message

    Returns:
        JSONResponse with 402 status and X-PAYMENT-REQUEST header

    Usage:
        ```python
        payment_request = await payment_service.generate_x402_payment_request(workflow)
        return create_402_response(payment_request)
        ```
    """
    # Encode payment request as base64 JSON (x402 spec)
    payment_json = json.dumps(payment_request)
    payment_b64 = base64.b64encode(payment_json.encode()).decode()

    response = JSONResponse(
        status_code=status.HTTP_402_PAYMENT_REQUIRED,
        content={
            "success": False,
            "error": {
                "code": "PAYMENT_REQUIRED",
                "message": detail,
                "details": "Include X-PAYMENT header with payment proof to proceed",
                "retry": True
            }
        },
        headers={
            "X-PAYMENT-REQUEST": payment_b64,
        }
    )

    return response
