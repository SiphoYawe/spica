"""
Payment service for workflow monetization using x402 protocol.

This service handles:
- Workflow complexity calculation
- Payment request generation
- x402 integration for payment processing
"""

import logging
import base64
import json
import time
from decimal import Decimal
from typing import Optional, Dict, Any
from uuid import uuid4

from app.models.payment_models import (
    WorkflowComplexity,
    WorkflowPricing,
    PaymentRequestData,
    PaymentVerificationResult,
    PaymentPayload,
    PaymentErrorCode,
)
from app.models.workflow_models import WorkflowSpec
from app.config import settings

logger = logging.getLogger(__name__)


# ============================================================================
# Network-Specific Asset Addresses
# ============================================================================

# USDC contract addresses by network
USDC_ADDRESSES = {
    "base-sepolia": "0xa063B8d5ada3bE64A24Df594F96aB75F0fb78160",
    "base": "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913",
    "ethereum": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
    "sepolia": "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238",
}


def get_asset_address(network: str, asset: str) -> str:
    """
    Get the contract address for an asset on a specific network.

    Args:
        network: Network name (e.g., "base-sepolia", "base")
        asset: Asset symbol (e.g., "USDC")

    Returns:
        str: Contract address for the asset on the network

    Raises:
        ValueError: If network or asset is not supported
    """
    if asset != "USDC":
        raise ValueError(f"Unsupported asset: {asset}. Only USDC is supported.")

    if network not in USDC_ADDRESSES:
        raise ValueError(
            f"Unsupported network: {network}. "
            f"Supported networks: {', '.join(USDC_ADDRESSES.keys())}"
        )

    return USDC_ADDRESSES[network]


class PaymentService:
    """
    Service for calculating payments and generating x402 payment requests.

    This service integrates with SpoonOS X402PaymentService when available,
    or provides a standalone implementation for payment request generation.
    """

    def __init__(self, pricing: Optional[WorkflowPricing] = None):
        """
        Initialize payment service.

        Args:
            pricing: Optional custom pricing configuration. Uses defaults if not provided.
        """
        self.pricing = pricing or WorkflowPricing()
        self._x402_service: Optional[object] = None
        self._x402_available = self._init_x402_service()

    def _init_x402_service(self) -> bool:
        """
        Initialize SpoonOS X402PaymentService if available.

        Returns:
            bool: True if x402 service is available and initialized
        """
        try:
            # Import SpoonOS x402 service
            from spoon_ai.payments import X402PaymentService, X402Settings

            # Check if required configuration is present
            if not settings.x402_receiver_address:
                logger.warning("x402_receiver_address not configured, x402 integration disabled")
                return False

            # Initialize x402 settings from environment
            x402_settings = X402Settings.load()

            # Override with Spica-specific settings
            x402_settings.pay_to = settings.x402_receiver_address
            x402_settings.default_network = settings.x402_network
            x402_settings.asset_name = settings.x402_default_asset
            x402_settings.resource = "spica://workflow"
            x402_settings.description = "Spica Workflow Execution"

            self._x402_service = X402PaymentService(settings=x402_settings)
            logger.info("x402 payment service initialized successfully")
            return True

        except ImportError as e:
            logger.info(f"SpoonOS x402 not available: {e}. Using fallback implementation.")
            return False
        except Exception as e:
            logger.warning(f"Failed to initialize x402 service: {e}. Using fallback implementation.")
            return False

    def calculate_complexity(self, workflow: WorkflowSpec) -> WorkflowComplexity:
        """
        Calculate workflow complexity based on structure.

        Rules:
        1. Single step workflow without trigger = SIMPLE
        2. Any workflow with a trigger = TRIGGERED
        3. Workflow with 3+ steps = COMPLEX

        Args:
            workflow: WorkflowSpec to analyze

        Returns:
            WorkflowComplexity: The calculated complexity level
        """
        num_steps = len(workflow.steps)

        # Rule 2: Workflows with triggers are always TRIGGERED complexity
        # (Note: All WorkflowSpec instances have triggers per the model)
        if workflow.trigger:
            # If it also has 3+ steps, it's COMPLEX
            if num_steps >= 3:
                return WorkflowComplexity.COMPLEX
            # Otherwise it's TRIGGERED
            return WorkflowComplexity.TRIGGERED

        # Rule 3: 3+ steps = COMPLEX (even without trigger, though trigger is required in model)
        if num_steps >= 3:
            return WorkflowComplexity.COMPLEX

        # Rule 1: Single step = SIMPLE
        return WorkflowComplexity.SIMPLE

    def calculate_price(self, workflow: WorkflowSpec) -> Decimal:
        """
        Calculate price for workflow execution.

        Args:
            workflow: WorkflowSpec to price

        Returns:
            Decimal: Price in USDC
        """
        complexity = self.calculate_complexity(workflow)
        return self.pricing.get_price(complexity)

    def generate_workflow_id(self) -> str:
        """
        Generate a unique workflow execution ID.

        Returns:
            str: Unique workflow ID with 'wf_' prefix
        """
        return f"wf_{uuid4().hex[:12]}"

    def create_payment_request(
        self,
        workflow: WorkflowSpec,
        workflow_id: Optional[str] = None,
    ) -> PaymentRequestData:
        """
        Create a payment request for workflow execution.

        Args:
            workflow: WorkflowSpec to create payment for
            workflow_id: Optional custom workflow ID. Generated if not provided.

        Returns:
            PaymentRequestData: Payment request information

        Example:
            >>> service = PaymentService()
            >>> workflow = WorkflowSpec(...)
            >>> payment_request = service.create_payment_request(workflow)
            >>> print(payment_request.amount_usdc)  # 0.01 for simple workflow
        """
        # Generate workflow ID if not provided
        if not workflow_id:
            workflow_id = self.generate_workflow_id()

        # Calculate complexity and price
        complexity = self.calculate_complexity(workflow)
        amount = self.pricing.get_price(complexity)

        # Create memo with workflow_id
        memo = f"Spica workflow execution: {workflow_id}"

        # Create payment request data
        payment_request = PaymentRequestData(
            workflow_id=workflow_id,
            complexity=complexity,
            amount_usdc=amount,
            currency=settings.x402_default_asset,
            memo=memo,
            resource=f"workflow://{workflow_id}",
            description=f"Execute workflow: {workflow.name}",
            network=settings.x402_network,
            receiver_address=settings.x402_receiver_address,
        )

        return payment_request

    async def generate_x402_payment_request(
        self,
        workflow: WorkflowSpec,
        workflow_id: Optional[str] = None,
    ) -> dict:
        """
        Generate x402 protocol payment request JSON.

        This method integrates with SpoonOS X402PaymentService if available,
        or generates a compatible payment request structure as fallback.

        Args:
            workflow: WorkflowSpec to create payment for
            workflow_id: Optional custom workflow ID

        Returns:
            dict: x402 payment request JSON structure

        Example:
            >>> service = PaymentService()
            >>> workflow = WorkflowSpec(...)
            >>> x402_request = await service.generate_x402_payment_request(workflow)
            >>> # Returns x402 PaymentRequirements or compatible structure
        """
        payment_data = self.create_payment_request(workflow, workflow_id)

        if self._x402_available and self._x402_service:
            try:
                # Use SpoonOS x402 service to build payment requirements
                from spoon_ai.payments import X402PaymentRequest

                x402_request = X402PaymentRequest(
                    amount_usdc=payment_data.amount_usdc,
                    resource=payment_data.resource,
                    description=payment_data.description,
                    memo=payment_data.memo,
                    currency=payment_data.currency,
                    network=payment_data.network,
                    pay_to=payment_data.receiver_address,
                )

                # Build payment requirements using SpoonOS service
                requirements = self._x402_service.build_payment_requirements(x402_request)

                # Convert to dict for JSON serialization
                return requirements.model_dump(by_alias=True)

            except Exception as e:
                logger.error(f"Failed to generate x402 payment request: {e}. Using fallback.")
                # Fall through to fallback implementation

        # Fallback: Generate compatible payment request structure
        return self._generate_fallback_payment_request(payment_data)

    def _generate_fallback_payment_request(self, payment_data: PaymentRequestData) -> dict:
        """
        Generate a fallback payment request structure when x402 service is unavailable.

        Args:
            payment_data: PaymentRequestData to convert

        Returns:
            dict: Payment request structure compatible with x402 protocol

        Raises:
            ValueError: If network or asset is not supported
        """
        # Convert USDC to atomic units (6 decimals for USDC)
        amount_atomic = int(payment_data.amount_usdc * Decimal("1000000"))

        # Get network-specific asset address
        try:
            asset_address = get_asset_address(payment_data.network, payment_data.currency)
        except ValueError as e:
            logger.error(f"Failed to get asset address: {e}")
            raise

        return {
            "scheme": "exact",
            "network": payment_data.network,
            "max_amount_required": str(amount_atomic),
            "resource": payment_data.resource,
            "description": payment_data.description,
            "mime_type": "application/json",
            "pay_to": payment_data.receiver_address,
            "max_timeout_seconds": 120,
            "asset": asset_address,
            "extra": {
                "currency": payment_data.currency,
                "memo": payment_data.memo,
                "metadata": {
                    "workflow_id": payment_data.workflow_id,
                    "complexity": payment_data.complexity.value,
                    "service": "Spica Workflow Builder",
                }
            }
        }

    def _decode_payment_header(self, payment_header: str) -> Optional[PaymentPayload]:
        """
        Decode base64 X-PAYMENT header to PaymentPayload.

        Args:
            payment_header: Base64-encoded payment header

        Returns:
            PaymentPayload if successful, None if decoding fails
        """
        try:
            # Decode base64
            decoded_bytes = base64.b64decode(payment_header)
            decoded_json = decoded_bytes.decode('utf-8')

            # Parse JSON
            payload_dict = json.loads(decoded_json)

            # Validate and parse as PaymentPayload
            return PaymentPayload(**payload_dict)

        except Exception as e:
            logger.error(f"Failed to decode payment header: {e}")
            return None

    def _extract_workflow_id_from_payment(
        self,
        payment_payload: PaymentPayload,
        requirements: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Extract workflow_id from payment payload metadata/memo.

        The workflow_id should be in the payment requirements extra.metadata
        or in the memo field.

        Args:
            payment_payload: Decoded payment payload
            requirements: Optional payment requirements to match against

        Returns:
            workflow_id if found, None otherwise
        """
        # For now, we'll return None and rely on the endpoint to match workflow_id
        # In a full implementation, we'd extract from the memo or metadata
        # This would require the payment requirements to be passed in
        return None

    def _verify_payment_structure(self, payment_payload: PaymentPayload) -> PaymentVerificationResult:
        """
        Verify the basic structure of the payment payload.

        Args:
            payment_payload: Decoded payment payload

        Returns:
            PaymentVerificationResult with validation result
        """
        # Check x402 version
        if payment_payload.x402Version != 1:
            return PaymentVerificationResult(
                is_valid=False,
                error_reason=f"Unsupported x402 version: {payment_payload.x402Version}",
                error_code=PaymentErrorCode.PAYMENT_INVALID_VERSION
            )

        # Verify payload structure
        if not payment_payload.payload:
            return PaymentVerificationResult(
                is_valid=False,
                error_reason="Payment payload is missing",
                error_code=PaymentErrorCode.PAYMENT_MISSING_PAYLOAD
            )

        # Verify authorization exists
        authorization = payment_payload.payload.get("authorization")
        if not authorization:
            return PaymentVerificationResult(
                is_valid=False,
                error_reason="Payment authorization is missing",
                error_code=PaymentErrorCode.PAYMENT_MISSING_AUTHORIZATION
            )

        # Verify signature exists
        signature = payment_payload.payload.get("signature")
        if not signature:
            return PaymentVerificationResult(
                is_valid=False,
                error_reason="Payment signature is missing",
                error_code=PaymentErrorCode.PAYMENT_MISSING_SIGNATURE
            )

        return PaymentVerificationResult(
            is_valid=True,
            payer=authorization.get("from"),
        )

    def _verify_payment_expiry(self, payment_payload: PaymentPayload) -> PaymentVerificationResult:
        """
        Verify that payment has not expired.

        Args:
            payment_payload: Decoded payment payload

        Returns:
            PaymentVerificationResult with expiry check result
        """
        authorization = payment_payload.payload.get("authorization", {})
        valid_before = authorization.get("validBefore")

        if not valid_before:
            return PaymentVerificationResult(
                is_valid=False,
                error_reason="Payment validBefore timestamp is missing",
                error_code=PaymentErrorCode.PAYMENT_MISSING_EXPIRY
            )

        try:
            valid_before_timestamp = int(valid_before)
            current_timestamp = int(time.time())

            if current_timestamp > valid_before_timestamp:
                return PaymentVerificationResult(
                    is_valid=False,
                    error_reason="Payment has expired",
                    error_code=PaymentErrorCode.PAYMENT_EXPIRED
                )

            return PaymentVerificationResult(
                is_valid=True,
                payer=authorization.get("from"),
            )

        except (ValueError, TypeError) as e:
            return PaymentVerificationResult(
                is_valid=False,
                error_reason=f"Invalid validBefore timestamp: {e}",
                error_code=PaymentErrorCode.PAYMENT_INVALID_TIMESTAMP
            )

    def _verify_payment_amount(
        self,
        payment_payload: PaymentPayload,
        required_amount: Decimal
    ) -> PaymentVerificationResult:
        """
        Verify that payment amount matches requirements.

        Args:
            payment_payload: Decoded payment payload
            required_amount: Required payment amount in USDC

        Returns:
            PaymentVerificationResult with amount check result
        """
        authorization = payment_payload.payload.get("authorization", {})
        payment_value = authorization.get("value")

        if not payment_value:
            return PaymentVerificationResult(
                is_valid=False,
                error_reason="Payment value is missing",
                error_code=PaymentErrorCode.PAYMENT_MISSING_AMOUNT
            )

        try:
            # Convert required USDC to atomic units (6 decimals)
            required_atomic = int(required_amount * Decimal("1000000"))

            # Parse payment value (should be string in atomic units)
            payment_atomic = int(payment_value)

            if payment_atomic < required_atomic:
                return PaymentVerificationResult(
                    is_valid=False,
                    error_reason=f"Payment amount does not match required amount (got {payment_atomic}, need {required_atomic})",
                    error_code=PaymentErrorCode.PAYMENT_AMOUNT_MISMATCH
                )

            return PaymentVerificationResult(
                is_valid=True,
                payer=authorization.get("from"),
            )

        except (ValueError, TypeError) as e:
            return PaymentVerificationResult(
                is_valid=False,
                error_reason=f"Invalid payment amount: {e}",
                error_code=PaymentErrorCode.PAYMENT_INVALID_AMOUNT
            )

    async def verify_payment(
        self,
        payment_header: str,
        required_amount: Optional[Decimal] = None,
        workflow_id: Optional[str] = None
    ) -> PaymentVerificationResult:
        """
        Verify an x402 payment header.

        This method performs comprehensive payment verification:
        1. Decode the X-PAYMENT header (base64 JSON)
        2. Verify basic structure (version, payload, signature)
        3. Verify payment hasn't expired (validBefore > now)
        4. Verify amount matches requirements (if provided)
        5. Use SpoonOS X402 service for cryptographic verification (if available)

        Args:
            payment_header: X-PAYMENT header value from client (base64-encoded)
            required_amount: Optional required payment amount in USDC
            workflow_id: Optional workflow_id to match against payment memo

        Returns:
            PaymentVerificationResult: Verification result with detailed error info

        Example:
            >>> service = PaymentService()
            >>> result = await service.verify_payment(
            ...     payment_header="eyJ4NDAyVmVyc2lvbiI6MSw...",
            ...     required_amount=Decimal("0.01")
            ... )
            >>> if result.is_valid:
            ...     print(f"Payment verified from {result.payer}")
            ... else:
            ...     print(f"Payment failed: {result.error_reason}")
        """
        logger.info("Verifying payment header")

        # ====================================================================
        # Step 1: Decode payment header
        # ====================================================================

        payment_payload = self._decode_payment_header(payment_header)
        if not payment_payload:
            return PaymentVerificationResult(
                is_valid=False,
                error_reason="Failed to decode payment header (invalid base64 or JSON)",
                error_code=PaymentErrorCode.PAYMENT_DECODE_FAILED
            )

        logger.debug(f"Decoded payment payload: version={payment_payload.x402Version}, scheme={payment_payload.scheme}")

        # ====================================================================
        # Step 2: Verify payment structure
        # ====================================================================

        structure_result = self._verify_payment_structure(payment_payload)
        if not structure_result.is_valid:
            return structure_result

        # ====================================================================
        # Step 3: Verify payment hasn't expired
        # ====================================================================

        expiry_result = self._verify_payment_expiry(payment_payload)
        if not expiry_result.is_valid:
            return expiry_result

        # ====================================================================
        # Step 4: Verify amount if required
        # ====================================================================

        if required_amount is not None:
            amount_result = self._verify_payment_amount(payment_payload, required_amount)
            if not amount_result.is_valid:
                return amount_result

        # ====================================================================
        # Step 5: Use SpoonOS x402 service for cryptographic verification
        # ====================================================================

        if self._x402_available and self._x402_service:
            try:
                logger.info("Using SpoonOS x402 service for cryptographic verification")

                # Build payment requirements for verification
                requirements = None
                if required_amount is not None:
                    try:
                        from spoon_ai.payments import X402PaymentRequest
                        x402_request = X402PaymentRequest(
                            amount_usdc=required_amount,
                            resource=f"workflow://{workflow_id}" if workflow_id else "workflow://unknown",
                        )
                        requirements = self._x402_service.build_payment_requirements(x402_request)
                    except ImportError:
                        # SpoonOS not available - x402_service won't work properly
                        logger.warning("SpoonOS import failed during verification - falling back")
                        raise

                # Verify using SpoonOS service
                verify_result = await self._x402_service.verify_payment(
                    payment_header,
                    requirements=requirements
                )

                if not verify_result.is_valid:
                    return PaymentVerificationResult(
                        is_valid=False,
                        error_reason=verify_result.invalid_reason or "Payment signature verification failed",
                        error_code=PaymentErrorCode.PAYMENT_SIGNATURE_INVALID,
                        payer=verify_result.payer,
                    )

                logger.info(f"Payment cryptographically verified from payer: {verify_result.payer}")

                # Extract workflow_id from memo if available
                extracted_workflow_id = self._extract_workflow_id_from_payment(
                    payment_payload,
                    requirements
                )

                return PaymentVerificationResult(
                    is_valid=True,
                    workflow_id=extracted_workflow_id or workflow_id,
                    payer=verify_result.payer,
                )

            except Exception as e:
                logger.error(f"SpoonOS x402 verification failed: {e}", exc_info=True)
                return PaymentVerificationResult(
                    is_valid=False,
                    error_reason=f"Payment verification error: {str(e)}",
                    error_code=PaymentErrorCode.PAYMENT_VERIFICATION_ERROR
                )

        # ====================================================================
        # Fallback: REJECT payment when x402 service unavailable
        # ====================================================================

        logger.error("x402 service not available - rejecting payment (cryptographic verification required)")

        return PaymentVerificationResult(
            is_valid=False,
            error_reason="Payment verification service unavailable - cryptographic verification required for production",
            error_code=PaymentErrorCode.PAYMENT_SERVICE_UNAVAILABLE
        )


# Global payment service instance
_payment_service: Optional[PaymentService] = None


def get_payment_service() -> PaymentService:
    """
    Get or create the global PaymentService instance.

    Returns:
        PaymentService: Singleton payment service instance
    """
    global _payment_service
    if _payment_service is None:
        _payment_service = PaymentService()
    return _payment_service
