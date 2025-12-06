"""Solana environment configuration validation."""

from __future__ import annotations

import os
import logging
from typing import Any, Optional

from pydantic import BaseModel, Field, ValidationError, model_validator, ConfigDict

logger = logging.getLogger(__name__)


class SolanaConfig(BaseModel):
    """Validated configuration required for Solana toolkit operations."""

    wallet_secret_salt: Optional[str] = Field(default=None, alias="WALLET_SECRET_SALT")
    wallet_secret_key: Optional[str] = Field(default=None, alias="WALLET_SECRET_KEY")
    wallet_public_key: Optional[str] = Field(default=None, alias="WALLET_PUBLIC_KEY")

    sol_address: str = Field(alias="SOL_ADDRESS")
    slippage: str = Field(alias="SLIPPAGE")
    solana_rpc_url: str = Field(alias="SOLANA_RPC_URL")
    helius_api_key: str = Field(alias="HELIUS_API_KEY")
    birdeye_api_key: str = Field(alias="BIRDEYE_API_KEY")

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    @model_validator(mode="after")
    def _validate_key_material(cls, values: "SolanaConfig") -> "SolanaConfig":
        """Ensure either a secret salt or keypair credentials are present."""
        has_salt = bool(values.wallet_secret_salt)
        has_keypair = bool(values.wallet_secret_key and values.wallet_public_key)

        if not (has_salt or has_keypair):
            raise ValueError(
                "Provide WALLET_SECRET_SALT or both WALLET_SECRET_KEY and WALLET_PUBLIC_KEY."
            )
        return values


def _runtime_get(runtime: Any, key: str) -> Optional[str]:
    """Attempt to read a setting from a runtime object if available."""
    if runtime is None:
        return None

    for attr in ("get_setting", "getSetting", "get"):
        getter = getattr(runtime, attr, None)
        if callable(getter):
            try:
                value = getter(key)
            except TypeError:
                # Getter signature mismatch – try next option
                continue
            if value is not None:
                return value

    # Common pattern: runtime.settings dict
    settings = getattr(runtime, "settings", None)
    if isinstance(settings, dict):
        return settings.get(key)

    return None


def _read_config_value(runtime: Any, *keys: str) -> Optional[str]:
    """Return the first non-empty value from runtime or environment for the provided keys."""
    for key in keys:
        value = _runtime_get(runtime, key)
        if value is None:
            value = os.getenv(key)

        if isinstance(value, str):
            value = value.strip()

        if value:
            return value

    return None


def load_solana_config(runtime: Any = None) -> SolanaConfig:
    """Validate and return Solana configuration based on runtime settings and environment variables.

    Args:
        runtime: Optional runtime object providing a ``get_setting``-style API.

    Returns:
        SolanaConfig: Validated configuration object.

    Raises:
        ValueError: When validation fails or required fields are missing.
    """
    config_payload = {
        "WALLET_SECRET_SALT": _read_config_value(runtime, "WALLET_SECRET_SALT"),
        "WALLET_SECRET_KEY": _read_config_value(runtime, "WALLET_SECRET_KEY"),
        "WALLET_PUBLIC_KEY": _read_config_value(
            runtime,
            "SOLANA_PUBLIC_KEY",
            "WALLET_PUBLIC_KEY",
        ),
        "SOL_ADDRESS": _read_config_value(runtime, "SOL_ADDRESS"),
        "SLIPPAGE": _read_config_value(runtime, "SLIPPAGE"),
        "SOLANA_RPC_URL": _read_config_value(runtime, "SOLANA_RPC_URL"),
        "HELIUS_API_KEY": _read_config_value(runtime, "HELIUS_API_KEY"),
        "BIRDEYE_API_KEY": _read_config_value(runtime, "BIRDEYE_API_KEY"),
    }

    try:
        return SolanaConfig(**config_payload)
    except ValidationError as exc:
        messages = []
        for error in exc.errors():
            location = ".".join(str(part) for part in error.get("loc", ()))
            messages.append(f"{location or 'configuration'}: {error.get('msg')}")

        detail = "\n".join(messages) or str(exc)
        logger.error("Solana configuration validation failed:\n%s", detail)
        raise ValueError(f"Solana configuration validation failed:\n{detail}") from exc

