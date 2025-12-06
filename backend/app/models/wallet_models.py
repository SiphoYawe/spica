"""
Pydantic models for wallet-related API schemas
"""

from typing import Optional
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, UTC


class WalletBalance(BaseModel):
    """Wallet balance for a specific token"""
    token: str = Field(..., description="Token symbol (GAS, NEO)")
    balance: Decimal = Field(..., ge=0, description="Token balance")
    decimals: int = Field(..., ge=0, description="Number of decimal places")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "token": "GAS",
                "balance": "1543.75000000",
                "decimals": 8
            }
        }
    )


class WalletInfo(BaseModel):
    """Demo wallet information and balances"""
    address: str = Field(..., description="Neo N3 wallet address (format: N...)")
    balances: list[WalletBalance] = Field(
        default_factory=list,
        description="List of token balances"
    )
    network: str = Field(default="testnet", description="Network: testnet or mainnet")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Timestamp when wallet info was retrieved"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "address": "NhGomBpYnKXArr55nHRQ5rzy79TwKVXZbr",
                "balances": [
                    {
                        "token": "GAS",
                        "balance": "1543.75000000",
                        "decimals": 8
                    },
                    {
                        "token": "NEO",
                        "balance": "100",
                        "decimals": 0
                    }
                ],
                "network": "testnet",
                "timestamp": "2025-12-06T00:00:00.000000"
            }
        }
    )


class WalletResponse(BaseModel):
    """API response for wallet endpoint"""
    success: bool = Field(True, description="Indicates if the request was successful")
    data: Optional[WalletInfo] = Field(None, description="Wallet information")
    message: Optional[str] = Field(None, description="Optional message")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Response timestamp"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "data": {
                    "address": "NhGomBpYnKXArr55nHRQ5rzy79TwKVXZbr",
                    "balances": [
                        {
                            "token": "GAS",
                            "balance": "1543.75000000",
                            "decimals": 8
                        },
                        {
                            "token": "NEO",
                            "balance": "100",
                            "decimals": 0
                        }
                    ],
                    "network": "testnet",
                    "timestamp": "2025-12-06T00:00:00.000000"
                },
                "message": "Wallet info retrieved successfully",
                "timestamp": "2025-12-06T00:00:00.000000"
            }
        }
    )
