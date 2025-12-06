import os
import asyncio
import logging
from typing import Optional

from pydantic import Field

from spoon_ai.tools.base import BaseTool, ToolResult
from .signers import EvmSigner, SignerManager

logger = logging.getLogger(__name__)


class EvmTransferTool(BaseTool):
    """Transfer native tokens on an EVM chain.

    Mirrors plugin-evm transfer behavior: sends a native value transfer with optional data.
    Supports both local private key and Turnkey secure signing.
    """

    name: str = "evm_transfer"
    description: str = (
        "Transfer native tokens on an EVM chain. Supports local and Turnkey secure signing."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "rpc_url": {
                "type": "string",
                "description": "RPC endpoint for the target chain. If omitted, uses EVM_PROVIDER_URL env.",
            },
            "signer_type": {
                "type": "string",
                "enum": ["local", "turnkey", "auto"],
                "description": "Signing method: 'local' (private key), 'turnkey' (secure API), or 'auto' (detect from env)",
                "default": "auto",
            },
            "private_key": {
                "type": "string",
                "description": "Sender private key (0x-prefixed). Required for local signing. If omitted, uses EVM_PRIVATE_KEY env.",
            },
            "turnkey_sign_with": {
                "type": "string",
                "description": "Turnkey signing identity (address/ID). Required for Turnkey signing. If omitted, uses TURNKEY_SIGN_WITH env.",
            },
            "turnkey_address": {
                "type": "string",
                "description": "Turnkey signer address. Optional for Turnkey signing. If omitted, uses TURNKEY_ADDRESS env.",
            },
            "to_address": {
                "type": "string",
                "description": "Recipient address (0x-prefixed)",
            },
            "amount_ether": {
                "type": "string",
                "description": "Amount in ether (decimal string)",
            },
            "data": {
                "type": "string",
                "description": "Optional hex data payload (0x-prefixed)",
                "default": "0x",
            },
            "gas_limit": {
                "type": "integer",
                "description": "Optional gas limit override",
            },
            "gas_price_gwei": {
                "type": "number",
                "description": "Optional gas price in gwei",
            },
            "nonce": {
                "type": "integer",
                "description": "Optional nonce override",
            },
        },
        "required": ["to_address", "amount_ether"],
    }

    rpc_url: Optional[str] = Field(default=None)
    signer_type: str = Field(default="auto")
    private_key: Optional[str] = Field(default=None)
    turnkey_sign_with: Optional[str] = Field(default=None)
    turnkey_address: Optional[str] = Field(default=None)
    to_address: Optional[str] = Field(default=None)
    amount_ether: Optional[str] = Field(default=None)
    data: str = Field(default="0x")
    gas_limit: Optional[int] = Field(default=None)
    gas_price_gwei: Optional[float] = Field(default=None)
    nonce: Optional[int] = Field(default=None)

    async def execute(
        self,
        rpc_url: Optional[str] = None,
        signer_type: Optional[str] = None,
        private_key: Optional[str] = None,
        turnkey_sign_with: Optional[str] = None,
        turnkey_address: Optional[str] = None,
        to_address: Optional[str] = None,
        amount_ether: Optional[str] = None,
        data: Optional[str] = None,
        gas_limit: Optional[int] = None,
        gas_price_gwei: Optional[float] = None,
        nonce: Optional[int] = None,
    ) -> ToolResult:
        try:
            # Resolve inputs with env and defaults
            rpc_url = rpc_url or self.rpc_url or os.getenv("EVM_PROVIDER_URL") or os.getenv("RPC_URL")
            signer_type = signer_type or self.signer_type
            private_key = private_key or self.private_key
            turnkey_sign_with = turnkey_sign_with or self.turnkey_sign_with
            turnkey_address = turnkey_address or self.turnkey_address
            to_address = to_address or self.to_address
            amount_ether = amount_ether or self.amount_ether
            data = (data if data is not None else self.data) or "0x"

            if not rpc_url:
                return ToolResult(error="Missing rpc_url and no EVM_PROVIDER_URL/RPC_URL set")
            if not to_address or not to_address.startswith("0x"):
                return ToolResult(error="Missing or invalid to_address; must be 0x-prefixed")
            if not amount_ether:
                return ToolResult(error="Missing amount_ether")

            # Lazy import web3 to avoid import cost when unused
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

            # Build transaction
            value_wei = w3.to_wei(amount_ether, "ether")
            tx = {
                "to": Web3.to_checksum_address(to_address),
                "from": signer_address,
                "value": value_wei,
                "data": data if data and data != "null" else "0x",
            }

            # Gas params
            if gas_limit is not None:
                tx["gas"] = gas_limit
            else:
                try:
                    tx["gas"] = w3.eth.estimate_gas({**tx, "from": signer_address})
                except Exception:
                    # Fallback gas if estimation fails
                    tx["gas"] = 21000 if (tx["data"] == "0x") else 100000

            if gas_price_gwei is not None:
                tx["gasPrice"] = w3.to_wei(gas_price_gwei, "gwei")
            else:
                try:
                    tx["gasPrice"] = w3.eth.gas_price
                except Exception:
                    pass

            # Nonce
            if nonce is not None:
                tx["nonce"] = nonce
            else:
                tx["nonce"] = w3.eth.get_transaction_count(signer_address)

            # Chain ID
            try:
                tx["chainId"] = w3.eth.chain_id
            except Exception:
                pass

            # Sign and send transaction using the signer
            signed_tx_hex = await signer.sign_transaction(tx, rpc_url)
            tx_hash = w3.eth.send_raw_transaction(signed_tx_hex)

            # Wait for receipt with timeout to avoid hanging
            def wait_receipt():
                return w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

            loop = asyncio.get_event_loop()
            receipt = await loop.run_in_executor(None, wait_receipt)

            if getattr(receipt, "status", 1) == 0:
                return ToolResult(error=f"Transaction reverted: {tx_hash.hex()}")

            return ToolResult(
                output={
                    "hash": tx_hash.hex(),
                    "from": signer_address,
                    "to": Web3.to_checksum_address(to_address),
                    "value_wei": str(value_wei),
                    "chainId": tx.get("chainId"),
                    "signer_type": signer.signer_type,
                }
            )
        except Exception as e:
            logger.error(f"EvmTransferTool error: {e}")
            return ToolResult(error=f"Transfer failed: {str(e)}")


