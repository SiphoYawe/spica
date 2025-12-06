import os
import logging
from typing import Optional

from pydantic import Field

from spoon_ai.tools.base import BaseTool, ToolResult

logger = logging.getLogger(__name__)


ERC20_ABI = [
    {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"},
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"},
]


class EvmBalanceTool(BaseTool):
    name: str = "evm_get_balance"
    description: str = "Get native or ERC20 balance for an address."
    parameters: dict = {
        "type": "object",
        "properties": {
            "rpc_url": {"type": "string", "description": "RPC endpoint. Defaults to EVM_PROVIDER_URL/RPC_URL env."},
            "address": {"type": "string", "description": "Address to query"},
            "token_address": {"type": "string", "description": "Optional ERC20 token address; if omitted, returns native balance"},
        },
        "required": ["address"],
    }

    rpc_url: Optional[str] = Field(default=None)
    address: Optional[str] = Field(default=None)
    token_address: Optional[str] = Field(default=None)

    async def execute(self, rpc_url: Optional[str] = None, address: Optional[str] = None, token_address: Optional[str] = None) -> ToolResult:
        try:
            rpc_url = rpc_url or self.rpc_url or os.getenv("EVM_PROVIDER_URL") or os.getenv("RPC_URL")
            address = address or self.address
            token_address = token_address or self.token_address
            if not rpc_url:
                return ToolResult(error="Missing rpc_url and no EVM_PROVIDER_URL/RPC_URL set")
            if not address or not address.startswith("0x"):
                return ToolResult(error="Missing or invalid address: must start with '0x'")
            
            # Validate address length (must be 42 characters: '0x' + 40 hex chars)
            if len(address) != 42:
                return ToolResult(error=f"Invalid address length: {len(address)} characters. Ethereum addresses must be exactly 42 characters (0x + 40 hex digits). Address provided: {address}")
            
            # Validate hex characters
            try:
                int(address[2:], 16)
            except ValueError:
                return ToolResult(error=f"Invalid address format: contains non-hexadecimal characters. Address: {address}")

            try:
                from web3 import Web3, HTTPProvider
            except Exception as e:
                return ToolResult(error=f"web3 dependency not available: {str(e)}")

            try:
                w3 = Web3(HTTPProvider(rpc_url, request_kwargs={'timeout': 10}))
                if not w3.is_connected():
                    return ToolResult(error=f"Failed to connect to RPC: {rpc_url}. Please check if the RPC endpoint is available or try an alternative RPC URL like https://ethereum-sepolia-rpc.publicnode.com")
            except Exception as conn_error:
                error_msg = str(conn_error)
                return ToolResult(error=f"RPC connection error: {error_msg}. URL: {rpc_url}. Please verify the RPC endpoint is correct and accessible. Try alternative RPCs like https://ethereum-sepolia-rpc.publicnode.com")

            # Validate and convert addresses to checksum format
            try:
                checksum_address = Web3.to_checksum_address(address)
            except ValueError as e:
                return ToolResult(error=f"Invalid Ethereum address format: {str(e)}. Address: {address}. Please verify the address is correct (42 characters, valid hex).")
            
            if token_address:
                # Validate token address
                if len(token_address) != 42 or not token_address.startswith("0x"):
                    return ToolResult(error=f"Invalid token address format: {token_address}. Must be 42 characters starting with '0x'")
                try:
                    checksum_token_address = Web3.to_checksum_address(token_address)
                except ValueError as e:
                    return ToolResult(error=f"Invalid token address format: {str(e)}. Token address: {token_address}")
                
                token = w3.eth.contract(address=checksum_token_address, abi=ERC20_ABI)
                decimals = int(token.functions.decimals().call())
                bal = token.functions.balanceOf(checksum_address).call()
                value = float(bal) / (10 ** decimals)
                return ToolResult(output={"address": checksum_address, "token": checksum_token_address, "balance": value})
            else:
                wei = w3.eth.get_balance(checksum_address)
                eth = float(wei) / (10 ** 18)
                return ToolResult(output={"address": checksum_address, "balance": eth})
        except Exception as e:
            logger.error(f"EvmBalanceTool error: {e}")
            return ToolResult(error=f"Get balance failed: {str(e)}")


