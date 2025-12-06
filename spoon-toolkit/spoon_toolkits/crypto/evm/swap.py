import os
import asyncio
import logging
from typing import Optional, Dict, Any

import requests
from pydantic import Field

from spoon_ai.tools.base import BaseTool, ToolResult
from .signers import SignerManager

logger = logging.getLogger(__name__)


class EvmSwapTool(BaseTool):
    """Swap tokens on the same EVM chain via Bebop aggregator (with approval handling).

    Note: Token addresses should be provided as 0x-prefixed addresses for reliability.
    """

    name: str = "evm_swap"
    description: str = (
        "Swap tokens on the same EVM chain using Bebop aggregator. Supports local and Turnkey secure signing."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "rpc_url": {"type": "string", "description": "RPC endpoint. Defaults to EVM_PROVIDER_URL/RPC_URL env."},
            "signer_type": {"type": "string", "enum": ["local", "turnkey", "auto"], "description": "Signing method: 'local', 'turnkey', or 'auto'", "default": "auto"},
            "private_key": {"type": "string", "description": "Sender private key (0x-prefixed). Required for local signing. Defaults to EVM_PRIVATE_KEY env."},
            "turnkey_sign_with": {"type": "string", "description": "Turnkey signing identity (address/ID). Required for Turnkey signing. Defaults to TURNKEY_SIGN_WITH env."},
            "turnkey_address": {"type": "string", "description": "Turnkey signer address. Optional for Turnkey signing. Defaults to TURNKEY_ADDRESS env."},
            "from_token": {"type": "string", "description": "Sell token address (0x...) or '0x000..000' for native"},
            "to_token": {"type": "string", "description": "Buy token address (0x...)"},
            "amount": {"type": "string", "description": "Sell amount (decimal)"},
            "slippage_bps": {"type": "integer", "description": "Slippage in basis points (ignored by Bebop)"},
            "gas_price_gwei": {"type": "number", "description": "Optional gas price override in gwei"},
        },
        "required": ["from_token", "to_token", "amount"],
    }

    rpc_url: Optional[str] = Field(default=None)
    signer_type: str = Field(default="auto")
    private_key: Optional[str] = Field(default=None)
    turnkey_sign_with: Optional[str] = Field(default=None)
    turnkey_address: Optional[str] = Field(default=None)
    from_token: Optional[str] = Field(default=None)
    to_token: Optional[str] = Field(default=None)
    amount: Optional[str] = Field(default=None)
    slippage_bps: Optional[int] = Field(default=None)
    gas_price_gwei: Optional[float] = Field(default=None)

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
        signer_type: Optional[str] = None,
        private_key: Optional[str] = None,
        turnkey_sign_with: Optional[str] = None,
        turnkey_address: Optional[str] = None,
        from_token: Optional[str] = None,
        to_token: Optional[str] = None,
        amount: Optional[str] = None,
        slippage_bps: Optional[int] = None,
        gas_price_gwei: Optional[float] = None,
    ) -> ToolResult:
        try:
            rpc_url = rpc_url or self.rpc_url or os.getenv("EVM_PROVIDER_URL") or os.getenv("RPC_URL")
            signer_type = signer_type or self.signer_type
            private_key = private_key or self.private_key
            turnkey_sign_with = turnkey_sign_with or self.turnkey_sign_with
            turnkey_address = turnkey_address or self.turnkey_address
            from_token = from_token or self.from_token
            to_token = to_token or self.to_token
            amount = amount or self.amount
            gas_price_gwei = gas_price_gwei or self.gas_price_gwei

            if not rpc_url:
                return ToolResult(error="Missing rpc_url and no EVM_PROVIDER_URL/RPC_URL set")
            if not from_token or not to_token:
                return ToolResult(error="Missing from_token or to_token")
            if not amount:
                return ToolResult(error="Missing amount")

            try:
                from web3 import Web3, HTTPProvider
            except Exception as e:
                return ToolResult(error=f"web3 dependency not available: {str(e)}")

            w3 = Web3(HTTPProvider(rpc_url))
            if not w3.is_connected():
                return ToolResult(error=f"Failed to connect to RPC: {rpc_url}")

            # Create signer
            try:
                signer = SignerManager.create_signer(
                    signer_type=signer_type,
                    private_key=private_key,
                    turnkey_sign_with=turnkey_sign_with,
                    turnkey_address=turnkey_address
                )
            except Exception as e:
                return ToolResult(error=f"Failed to create signer: {str(e)}")

            signer_address = await signer.get_address()
            chain_id = w3.eth.chain_id

            # Determine decimals for from_token
            decimals = 18
            is_native = (from_token.lower() == "0x0000000000000000000000000000000000000000")
            if not is_native:
                erc20_abi = [{
                    "constant": True,
                    "inputs": [],
                    "name": "decimals",
                    "outputs": [{"name": "", "type": "uint8"}],
                    "payable": False,
                    "stateMutability": "view",
                    "type": "function",
                }]
                token_contract = w3.eth.contract(address=Web3.to_checksum_address(from_token), abi=erc20_abi)
                try:
                    decimals = int(token_contract.functions.decimals().call())
                except Exception:
                    decimals = 18

            sell_amount = int(float(amount) * (10 ** decimals))

            chain_key = self._BEBOP_CHAIN_MAP.get(chain_id)
            if not chain_key:
                return ToolResult(error=f"Unsupported chain for Bebop: {chain_id}")

            url = f"https://api.bebop.xyz/router/{chain_key}/v1/quote"
            params = {
                "sell_tokens": Web3.to_checksum_address(from_token) if not is_native else from_token,
                "buy_tokens": Web3.to_checksum_address(to_token),
                "sell_amounts": str(sell_amount),
                "taker_address": signer_address,
                "approval_type": "Standard",
                "skip_validation": "true",
                "gasless": "false",
                "source": "spoonai",
            }

            try:
                response = requests.get(url, params=params, timeout=30)
            except Exception as e:
                return ToolResult(error=f"Failed to request Bebop quote: {str(e)}")

            if response.status_code != 200:
                return ToolResult(error=f"Bebop API error: {response.status_code} {response.text}")

            data: Dict[str, Any] = response.json()
            routes = data.get("routes", [])
            if not routes:
                return ToolResult(error="No routes found from Bebop")

            route = routes[0]
            quote = route.get("quote", {})
            tx = quote.get("tx") or {}
            approval_target = quote.get("approvalTarget")

            if not tx or not tx.get("to") or not tx.get("data"):
                return ToolResult(error="Invalid Bebop route structure")

            # Approve if ERC20
            if not is_native and approval_target:
                allowance_abi = [{
                    "constant": True,
                    "inputs": [
                        {"name": "owner", "type": "address"},
                        {"name": "spender", "type": "address"}
                    ],
                    "name": "allowance",
                    "outputs": [{"name": "", "type": "uint256"}],
                    "payable": False,
                    "stateMutability": "view",
                    "type": "function",
                }, {
                    "constant": False,
                    "inputs": [
                        {"name": "spender", "type": "address"},
                        {"name": "value", "type": "uint256"}
                    ],
                    "name": "approve",
                    "outputs": [{"name": "", "type": "bool"}],
                    "payable": False,
                    "stateMutability": "nonpayable",
                    "type": "function",
                }]
                token_contract = w3.eth.contract(address=Web3.to_checksum_address(from_token), abi=allowance_abi)
                current_allowance = token_contract.functions.allowance(signer_address, Web3.to_checksum_address(approval_target)).call()
                if current_allowance < sell_amount:
                    approve_tx = token_contract.functions.approve(Web3.to_checksum_address(approval_target), sell_amount)
                    tx_dict = approve_tx.build_transaction({
                        "from": signer_address,
                        "nonce": w3.eth.get_transaction_count(signer_address),
                        "gas": 120000,
                        "chainId": chain_id,
                    })
                    if gas_price_gwei is not None:
                        tx_dict["gasPrice"] = w3.to_wei(gas_price_gwei, "gwei")
                    else:
                        try:
                            tx_dict["gasPrice"] = w3.eth.gas_price
                        except Exception:
                            pass
                    signed_hex = await signer.sign_transaction(tx_dict, rpc_url)
                    tx_hash = w3.eth.send_raw_transaction(bytes.fromhex(signed_hex[2:]) if signed_hex.startswith("0x") else bytes.fromhex(signed_hex))

                    def wait_receipt():
                        return w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

                    loop = asyncio.get_event_loop()
                    receipt = await loop.run_in_executor(None, wait_receipt)
                    if getattr(receipt, "status", 1) == 0:
                        return ToolResult(error=f"Approval failed: {tx_hash.hex()}")

            # Execute swap transaction
            send_tx = {
                "to": Web3.to_checksum_address(tx["to"]),
                "from": signer_address,
                "data": tx.get("data", "0x"),
                "value": int(tx.get("value") or 0),
                "nonce": w3.eth.get_transaction_count(signer_address),
                "chainId": chain_id,
            }
            # Estimate gas or set from suggested
            try:
                send_tx["gas"] = int(tx.get("gas") or 0) or w3.eth.estimate_gas({**send_tx, "from": account.address})
            except Exception:
                send_tx["gas"] = int(1.2 * 300000)
            if gas_price_gwei is not None:
                send_tx["gasPrice"] = w3.to_wei(gas_price_gwei, "gwei")
            else:
                try:
                    # Use tx gas price if provided
                    if tx.get("gasPrice"):
                        send_tx["gasPrice"] = int(tx["gasPrice"])
                    else:
                        send_tx["gasPrice"] = w3.eth.gas_price
                except Exception:
                    pass

            signed_hex = await signer.sign_transaction(send_tx, rpc_url)
            swap_hash = w3.eth.send_raw_transaction(bytes.fromhex(signed_hex[2:]) if signed_hex.startswith("0x") else bytes.fromhex(signed_hex))

            def wait_swap_receipt():
                return w3.eth.wait_for_transaction_receipt(swap_hash, timeout=180)

            loop = asyncio.get_event_loop()
            swap_receipt = await loop.run_in_executor(None, wait_swap_receipt)
            if getattr(swap_receipt, "status", 1) == 0:
                return ToolResult(error=f"Swap reverted: {swap_hash.hex()}")

            return ToolResult(
                output={
                    "hash": swap_hash.hex(),
                    "from": signer_address,
                    "to": send_tx["to"],
                    "value": str(send_tx["value"]),
                    "chainId": chain_id,
                    "signer_type": signer.signer_type,
                }
            )
        except Exception as e:
            logger.error(f"EvmSwapTool error: {e}")
            return ToolResult(error=f"Swap failed: {str(e)}")


