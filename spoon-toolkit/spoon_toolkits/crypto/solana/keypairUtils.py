"""Utilities for loading Solana keypairs and public keys."""

import base64
import logging
import os
from typing import Any, Iterable, Optional

import base58
from solders.keypair import Keypair
from solders.pubkey import Pubkey

from .types import KeypairResult

logger = logging.getLogger(__name__)

PRIVATE_KEY_KEYS = ("SOLANA_PRIVATE_KEY", "WALLET_PRIVATE_KEY")
PUBLIC_KEY_KEYS = ("SOLANA_PUBLIC_KEY", "WALLET_PUBLIC_KEY")


def _runtime_get(runtime: Any, key: str) -> Optional[str]:
    """Attempt to retrieve a configuration value from an agent runtime."""
    if runtime is None:
        return None

    for attr in ("get_setting", "getSetting", "get"):
        getter = getattr(runtime, attr, None)
        if callable(getter):
            try:
                value = getter(key)
            except TypeError:
                # Getter signature mismatch, try the next option
                continue
            if value is not None:
                return value

    settings = getattr(runtime, "settings", None)
    if isinstance(settings, dict):
        return settings.get(key)

    return None


def _first_non_empty(values: Iterable[Optional[str]]) -> Optional[str]:
    """Return the first non-empty string from an iterable."""
    for value in values:
        if isinstance(value, str):
            stripped = value.strip()
            if stripped:
                return stripped
        elif value:
            return value  # Already a truthy value (e.g., bytes)
    return None


def _read_setting(runtime: Any, keys: Iterable[str]) -> Optional[str]:
    resolved = (
        _runtime_get(runtime, key) if runtime else os.getenv(key)
        for key in keys
    )
    return _first_non_empty(resolved)


def _decode_private_key(private_key: str) -> Keypair:
    """Decode a private key string into a Keypair object.

    The decoding attempts base58 first and then base64, mirroring the
    behaviour implemented in the TypeScript utilities.
    """
    if not isinstance(private_key, str):
        raise TypeError("Private key must be provided as a string")

    last_error: Optional[Exception] = None

    try:
        secret = base58.b58decode(private_key)
        if len(secret) != 64:
            raise ValueError("Invalid private key length (expected 64 bytes)")
        return Keypair.from_bytes(secret)
    except Exception as exc:  # pylint: disable=broad-except
        last_error = exc
        logger.debug("Failed to decode private key as base58: %s", exc)

    try:
        secret = base64.b64decode(private_key)
        if len(secret) != 64:
            raise ValueError("Invalid private key length (expected 64 bytes)")
        return Keypair.from_bytes(secret)
    except Exception as exc:  # pylint: disable=broad-except
        last_error = exc
        logger.debug("Failed to decode private key as base64: %s", exc)

    raise ValueError("Unable to decode private key") from last_error


def get_private_key(runtime: Any = None) -> Optional[str]:
    """Return the configured Solana private key string, if available."""
    return _read_setting(runtime, PRIVATE_KEY_KEYS)


def get_public_key(runtime: Any = None) -> Optional[str]:
    """Return the configured Solana public key string, if available."""
    return _read_setting(runtime, PUBLIC_KEY_KEYS)


def get_wallet_keypair(
    runtime: Any = None,
    *,
    require_private_key: bool = True,
    private_key: Optional[str] = None,
    public_key: Optional[str] = None,
) -> KeypairResult:
    """Get a Solana wallet keypair or public key from runtime or environment settings.

    Args:
        runtime: Optional runtime object providing configuration.
        require_private_key: Whether a private key is required.
        private_key: Optional private key override string.
        public_key: Optional public key override string.

    Returns:
        KeypairResult containing either a ``keypair`` when ``require_private_key``
        is True, or a ``public_key`` otherwise.
    """
    if require_private_key:
        private_key_str = _first_non_empty(
            [private_key, get_private_key(runtime)]
        )
        if not private_key_str:
            raise ValueError("Private key not found in runtime settings or environment variables")

        keypair = _decode_private_key(private_key_str)
        return KeypairResult(keypair=keypair, public_key=keypair.pubkey())

    public_key_str = _first_non_empty(
        [public_key, get_public_key(runtime)]
    )

    if public_key_str:
        try:
            pubkey = Pubkey.from_string(public_key_str)
        except Exception as exc:  # pylint: disable=broad-except
            logger.debug("Failed to parse public key '%s': %s", public_key_str, exc)
            raise ValueError("Invalid public key format") from exc
        return KeypairResult(public_key=pubkey)

    # If only a private key is supplied, derive the public key
    if private_key:
        keypair = _decode_private_key(private_key)
        return KeypairResult(public_key=keypair.pubkey())

    raise ValueError("Public key not found in runtime settings or environment variables")


def get_wallet_key(
    require_private_key: bool = True,
    private_key: Optional[str] = None,
    runtime: Any = None,
) -> KeypairResult:
    """Backward-compatible wrapper matching previous utility signature."""
    return get_wallet_keypair(
        runtime=runtime,
        require_private_key=require_private_key,
        private_key=private_key,
    )


__all__ = [
    "get_private_key",
    "get_public_key",
    "get_wallet_keypair",
    "get_wallet_key",
]
