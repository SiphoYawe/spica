import os
import logging
from typing import Optional, Dict, Any, List

import requests
from pydantic import Field

from spoon_ai.tools.base import BaseTool, ToolResult

logger = logging.getLogger(__name__)


class EvmSwapQuoteTool(BaseTool):
    """Get a swap quote (expected output and tx data) without executing the swap.

    Uses Bebop aggregator to fetch a route and returns the minimum output and tx info.
    """

    name: str = "evm_swap_quote"
    description: str = (
        "Fetch a swap quote on the same EVM chain via aggregator(s). "
        "Supports Bebop and LiFi; can compare both and return best."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "rpc_url": {"type": "string", "description": "RPC endpoint; used to infer chain id when chain_id omitted"},
            "chain_id": {"type": "integer", "description": "EVM chain id (e.g., 1, 8453). Overrides rpc_url inference"},
            "from_token": {"type": "string", "description": "Sell token address (0x...) or zero-address for native"},
            "to_token": {"type": "string", "description": "Buy token address (0x...)"},
            "amount": {"type": "string", "description": "Sell amount in decimal units"},
            "aggregator": {
                "type": "string",
                "description": "Aggregator to use: 'bebop' | 'lifi' | 'both'",
                "enum": ["bebop", "lifi", "both"],
                "default": "both"
            },
            "slippage": {
                "type": "number",
                "description": "Optional slippage (e.g., 0.005 for 0.5%) used for LiFi",
                "default": 0.005
            },
            "taker_address": {
                "type": "string",
                "description": "Optional taker address for Bebop quotes. Uses default if not provided.",
                "default": None
            }
        },
        "required": ["from_token", "to_token", "amount"],
    }

    rpc_url: Optional[str] = Field(default=None)
    chain_id: Optional[int] = Field(default=None)
    from_token: Optional[str] = Field(default=None)
    to_token: Optional[str] = Field(default=None)
    amount: Optional[str] = Field(default=None)
    aggregator: str = Field(default="both")
    slippage: float = Field(default=0.005)
    taker_address: Optional[str] = Field(default=None)

    _BEBOP_CHAIN_MAP: Dict[int, str] = {
        1: "ethereum",
        10: "optimism",
        137: "polygon",
        42161: "arbitrum",
        8453: "base",
        59144: "linea",
    }

    async def execute(
        self,
        rpc_url: Optional[str] = None,
        chain_id: Optional[int] = None,
        from_token: Optional[str] = None,
        to_token: Optional[str] = None,
        amount: Optional[str] = None,
        aggregator: Optional[str] = None,
        slippage: Optional[float] = None,
        taker_address: Optional[str] = None,
    ) -> ToolResult:
        try:
            rpc_url = rpc_url or self.rpc_url or os.getenv("EVM_PROVIDER_URL") or os.getenv("RPC_URL")
            chain_id = chain_id or self.chain_id
            from_token = from_token or self.from_token
            to_token = to_token or self.to_token
            amount = amount or self.amount
            aggregator = (aggregator or self.aggregator or "both").lower()
            slippage = slippage if slippage is not None else self.slippage
            taker_address = taker_address or self.taker_address

            if not from_token or not to_token or not amount:
                return ToolResult(error="Missing from_token/to_token/amount")

            # Resolve chain id via rpc if not provided
            if chain_id is None:
                if not rpc_url:
                    return ToolResult(error="Provide rpc_url or chain_id to infer chain")
                try:
                    from web3 import Web3, HTTPProvider
                    w3 = Web3(HTTPProvider(rpc_url))
                    if not w3.is_connected():
                        return ToolResult(error=f"Failed to connect to RPC: {rpc_url}")
                    chain_id = w3.eth.chain_id
                except Exception as e:
                    return ToolResult(error=f"web3 init failed: {str(e)}")

            # Determine decimals for from_token to build sell_amounts
            decimals = 18
            is_native = (from_token.lower() == "0x0000000000000000000000000000000000000000")
            if not is_native:
                try:
                    from web3 import Web3, HTTPProvider
                    if rpc_url is None:
                        return ToolResult(error="rpc_url required to resolve ERC20 decimals")
                    w3 = Web3(HTTPProvider(rpc_url))
                    token_contract = w3.eth.contract(address=Web3.to_checksum_address(from_token), abi=[
                        {
                            "constant": True,
                            "inputs": [],
                            "name": "decimals",
                            "outputs": [{"name": "", "type": "uint8"}],
                            "type": "function",
                        }
                    ])
                    decimals = int(token_contract.functions.decimals().call())
                except Exception:
                    decimals = 18

            sell_amount = int(float(amount) * (10 ** decimals))
            quotes: List[Dict[str, Any]] = []

            if aggregator in ("bebop", "both"):
                chain_key = self._BEBOP_CHAIN_MAP.get(chain_id)
                if chain_key:
                    try:
                        bebop = self._get_bebop_quote(chain_key, from_token, to_token, sell_amount, taker_address)
                        #bebop api missing taker address
                        quotes.append(bebop)
                    except Exception as e:
                        logger.warning(f"Bebop quote failed: {e}")
                else:
                    logger.warning(f"Unsupported chain id for Bebop: {chain_id}")

            if aggregator in ("lifi", "both"):
                try:
                    lifi = self._get_lifi_quote(chain_id, from_token, to_token, sell_amount, slippage)
                    quotes.append(lifi)
                except Exception as e:
                    logger.warning(f"LiFi quote failed: {e}")

            if not quotes:
                return ToolResult(error="No quotes available")

            # Pick best by min_output_amount (as int, default 0)
            def to_int(x: Optional[str]) -> int:
                try:
                    return int(x) if x is not None else 0
                except Exception:
                    return 0

            best = max(quotes, key=lambda q: to_int(q.get("min_output_amount")))
            return ToolResult(output={
                "chain_id": chain_id,
                "sell_amount": str(sell_amount),
                "quotes": quotes,
                "best": best,
            })
        except Exception as e:
            logger.error(f"EvmSwapQuoteTool error: {e}")
            return ToolResult(error=f"Swap quote failed: {str(e)}")

    def _get_bebop_quote(self, chain_key: str, from_token: str, to_token: str, sell_amount: int, taker_address: str = None) -> Dict[str, Any]:
        url = f"https://api.bebop.xyz/router/{chain_key}/v1/quote"
        params = {
            "sell_tokens": from_token,
            "buy_tokens": to_token,
            "sell_amounts": str(sell_amount),
            "approval_type": "Standard",
            "skip_validation": "true",
            "gasless": "false",
            "source": "spoonai",
        }

        # Add taker_address if provided
        if taker_address:
            params["taker_address"] = taker_address    
        resp = requests.get(url, params=params, timeout=30)
        if resp.status_code != 200:
            raise RuntimeError(f"Bebop API error: {resp.status_code} {resp.text}")
        data: Dict[str, Any] = resp.json()
        routes = data.get("routes", [])
        if not routes:
            raise RuntimeError("No routes returned")
        route = routes[0]
        q = route.get("quote", {})
        tx = q.get("tx") or {}
        buy_tokens = q.get("buyTokens") or {}
        min_out = (buy_tokens.get(to_token) or buy_tokens.get(to_token.lower()) or {}).get("minimumAmount")
        return {
            "aggregator": "bebop",
            "min_output_amount": str(min_out) if min_out is not None else None,
            "tx": tx,
            "approval_target": q.get("approvalTarget"),
        }

    def _get_lifi_quote(self, chain_id: int, from_token: str, to_token: str, sell_amount: int, slippage: float) -> Dict[str, Any]:
        url = "https://li.quest/v1/advanced/routes"
        payload = {
            "fromChainId": chain_id,
            "toChainId": chain_id,
            "fromTokenAddress": from_token,
            "toTokenAddress": to_token,
            "fromAmount": str(sell_amount),
            "options": {"slippage": slippage},
        }
        resp = requests.post(url, json=payload, timeout=45)
        if resp.status_code != 200:
            raise RuntimeError(f"LiFi API error: {resp.status_code} {resp.text}")
        data: Dict[str, Any] = resp.json()
        routes = data.get("routes", []) or data.get("data", {}).get("routes", [])
        if not routes:
            raise RuntimeError("No LiFi routes returned")
        route = routes[0]
        steps = route.get("steps", [])
        if not steps:
            raise RuntimeError("LiFi route missing steps")
        estimate = (steps[0].get("estimate") or {})
        min_out = estimate.get("toAmountMin")
        return {
            "aggregator": "lifi",
            "min_output_amount": str(min_out) if min_out is not None else None,
            "route": {"fromChainId": route.get("fromChainId"), "toChainId": route.get("toChainId")},
        }


