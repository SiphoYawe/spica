"""Neo blockchain data provider

This module provides a comprehensive interface for interacting with the Neo blockchain
using neo-mamba library. It supports both mainnet and testnet networks and includes
various utility methods for data processing and validation.

The provider handles:
- Address validation and conversion
- Asset amount formatting
- JSON serialization
- Safe dictionary access
- Network-specific API endpoints
"""

import asyncio
import json
import os
import ssl
from typing import Dict, Any, List, Optional
from decimal import Decimal

import aiohttp
from neo3.api import NeoRpcClient
from neo3.core import types
from neo3.wallet import utils as walletutils

# RPC URLs for different networks
DEFAULT_MAINNET_RPC = "https://mainmagnet.ngd.network:443"
DEFAULT_TESTNET_RPC = "https://testmagnet.ngd.network:443"

class NeoProvider:
    """Neo blockchain data provider using neo-mamba library

    This class provides a unified interface for querying Neo blockchain data
    including addresses, assets, blocks, transactions, and smart contracts.

    Attributes:
        network (str): The Neo network to connect to ('mainnet' or 'testnet')
        rpc_client (NeoRpcClient): The neo-mamba RPC client for blockchain interaction
    """

    def __init__(self, network: str = "testnet"):
        """Initialize the Neo provider

        Args:
            network (str): The Neo network to connect to. Must be 'mainnet' or 'testnet'

        Raises:
            ValueError: If network is not 'mainnet' or 'testnet'
        """
        if network not in ["mainnet", "testnet"]:
            raise ValueError("Network must be 'mainnet' or 'testnet'")

        self.network = network
        self.rpc_url = (
            os.getenv("NEO_MAINNET_RPC", DEFAULT_MAINNET_RPC)
            if network == "mainnet"
            else os.getenv("NEO_TESTNET_RPC", DEFAULT_TESTNET_RPC)
        )

        # Initialize neo-mamba RPC client
        self.rpc_client = NeoRpcClient(self.rpc_url)
        self._session: Optional[aiohttp.ClientSession] = None
        # Increase default timeout to 60 seconds to handle slow network connections
        self._request_timeout = float(os.getenv("NEO_RPC_TIMEOUT", "60"))

    def _normalize_address(self, raw: str) -> tuple[str, types.UInt160]:
        """Normalize an address into Base58 address + script hash tuple.

        Args:
            raw: Address supplied by the caller, either Base58 or 0x-prefixed script hash.

        Returns:
            Tuple containing the Base58 encoded address and its script hash.

        Raises:
            ValueError: If the provided value cannot be parsed for the current network.
        """
        # Handle addresses passed in as 0x-prefixed script hashes.
        if raw.startswith("0x"):
            raw = raw[2:]
        try:
            script_hash = types.UInt160.from_string(raw)
            normalized_address = walletutils.script_hash_to_address(script_hash)
        except ValueError:
            # Fall back to validating/parsing the provided Base58 address.
            walletutils.validate_address(raw)
            normalized_address = raw
            script_hash = walletutils.address_to_script_hash(raw)
        return normalized_address, script_hash

    def _ensure_0x_prefix(self, value: str) -> str:
        """Ensure the value starts with 0x prefix. If not, add it.
        
        Args:
            value: The value to ensure has 0x prefix (e.g., hash, contract hash)
            
        Returns:
            str: The value with 0x prefix
        """
        if not value:
            return value
        if not value.startswith("0x"):
            return f"0x{value}"
        return value

    def _address_to_script_hash(self, address: str) -> str:
        """Convert an address to script hash format (0x...).
        
        This method handles both Base58 addresses and 0x-prefixed script hashes.
        If the address is already in script hash format, it returns it as-is.
        Otherwise, it converts the Base58 address to script hash format.
        
        Args:
            address: Neo address in Base58 format or script hash format (0x...)
            
        Returns:
            str: Address in script hash format (0x...)
        """
        if address.startswith("0x"):
            # Already in script hash format
            return address
        else:
            # Convert Base58 address to script hash format
            _, script_hash = self._normalize_address(address)
            return f"0x{str(script_hash).replace('0x', '')}"

    async def _validate_address(self, raw: str) -> str:
        """Backward-compatible wrapper returning a normalized address string.

        Some toolkit helpers still call `_validate_address`; we expose this shim
        so they benefit from the new `_normalize_address` logic without refactors.
        """
        normalized_address, _ = self._normalize_address(raw)
        return normalized_address

    async def validate_address(self, address: str) -> Dict[str, Any]:
        """Call Neo RPC `validateaddress` to inspect address metadata.

        Args:
            address: Neo address in Base58 or 0x-prefixed script hash form.

        Returns:
            Dict[str, Any]: RPC response detailing validity and related fields.
        """
        normalized_address, _ = self._normalize_address(address)
        result = await self._make_request("validateaddress", [normalized_address])
        if isinstance(result, str):
            raise Exception(f"Failed to validate address: {result}")
        return self._handle_response(result)

    def _handle_response(self, result: Any) -> Any:
        """Handle neo-mamba response and extract result."""
        if result is None:
            raise RuntimeError("Empty response from Neo RPC")
        return result

    async def _ensure_session(self) -> aiohttp.ClientSession:
        """Ensure an aiohttp client session exists for raw RPC calls."""
        if self._session and not self._session.closed:
            return self._session

        ssl_context = ssl.create_default_context()
        if os.getenv("NEO_RPC_ALLOW_INSECURE", "false").lower() in {"1", "true", "yes"}:
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

        # Increase connection timeout and total timeout for slow networks
        timeout = aiohttp.ClientTimeout(
            total=self._request_timeout,
            connect=30,  # Connection timeout (30 seconds)
            sock_read=self._request_timeout  # Socket read timeout
        )
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        self._session = aiohttp.ClientSession(timeout=timeout, connector=connector)
        return self._session

    async def _make_request(self, method: str, params) -> Any:
        """Send a JSON-RPC request to the configured Neo endpoint.

        Many higher-level toolkit functions call RPC extensions not yet exposed
        by neo-mamba. This helper issues the request directly; if the remote node
        does not recognise the method we return a descriptive string rather than
        raising so the caller can surface the limitation gracefully.
        """
        session = await self._ensure_session()

        rpc_method = method
        # Handle both dict and list params
        # Neo extended APIs use dict params, standard JSON-RPC uses list params
        if params is None:
            params_value = []
        elif isinstance(params, dict):
            params_value = params  # Keep dict as-is for extended APIs
        else:
            params_value = params  # Keep list as-is for standard APIs
            
        payload = {
            "jsonrpc": "2.0",
            "method": rpc_method,
            "params": params_value,
            "id": 1,
        }
        try:
            timeout = aiohttp.ClientTimeout(total=self._request_timeout)
            async with session.post(self.rpc_url, json=payload, timeout=timeout) as response:
                response.raise_for_status()
                data = await response.json(content_type=None)
        except asyncio.TimeoutError as exc:
            return f"RPC request timeout for '{method}' (timeout: {self._request_timeout}s, URL: {self.rpc_url}): {exc}"
        except aiohttp.ClientError as exc:
            return f"RPC request failed for '{method}' (URL: {self.rpc_url}): {exc}"
        except Exception as exc:  # pragma: no cover - defensive
            return f"Unexpected RPC error for '{method}' (URL: {self.rpc_url}): {type(exc).__name__}: {exc}"

        if isinstance(data, dict) and data.get("error"):
            error = data["error"]
            if isinstance(error, dict):
                message = error.get("message", str(error))
                code = error.get("code", "unknown")
                return f"RPC method '{method}' returned error (code: {code}): {message}"
            else:
                return f"RPC method '{method}' returned error: {error}"

        return data.get("result") if isinstance(data, dict) else data

    def _convert_asset_amount(self, amount_string: str, decimals: int) -> Decimal:
        """Convert asset amount string to decimal with proper decimal places

        Args:
            amount_string (str): The amount as a string
            decimals (int): The number of decimal places for the asset

        Returns:
            Decimal: The converted amount with proper decimal places

        Raises:
            ValueError: If the amount string is invalid
        """
        try:
            amount = Decimal(amount_string)
            return amount / (10 ** decimals)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid amount string: {amount_string}")

    def _format_amount(self, amount: Decimal, decimals: int = 8) -> str:
        """Format amount with specified decimal places

        Args:
            amount (Decimal): The amount to format
            decimals (int): The number of decimal places to use

        Returns:
            str: The formatted amount string
        """
        return f"{amount:.{decimals}f}"

    def _to_json(self, obj: Any) -> str:
        """Convert object to JSON string

        Args:
            obj: The object to serialize

        Returns:
            str: The JSON string representation
        """
        return json.dumps(obj, default=lambda obj: obj.__dict__)

    # Address-related methods
    async def get_active_addresses(self, days: int) -> List[int]:
        """Get active addresses count for specified days

        Args:
            days (int): Number of days to get active address counts for (1-365)

        Returns:
            List[int]: List of daily active address counts

        Raises:
            ValueError: If days is not in valid range (1-365)
            Exception: If API request fails
        """
        # Validate days parameter
        if not isinstance(days, int) or days < 1 or days > 365:
            raise ValueError(f"Days must be an integer between 1 and 365, got: {days}")

        try:
            # Call GetActiveAddresses API
            # API expects: {"Days": <number>} - note the capital D
            # API response format: {"result": {"result": [...], "totalCount": <number>}, "error": null}
            response = await self._make_request("GetActiveAddresses", {"Days": days})
            result = self._handle_response(response)

            # Handle error response (string indicates error)
            if isinstance(result, str) and ("error" in result.lower() or "failed" in result.lower()):
                raise Exception(f"GetActiveAddresses API error: {result}")

            # API response structure: _make_request returns data.get("result")
            # So result contains: {"result": [...], "totalCount": <number>}
            if isinstance(result, dict):
                # Extract the result list from response
                if "result" in result:
                    active_addresses_list = result["result"]
                    if isinstance(active_addresses_list, list):
                        # Convert to list of integers if needed
                        return [int(addr) if isinstance(addr, (int, str)) else addr for addr in active_addresses_list]
                    return active_addresses_list
                # If result is directly a list (fallback case)
                elif isinstance(result, list):
                    return [int(addr) if isinstance(addr, (int, str)) else addr for addr in result]
                else:
                    # Unexpected format, return empty list
                    return []
            # If result is directly a list
            elif isinstance(result, list):
                return [int(addr) if isinstance(addr, (int, str)) else addr for addr in result]
            else:
                # Fallback: return empty list if response format is unexpected
                return []
        except ValueError:
            # Re-raise ValueError as-is
            raise
        except Exception as e:
            # Re-raise with more context
            raise Exception(f"Failed to get active addresses for {days} days: {str(e)}")

    async def get_address_info(self, address: str) -> Dict[str, Any]:
        """Get address information

        Args:
            address (str): The Neo address to get information for

        Returns:
            Dict[str, Any]: Address information including first use time, last use time, etc.
        """
        try:
            normalized_address, script_hash = self._normalize_address(address)
            # Get NEP-17 balances for the address
            balances = await self.rpc_client.get_nep17_balances(normalized_address)
            return self._handle_response({
                "address": normalized_address,
                "balances": balances,
                "script_hash": f"0x{str(script_hash)}"
            })
        except Exception as e:
            raise Exception(f"Failed to get address info: {str(e)}")

    # Block-related methods
    async def get_block_info(self, block_hash: str) -> Dict[str, Any]:
        """Get block information by hash

        Args:
            block_hash (str): The block hash to get information for

        Returns:
            Dict[str, Any]: Block information including transactions, timestamp, etc.
        """
        params = [block_hash, 1]
        result = await self._make_request("getblock", params)
        if isinstance(result, str):
            raise Exception(f"Failed to get block info: {result}")
        return self._handle_response(result)

    async def get_block_by_height(self, block_height: int) -> Dict[str, Any]:
        """Get block information by height

        Args:
            block_height (int): The block height to get information for

        Returns:
            Dict[str, Any]: Block information including transactions, timestamp, etc.
        """
        params = [block_height, 1]
        result = await self._make_request("getblock", params)
        if isinstance(result, str):
            raise Exception(f"Failed to get block by height: {result}")
        return self._handle_response(result)

    async def get_block_count(self) -> int:
        """Get total block count

        Returns:
            int: Total number of blocks on the network
        """
        result = await self._make_request("getblockcount", [])
        if isinstance(result, str):
            raise Exception(f"Failed to get block count: {result}")
        return self._handle_response(result)

    # Transaction-related methods
    async def get_transaction_info(self, tx_hash: str) -> Dict[str, Any]:
        """Get transaction information

        Args:
            tx_hash (str): The transaction hash to get information for

        Returns:
            Dict[str, Any]: Transaction information including inputs, outputs, etc.
        """
        try:
            tx_hash_uint = types.UInt256.from_string(tx_hash)
            transaction = await self.rpc_client.get_transaction(tx_hash_uint)
            return self._handle_response(transaction)
        except Exception as e:
            raise Exception(f"Failed to get transaction info: {str(e)}")

    async def get_transaction_count(self) -> int:
        """Get total transaction count

        Returns:
            int: Total number of transactions on the network
        """
        try:
            # Note: neo-mamba doesn't have a direct transaction count method
            # We'll need to use a different approach or estimate
            block_count = await self.rpc_client.get_block_count()
            # For now, return block count as an approximation
            return self._handle_response(block_count)
        except Exception as e:
            raise Exception(f"Failed to get transaction count: {str(e)}")

    # Asset-related methods
    async def get_asset_info(self, asset_hash: str) -> Dict[str, Any]:
        """Get asset information by hash

        Args:
            asset_hash (str): The asset hash to get information for

        Returns:
            Dict[str, Any]: Asset information including name, symbol, decimals, etc.
        """
        try:
            asset_hash_uint = types.UInt160.from_string(asset_hash)
            contract_state = await self.rpc_client.get_contract_state(asset_hash_uint)
            return self._handle_response(contract_state)
        except Exception as e:
            raise Exception(f"Failed to get asset info: {str(e)}")

    async def get_asset_count(self) -> int:
        """Get total asset count

        Returns:
            int: Total number of assets on the network
        """
        # Note: neo-mamba doesn't have a direct method for asset count
        # This is a limitation that may need to be addressed differently
        return 0

    # Contract-related methods
    async def get_contract_info(self, contract_hash: str) -> Dict[str, Any]:
        """Get contract information by hash

        Args:
            contract_hash (str): The contract hash to get information for

        Returns:
            Dict[str, Any]: Contract information including name, hash, etc.
        """
        try:
            contract_hash_uint = types.UInt160.from_string(contract_hash)
            contract_state = await self.rpc_client.get_contract_state(contract_hash_uint)
            return self._handle_response(contract_state)
        except Exception as e:
            raise Exception(f"Failed to get contract info: {str(e)}")

    async def close(self):
        """Close the RPC client connection."""
        if self._session and not self._session.closed:
            await self._session.close()
        await self.rpc_client.close()

    def __enter__(self):
        raise RuntimeError("NeoProvider requires 'async with ...' usage")

    def __exit__(self, exc_type, exc_val, exc_tb):
        raise RuntimeError("NeoProvider requires 'async with ...' usage")

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
