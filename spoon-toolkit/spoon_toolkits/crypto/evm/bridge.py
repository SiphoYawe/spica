import os
import asyncio
import logging
from typing import Optional, Dict, Any

import requests
from pydantic import Field

from spoon_ai.tools.base import BaseTool, ToolResult
from .signers import SignerManager

logger = logging.getLogger(__name__)


class EvmBridgeTool(BaseTool):
    """Bridge tokens across EVM chains via LiFi REST API.

    Note: This uses LiFi's public API to fetch a route and its transactionRequest for the first step,
    then executes it locally with web3.py.
    """

    name: str = "evm_bridge"
    description: str = (
        "Bridge tokens across EVM chains using LiFi. Supports local and Turnkey secure signing."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "rpc_url": {"type": "string", "description": "RPC endpoint. Defaults to EVM_PROVIDER_URL/RPC_URL env."},
            "signer_type": {"type": "string", "enum": ["local", "turnkey", "auto"], "description": "Signing method: 'local', 'turnkey', or 'auto'", "default": "auto"},
            "private_key": {"type": "string", "description": "Sender private key (0x-prefixed). Required for local signing. Defaults to EVM_PRIVATE_KEY env."},
            "turnkey_sign_with": {"type": "string", "description": "Turnkey signing identity (address/ID). Required for Turnkey signing. Defaults to TURNKEY_SIGN_WITH env."},
            "turnkey_address": {"type": "string", "description": "Turnkey signer address. Optional for Turnkey signing. Defaults to TURNKEY_ADDRESS env."},
            "from_chain_id": {"type": "integer", "description": "Source chain ID"},
            "to_chain_id": {"type": "integer", "description": "Destination chain ID"},
            "from_token": {"type": "string", "description": "Source token address (0x...) or zero for native"},
            "to_token": {"type": "string", "description": "Destination token address (0x...)"},
            "amount": {"type": "string", "description": "Amount (decimal) in source token units"},
            "to_address": {"type": "string", "description": "Recipient address on destination chain; default sender"},
            "gas_price_gwei": {"type": "number", "description": "Optional gas price override in gwei"},
            "slippage": {"type": "number", "description": "Optional slippage (e.g., 0.005 for 0.5%)", "default": 0.005},
        },
        "required": ["from_chain_id", "to_chain_id", "from_token", "to_token", "amount"],
    }

    rpc_url: Optional[str] = Field(default=None)
    signer_type: str = Field(default="auto")
    private_key: Optional[str] = Field(default=None)
    turnkey_sign_with: Optional[str] = Field(default=None)
    turnkey_address: Optional[str] = Field(default=None)
    from_chain_id: Optional[int] = Field(default=None)
    to_chain_id: Optional[int] = Field(default=None)
    from_token: Optional[str] = Field(default=None)
    to_token: Optional[str] = Field(default=None)
    amount: Optional[str] = Field(default=None)
    to_address: Optional[str] = Field(default=None)
    gas_price_gwei: Optional[float] = Field(default=None)
    slippage: float = Field(default=0.005)

    _LIFI_BASE = "https://li.quest/v1"

    async def execute(
        self,
        rpc_url: Optional[str] = None,
        signer_type: Optional[str] = None,
        private_key: Optional[str] = None,
        turnkey_sign_with: Optional[str] = None,
        turnkey_address: Optional[str] = None,
        from_chain_id: Optional[int] = None,
        to_chain_id: Optional[int] = None,
        from_token: Optional[str] = None,
        to_token: Optional[str] = None,
        amount: Optional[str] = None,
        to_address: Optional[str] = None,
        gas_price_gwei: Optional[float] = None,
        slippage: Optional[float] = None,
    ) -> ToolResult:
        try:
            rpc_url = rpc_url or self.rpc_url or os.getenv("EVM_PROVIDER_URL") or os.getenv("RPC_URL")
            signer_type = signer_type or self.signer_type
            private_key = private_key or self.private_key
            turnkey_sign_with = turnkey_sign_with or self.turnkey_sign_with
            turnkey_address = turnkey_address or self.turnkey_address
            from_chain_id = from_chain_id or self.from_chain_id
            to_chain_id = to_chain_id or self.to_chain_id
            from_token = from_token or self.from_token
            to_token = to_token or self.to_token
            amount = amount or self.amount
            to_address = to_address or self.to_address
            slippage = slippage if slippage is not None else self.slippage
            gas_price_gwei = gas_price_gwei or self.gas_price_gwei

            if not rpc_url:
                return ToolResult(error="Missing rpc_url and no EVM_PROVIDER_URL/RPC_URL set")
            if not all([from_chain_id, to_chain_id, from_token, to_token, amount]):
                return ToolResult(error="Missing required parameters for bridge")

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

            from_amount = int(float(amount) * (10 ** decimals))

            # Resolve recipient address
            to_address = to_address or signer_address

            # Get LiFi routes
            params = {
                "fromChainId": from_chain_id,
                "toChainId": to_chain_id,
                "fromTokenAddress": from_token,
                "toTokenAddress": to_token,
                "fromAmount": str(from_amount),
                "fromAddress": signer_address,
                "toAddress": to_address,
                "options": {"slippage": slippage, "order": "RECOMMENDED"},
            }
            try:
                routes_resp = requests.post(f"{self._LIFI_BASE}/advanced/routes", json=params, timeout=45)
            except Exception as e:
                return ToolResult(error=f"Failed to fetch LiFi routes: {str(e)}")

            if routes_resp.status_code != 200:
                return ToolResult(error=f"LiFi routes error: {routes_resp.status_code} {routes_resp.text}")

            routes_json: Dict[str, Any] = routes_resp.json()
            routes = routes_json.get("routes", []) or routes_json.get("data", {}).get("routes", [])
            if not routes:
                return ToolResult(error="No bridge routes found")

            route = routes[0]
            steps = route.get("steps", [])
            if not steps:
                return ToolResult(error="No steps in LiFi route")

            # Get step transaction request
            step = steps[0]
            try:
                step_tx_resp = requests.post(f"{self._LIFI_BASE}/advanced/stepTransaction", json=step, timeout=45)
            except Exception as e:
                return ToolResult(error=f"Failed to get step transaction: {str(e)}")

            if step_tx_resp.status_code != 200:
                return ToolResult(error=f"LiFi step tx error: {step_tx_resp.status_code} {step_tx_resp.text}")

            step_tx = step_tx_resp.json().get("transactionRequest")
            if not step_tx:
                return ToolResult(error="Missing transactionRequest in LiFi step response")

            # Approve ERC20 if needed
            if not is_native:
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
                spender = step_tx.get("to")
                allowance = token_contract.functions.allowance(signer_address, Web3.to_checksum_address(spender)).call()
                if allowance < from_amount:
                    approve_tx = token_contract.functions.approve(Web3.to_checksum_address(spender), from_amount)
                    tx_dict = approve_tx.build_transaction({
                        "from": signer_address,
                        "nonce": w3.eth.get_transaction_count(signer_address),
                        "gas": 120000,
                        "chainId": w3.eth.chain_id,
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
                        return w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)

                    loop = asyncio.get_event_loop()
                    receipt = await loop.run_in_executor(None, wait_receipt)
                    if getattr(receipt, "status", 1) == 0:
                        return ToolResult(error=f"Approval failed: {tx_hash.hex()}")

            # Execute bridge tx
            # Safe conversion for hex values
            safe_int_convert = lambda value, default=0: int(value) if value else default

            send_tx = {
                "to": Web3.to_checksum_address(step_tx.get("to")),
                "from": signer_address,
                "value": safe_int_convert(step_tx.get("value")),
                "data": step_tx.get("data", "0x"),
                "nonce": w3.eth.get_transaction_count(signer_address),
                "chainId": w3.eth.chain_id,
            }
            try:
                suggested_gas = safe_int_convert(step_tx.get("gasLimit"))
            except Exception:
                suggested_gas = 0
            try:
                send_tx["gas"] = suggested_gas or w3.eth.estimate_gas({**send_tx, "from": account.address})
            except Exception:
                send_tx["gas"] = int(1.2 * 300000)
            if gas_price_gwei is not None:
                send_tx["gasPrice"] = w3.to_wei(gas_price_gwei, "gwei")
            else:
                try:
                    if step_tx.get("gasPrice"):
                        send_tx["gasPrice"] = safe_int_convert(step_tx["gasPrice"])
                    else:
                        send_tx["gasPrice"] = w3.eth.gas_price
                except Exception:
                    pass

            signed_hex = await signer.sign_transaction(send_tx, rpc_url)
            bridge_hash = w3.eth.send_raw_transaction(bytes.fromhex(signed_hex[2:]) if signed_hex.startswith("0x") else bytes.fromhex(signed_hex))

            def wait_bridge_receipt():
                return w3.eth.wait_for_transaction_receipt(bridge_hash, timeout=180)

            loop = asyncio.get_event_loop()
            bridge_receipt = await loop.run_in_executor(None, wait_bridge_receipt)
            if getattr(bridge_receipt, "status", 1) == 0:
                return ToolResult(error=f"Bridge reverted: {bridge_hash.hex()}")

            return ToolResult(
                output={
                    "hash": bridge_hash.hex(),
                    "from": signer_address,
                    "to": send_tx["to"],
                    "value": str(send_tx["value"]),
                    "fromChainId": from_chain_id,
                    "toChainId": to_chain_id,
                    "signer_type": signer.signer_type,
                }
            )
        except Exception as e:
            logger.error(f"EvmBridgeTool error: {e}")
            return ToolResult(error=f"Bridge failed: {str(e)}")


