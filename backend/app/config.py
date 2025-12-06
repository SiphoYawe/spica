"""
Application configuration using Pydantic Settings
"""

from pydantic_settings import BaseSettings
from pydantic import Field, field_validator, model_validator
from typing import Optional
import re


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    app_name: str = "Spica"
    environment: str = "development"
    debug: bool = True
    spica_demo_mode: bool = False  # Enable demo mode to bypass x402 payments

    # LLM Configuration
    openai_api_key: str = Field(
        ...,
        min_length=1,
        description="OpenAI API key (required for AI agent functionality)"
    )

    # Neo N3 Configuration
    neo_testnet_rpc: str = "https://testnet1.neo.coz.io:443"
    neo_testnet_rpc_fallback: str = "https://testnet2.neo.coz.io:443"
    neo_rpc_timeout: int = 60
    demo_wallet_wif: str = Field(
        ...,
        min_length=1,
        description="Neo N3 wallet WIF (required for demo transactions)"
    )

    # x402 Payment Configuration
    x402_facilitator_url: Optional[str] = None
    x402_receiver_address: Optional[str] = Field(
        None,
        min_length=1,
        description="Ethereum address to receive x402 payments"
    )
    x402_network: str = "base-sepolia"
    x402_default_asset: str = "USDC"

    # CoinGecko API (no key required for basic usage)
    coingecko_api_url: str = "https://api.coingecko.com/api/v3"

    # Storage
    workflows_dir: str = "./workflows"

    @field_validator("demo_wallet_wif")
    @classmethod
    def validate_wif(cls, v: str) -> str:
        """Validate Neo N3 WIF format"""
        if not v:
            raise ValueError("demo_wallet_wif is required")
        # Neo WIF starts with 'K' or 'L' and is 52 characters
        if not re.match(r"^[KL][1-9A-HJ-NP-Za-km-z]{51}$", v):
            raise ValueError(
                "Invalid Neo N3 WIF format. Must start with K or L and be 52 characters."
            )
        return v

    @field_validator("x402_receiver_address")
    @classmethod
    def validate_ethereum_address(cls, v: Optional[str]) -> Optional[str]:
        """Validate Ethereum address format"""
        if v is None:
            return None
        # Ethereum address: 0x followed by 40 hex characters
        if not re.match(r"^0x[a-fA-F0-9]{40}$", v):
            raise ValueError(
                "Invalid Ethereum address format. Must be 0x followed by 40 hex characters."
            )
        return v

    @model_validator(mode='after')
    def validate_production_requirements(self) -> 'Settings':
        """Validate that x402 configuration is complete when not in demo mode"""
        if not self.spica_demo_mode:
            # Production mode requires x402 configuration
            if not self.x402_receiver_address:
                raise ValueError(
                    "x402_receiver_address is required when spica_demo_mode is False. "
                    "Either set X402_RECEIVER_ADDRESS or enable SPICA_DEMO_MODE=true"
                )
        return self

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
