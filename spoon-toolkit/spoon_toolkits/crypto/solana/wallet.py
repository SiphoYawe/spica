"""Solana wallet management tools"""

import inspect
import logging
from decimal import InvalidOperation, ROUND_HALF_UP
from typing import Any, Dict, List, Optional

from pydantic import Field
from solders.keypair import Keypair

from .bignumber import BigNumber, toBN
from .constants import SOLANA_SERVICE_NAME, SOLANA_WALLET_DATA_CACHE_KEY
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from spoon_ai.tools.base import BaseTool, ToolResult
from .service import (
    get_rpc_url,
    get_wallet_cache_scheduler,
    truncate_address,
    validate_solana_address,
)
from .keypairUtils import get_wallet_keypair

logger = logging.getLogger(__name__)  

class SolanaWalletInfoTool(BaseTool):
    name: str = "solana_wallet_info"
    description: str = "Get comprehensive wallet information including balance and tokens"
    parameters: dict = {
        "type": "object",
        "properties": {
            "rpc_url": {
                "type": "string",
                "description": "Solana RPC endpoint URL"
            },
            "address": {
                "type": "string",
                "description": "Wallet address to query. If omitted, uses configured wallet."
            },
            "include_tokens": {
                "type": "boolean",
                "description": "Include SPL token balances",
                "default": True
            },
            "token_limit": {
                "type": "integer",
                "description": "Maximum number of tokens to include",
                "default": 20
            }
        },
        "required": [],
    }  

    rpc_url: Optional[str] = Field(default=None)
    address: Optional[str] = Field(default=None)
    include_tokens: bool = Field(default=True)
    token_limit: int = Field(default=20)  

    async def execute(
        self,
        rpc_url: Optional[str] = None,
        address: Optional[str] = None,
        include_tokens: bool = True,
        token_limit: int = 20
    ) -> ToolResult:
        """Execute wallet info query."""
        try:
            # Resolve parameters
            rpc_url = rpc_url or self.rpc_url or get_rpc_url()
            address = address or self.address
            include_tokens = include_tokens if include_tokens is not None else self.include_tokens
            token_limit = token_limit if token_limit is not None else self.token_limit  

            if not address:
                try:
                    keypair_result = get_wallet_keypair(require_private_key=False)
                    if keypair_result.public_key:
                        address = str(keypair_result.public_key)
                    else:
                        return ToolResult(error="No address provided and no wallet configured")
                except Exception:
                    return ToolResult(error="No address provided and no wallet configured")  

            if not validate_solana_address(address):
                return ToolResult(error=f"Invalid wallet address: {address}")  

            scheduler = get_wallet_cache_scheduler()
            await scheduler.ensure_running(rpc_url, address, include_tokens)
            cached = await scheduler.get_cached(rpc_url, address)  

            if cached and cached.get("data"):
                wallet_data = cached["data"]
            else:
                wallet_data = await scheduler.force_refresh(rpc_url, address, include_tokens)
            result = {
                "address": address,
                "truncated_address": truncate_address(address),
                "sol_balance": wallet_data.get("sol_balance", 0),
                "lamports": wallet_data.get("lamports", 0),
                "token_count": 0,
                "tokens": []
            }  

            # Process token balances
            if include_tokens and "token_balances" in wallet_data:
                tokens = wallet_data["token_balances"][:token_limit]
                result["token_count"] = len(wallet_data["token_balances"])
                result["tokens"] = []  

                for token in tokens:
                    result["tokens"].append({
                        "mint": token["mint"],
                        "balance": token["ui_amount"],
                        "decimals": token["decimals"],
                        "raw_balance": token["balance"]
                    })  

            return ToolResult(output=result)  

        except Exception as e:
            logger.error(f"SolanaWalletInfoTool error: {e}")
            return ToolResult(error=f"Wallet info query failed: {str(e)}")  

async def wallet_provider(
    runtime: Any,
    _message: Any = None,
    state: Any = None,
) -> Dict[str, Any]:
    """Provide Solana wallet context aligned with the TypeScript provider."""
    try:
        portfolio = await _runtime_get_cache(runtime, SOLANA_WALLET_DATA_CACHE_KEY)
        if not portfolio:
            logger.info("solana::wallet provider - portfolio cache is not ready")
            return {"data": None, "values": {}, "text": ""}

        agent_name = _get_agent_name(runtime, state)

        public_key_str = ""
        try:
            keypair_result = get_wallet_keypair(runtime=runtime, require_private_key=False)
            if keypair_result.public_key:
                if _runtime_has_service(runtime, "solana", SOLANA_SERVICE_NAME):
                    public_key_str = f" ({str(keypair_result.public_key)})"
        except Exception:
            logger.debug("solana::wallet provider - unable to resolve public key", exc_info=True)

        total_usd = _format_decimal(portfolio.get("totalUsd"), precision="0.01", default="0.00")
        total_sol_raw = portfolio.get("totalSol")
        total_sol = str(total_sol_raw) if total_sol_raw is not None else "0"

        values: Dict[str, str] = {
            "total_usd": total_usd,
            "total_sol": total_sol,
        }

        items = portfolio.get("items") or []
        non_zero_items = []
        for item in items:
            amount = _to_decimal(item.get("uiAmount") or item.get("balance") or 0)
            if amount > 0:
                non_zero_items.append((item, amount))

        for index, (item, amount) in enumerate(non_zero_items):
            values[f"token_{index}_name"] = item.get("name") or "Unknown"
            values[f"token_{index}_symbol"] = item.get("symbol") or ""
            values[f"token_{index}_amount"] = _format_decimal(amount, precision="0.000001", default="0")
            values[f"token_{index}_usd"] = _format_decimal(item.get("valueUsd"), precision="0.01", default="0.00")
            value_sol_raw = item.get("valueSol")
            values[f"token_{index}_sol"] = str(value_sol_raw) if value_sol_raw is not None else "0"

        prices = portfolio.get("prices") or {}
        if isinstance(prices, dict) and prices:
            sol_price = prices.get("solana", {}).get("usd")
            btc_price = prices.get("bitcoin", {}).get("usd")
            eth_price = prices.get("ethereum", {}).get("usd")
            if sol_price is not None:
                values["sol_price"] = _format_decimal(sol_price, precision="0.01", default="0.00")
            if btc_price is not None:
                values["btc_price"] = _format_decimal(btc_price, precision="0.01", default="0.00")
            if eth_price is not None:
                values["eth_price"] = _format_decimal(eth_price, precision="0.01", default="0.00")

        text_lines = [
            "",
            "",
            f"{agent_name}'s Main Solana Wallet{public_key_str}",
            f"Total Value: ${values['total_usd']} ({values['total_sol']} SOL)",
            "",
            "Token Balances:",
        ]

        if not non_zero_items:
            text_lines.append("No tokens found with non-zero balance")
        else:
            for item, amount in non_zero_items:
                name = item.get("name") or "Unknown"
                symbol = item.get("symbol") or ""
                amount_str = _format_decimal(amount, precision="0.000001", default="0")
                usd_value = _format_decimal(item.get("valueUsd"), precision="0.01", default="0.00")
                value_sol_raw = item.get("valueSol")
                value_sol = str(value_sol_raw) if value_sol_raw is not None else "0"
                text_lines.append(f"{name} ({symbol}): {amount_str} (${usd_value} | {value_sol} SOL)")

        if {"sol_price", "btc_price", "eth_price"} & values.keys():
            text_lines.append("")
            text_lines.append("Market Prices:")
            if "sol_price" in values:
                text_lines.append(f"SOL: ${values['sol_price']}")
            if "btc_price" in values:
                text_lines.append(f"BTC: ${values['btc_price']}")
            if "eth_price" in values:
                text_lines.append(f"ETH: ${values['eth_price']}")

        text = "\n".join(text_lines)

        return {
            "data": portfolio,
            "values": values,
            "text": text,
        }
    except Exception as exc:
        logger.error("Error in Solana wallet provider: %s", exc, exc_info=True)
        return {"data": None, "values": {}, "text": ""}

def _format_decimal(value: Any, precision: str = "0.01", default: str = "0") -> str:
    """Format arbitrary numeric input using BigNumber with fixed precision."""
    try:
        decimal_value = toBN(value)
        quantizer = toBN(precision)
        formatted = decimal_value.quantize(quantizer, rounding=ROUND_HALF_UP)
    except (InvalidOperation, TypeError, ValueError):
        return default
    return format(formatted, "f")


def _to_decimal(value: Any) -> BigNumber:
    """Best-effort conversion into a BigNumber, returning zero on failure."""
    try:
        return toBN(value)
    except (InvalidOperation, TypeError, ValueError):
        return toBN(0)


async def _runtime_get_cache(runtime: Any, key: str) -> Any:
    """Retrieve a cache value from the runtime using either sync or async getters."""
    if runtime is None:
        return None

    for attr in ("get_cache", "getCache"):
        getter = getattr(runtime, attr, None)
        if callable(getter):
            try:
                result = getter(key)
            except TypeError:
                continue
            if inspect.isawaitable(result):
                return await result
            return result

    cache_attr = getattr(runtime, "cache", None)
    if isinstance(cache_attr, dict):
        return cache_attr.get(key)
    return None


def _get_agent_name(runtime: Any, state: Any) -> str:
    """Extract a human-readable agent name from runtime or state."""
    if state is not None:
        if isinstance(state, dict):
            for key in ("agent_name", "agentName"):
                value = state.get(key)
                if value:
                    return str(value)
        for key in ("agent_name", "agentName"):
            value = getattr(state, key, None)
            if value:
                return str(value)

    if runtime is not None:
        character = getattr(runtime, "character", None)
        if character and getattr(character, "name", None):
            return str(character.name)
        agent = getattr(runtime, "agent", None)
        if agent and getattr(agent, "name", None):
            return str(agent.name)
        name = getattr(runtime, "name", None)
        if name:
            return str(name)

    return "The agent"


def _runtime_has_service(runtime: Any, *service_names: str) -> bool:
    """Check whether the runtime exposes any of the requested services."""
    if runtime is None:
        return False

    for service_name in service_names:
        for attr in ("get_service", "getService", "get"):
            getter = getattr(runtime, attr, None)
            if callable(getter):
                try:
                    service = getter(service_name)
                except TypeError:
                    continue
                if service:
                    return True
        services_attr = getattr(runtime, "services", None)
        if isinstance(services_attr, dict) and services_attr.get(service_name):
            return True
    return False
