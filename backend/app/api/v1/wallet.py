"""
Wallet API endpoints for demo wallet information
"""

import logging
from fastapi import APIRouter, HTTPException, status, Path
from datetime import datetime, UTC
from pydantic import StringConstraints
from typing import Annotated

from app.models.wallet_models import WalletResponse, WalletInfo
from app.models.api_models import ErrorResponse, ErrorDetail
from app.services.wallet_service import get_wallet_service, WalletSecurityError

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/wallet", tags=["wallet"])


@router.get(
    "",
    response_model=WalletResponse,
    summary="Get demo wallet information",
    description="""
    Get demo wallet address and balances.

    This endpoint returns the public address and token balances for the demo wallet
    used to execute workflows. The wallet private key is NEVER exposed.

    Returns balances for:
    - GAS (with 8 decimals)
    - NEO (indivisible, 0 decimals)
    """,
    responses={
        200: {
            "description": "Wallet information retrieved successfully",
            "model": WalletResponse
        },
        500: {
            "description": "Internal server error (wallet loading failed)",
            "model": ErrorResponse
        }
    }
)
async def get_wallet():
    """
    Get demo wallet information and balances.

    Returns:
        WalletResponse with address and balances

    Raises:
        HTTPException: If wallet service fails
    """
    try:
        # Get wallet service
        wallet_service = await get_wallet_service()

        # Get wallet info with balances
        wallet_info = await wallet_service.get_wallet_info()

        logger.info(f"Wallet info retrieved for address: {wallet_info.address}")

        return WalletResponse(
            success=True,
            data=wallet_info,
            message="Wallet info retrieved successfully",
            timestamp=datetime.now(UTC)
        )

    except WalletSecurityError as e:
        logger.error(f"Wallet security error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "WALLET_SECURITY_ERROR",
                "message": "Failed to load demo wallet",
                "details": type(e).__name__,  # Only expose error type, not details
                "retry": False
            }
        )

    except Exception as e:
        logger.error(f"Unexpected error fetching wallet info: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "WALLET_ERROR",
                "message": "Failed to retrieve wallet information",
                "details": type(e).__name__,  # Only expose error type, not full message
                "retry": True
            }
        )


@router.get(
    "/balance/{token}",
    response_model=dict,
    summary="Get balance for specific token",
    description="""
    Get balance for a specific token (GAS or NEO).

    Supported tokens:
    - GAS: Gas token with 8 decimals
    - NEO: NEO token with 0 decimals (indivisible)
    """,
    responses={
        200: {
            "description": "Token balance retrieved successfully"
        },
        400: {
            "description": "Invalid token specified",
            "model": ErrorResponse
        },
        500: {
            "description": "Internal server error",
            "model": ErrorResponse
        }
    }
)
async def get_token_balance(
    token: Annotated[
        str,
        Path(
            min_length=2,
            max_length=10,
            pattern="^[A-Za-z]+$",
            description="Token symbol (GAS or NEO)"
        )
    ]
):
    """
    Get balance for a specific token.

    Args:
        token: Token symbol (GAS or NEO)

    Returns:
        Dict with token and balance

    Raises:
        HTTPException: If token is invalid or service fails
    """
    try:
        # Validate token
        token_upper = token.upper()
        if token_upper not in ["GAS", "NEO"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "INVALID_TOKEN",
                    "message": f"Unsupported token: {token}",
                    "details": "Supported tokens: GAS, NEO",
                    "retry": False
                }
            )

        # Get wallet service
        wallet_service = await get_wallet_service()

        # Get balance
        balance = await wallet_service.get_balance(token_upper)

        logger.info(f"Balance retrieved for {token_upper}: {balance}")

        return {
            "success": True,
            "data": {
                "token": token_upper,
                "balance": str(balance),
                "decimals": 8 if token_upper == "GAS" else 0
            },
            "timestamp": datetime.now(UTC).isoformat()
        }

    except HTTPException:
        # Re-raise HTTP exceptions (validation errors)
        raise

    except Exception as e:
        logger.error(f"Error fetching {token} balance: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "BALANCE_ERROR",
                "message": f"Failed to retrieve {token} balance",
                "details": type(e).__name__,  # Only expose error type
                "retry": True
            }
        )
