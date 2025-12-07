"""
Workflow deployment endpoint with x402 payment integration.

This endpoint handles workflow deployment with payment verification:
- Returns 402 when no payment is provided
- Verifies payment and activates workflow on valid payment
- Returns 402 again on invalid payment
"""

import logging
import uuid
from datetime import datetime, UTC
from typing import Optional

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field

from app.middleware import require_payment, create_402_response
from app.models.payment_models import PaymentVerificationResult, PaymentErrorCode
from app.services.payment_service import get_payment_service
from app.services.workflow_storage import get_workflow_storage
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================

class DeploySuccessResponse(BaseModel):
    """Successful deployment response"""
    success: bool = Field(True, description="Always true for successful deployment")
    workflow_id: str = Field(..., description="Workflow identifier")
    status: str = Field(..., description="Workflow status after deployment")
    message: str = Field(..., description="Deployment success message")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "workflow_id": "wf_a1b2c3d4e5f6",
                "status": "active",
                "message": "Workflow deployed and activated successfully",
                "timestamp": "2025-12-06T00:00:00.000000"
            }
        }
    }


class DeployErrorResponse(BaseModel):
    """Error deployment response"""
    success: bool = Field(False, description="Always false for errors")
    error: dict = Field(..., description="Error details")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


# ============================================================================
# Deploy Endpoint
# ============================================================================

@router.post(
    "/workflows/{workflow_id}/deploy",
    response_model=DeploySuccessResponse,
    summary="Deploy workflow (requires payment)",
    description="Deploy a workflow to production. Requires x402 payment via X-PAYMENT header.",
    responses={
        200: {
            "description": "Workflow deployed successfully",
            "model": DeploySuccessResponse
        },
        402: {
            "description": "Payment required or invalid",
            "model": DeployErrorResponse,
            "headers": {
                "X-PAYMENT-REQUEST": {
                    "description": "Base64-encoded x402 payment request",
                    "schema": {"type": "string"}
                }
            }
        },
        404: {
            "description": "Workflow not found",
            "model": DeployErrorResponse
        },
        500: {
            "description": "Internal server error",
            "model": DeployErrorResponse
        }
    },
    tags=["deployment"]
)
async def deploy_workflow(
    workflow_id: str,
    payment_header: Optional[str] = Depends(require_payment)
) -> DeploySuccessResponse:
    """
    Deploy a workflow to production with x402 payment verification.

    This endpoint implements the x402 payment protocol:
    1. **No X-PAYMENT header**: Returns 402 with X-PAYMENT-REQUEST header
    2. **Invalid X-PAYMENT**: Returns 402 with X-PAYMENT-REQUEST header
    3. **Valid X-PAYMENT**: Activates workflow and returns 200

    **x402 Payment Flow:**
    ```
    Client: POST /workflows/wf_xxx/deploy
    Server: 402 Payment Required
            X-PAYMENT-REQUEST: base64(payment_requirements)

    Client: POST /workflows/wf_xxx/deploy
            X-PAYMENT: base64(payment_proof)
    Server: 200 OK (workflow activated)
    ```

    **Demo Mode:**
    If `SPICA_DEMO_MODE=true`, payments are bypassed and deployment succeeds immediately.

    Args:
        workflow_id: Workflow identifier to deploy
        payment_header: X-PAYMENT header value from require_payment dependency

    Returns:
        DeploySuccessResponse: Workflow activated successfully

    Raises:
        HTTPException 402: Payment required or invalid
        HTTPException 404: Workflow not found
        HTTPException 500: Internal server error
    """
    logger.info(f"Deploy request for workflow: {workflow_id}")

    try:
        # ====================================================================
        # Step 1: Load workflow from storage
        # ====================================================================

        storage = get_workflow_storage()

        try:
            stored_workflow = await storage.load_workflow(workflow_id)
        except FileNotFoundError:
            logger.warning(f"Workflow not found: {workflow_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "success": False,
                    "error": {
                        "code": "WORKFLOW_NOT_FOUND",
                        "message": "Workflow not found",
                        "details": f"No workflow exists with ID: {workflow_id}",
                        "retry": False
                    },
                    "timestamp": datetime.now(UTC).isoformat()
                }
            )
        except ValueError as e:
            # Invalid workflow_id format
            logger.warning(f"Invalid workflow_id format: {workflow_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "success": False,
                    "error": {
                        "code": "INVALID_WORKFLOW_ID",
                        "message": "Invalid workflow identifier",
                        "details": str(e),
                        "retry": False
                    },
                    "timestamp": datetime.now(UTC).isoformat()
                }
            )

        # ====================================================================
        # Step 2: Verify payment (or check demo mode)
        # ====================================================================

        # Get payment service and workflow spec for pricing
        payment_service = get_payment_service()
        workflow_spec = stored_workflow.assembled_graph.workflow_spec

        # Handle legacy workflows that don't have workflow_spec
        if workflow_spec is None:
            # Create a minimal workflow spec from state_graph_config for pricing
            from app.models.workflow_models import WorkflowSpec, TriggerSpec
            state_config = stored_workflow.assembled_graph.state_graph_config
            trigger_data = state_config.get("trigger", {})
            steps_data = state_config.get("steps", [])

            workflow_spec = WorkflowSpec(
                intent=stored_workflow.assembled_graph.workflow_description,
                name=stored_workflow.assembled_graph.workflow_name,
                trigger=TriggerSpec(
                    type=trigger_data.get("type", "time"),
                    **trigger_data.get("params", {})
                ),
                steps=[{"type": s.get("action_type", "unknown"), **s.get("params", {})} for s in steps_data]
            )

        # Calculate required amount for this workflow
        required_amount = payment_service.calculate_price(workflow_spec)

        # ALWAYS return 402 on first call (no payment header) - even in demo mode
        # This allows the frontend to show the payment UI for demonstration purposes
        if not payment_header or payment_header == "":
            logger.info(f"No payment header provided for workflow {workflow_id} (demo_mode={settings.spica_demo_mode})")

            # Generate payment request
            payment_request = await payment_service.generate_x402_payment_request(
                workflow=workflow_spec,
                workflow_id=workflow_id
            )

            # Wrap payment request in x402 format
            x402_request = {
                "x402Version": 1,
                "accepts": [payment_request]
            }

            # Return 402 with X-PAYMENT-REQUEST header
            return create_402_response(
                payment_request=x402_request,
                detail="Payment required to deploy workflow"
            )

        # Payment header is present - verify or bypass based on demo mode
        if settings.spica_demo_mode:
            # Demo mode - accept any payment header (bypass verification)
            logger.info(f"Demo mode - bypassing payment verification for workflow {workflow_id}")
        else:
            # Production mode - verify payment
            payment_verification = await payment_service.verify_payment(
                payment_header=payment_header,
                required_amount=required_amount,
                workflow_id=workflow_id
            )

            if not payment_verification.is_valid:
                logger.info(f"Payment verification failed for workflow {workflow_id}: {payment_verification.error_reason}")

                # Map error codes to user-friendly messages
                error_messages = {
                    PaymentErrorCode.PAYMENT_MISSING: "Payment required to deploy workflow",
                    PaymentErrorCode.PAYMENT_DECODE_FAILED: "Invalid payment format - please check payment header encoding",
                    PaymentErrorCode.PAYMENT_INVALID_VERSION: "Unsupported payment protocol version",
                    PaymentErrorCode.PAYMENT_MISSING_SIGNATURE: "Payment signature is missing",
                    PaymentErrorCode.PAYMENT_SIGNATURE_INVALID: "Payment signature verification failed",
                    PaymentErrorCode.PAYMENT_SERVICE_UNAVAILABLE: "Payment verification service unavailable - please try again later",
                    PaymentErrorCode.PAYMENT_AMOUNT_MISMATCH: f"Payment amount does not match required amount ({required_amount} USDC)",
                    PaymentErrorCode.PAYMENT_EXPIRED: "Payment has expired - please generate a new payment",
                    PaymentErrorCode.PAYMENT_VERIFICATION_ERROR: "Payment verification error - please try again",
                }

                error_detail = error_messages.get(
                    payment_verification.error_code,
                    f"Payment verification failed: {payment_verification.error_reason}"
                )

                logger.warning(f"Returning 402 for workflow {workflow_id}: {error_detail}")

                # Generate new payment request
                payment_request = await payment_service.generate_x402_payment_request(
                    workflow=workflow_spec,
                    workflow_id=workflow_id
                )

                # Wrap payment request in x402 format
                x402_request = {
                    "x402Version": 1,
                    "accepts": [payment_request]
                }

                # Return 402 with X-PAYMENT-REQUEST header
                return create_402_response(
                    payment_request=x402_request,
                    detail=error_detail
                )

            # Payment is valid - log payer
            logger.info(f"Payment verified for workflow {workflow_id} from {payment_verification.payer}")

        # ====================================================================
        # Step 3: Activate workflow
        # ====================================================================

        logger.info(f"Activating workflow: {workflow_id}")

        # Update workflow status to active
        updated_workflow = await storage.update_workflow(
            workflow_id=workflow_id,
            updates={
                "status": "active",
                "enabled": True,
            }
        )

        logger.info(f"Successfully deployed workflow: {workflow_id}")

        # ====================================================================
        # Step 4: Return success response
        # ====================================================================

        return DeploySuccessResponse(
            success=True,
            workflow_id=workflow_id,
            status=updated_workflow.status,
            message="Workflow deployed and activated successfully"
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise

    except Exception as e:
        # Unexpected errors
        error_id = str(uuid.uuid4())[:8]
        logger.error(f"Unexpected error deploying workflow {workflow_id} [error_id={error_id}]: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred during deployment",
                    "details": f"Please contact support with error ID: {error_id}",
                    "retry": True
                },
                "timestamp": datetime.now(UTC).isoformat()
            }
        )
