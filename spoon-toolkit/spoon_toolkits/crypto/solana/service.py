"""Solana blockchain service tools，this module provides comprehensive blockchain service tools,"""

import asyncio
import contextlib
import inspect
import json
import logging
import os
import re
import time
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Awaitable, Callable, Dict, List, Optional, Sequence, Union

import base58
import base64
import httpx

from .constants import (
    BIRDEYE_API_BASE_URL,
    ENV_KEYS,
    LAMPORTS_PER_SOL,
    MAX_RETRIES,
    METADATA_PROGRAM_ID,
    NATIVE_SOL_ADDRESS,
    RETRY_DELAY,
    SOLANA_SERVICE_NAME,
    SOLANA_WALLET_DATA_CACHE_KEY,
    TOKEN_2022_PROGRAM_ID,
    TOKEN_ADDRESSES,
    TOKEN_PROGRAM_ID,
    TOKEN_ACCOUNT_DATA_LENGTH,
    TOKEN_MINT_DATA_LENGTH,
    UPDATE_INTERVAL,
)
from .keypairUtils import get_wallet_keypair

from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair
from solders.pubkey import Pubkey

from solana.rpc.websocket_api import connect as solana_ws_connect


logger = logging.getLogger(__name__)

def get_env_value(keys: List[str], default: Optional[str] = None) -> Optional[str]:
    """Return the first non-empty environment variable from the provided keys."""
    for key in keys:
        value = os.getenv(key)
        if value:
            return value
    return default

def get_rpc_url() -> str:
    """Resolve the default Solana RPC URL from environment configuration."""
    return get_env_value(ENV_KEYS["RPC_URL"]) or "https://api.mainnet-beta.solana.com"

def get_api_key(service: str) -> Optional[str]:
    """Retrieve API keys (Helius/Birdeye) using the same semantics as the plugin."""
    key_map = {
        "helius": ENV_KEYS["HELIUS_API_KEY"],
        "birdeye": ENV_KEYS["BIRDEYE_API_KEY"],
    }
    keys = key_map.get(service)
    if not keys:
        return None
    return get_env_value(keys)

def validate_solana_address(address: Optional[str]) -> bool:
    """Validate that a string is a well-formed Solana public key."""
    if not address or not isinstance(address, str):
        return False
    address = address.strip()
    if not address:
        return False
    if not re.match(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$", address):
        return False
    try:
        raw = base58.b58decode(address)
        if len(raw) != 32:
            return False
        if Pubkey:
            Pubkey.from_bytes(raw)
        return True
    except Exception:
        return False

def validate_private_key(private_key: Optional[str]) -> bool:
    """Validate Solana private key material (base58 or base64 encoded)."""
    if not private_key or not isinstance(private_key, str):
        return False
    key = private_key.strip()
    if not key:
        return False
    try:
        decoded = base58.b58decode(key)
        if len(decoded) == 64:
            return True
    except Exception:
        pass
    try:
        decoded = base64.b64decode(key)
        return len(decoded) == 64
    except Exception:
        return False

def lamports_to_sol(lamports: int) -> float:
    """Convert lamports to SOL."""
    return lamports / LAMPORTS_PER_SOL

def sol_to_lamports(sol: Union[float, str]) -> int:
    """Convert SOL to lamports using precise decimal arithmetic."""
    if isinstance(sol, float):
        sol_decimal = Decimal(str(sol))
    else:
        sol_decimal = Decimal(str(sol))
    lamports_decimal = sol_decimal * Decimal(str(LAMPORTS_PER_SOL))
    if lamports_decimal % 1 != 0:
        raise ValueError(
            f"SOL amount {sol} has more fractional precision than supported. "
            "Maximum precision: 0.000000001 SOL (1 lamport)"
        )
    return int(lamports_decimal)

def format_token_amount(amount: Union[int, str], decimals: int) -> float:
    """Format raw token amount to UI units."""
    return float(amount) / (10 ** decimals)

def parse_token_amount(amount: Union[float, str], decimals: int) -> int:
    """Parse human-readable token amount into raw units."""
    from decimal import InvalidOperation

    try:
        amount_decimal = Decimal(str(amount))
        multiplier = Decimal(10) ** decimals
        raw_amount = amount_decimal * multiplier
        if raw_amount % 1 != 0:
            raise ValueError(
                f"Amount {amount} has more fractional precision than supported by {decimals} decimals. "
                f"Maximum precision: {1 / (10 ** decimals)}"
            )
        return int(raw_amount)
    except InvalidOperation as exc:
        raise ValueError(f"Invalid amount format: {amount}") from exc


def is_native_sol(token_address: Optional[str]) -> bool:
    """Check whether the provided token identifier represents native SOL."""
    if not token_address:
        return True
    return (
        token_address.lower() == "sol"
        or token_address == NATIVE_SOL_ADDRESS
        or token_address == TOKEN_ADDRESSES["SOL"]
        or token_address == "0x0000000000000000000000000000000000000000"
    )

async def get_mint_program_id(client: Any, mint_address: str) -> str:
    """Detect which token program owns a mint (legacy SPL or Token-2022)."""
    from .constants import TOKEN_PROGRAM_ID as LEGACY_TOKEN_PROGRAM_ID

    mint_pubkey = Pubkey.from_string(mint_address)
    account_info = await client.get_account_info(mint_pubkey)
    if not account_info.value:
        raise ValueError(f"Mint account not found: {mint_address}")
    owner_str = str(account_info.value.owner)
    if owner_str == LEGACY_TOKEN_PROGRAM_ID:
        return LEGACY_TOKEN_PROGRAM_ID
    if owner_str == TOKEN_2022_PROGRAM_ID:
        return TOKEN_2022_PROGRAM_ID
    raise ValueError(f"Mint {mint_address} is not owned by a known token program. Owner: {owner_str}")

def get_associated_token_address_for_program(owner_address: str, mint_address: str, program_id: str) -> str:
    """Derive the associated token address for a specific token program."""
    if not Pubkey:
        raise RuntimeError("solders dependency not available")
    try:
        from spl.token.instructions import get_associated_token_address as derive_ata  # type: ignore
    except Exception as exc:
        raise ImportError("SPL token library not available") from exc

    owner_pubkey = Pubkey.from_string(owner_address)
    mint_pubkey = Pubkey.from_string(mint_address)
    program_pubkey = Pubkey.from_string(program_id)
    return str(derive_ata(owner_pubkey, mint_pubkey, program_pubkey))


def get_associated_token_address(mint_address: str, owner_address: str) -> str:
    """Derive the default associated token account (legacy token program)."""
    try:
        from spl.token.instructions import get_associated_token_address as derive_ata  # type: ignore
    except Exception as exc:
        raise ImportError("SPL token library not available") from exc

    owner_pubkey = Pubkey.from_string(owner_address)
    mint_pubkey = Pubkey.from_string(mint_address)
    return str(derive_ata(owner_pubkey, mint_pubkey))


def create_request_headers(api_key: Optional[str] = None) -> Dict[str, str]:
    """Create standard JSON headers with optional API key."""
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if api_key:
        headers["X-API-KEY"] = api_key
        headers["x-chain"] = "solana"
    return headers


def truncate_address(address: str, start_chars: int = 4, end_chars: int = 4) -> str:
    """Truncate a Solana address for display usage."""
    if len(address) <= start_chars + end_chars:
        return address
    return f"{address[:start_chars]}...{address[-end_chars:]}"


def verify_solana_signature(message: str, signature_base64: str, public_key_base58: str) -> bool:
    """Verify a Solana Ed25519 signature."""
    try:
        import nacl.signing  # type: ignore

        signature = base64.b64decode(signature_base64)
        message_bytes = message.encode("utf-8")
        public_key_bytes = base58.b58decode(public_key_base58)
        verify_key = nacl.signing.VerifyKey(public_key_bytes)
        verify_key.verify(message_bytes, signature)
        return True
    except Exception as exc:
        logger.debug("Signature verification failed: %s", exc)
        return False


def detect_pubkeys_from_string(input_text: str, check_curve: bool = False) -> List[str]:
    """Detect Solana public keys in arbitrary text."""
    results: set[str] = set()
    pattern = r"\b[1-9A-HJ-NP-Za-km-z]{32,44}\b"
    for match in re.findall(pattern, input_text):
        try:
            buf = base58.b58decode(match)
            if len(buf) != 32:
                continue
            if check_curve and Pubkey:
                try:
                    Pubkey.from_bytes(buf)
                except Exception:
                    continue
            results.add(match)
        except Exception:
            continue
    return list(results)


def detect_private_keys_from_string(input_text: str) -> List[Dict[str, Any]]:
    """Detect Solana private keys in text and return metadata only."""
    results: List[Dict[str, Any]] = []
    base58_pattern = r"\b[1-9A-HJ-NP-Za-km-z]{86,90}\b"
    hex_pattern = r"\b[a-fA-F0-9]{128}\b"

    for match in re.finditer(base58_pattern, input_text):
        try:
            decoded = base58.b58decode(match.group())
            if len(decoded) == 64:
                results.append(
                    {
                        "format": "base58",
                        "match_length": len(match.group()),
                        "position": match.span(),
                        "bytes_length": len(decoded),
                    }
                )
        except Exception:
            continue

    for match in re.finditer(hex_pattern, input_text):
        try:
            decoded = bytes.fromhex(match.group())
            if len(decoded) == 64:
                results.append(
                    {
                        "format": "hex",
                        "match_length": len(match.group()),
                        "position": match.span(),
                        "bytes_length": len(decoded),
                    }
                )
        except Exception:
            continue

    return results


def parse_transaction_error(error_message: str) -> str:
    """Normalize transaction error messages for display."""
    return error_message or "Unknown transaction error"


_BALANCE_ERROR_MESSAGES = {
    "account_not_found": "Failed to get account information",
    "invalid_address": "Invalid Solana address",
    "rpc_unavailable": "Solana dependencies not available",
}

_PRICE_CACHE: Dict[str, Any] = {}
_PRICE_CACHE_TTL: int = 300

_PRICE_TOKEN_MAP = {
    "SOL": ("solana", TOKEN_ADDRESSES.get("SOL", "So11111111111111111111111111111111111111112")),
    "BTC": ("bitcoin", TOKEN_ADDRESSES.get("BTC", "9n4nbM75f5Ui33ZbPYXn59EwSgE8CGsHtAeTH5YFeJ9E")),
    "ETH": ("ethereum", TOKEN_ADDRESSES.get("ETH", "2FPyTwcZLUg1MDrwsyoP4D6s1tM7hAkHYRjkNb5w6Pxk")),
}


async def _get_token_balances(
    client: Any,
    owner_pubkey: Any,
) -> List[Dict[str, Any]]:
    """Fetch SPL token balances for a wallet across legacy and Token-2022 programs."""
    balances: List[Dict[str, Any]] = []

    for program_id in (TOKEN_PROGRAM_ID, TOKEN_2022_PROGRAM_ID):
        try:
            response = await client.get_token_accounts_by_owner(
                owner_pubkey,
                {"programId": program_id},
                encoding="jsonParsed",
            )
        except Exception as exc:
            logger.debug("Failed to query token accounts for %s: %s", program_id, exc)
            continue

        accounts = getattr(response, "value", None)
        if not accounts:
            continue

        for account_info in accounts:
            try:
                parsed = account_info.account.data.parsed
                token_info = parsed["info"]["tokenAmount"]
                ui_amount = token_info.get("uiAmount") or 0
                if float(ui_amount) <= 0:
                    continue
                balances.append(
                    {
                        "mint": parsed["info"]["mint"],
                        "balance": token_info.get("amount", "0"),
                        "ui_amount": ui_amount,
                        "decimals": token_info.get("decimals", 0),
                        "program_id": program_id,
                    }
                )
            except Exception as exc:
                logger.debug("Error parsing token account: %s", exc)

    return balances


async def _get_spl_token_balance(
    client: Any,
    owner_pubkey: Any,
    token_mint: str,
) -> Optional[Dict[str, Any]]:
    """Fetch balance information for a specific SPL token mint."""
    if Pubkey is None:
        raise RuntimeError(_BALANCE_ERROR_MESSAGES["rpc_unavailable"])

    try:
        program_id = await get_mint_program_id(client, token_mint)
    except ValueError as exc:
        logger.debug("Failed to detect program for mint %s: %s", token_mint, exc)
        program_id = TOKEN_PROGRAM_ID

    try:
        ata_address = get_associated_token_address_for_program(
            str(owner_pubkey),
            token_mint,
            program_id,
        )
        ata_pubkey = Pubkey.from_string(ata_address)
        response = await client.get_account_info(ata_pubkey, encoding="jsonParsed")
    except Exception as exc:
        logger.debug("Error fetching token account info: %s", exc)
        return None

    value = getattr(response, "value", None)
    if not value or not getattr(value, "data", None):
        return {
            "balance": "0",
            "ui_amount": 0.0,
            "decimals": 0,
            "program_id": program_id,
        }

    parsed = value.data.parsed
    token_amount = parsed["info"]["tokenAmount"]
    return {
        "balance": token_amount.get("amount", "0"),
        "ui_amount": token_amount.get("uiAmount") or 0.0,
        "decimals": token_amount.get("decimals", 0),
        "program_id": program_id,
    }


async def get_balance_for_address(
    rpc_url: str,
    address: str,
    *,
    token_address: Optional[str] = None,
    include_tokens: bool = False,
) -> Dict[str, Any]:
    """Return SOL and optional token balances for a single address."""
    if AsyncClient is None or Pubkey is None:
        raise RuntimeError(_BALANCE_ERROR_MESSAGES["rpc_unavailable"])

    if not validate_solana_address(address):
        raise ValueError(_BALANCE_ERROR_MESSAGES["invalid_address"])

    async with AsyncClient(rpc_url) as client:
        pubkey = Pubkey.from_string(address)

        if not token_address or is_native_sol(token_address):
            response = await client.get_balance(pubkey)
            value = getattr(response, "value", None)
            if value is None:
                raise RuntimeError(_BALANCE_ERROR_MESSAGES["account_not_found"])

            result: Dict[str, Any] = {
                "address": address,
                "sol_balance": lamports_to_sol(value),
                "lamports": value,
            }

            if include_tokens:
                result["token_balances"] = await _get_token_balances(client, pubkey)
            return result

        token_balance = await _get_spl_token_balance(client, pubkey, token_address)
        return {
            "address": address,
            "token_address": token_address,
            "token_balance": token_balance
            or {"balance": "0", "ui_amount": 0.0, "decimals": 0},
        }


async def get_balances_for_addresses(
    rpc_url: str,
    addresses: Sequence[str],
    *,
    token_address: Optional[str] = None,
    include_tokens: bool = False,
) -> Dict[str, Any]:
    """Return balances for multiple addresses."""
    if AsyncClient is None or Pubkey is None:
        raise RuntimeError(_BALANCE_ERROR_MESSAGES["rpc_unavailable"])

    pubkeys = [Pubkey.from_string(addr) for addr in addresses]

    async with AsyncClient(rpc_url) as client:
        results: Dict[str, Any] = {}

        if not token_address or is_native_sol(token_address):
            response = await client.get_multiple_accounts(pubkeys)
            accounts = getattr(response, "value", None)
            if accounts is None:
                raise RuntimeError(_BALANCE_ERROR_MESSAGES["account_not_found"])

            for addr, account_info, pk in zip(addresses, accounts, pubkeys):
                if account_info:
                    sol_balance = lamports_to_sol(account_info.lamports)
                    entry: Dict[str, Any] = {
                        "sol_balance": sol_balance,
                        "lamports": account_info.lamports,
                    }
                    if include_tokens:
                        entry["token_balances"] = await _get_token_balances(client, pk)
                    results[addr] = entry
                else:
                    results[addr] = {"sol_balance": 0.0, "lamports": 0}
        else:
            for addr, pk in zip(addresses, pubkeys):
                token_balance = await _get_spl_token_balance(client, pk, token_address)
                results[addr] = token_balance or {
                    "balance": "0",
                    "ui_amount": 0.0,
                    "decimals": 0,
                }

    return {
        "addresses": list(addresses),
        "token_address": token_address,
        "balances": results,
    }


async def fetch_prices_with_cache(force_refresh: bool = False) -> Dict[str, Dict[str, str]]:
    """Fetch SOL/BTC/ETH prices using Birdeye with a lightweight cache."""
    cache_key = "prices"
    now = time.time()

    if not force_refresh and cache_key in _PRICE_CACHE:
        cached = _PRICE_CACHE[cache_key]
        if now - cached["timestamp"] < _PRICE_CACHE_TTL:
            return cached["data"]

    prices = {
        "solana": {"usd": "0"},
        "bitcoin": {"usd": "0"},
        "ethereum": {"usd": "0"},
    }

    api_key = get_api_key("birdeye")
    if not api_key:
        return prices

    headers = create_request_headers(api_key)

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            for symbol, (key, address) in _PRICE_TOKEN_MAP.items():
                try:
                    response = await client.get(
                        f"{BIRDEYE_API_BASE_URL}/defi/price",
                        params={"address": address},
                        headers=headers,
                    )
                    if response.status_code != 200:
                        continue
                    data = response.json()
                    value = data.get("data", {}).get("value")
                    if value is not None:
                        prices[key]["usd"] = str(value)
                except Exception as exc:
                    logger.debug("Failed to fetch price for %s: %s", symbol, exc)
    except Exception as exc:
        logger.error("Error fetching prices: %s", exc)
        return prices

    _PRICE_CACHE[cache_key] = {"data": prices, "timestamp": now}
    return prices

async def get_portfolio_overview(
    rpc_url: str,
    address: str,
    *,
    include_prices: bool = True,
) -> Dict[str, Any]:
    """Return a wallet portfolio overview with optional price data."""
    portfolio = await get_balance_for_address(
        rpc_url,
        address,
        include_tokens=True,
    )

    if include_prices:
        prices = await fetch_prices_with_cache()
        portfolio["prices"] = prices
        try:
            sol_price = float(prices.get("solana", {}).get("usd", "0"))
            portfolio["sol_value_usd"] = portfolio.get("sol_balance", 0) * sol_price
        except Exception as exc:
            logger.debug("Failed to compute SOL value in USD: %s", exc)

    return portfolio


@dataclass
class _AccountSubscription:
    account_address: str
    rpc_url: str
    ws_url: str
    websocket: Any
    subscription_id: int
    task: asyncio.Task = field(init=False, repr=False)
    encoding: str
    commitment: str
    last_update: Optional[Dict[str, Any]] = None
    last_error: Optional[str] = None
    handler: Optional[Callable[[str, Any, Any], Union[None, Awaitable[Any]]]] = None


class SolanaService:
    
    service_type: str = SOLANA_SERVICE_NAME
    capability_description: str = (
        "The agent is able to interact with the Solana blockchain, "
        "and has access to the wallet data"
    )

    LAMPORTS2SOL: float = 1 / LAMPORTS_PER_SOL
    SOL2LAMPORTS: int = LAMPORTS_PER_SOL
    _PRICE_CACHE_KEY: str = "solana/prices"
    _TOKEN_CACHE_TEMPLATE: str = "solana_{addr}_tokens"
    _DEFAULT_DECIMALS_CACHE: Dict[str, int] = {
        "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v": 6,  # USDC
        "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB": 6,  # USDT
        "So11111111111111111111111111111111111111112": 9,  # SOL
    }

    def __init__(self, runtime: Any) -> None:
        self.runtime = runtime
        self.rpc_url = self._resolve_rpc_url()
        self.connection: Optional[AsyncClient] = None
        self.public_key: Optional[str] = None
        self.exchange_registry: Dict[int, Any] = {}
        self._registry_counter = 0
        self.subscriptions: Dict[str, _AccountSubscription] = {}
        self._subscription_lock = asyncio.Lock()
        self.decimals_cache: Dict[str, int] = dict(self._DEFAULT_DECIMALS_CACHE)
        self.jupiter_service: Optional[Any] = None
        self.last_update: float = 0.0
        self.update_interval: int = UPDATE_INTERVAL
        self._wallet_cache: Optional[Dict[str, Any]] = None
        self._update_task: Optional[asyncio.Task] = None
        self._jupiter_task: Optional[asyncio.Task] = None
        self._running = False
        self._cache_lock = asyncio.Lock()

    @classmethod
    async def start(cls, runtime: Any) -> "SolanaService":
        service = cls(runtime)
        await service._start_internal()
        return service

    async def start_service(self) -> None:
        await self._start_internal()

    async def _start_internal(self) -> None:
        await self._ensure_connection()
        self._resolve_public_key()
        self._running = True
        if self._update_task is None:
            self._update_task = asyncio.create_task(
                self._wallet_update_loop(),
                name="solana-wallet-refresh",
            )
        if self._jupiter_task is None:
            self._jupiter_task = asyncio.create_task(
                self._watch_jupiter_service(),
                name="solana-jupiter-service",
            )

    @staticmethod
    async def stop(runtime: Any) -> None:
        if runtime is None:
            return

        service: Optional[SolanaService] = None
        for attr in ("get_service", "getService", "get"):
            getter = getattr(runtime, attr, None)
            if callable(getter):
                try:
                    maybe_value = getter(SOLANA_SERVICE_NAME)
                except TypeError:
                    continue
                if inspect.isawaitable(maybe_value):
                    maybe_value = await maybe_value  # type: ignore[assignment]
                if isinstance(maybe_value, SolanaService):
                    service = maybe_value
                    break
        if service is None:
            candidate = getattr(runtime, SOLANA_SERVICE_NAME, None)
            if isinstance(candidate, SolanaService):
                service = candidate
        if service:
            await service.stop()

    async def stop_service(self) -> None:
        await self.stop()

    async def stop(self) -> None:
        await self._stop_internal()

    async def _stop_internal(self) -> None:
        self._running = False
        if self._update_task:
            self._update_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._update_task
            self._update_task = None

        # Unsubscribe from accounts
        async with self._subscription_lock:
            subscriptions = list(self.subscriptions.values())
            self.subscriptions.clear()
        for subscription in subscriptions:
            with contextlib.suppress(Exception):
                await self._stop_subscription(subscription)

        if self.connection:
            with contextlib.suppress(Exception):
                await self.connection.close()  # type: ignore[union-attr]
            self.connection = None
        if self._jupiter_task:
            self._jupiter_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._jupiter_task
            self._jupiter_task = None

    # ------------------------------------------------------------------
    # Runtime helpers
    # ------------------------------------------------------------------

    def _resolve_rpc_url(self) -> str:
        runtime_url = self._get_setting("SOLANA_RPC_URL") or self._get_setting("RPC_URL")
        return runtime_url or get_rpc_url()

    def _get_setting(self, key: str) -> Optional[str]:
        if not self.runtime:
            return None
        for attr in ("get_setting", "getSetting", "get"):
            getter = getattr(self.runtime, attr, None)
            if not callable(getter):
                continue
            try:
                value = getter(key)
            except TypeError:
                continue
            if inspect.isawaitable(value):  # pragma: no cover - defensive
                continue
            if value is not None:
                return value
        settings = getattr(self.runtime, "settings", None)
        if isinstance(settings, dict):
            val = settings.get(key)
            if val is not None:
                return val
        return None

    async def _runtime_call(
        self,
        attr_names: Sequence[str],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        if not self.runtime:
            return None
        for name in attr_names:
            func = getattr(self.runtime, name, None)
            if not callable(func):
                continue
            try:
                value = func(*args, **kwargs)
            except TypeError:
                continue
            if inspect.isawaitable(value):
                return await value
            return value
        return None

    async def _locate_runtime_service(self, service_type: str) -> Optional[Any]:
        service = await self._runtime_call(("get_service", "getService", "get"), service_type)
        if service:
            return service
        services_attr = getattr(self.runtime, "services", None)
        if isinstance(services_attr, dict):
            candidate = services_attr.get(service_type)
            if inspect.isawaitable(candidate):
                candidate = await candidate  # type: ignore[assignment]
            if candidate:
                return candidate
        return None

    async def _watch_jupiter_service(self) -> None:
        while True:
            if not self._running:
                return
            try:
                service = await self._locate_runtime_service("JUPITER_SERVICE")
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.debug("Error locating JUPITER_SERVICE: %s", exc)
                service = None
            if service:
                self.jupiter_service = service
                logger.info("Solana service acquired JUPITER_SERVICE integration")
                return
            await asyncio.sleep(1.0)

    async def _get_jupiter_service(self) -> Optional[Any]:
        if self.jupiter_service:
            return self.jupiter_service
        if not self._running:
            return None
        service = await self._locate_runtime_service("JUPITER_SERVICE")
        if service:
            self.jupiter_service = service
        return service

    async def _call_jupiter_service(self, method_name: str, *args: Any, **kwargs: Any) -> Any:
        service = await self._get_jupiter_service()
        if not service:
            return None
        method = getattr(service, method_name, None)
        if not callable(method):
            logger.debug("Jupiter service missing method %s", method_name)
            return None
        try:
            result = method(*args, **kwargs)
            if inspect.isawaitable(result):
                result = await result
            return result
        except Exception as exc:
            logger.debug("Jupiter service call %s failed: %s", method_name, exc)
            return None

    async def _get_runtime_cache(self, key: str) -> Any:
        return await self._runtime_call(("get_cache", "getCache"), key)

    async def _set_runtime_cache(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
    ) -> None:
        for attr in ("set_cache", "setCache"):
            setter = getattr(self.runtime, attr, None) if self.runtime else None
            if callable(setter):
                try:
                    maybe = setter(key, value, ttl_seconds=ttl_seconds)
                except TypeError:
                    try:
                        maybe = setter(key, value)
                    except TypeError:
                        continue
                if inspect.isawaitable(maybe):
                    await maybe
                return

    def _resolve_public_key(self) -> None:
        if self.public_key:
            return
        try:
            result = get_wallet_keypair(runtime=self.runtime, require_private_key=False)
            if result.public_key:
                self.public_key = str(result.public_key)
        except Exception as exc:  # pragma: no cover - optional runtime configuration
            logger.debug("Unable to resolve Solana public key: %s", exc)

    async def _ensure_connection(self) -> AsyncClient:
        if AsyncClient is None:  # pragma: no cover - optional dependency
            raise RuntimeError("Solana dependencies not available: install solana-py")
        if self.connection is None:
            self.connection = AsyncClient(self.rpc_url)
        return self.connection

    async def _wallet_update_loop(self) -> None:
        while self._running:
            try:
                await self.updateWalletData()
            except Exception as exc:  # pragma: no cover - background task resilience
                logger.warning("solana::updateWalletData failed: %s", exc)
            await asyncio.sleep(self.update_interval)

    def getConnection(self) -> Optional[AsyncClient]:
        return self.connection

    def getPublicKey(self) -> Optional[str]:
        self._resolve_public_key()
        return self.public_key

    async def registerExchange(self, provider: Any) -> int:
        self._registry_counter += 1
        provider_id = self._registry_counter
        self.exchange_registry[provider_id] = provider
        logger.info(
            "Registered %s as Solana provider #%s",
            getattr(provider, "name", "provider"),
            provider_id,
        )
        return provider_id

    async def getBalance(
        self,
        address: str,
        *,
        token_address: Optional[str] = None,
        include_tokens: bool = False,
        rpc_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        rpc = rpc_url or self.rpc_url
        return await get_balance_for_address(
            rpc,
            address,
            token_address=token_address,
            include_tokens=include_tokens,
        )

    async def getBalances(
        self,
        addresses: Sequence[str],
        *,
        token_address: Optional[str] = None,
        include_tokens: bool = False,
        rpc_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        rpc = rpc_url or self.rpc_url
        return await get_balances_for_addresses(
            rpc,
            addresses,
            token_address=token_address,
            include_tokens=include_tokens,
        )

    async def getPortfolio(
        self,
        address: str,
        *,
        include_prices: bool = True,
        rpc_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        rpc = rpc_url or self.rpc_url
        return await get_portfolio_overview(
            rpc,
            address,
            include_prices=include_prices,
        )

    async def getPrices(
        self,
        *,
        force_refresh: bool = False,
    ) -> Dict[str, Dict[str, str]]:
        return await fetch_prices_with_cache(force_refresh=force_refresh)

    async def getCirculatingSupply(self, mint: str) -> float:
        if not Pubkey:  # pragma: no cover - optional dependency
            raise RuntimeError("solders dependency not available")
        client = await self._ensure_connection()
        mint_pubkey = Pubkey.from_string(mint)
        try:
            response = await client.get_token_accounts_by_mint(
                mint_pubkey,
                encoding="jsonParsed",
            )
        except Exception as exc:
            logger.error("Error fetching token accounts for mint %s: %s", mint, exc)
            raise

        accounts = self._extract_value(response) or []
        known_excluded = {
            "11111111111111111111111111111111",
            "MINT_AUTHORITY_WALLET",
            "TREASURY_WALLET",
            "BURN_ADDRESS",
        }
        circulating = 0.0
        for account in accounts:
            try:
                info = account["account"]["data"]["parsed"]["info"]
                owner = info.get("owner")
                if owner in known_excluded:
                    continue
                token_amount = info.get("tokenAmount", {})
                ui_amount = token_amount.get("uiAmount")
                decimals = token_amount.get("decimals", 0)
                amount = token_amount.get("amount")
                if ui_amount is not None:
                    value = float(ui_amount)
                elif amount is not None:
                    value = int(amount) / (10 ** decimals)
                else:
                    value = 0.0
                circulating += value
            except Exception:
                continue
        return circulating

    async def birdeyeFetchWithRetry(
        self,
        url: str,
        *,
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        last_error: Optional[Exception] = None
        for attempt in range(MAX_RETRIES):
            try:
                request_headers = {
                    "Accept": "application/json",
                    "x-chain": "solana",
                }
                api_key = self._get_setting("BIRDEYE_API_KEY") or get_api_key("birdeye")
                if api_key:
                    request_headers["X-API-KEY"] = api_key
                if headers:
                    request_headers.update(headers)

                async with httpx.AsyncClient(timeout=30) as client:
                    response = await client.request(
                        method,
                        url,
                        headers=request_headers,
                        params=params,
                        json=json_body,
                    )
                response.raise_for_status()
                return response.json()
            except Exception as exc:
                last_error = exc
                logger.error(
                    "Birdeye request failed (%s/%s): %s",
                    attempt + 1,
                    MAX_RETRIES,
                    exc,
                )
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_DELAY * (2 ** attempt))
        if last_error:
            raise last_error
        return None

    birdeye_fetch_with_retry = birdeyeFetchWithRetry

    async def fetchPrices(self) -> Dict[str, Dict[str, str]]:
        cached = await self._get_runtime_cache(self._PRICE_CACHE_KEY)
        if cached:
            return cached

        tokens = {
            "solana": "So11111111111111111111111111111111111111112",
            "bitcoin": "3NZ9JMVBmGAqocybic2c7LQCJScmgsAZ6vQqTDzcqmJh",
            "ethereum": "7vfCXTUXx5WJV5JADk17DUJ4ksgau7utNKj4b963voxs",
        }
        prices: Dict[str, Dict[str, str]] = {
            "solana": {"usd": "0"},
            "bitcoin": {"usd": "0"},
            "ethereum": {"usd": "0"},
        }

        for key, address in tokens.items():
            try:
                response = await self.birdeyeFetchWithRetry(
                    f"{BIRDEYE_API_BASE_URL}/defi/price",
                    params={"address": address},
                )
            except Exception as exc:
                logger.debug("Failed to fetch price for %s: %s", key, exc)
                continue
            if response and response.get("data") and response["data"].get("value") is not None:
                prices[key]["usd"] = str(response["data"]["value"])

        await self._set_runtime_cache(self._PRICE_CACHE_KEY, prices, ttl_seconds=300)
        return prices

    fetch_prices = fetchPrices

    async def updateWalletData(self, force: bool = False) -> Dict[str, Any]:
        self._resolve_public_key()
        if not self.public_key:
            logger.info("solana::updateWalletData - no Public Key yet")
            return {}

        now = time.time()
        if not force and now - self.last_update < self.update_interval:
            cached = await self.getCachedData()
            if cached:
                return cached

        portfolio = await self._build_portfolio_from_birdeye(self.public_key)
        if portfolio is None:
            portfolio = await self._build_portfolio_from_rpc(self.public_key)

        if portfolio is None:
            return {}

        await self._store_wallet_cache(portfolio)
        self.last_update = now
        return portfolio

    update_wallet_data = updateWalletData

    async def getCachedData(self) -> Optional[Dict[str, Any]]:
        async with self._cache_lock:
            if self._wallet_cache is not None:
                return self._wallet_cache
        cached = await self._get_runtime_cache(SOLANA_WALLET_DATA_CACHE_KEY)
        if cached:
            async with self._cache_lock:
                self._wallet_cache = cached
        return cached

    async def forceUpdate(self) -> Dict[str, Any]:
        return await self.updateWalletData(force=True)

    # ------------------------------------------------------------------
    # Wallet helpers
    # ------------------------------------------------------------------

    async def getWalletKeypair(self) -> Any:
        result = get_wallet_keypair(runtime=self.runtime, require_private_key=True)
        if not result.keypair:
            raise ValueError("Failed to get wallet keypair")
        return result.keypair

    async def createWallet(self, returnPrivateKey: bool = True) -> Dict[str, str]:
        if Keypair is None:  # pragma: no cover - optional dependency
            raise RuntimeError("solders dependency not available to create wallet")
        wallet = Keypair()
        public_key = str(wallet.pubkey())
        result = {
            "publicKey": public_key,
            "address": public_key,
        }
        if returnPrivateKey:
            result["privateKey"] = base58.b58encode(wallet.to_bytes()).decode("utf-8")
        return result

    async def _build_portfolio_from_birdeye(self, wallet_address: str) -> Optional[Dict[str, Any]]:
        api_key = self._get_setting("BIRDEYE_API_KEY") or get_api_key("birdeye")
        if not api_key:
            return None
        url = f"{BIRDEYE_API_BASE_URL}/v1/wallet/token_list?wallet={wallet_address}"
        try:
            response = await self.birdeyeFetchWithRetry(url)
        except Exception as exc:
            logger.debug("Birdeye wallet fetch failed: %s", exc)
            return None

        if not response or not response.get("success") or not response.get("data"):
            return None

        data = response["data"]
        prices = await self.fetchPrices()
        sol_price = Decimal(prices.get("solana", {}).get("usd", "0") or "0")
        total_usd = Decimal(str(data.get("totalUsd", "0")))
        total_sol = str(total_usd / sol_price) if sol_price else "0"

        items: List[Dict[str, Any]] = []
        for item in data.get("items", []):
            symbol = item.get("symbol") or "Unknown"
            decimals = item.get("decimals", 0)
            value_usd = Decimal(str(item.get("valueUsd", "0")))
            value_sol = value_usd / sol_price if sol_price else Decimal(0)
            mint = item.get("address") or item.get("mint") or ""
            balance = item.get("balance") or item.get("amount") or "0"
            ui_amount = item.get("uiAmount") or item.get("balance") or "0"

            items.append({
                "name": item.get("name") or "Unknown",
                "address": mint,
                "mint": mint,
                "symbol": symbol,
                "decimals": decimals,
                "balance": str(balance),
                "uiAmount": str(ui_amount),
                "priceUsd": str(item.get("priceUsd") or "0"),
                "valueUsd": str(value_usd),
                "valueSol": f"{value_sol:.6f}",
            })
            if mint and isinstance(decimals, int):
                self.decimals_cache[mint] = decimals

        portfolio = {
            "address": wallet_address,
            "totalUsd": str(total_usd),
            "totalSol": total_sol,
            "prices": prices,
            "lastUpdated": int(time.time() * 1000),
            "items": items,
        }
        return portfolio

    async def _build_portfolio_from_rpc(self, wallet_address: str) -> Optional[Dict[str, Any]]:
        try:
            from .wallet import SolanaWalletInfoTool  # pylint: disable=import-outside-toplevel
        except Exception as exc:  # pragma: no cover - fallback path
            logger.debug("Wallet info tool unavailable: %s", exc)
            return None

        tool = SolanaWalletInfoTool()
        result = await tool.execute(address=wallet_address, include_tokens=True)
        if result.error:
            logger.debug("Wallet info tool failed: %s", result.error)
            return None

        output = result.output or {}
        tokens = output.get("tokens") or []

        items: List[Dict[str, Any]] = []
        for token in tokens:
            mint = token.get("mint")
            balance = token.get("balance", token.get("ui_amount", 0))
            decimals = token.get("decimals", 0)
            items.append({
                "name": token.get("name") or "Unknown",
                "address": mint,
                "mint": mint,
                "symbol": token.get("symbol") or mint or "Unknown",
                "decimals": decimals,
                "balance": str(balance),
                "uiAmount": balance,
                "priceUsd": "0",
                "valueUsd": "0",
                "valueSol": "0",
            })
            if mint and isinstance(decimals, int):
                self.decimals_cache[mint] = decimals

        portfolio = {
            "address": wallet_address,
            "totalUsd": "0",
            "totalSol": str(output.get("sol_balance", 0)),
            "prices": {},
            "lastUpdated": int(time.time() * 1000),
            "items": items,
        }
        return portfolio

    async def _store_wallet_cache(self, portfolio: Dict[str, Any]) -> None:
        async with self._cache_lock:
            self._wallet_cache = portfolio
        await self._set_runtime_cache(
            SOLANA_WALLET_DATA_CACHE_KEY,
            portfolio,
            ttl_seconds=self.update_interval,
        )

    def isValidSolanaAddress(self, address: str, onCurveOnly: bool = False) -> bool:
        if not validate_solana_address(address):
            return False
        if not onCurveOnly:
            return True
        if not Pubkey:
            return False
        try:
            pubkey = Pubkey.from_string(address)
            return Pubkey.is_on_curve(pubkey.to_bytes())
        except Exception:  # pragma: no cover - defensive
            return False

    def validateAddress(self, address: Optional[str]) -> bool:
        return validate_solana_address(address)

    async def getAddressType(self, address: str) -> str:
        if not validate_solana_address(address):
            return "Invalid address"

        if not Pubkey:
            return "Invalid address"

        try:
            pubkey = Pubkey.from_string(address)
        except Exception:
            return "Invalid address"

        try:
            client = await self._ensure_connection()
            response = await client.get_account_info(pubkey)
        except Exception as exc:
            logger.error("Error fetching account info for %s: %s", address, exc)
            return "Unknown (Data length: -1)"

        account_info = self._extract_value(response)
        if not account_info:
            return "Account does not exist"

        data = getattr(account_info, "data", None)
        data_length = self._decode_account_data_length(data)

        if data_length == 0:
            return "Wallet"
        if data_length == TOKEN_ACCOUNT_DATA_LENGTH:
            return "Token Account"
        if data_length == TOKEN_MINT_DATA_LENGTH:
            return "Token"
        if data_length is not None and data_length >= 0:
            return f"Unknown (Data length: {data_length})"
        return "Unknown"

    def detectPubkeysFromString(self, input_text: str, checkCurve: bool = False) -> List[str]:
        return detect_pubkeys_from_string(input_text, check_curve=checkCurve)

    def detectPrivateKeysFromString(self, input_text: str) -> List[Dict[str, Any]]:
        return detect_private_keys_from_string(input_text)

    def verifySolanaSignature(
        self,
        *,
        message: str,
        signatureBase64: str,
        publicKeyBase58: str,
    ) -> bool:
        return verify_solana_signature(message, signatureBase64, publicKeyBase58)

    def _token_cache_key(self, wallet_address: str) -> str:
        return self._TOKEN_CACHE_TEMPLATE.format(addr=wallet_address)

    async def _get_token_accounts(self) -> List[Any]:
        if not self.public_key:
            return []
        if not Pubkey:
            raise RuntimeError("solders dependency not available")
        return await self.getTokenAccountsByKeypair(Pubkey.from_string(self.public_key))

    async def getTokenAccountsByKeypair(
        self,
        wallet_address: Union[str, Any],
        options: Optional[Dict[str, Any]] = None,
    ) -> List[Any]:
        options = options or {}
        ttl_ms = options.get("ttl", 60_000)
        if isinstance(wallet_address, str):
            wallet_str = wallet_address
            if not Pubkey:
                raise RuntimeError("solders dependency not available")
            owner = Pubkey.from_string(wallet_address)
        else:
            owner = wallet_address
            wallet_str = str(owner)

        cache_key = self._token_cache_key(wallet_str)
        now_ms = int(time.time() * 1000)

        cached = await self._get_runtime_cache(cache_key)
        if cached and ttl_ms != 0:
            fetched_at = cached.get("fetchedAt") or cached.get("timestamp")
            if fetched_at and now_ms - int(fetched_at) < ttl_ms:
                return cached.get("data") or []

        client = await self._ensure_connection()
        try:
            response = await client.get_parsed_token_accounts_by_owner(
                owner,
                program_id=Pubkey.from_string(TOKEN_PROGRAM_ID) if Pubkey else None,
            )
        except Exception as exc:
            logger.error("Error fetching token accounts: %s", exc)
            return []

        accounts = self._extract_value(response) or []
        have_tokens: List[Any] = []
        for account in accounts:
            try:
                info = account["account"]["data"]["parsed"]["info"]
                token_amount = info.get("tokenAmount", {})
                decimals = token_amount.get("decimals", 0)
                amount_str = token_amount.get("amount")
                ui_amount = token_amount.get("uiAmount")
                if ui_amount is not None:
                    balance = float(ui_amount)
                elif amount_str is not None:
                    balance = int(amount_str) / (10 ** decimals)
                else:
                    balance = 0
                if balance > 0:
                    have_tokens.append(account)
                    mint = info.get("mint")
                    if mint and isinstance(decimals, int):
                        self.decimals_cache[mint] = decimals
            except Exception:
                continue

        await self._set_runtime_cache(
            cache_key,
            {"fetchedAt": now_ms, "data": have_tokens},
            ttl_seconds=int(ttl_ms / 1000) if ttl_ms and ttl_ms > 0 else None,
        )
        return have_tokens

    async def getBalancesByAddrs(self, wallet_address_arr: Sequence[str]) -> Union[Dict[str, float], int]:
        if not wallet_address_arr:
            return {}
        if not Pubkey:
            return -1

        try:
            pubkeys = [Pubkey.from_string(addr) for addr in wallet_address_arr]
        except Exception as exc:
            logger.error("Invalid wallet address: %s", exc)
            return -1

        client = await self._ensure_connection()
        try:
            response = await client.get_multiple_accounts(pubkeys)
        except Exception as exc:
            logger.error("Error fetching wallet balances: %s", exc)
            if "429" in str(exc):
                await asyncio.sleep(1)
                return await self.getBalancesByAddrs(wallet_address_arr)
            return -1

        accounts = self._extract_value(response) or []
        result: Dict[str, float] = {}
        for idx, account in enumerate(accounts):
            lamports = None
            if hasattr(account, "lamports"):
                lamports = account.lamports
            elif isinstance(account, dict):
                lamports = account.get("lamports")
            address = wallet_address_arr[idx]
            result[address] = lamports_to_sol(lamports) if lamports else 0.0
        return result

    async def walletAddressToHumanString(self, pub_key: str) -> str:
        balances_future = asyncio.create_task(self.getBalancesByAddrs([pub_key]))
        tokens_future = asyncio.create_task(self.getTokenAccountsByKeypair(pub_key))
        balances = await balances_future
        held_tokens = await tokens_future

        balance_map = balances if isinstance(balances, dict) else {}
        sol_balance = balance_map.get(pub_key, 0.0)
        parsed_tokens = await self.parseTokenAccounts(held_tokens)

        lines = [
            f"Wallet Address: {pub_key}",
            "  Token Address (Symbol)",
            f"  So11111111111111111111111111111111111111111 ($sol) balance: {sol_balance}",
        ]

        for mint, token in parsed_tokens.items():
            lines.append(f"  {mint} (${token.get('symbol', mint)}) balance: {token.get('balanceUi', 0)}")

        lines.append("")
        return "\n".join(lines)

    async def walletAddressToLLMString(self, pub_key: str) -> str:
        balances_future = asyncio.create_task(self.getBalancesByAddrs([pub_key]))
        tokens_future = asyncio.create_task(self.getTokenAccountsByKeypair(pub_key))
        balances = await balances_future
        held_tokens = await tokens_future

        balance_map = balances if isinstance(balances, dict) else {}
        sol_balance = balance_map.get(pub_key, 0.0)
        parsed_tokens = await self.parseTokenAccounts(held_tokens)

        lines = [
            f"Wallet Address: {pub_key}",
            "Current wallet contents in csv format:",
            "Token Address,Symbol,Balance",
            f"So11111111111111111111111111111111111111111,sol,{sol_balance}",
        ]

        for mint, token in parsed_tokens.items():
            lines.append(f"{mint},{token.get('symbol', mint)},{token.get('balanceUi', 0)}")

        lines.append("")
        return "\n".join(lines)

    async def getTokenBalanceForWallets(
        self,
        mint: Union[str, Any],
        wallet_addresses: Sequence[str],
    ) -> Dict[str, float]:
        mint_str = str(mint)
        balances: Dict[str, float] = {}
        for wallet in wallet_addresses:
            accounts = await self.getTokenAccountsByKeypair(wallet, options={"ttl": 0})
            total = 0.0
            for account in accounts:
                try:
                    info = account["account"]["data"]["parsed"]["info"]
                    if info.get("mint") != mint_str:
                        continue
                    token_amount = info.get("tokenAmount", {})
                    decimals = token_amount.get("decimals", 0)
                    ui_amount = token_amount.get("uiAmount")
                    amount = token_amount.get("amount")
                    if ui_amount is not None:
                        value = float(ui_amount)
                    elif amount is not None:
                        value = int(amount) / (10 ** decimals)
                    else:
                        value = 0.0
                    total += value
                except Exception:
                    continue
            balances[wallet] = total
        return balances

    async def getDecimal(self, mint_public_key: Union[str, Any]) -> int:
        mint_str = str(mint_public_key)
        if mint_str in self.decimals_cache:
            return self.decimals_cache[mint_str]

        client = await self._ensure_connection()
        try:
            pubkey = (
                Pubkey.from_string(mint_public_key)
                if isinstance(mint_public_key, str)
                else mint_public_key
            )
        except Exception:
            return -1

        try:
            response = await client.get_parsed_account_info(pubkey)
            value = self._extract_value(response)
            decimals = None
            if value and isinstance(value, dict):
                data = value.get("data")
                if isinstance(data, dict) and data.get("parsed"):
                    parsed = data["parsed"]
                    info = parsed.get("info", {})
                    decimals = info.get("decimals")
            if decimals is None:
                supply = await client.get_token_supply(pubkey)
                supply_value = self._extract_value(supply)
                if isinstance(supply_value, dict):
                    decimals = supply_value.get("decimals")
            if isinstance(decimals, int):
                self.decimals_cache[mint_str] = decimals
                return decimals
        except Exception as exc:
            logger.error("Failed to fetch token decimals: %s", exc)
        return -1

    async def getMetadataAddress(self, mint: Union[str, Any]) -> Optional[str]:
        if not Pubkey:
            return None
        mint_pubkey = Pubkey.from_string(mint) if isinstance(mint, str) else mint
        metadata_program = Pubkey.from_string(METADATA_PROGRAM_ID)
        seeds = [
            b"metadata",
            metadata_program.to_bytes(),
            mint_pubkey.to_bytes(),
        ]
        metadata_pda, _ = Pubkey.find_program_address(seeds, metadata_program)
        return str(metadata_pda)

    async def getTokenSymbol(self, mint: Union[str, Any]) -> Optional[str]:
        metadata_address = await self.getMetadataAddress(mint)
        if not metadata_address or not Pubkey:
            return None

        client = await self._ensure_connection()
        response = await client.get_account_info(Pubkey.from_string(metadata_address))
        value = self._extract_value(response)
        if not value:
            return None

        data = None
        if hasattr(value, "data"):
            data = value.data
        elif isinstance(value, dict):
            data = value.get("data")

        if isinstance(data, (list, tuple)) and data:
            data = data[0]
        if isinstance(data, str):
            import base64  # local import to avoid mandatory dependency
            data = base64.b64decode(data)
        if not isinstance(data, (bytes, bytearray)):
            return None

        try:
            offset = 1 + 32 + 32
            name_len = int.from_bytes(data[offset:offset + 4], "little")
            offset += 4 + name_len
            symbol_len = int.from_bytes(data[offset:offset + 4], "little")
            offset += 4
            symbol = data[offset:offset + symbol_len].decode("utf-8").replace("\x00", "")
            return symbol or None
        except Exception:
            return None

    async def getSupply(self, contract_addresses: Sequence[str]) -> Dict[str, Any]:
        client = await self._ensure_connection()
        results: Dict[str, Any] = {}
        for address in contract_addresses:
            try:
                pubkey = Pubkey.from_string(address) if Pubkey else None
            except Exception:
                results[address] = {"error": "Invalid mint address"}
                continue
            if not pubkey:
                results[address] = {"error": "Invalid mint address"}
                continue
            try:
                response = await client.get_token_supply(pubkey)
                value = self._extract_value(response) or {}
                amount = value.get("amount")
                decimals = value.get("decimals")
                human = None
                if amount is not None and decimals is not None:
                    human = Decimal(amount) / (Decimal(10) ** decimals)
                results[address] = {
                    "supply": int(amount) if amount is not None else None,
                    "decimals": decimals,
                    "human": human,
                }
            except Exception as exc:
                results[address] = {"error": str(exc)}
        return results

    async def parseTokenAccounts(self, held_tokens: Sequence[Any]) -> Dict[str, Dict[str, Any]]:
        results: Dict[str, Dict[str, Any]] = {}
        for token in held_tokens:
            try:
                info = token["account"]["data"]["parsed"]["info"]
                mint = info.get("mint")
                if not mint:
                    continue
                token_amount = info.get("tokenAmount", {})
                decimals = token_amount.get("decimals", 0)
                amount = token_amount.get("amount")
                ui_amount = token_amount.get("uiAmount")
                if ui_amount is not None:
                    balance = float(ui_amount)
                elif amount is not None:
                    balance = int(amount) / (10 ** decimals)
                else:
                    balance = 0.0
                symbol = token.get("symbol") or info.get("tokenSymbol") or mint
                results[mint] = {
                    "symbol": symbol,
                    "decimals": decimals,
                    "balanceUi": balance,
                }
                self.decimals_cache[mint] = decimals
            except Exception:
                continue
        return results

    # ------------------------------------------------------------------
    # Swap helpers
    # ------------------------------------------------------------------

    async def calculateOptimalBuyAmount(
        self,
        inputMint: str,
        outputMint: str,
        availableAmount: Union[int, float],
    ) -> Dict[str, float]:
        amount = float(availableAmount)
        if amount <= 0:
            raise ValueError("availableAmount must be positive")

        if await self._get_jupiter_service():
            amount_arg: Union[int, float] = self._coerce_int_amount(availableAmount) or amount
            price_impact_raw = await self._call_jupiter_service(
                "getPriceImpact",
                inputMint=inputMint,
                outputMint=outputMint,
                amount=amount_arg,
            )
            slippage_raw = await self._call_jupiter_service(
                "findBestSlippage",
                inputMint=inputMint,
                outputMint=outputMint,
                amount=amount_arg,
            )
            price_impact = self._safe_float(price_impact_raw)
            slippage = self._safe_float(slippage_raw)
            if price_impact is not None and slippage is not None:
                optimal_amount = float(amount_arg)
                if price_impact > 5:
                    optimal_amount *= 0.5
                return {"amount": optimal_amount, "slippage": float(slippage)}

        # Basic heuristic when Jupiter service is unavailable or inconclusive
        if amount <= 1:
            slippage = 100  # 1%
        elif amount <= 10:
            slippage = 150
        else:
            slippage = 200
        return {"amount": amount, "slippage": float(slippage)}

    async def calculateOptimalBuyAmount2(
        self,
        quote: Dict[str, Any],
        available_amount: Union[int, float],
    ) -> Dict[str, float]:
        price_impact = self._safe_float(quote.get("priceImpactPct")) or 0.0
        optimal_amount = float(available_amount)
        if price_impact > 5:
            optimal_amount = float(available_amount) * 0.5

        if await self._get_jupiter_service():
            amount_arg: Union[int, float] = self._coerce_int_amount(available_amount) or available_amount
            slippage_raw = await self._call_jupiter_service(
                "findBestSlippage",
                inputMint=quote.get("inputMint"),
                outputMint=quote.get("outputMint"),
                amount=amount_arg,
            )
            slippage_value = self._safe_float(slippage_raw)
            if slippage_value is not None:
                return {
                    "amount": float(optimal_amount),
                    "slippage": float(slippage_value),
                }

        if price_impact < 0.5:
            slippage = 50
        elif price_impact < 1:
            slippage = 100
        else:
            slippage = 200
        return {"amount": optimal_amount, "slippage": slippage}

    async def executeSwap(self, wallets: Sequence[Dict[str, Any]], signal: Any) -> Dict[str, Any]:
        from .swap import SolanaSwapTool  # Local import to avoid circular dependency

        responses: Dict[str, Any] = {}
        swap_tool = SolanaSwapTool()

        input_token = (
            (signal.get("sourceTokenCA") if isinstance(signal, dict) else getattr(signal, "sourceTokenCA", None))
            if signal
            else None
        )
        if not input_token and isinstance(signal, dict):
            input_token = signal.get("inputMint") or signal.get("sourceToken")

        output_token = (
            (signal.get("targetTokenCA") if isinstance(signal, dict) else getattr(signal, "targetTokenCA", None))
            if signal
            else None
        )
        if not output_token and isinstance(signal, dict):
            output_token = signal.get("outputMint") or signal.get("targetToken")

        for wallet in wallets:
            keypair_info = wallet.get("keypair", {}) or {}
            raw_pubkey = keypair_info.get("publicKey")
            pubkey = self._stringify_pubkey(raw_pubkey)
            wallet_label = pubkey or f"wallet_{len(responses)}"
            private_key = keypair_info.get("privateKey")
            amount = wallet.get("amount")

            if not private_key:
                responses[wallet_label] = {"success": False, "error": "private key missing"}
                continue

            amount_float = self._safe_float(amount)
            if amount_float is not None and amount_float <= 0:
                responses[wallet_label] = {"success": False, "error": "amount must be positive"}
                continue

            precheck = await self._run_jupiter_prechecks(
                wallet_address=pubkey,
                amount=amount,
                input_token=input_token,
                output_token=output_token,
            )
            precheck_error = precheck.get("error")
            if precheck_error:
                responses[wallet_label] = {"success": False, "error": precheck_error}
                continue

            slippage_bps = precheck.get("slippage_bps")
            if slippage_bps is not None:
                try:
                    slippage_bps = int(slippage_bps)
                except (TypeError, ValueError):
                    slippage_bps = None
            if slippage_bps is not None and slippage_bps <= 0:
                slippage_bps = None

            try:
                result = await swap_tool.execute(
                    rpc_url=self.rpc_url,
                    private_key=private_key,
                    input_token=input_token,
                    output_token=output_token,
                    amount=amount,
                    slippage_bps=slippage_bps,
                    runtime=self.runtime,
                )
            except Exception as exc:  # pragma: no cover - external dependency
                responses[wallet_label] = {"success": False, "error": str(exc)}
                continue

            if result.error:
                responses[wallet_label] = {"success": False, "error": result.error}
            else:
                payload = dict(result.output or {})
                if precheck.get("sol_balance") is not None:
                    payload.setdefault("sol_balance", precheck["sol_balance"])
                if slippage_bps is not None:
                    payload.setdefault("slippage_bps", slippage_bps)
                if precheck.get("quote") is not None:
                    payload.setdefault("quote", precheck["quote"])
                responses[wallet_label] = {"success": True, **payload}

        return responses

    async def _run_jupiter_prechecks(
        self,
        *,
        wallet_address: Optional[str],
        amount: Any,
        input_token: Optional[str],
        output_token: Optional[str],
    ) -> Dict[str, Any]:
        summary: Dict[str, Any] = {
            "error": None,
            "slippage_bps": None,
            "quote": None,
            "sol_balance": None,
            "available_lamports": None,
        }

        sol_balance = None
        available_lamports = 0
        if wallet_address:
            try:
                balances = await self.getBalancesByAddrs([wallet_address])
            except Exception as exc:  # pragma: no cover - network dependent
                logger.debug("Failed to fetch balances for %s: %s", wallet_address, exc)
                balances = {}
            sol_balance = balances.get(wallet_address)
            summary["sol_balance"] = sol_balance
            if isinstance(sol_balance, (int, float)):
                available_lamports = int(sol_balance * LAMPORTS_PER_SOL)
                summary["available_lamports"] = available_lamports

        if not await self._get_jupiter_service():
            return summary

        if not wallet_address or not input_token or not output_token:
            return summary

        int_amount = self._coerce_int_amount(amount)
        if int_amount is None or int_amount <= 0:
            return summary

        base_needed_raw = await self._call_jupiter_service(
            "estimateLamportsNeeded",
            inputMint=input_token,
            inAmount=int_amount,
        )
        base_needed = self._coerce_int_amount(base_needed_raw)
        if base_needed is not None and available_lamports and base_needed > available_lamports:
            summary["error"] = "not enough SOL"
            return summary

        quote = await self._call_jupiter_service(
            "getQuote",
            inputMint=input_token,
            outputMint=output_token,
            slippageBps=200,
            amount=int_amount,
        )
        if isinstance(quote, dict):
            summary["quote"] = quote
            total_needed = self._safe_float(quote.get("totalLamportsNeeded"))
            if total_needed is not None and available_lamports and total_needed > available_lamports:
                summary["error"] = "not enough SOL"
                return summary

            implied_slippage = self._compute_implied_slippage(quote)
            if implied_slippage is not None:
                summary["slippage_bps"] = max(1, int(implied_slippage))
            else:
                try:
                    optimal = await self.calculateOptimalBuyAmount2(quote, available_amount=int_amount)
                except Exception as exc:  # pragma: no cover - defensive
                    logger.debug("calculateOptimalBuyAmount2 failed: %s", exc)
                    optimal = None
                if isinstance(optimal, dict):
                    slippage_val = self._safe_float(optimal.get("slippage"))
                    if slippage_val is not None:
                        summary["slippage_bps"] = max(1, int(slippage_val))
        return summary

    @staticmethod
    def _decode_account_data_length(data: Any) -> int:
        if data is None:
            return -1

        if isinstance(data, (bytes, bytearray)):
            return len(data)

        if isinstance(data, str):
            try:
                return len(base64.b64decode(data))
            except Exception:
                return -1

        if isinstance(data, (list, tuple)) and data:
            first = data[0]
            if isinstance(first, (bytes, bytearray)):
                return len(first)
            if isinstance(first, str):
                try:
                    return len(base64.b64decode(first))
                except Exception:
                    return -1

        length_attr = getattr(data, "length", None)
        if isinstance(length_attr, int):
            return length_attr

        try:
            return len(data)  # type: ignore[arg-type]
        except Exception:
            return -1

    @staticmethod
    def _compute_implied_slippage(quote: Any) -> Optional[float]:
        if not isinstance(quote, dict):
            return None
        out_amount = SolanaService._safe_float(quote.get("outAmount"))
        other_amount = SolanaService._safe_float(quote.get("otherAmountThreshold"))
        if out_amount is None or other_amount is None or out_amount <= 0:
            return None
        return ((out_amount - other_amount) / out_amount) * 10_000

    @staticmethod
    def _safe_float(value: Any) -> Optional[float]:
        if value is None or isinstance(value, bool):
            return None
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return None
            try:
                return float(stripped)
            except ValueError:
                return None
        return None

    @staticmethod
    def _coerce_int_amount(value: Any) -> Optional[int]:
        if value is None or isinstance(value, bool):
            return None
        if isinstance(value, int):
            return value if value > 0 else None
        if isinstance(value, float):
            if value <= 0:
                return None
            if value.is_integer():
                return int(value)
            return None
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return None
            try:
                return int(stripped)
            except ValueError:
                try:
                    float_val = float(stripped)
                except ValueError:
                    return None
                if float_val <= 0 or not float_val.is_integer():
                    return None
                return int(float_val)
        return None

    @staticmethod
    def _stringify_pubkey(value: Any) -> Optional[str]:
        if value is None:
            return None
        if isinstance(value, str):
            return value
        for attr in ("to_base58", "toBase58", "to_string", "toString"):
            func = getattr(value, attr, None)
            if callable(func):
                try:
                    result = func()
                except Exception:
                    continue
                if isinstance(result, str):
                    return result
        return str(value)

    @staticmethod
    def _normalise_ws_url(rpc_url: str) -> str:
        if rpc_url.startswith(("wss://", "ws://")):
            return rpc_url
        if rpc_url.startswith("https://"):
            return "wss://" + rpc_url[len("https://") :]
        if rpc_url.startswith("http://"):
            return "ws://" + rpc_url[len("http://") :]
        return "wss://api.mainnet-beta.solana.com"

    async def subscribeToAccount(
        self,
        account_address: str,
        handler: Optional[Callable[[str, Any, Any], Union[None, Awaitable[Any]]]] = None,
        *,
        encoding: str = "jsonParsed",
        commitment: str = "finalized",
    ) -> int:
        if not validate_solana_address(account_address):
            raise ValueError("Invalid account address")

        async with self._subscription_lock:
            existing = self.subscriptions.get(account_address)
            if existing:
                if handler:
                    existing.handler = handler
                return existing.subscription_id

        subscription = await self._start_subscription(
            self.rpc_url,
            account_address,
            encoding,
            commitment,
            handler,
        )

        async with self._subscription_lock:
            self.subscriptions[account_address] = subscription
        logger.info("Subscribed to account %s with ID %s", account_address, subscription.subscription_id)
        return subscription.subscription_id

    async def unsubscribeFromAccount(self, account_address: str) -> bool:
        async with self._subscription_lock:
            subscription = self.subscriptions.pop(account_address, None)
        if not subscription:
            logger.warning("No subscription found for account %s", account_address)
            return False
        await self._stop_subscription(subscription)
        return True

    async def _start_subscription(
        self,
        rpc_url: str,
        account_address: str,
        encoding: str,
        commitment: str,
        handler: Optional[Callable[[str, Any, Any], Union[None, Awaitable[Any]]]],
    ) -> _AccountSubscription:
        if solana_ws_connect is None:  # pragma: no cover - optional dependency
            raise RuntimeError("Solana websocket dependencies not available")

        ws_url = self._normalise_ws_url(rpc_url)
        try:
            websocket = await solana_ws_connect(ws_url)
        except Exception as exc:
            raise RuntimeError(f"Failed to connect to WebSocket endpoint {ws_url}: {exc}") from exc

        try:
            response = await websocket.account_subscribe(
                account_address,
                commitment=commitment,
                encoding=encoding,
            )
        except Exception as exc:
            await websocket.close()
            raise RuntimeError(f"Account subscription failed: {exc}") from exc

        subscription_id = getattr(response, "result", None)
        if subscription_id is None and isinstance(response, dict):
            subscription_id = response.get("result")
        if subscription_id is None:
            await websocket.close()
            raise RuntimeError("Account subscription did not return a subscription id")

        subscription = _AccountSubscription(
            account_address=account_address,
            rpc_url=rpc_url,
            ws_url=ws_url,
            websocket=websocket,
            subscription_id=subscription_id,
            encoding=encoding,
            commitment=commitment,
            handler=handler,
        )
        subscription.task = asyncio.create_task(
            self._listen_for_updates(subscription),
            name=f"solana-subscription-{account_address}",
        )
        return subscription

    async def _listen_for_updates(self, subscription: _AccountSubscription) -> None:
        try:
            while True:
                message = await subscription.websocket.recv()
                if isinstance(message, (bytes, bytearray)):
                    try:
                        message = message.decode("utf-8")
                    except Exception:
                        continue
                if isinstance(message, str):
                    try:
                        message = json.loads(message)
                    except json.JSONDecodeError:
                        continue

                if not isinstance(message, dict):
                    continue

                result = message.get("result")
                context = message.get("context") or message.get("params", {}).get("context")
                if isinstance(result, dict):
                    subscription.last_update = result
                    await self._invoke_subscription_handler(subscription, result, context)
                    continue
                params = message.get("params")
                if isinstance(params, dict):
                    param_result = params.get("result")
                    if isinstance(param_result, dict):
                        subscription.last_update = param_result
                        await self._invoke_subscription_handler(subscription, param_result, params.get("context"))
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            subscription.last_error = str(exc)
            logger.error("Account subscription listener error: %s", exc)
        finally:
            with contextlib.suppress(Exception):
                await subscription.websocket.close()
            async with self._subscription_lock:
                self.subscriptions.pop(subscription.account_address, None)

    async def _invoke_subscription_handler(
        self,
        subscription: _AccountSubscription,
        payload: Any,
        context: Any,
    ) -> None:
        if not subscription.handler:
            return
        try:
            result = subscription.handler(subscription.account_address, payload, context)
            if inspect.isawaitable(result):
                await result
        except Exception as exc:
            logger.error("Account subscription handler error: %s", exc)

    async def _stop_subscription(self, subscription: _AccountSubscription) -> None:
        if hasattr(subscription, "task") and subscription.task:
            subscription.task.cancel()
        try:
            await subscription.websocket.account_unsubscribe(subscription.subscription_id)
        except Exception as exc:
            logger.debug("Failed to unsubscribe account %s: %s", subscription.account_address, exc)
        finally:
            with contextlib.suppress(Exception):
                if hasattr(subscription, "task") and subscription.task:
                    await subscription.task

    def _extract_value(self, response: Any) -> Any:
        if response is None:
            return None
        if hasattr(response, "value"):
            return response.value
        if isinstance(response, dict):
            if "result" in response and isinstance(response["result"], dict):
                return response["result"].get("value")
            return response.get("value")
        return response

    async def batchGetMultipleAccountsInfo(
        self,
        pubkeys: Sequence[Union[str, Any]],
        label: str = "",
    ) -> List[Any]:
        if not pubkeys:
            return []
        if not Pubkey:
            raise RuntimeError("solders dependency not available")

        converted = [
            Pubkey.from_string(key) if isinstance(key, str) else key
            for key in pubkeys
        ]
        client = await self._ensure_connection()
        results: List[Any] = []
        for index in range(0, len(converted), 100):
            chunk = converted[index:index + 100]
            response = await client.get_multiple_accounts(chunk)
            value = self._extract_value(response) or []
            results.extend(value)
        return results

    batch_get_multiple_accounts_info = batchGetMultipleAccountsInfo

class _WalletCacheScheduler:
    """Background refresher for wallet portfolio data."""

    UPDATE_INTERVAL = 120

    def __init__(self) -> None:
        self._tasks: Dict[str, asyncio.Task] = {}
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    @staticmethod
    def _cache_key(rpc_url: str, address: str) -> str:
        return f"{rpc_url}::{address.lower()}"

    async def _fetch_wallet_data(self, rpc_url: str, address: str, include_tokens: bool = True) -> Dict[str, Any]:
        return await get_balance_for_address(
            rpc_url,
            address,
            include_tokens=include_tokens,
        )

    async def _refresh_loop(self, key: str, rpc_url: str, address: str, include_tokens: bool) -> None:
        while True:
            try:
                wallet_data = await self._fetch_wallet_data(rpc_url, address, include_tokens)
                async with self._lock:
                    self._cache[key] = {
                        "data": wallet_data,
                        "timestamp": time.time(),
                    }
            except Exception as exc:
                logger.warning("Wallet cache refresh failed for %s: %s", address, exc)
            await asyncio.sleep(self.UPDATE_INTERVAL)

    async def ensure_running(self, rpc_url: str, address: str, include_tokens: bool = True) -> None:
        key = self._cache_key(rpc_url, address)
        async with self._lock:
            if key in self._tasks:
                return
            task = asyncio.create_task(self._refresh_loop(key, rpc_url, address, include_tokens))
            self._tasks[key] = task

    async def get_cached(self, rpc_url: str, address: str) -> Optional[Dict[str, Any]]:
        key = self._cache_key(rpc_url, address)
        async with self._lock:
            return self._cache.get(key)

    async def force_refresh(self, rpc_url: str, address: str, include_tokens: bool = True) -> Dict[str, Any]:
        key = self._cache_key(rpc_url, address)
        wallet_data = await self._fetch_wallet_data(rpc_url, address, include_tokens)
        async with self._lock:
            self._cache[key] = {
                "data": wallet_data,
                "timestamp": time.time(),
            }
        return wallet_data


_wallet_cache_scheduler = _WalletCacheScheduler()


def get_wallet_cache_scheduler() -> _WalletCacheScheduler:
    return _wallet_cache_scheduler
