import os
import asyncio
import logging
from typing import Optional

from pydantic import Field

from spoon_ai.tools.base import BaseTool, ToolResult
from .signers import SignerManager

logger = logging.getLogger(__name__)


ERC20_ABI = [
    {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"},
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"},
    {"constant": False, "inputs": [{"name": "_to", "type": "address"}, {"name": "_value", "type": "uint256"}], "name": "transfer", "outputs": [{"name": "", "type": "bool"}], "type": "function"},
]


class EvmErc20TransferTool(BaseTool):
    name: str = "evm_erc20_transfer"
    description: str = "Transfer ERC20 tokens on an EVM chain. Supports local and Turnkey secure signing."
    parameters: dict = {
        "type": "object",
        "properties": {
            "rpc_url": {"type": "string", "description": "RPC endpoint. Defaults to EVM_PROVIDER_URL/RPC_URL env."},
            "signer_type": {
                "type": "string",
                "enum": ["local", "turnkey", "auto"],
                "description": "Signing method: 'local' (private key), 'turnkey' (secure API), or 'auto' (detect from env)",
                "default": "auto",
            },
            "private_key": {"type": "string", "description": "Sender private key (0x-prefixed). Required for local signing. Defaults to EVM_PRIVATE_KEY env."},
            "turnkey_sign_with": {"type": "string", "description": "Turnkey signing identity (address/ID). Required for Turnkey signing. Defaults to TURNKEY_SIGN_WITH env."},
            "turnkey_address": {"type": "string", "description": "Turnkey signer address. Optional for Turnkey signing. Defaults to TURNKEY_ADDRESS env."},
            "token_address": {"type": "string", "description": "ERC20 token contract address"},
            "to_address": {"type": "string", "description": "Recipient address"},
            "amount": {"type": "string", "description": "Amount in human-readable units"},
            "gas_price_gwei": {"type": "number", "description": "Optional gas price override in gwei"},
        },
        "required": ["token_address", "to_address", "amount"],
    }

    rpc_url: Optional[str] = Field(default=None)
    signer_type: str = Field(default="auto")
    private_key: Optional[str] = Field(default=None)
    turnkey_sign_with: Optional[str] = Field(default=None)
    turnkey_address: Optional[str] = Field(default=None)
    token_address: Optional[str] = Field(default=None)
    to_address: Optional[str] = Field(default=None)
    amount: Optional[str] = Field(default=None)
    gas_price_gwei: Optional[float] = Field(default=None)

    async def execute(
        self,
        rpc_url: Optional[str] = None,
        signer_type: Optional[str] = None,
        private_key: Optional[str] = None,
        turnkey_sign_with: Optional[str] = None,
        turnkey_address: Optional[str] = None,
        token_address: Optional[str] = None,
        to_address: Optional[str] = None,
        amount: Optional[str] = None,
        gas_price_gwei: Optional[float] = None,
    ) -> ToolResult:
        try:
            rpc_url = rpc_url or self.rpc_url or os.getenv("EVM_PROVIDER_URL") or os.getenv("RPC_URL")
            signer_type = signer_type or self.signer_type
            private_key = private_key or self.private_key
            turnkey_sign_with = turnkey_sign_with or self.turnkey_sign_with
            turnkey_address = turnkey_address or self.turnkey_address
            token_address = token_address or self.token_address
            to_address = to_address or self.to_address
            amount = amount or self.amount
            gas_price_gwei = gas_price_gwei or self.gas_price_gwei

            if not rpc_url:
                return ToolResult(error="Missing rpc_url and no EVM_PROVIDER_URL/RPC_URL set")
            if not token_address or not token_address.startswith("0x"):
                return ToolResult(error="Missing or invalid token_address")
            if not to_address or not to_address.startswith("0x"):
                return ToolResult(error="Missing or invalid to_address")
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

            # Get signer address for transaction building
            signer_address = await signer.get_address()

            token = w3.eth.contract(address=Web3.to_checksum_address(token_address), abi=ERC20_ABI)
            try:
                decimals = int(token.functions.decimals().call())
            except Exception:
                decimals = 18

            amount_raw = int(float(amount) * (10 ** decimals))

            # Build transaction with gas estimation
            tx_params = {
                "from": signer_address,
                "nonce": w3.eth.get_transaction_count(signer_address),
                "chainId": w3.eth.chain_id,
            }
            
            # Add gas price if explicitly provided (for legacy transactions)
            # Otherwise let web3.py handle it automatically (supports both legacy and EIP-1559)
            if gas_price_gwei is not None:
                tx_params["gasPrice"] = w3.to_wei(gas_price_gwei, "gwei")
            
            tx = token.functions.transfer(Web3.to_checksum_address(to_address), amount_raw).build_transaction(tx_params)
            
            # Estimate gas if not already set
            if "gas" not in tx or tx["gas"] == 0:
                try:
                    gas_est = w3.eth.estimate_gas(tx)
                    tx["gas"] = int(gas_est * 1.2)
                except Exception:
                    tx["gas"] = 120000

            # Sign and send transaction using the signer
            signed_tx_hex = await signer.sign_transaction(tx, rpc_url)
            tx_hash = w3.eth.send_raw_transaction(signed_tx_hex)

            def wait_receipt():
                return w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)

            loop = asyncio.get_event_loop()
            receipt = await loop.run_in_executor(None, wait_receipt)
            if getattr(receipt, "status", 1) == 0:
                return ToolResult(error=f"ERC20 transfer reverted: {tx_hash.hex()}")

            return ToolResult(output={
                "hash": tx_hash.hex(),
                "from": signer_address,
                "to": Web3.to_checksum_address(to_address),
                "token": Web3.to_checksum_address(token_address),
                "amount": str(amount),
                "decimals": decimals,
                "signer_type": signer.signer_type,
            })
        except Exception as e:
            logger.error(f"EvmErc20TransferTool error: {e}")
            return ToolResult(error=f"ERC20 transfer failed: {str(e)}")


