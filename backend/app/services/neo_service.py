"""
Neo N3 blockchain service for interacting with Neo N3 testnet/mainnet.

This service provides methods to:
- Connect to Neo N3 RPC endpoints
- Query blockchain state (block height, balances)
- Execute transactions on Neo N3

Implements Story 1.3 acceptance criteria.
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List
from decimal import Decimal

import httpx
from pydantic import BaseModel

from app.config import settings

logger = logging.getLogger(__name__)

# Thread-safe singleton lock
_neo_service_lock = asyncio.Lock()


class NeoRPCError(Exception):
    """Exception raised when Neo RPC call fails"""
    pass


class NeoConnectionError(Exception):
    """Exception raised when connection to Neo network fails"""
    pass


class NeoAddress(BaseModel):
    """Neo N3 address with balance information"""
    address: str
    gas_balance: Decimal = Decimal("0")
    neo_balance: Decimal = Decimal("0")


class NeoService:
    """
    Service for interacting with Neo N3 blockchain via RPC.

    This implementation uses direct JSON-RPC calls via httpx for maximum
    control and minimal dependencies. Uses neo-mamba for transaction building
    when needed.

    Environment Variables Required:
    - NEO_TESTNET_RPC: Primary RPC endpoint
    - NEO_TESTNET_RPC_FALLBACK: Fallback RPC endpoint
    - NEO_RPC_TIMEOUT: Request timeout in seconds
    - DEMO_WALLET_WIF: Demo wallet private key (WIF format)
    """

    # Native contract hashes (Neo N3 - same for mainnet and testnet)
    GAS_CONTRACT = "0xd2a4cff31913016155e38e474a2c06d08be276cf"
    NEO_CONTRACT = "0xef4073a0f2b305a38ec4050e4d3d28bc40ea63f5"

    def __init__(
        self,
        rpc_url: Optional[str] = None,
        fallback_rpc_url: Optional[str] = None,
        timeout: Optional[int] = None
    ):
        """
        Initialize Neo N3 service.

        Args:
            rpc_url: Primary RPC endpoint (defaults to NEO_TESTNET_RPC from config)
            fallback_rpc_url: Fallback RPC endpoint (defaults to NEO_TESTNET_RPC_FALLBACK)
            timeout: Request timeout in seconds (defaults to NEO_RPC_TIMEOUT)
        """
        self.rpc_url = rpc_url or settings.neo_testnet_rpc
        self.fallback_rpc_url = fallback_rpc_url or settings.neo_testnet_rpc_fallback
        self.timeout = timeout or settings.neo_rpc_timeout

        self._current_rpc: str = self.rpc_url
        self._client: Optional[httpx.AsyncClient] = None

        logger.info(f"NeoService initialized with RPC: {self.rpc_url}")

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create httpx client with timeout configuration"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                headers={"Content-Type": "application/json"}
            )
        return self._client

    async def close(self):
        """Close the HTTP client connection"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
            logger.info("NeoService connection closed")

    async def _rpc_call(
        self,
        method: str,
        params: Optional[List[Any]] = None,
        retry_with_fallback: bool = True
    ) -> Dict[str, Any]:
        """
        Make a JSON-RPC call to Neo N3 node.

        Args:
            method: RPC method name (e.g., "getblockcount")
            params: List of parameters for the method
            retry_with_fallback: Whether to retry with fallback RPC on failure

        Returns:
            JSON-RPC result

        Raises:
            NeoConnectionError: If connection fails
            NeoRPCError: If RPC returns an error
        """
        if params is None:
            params = []

        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params
        }

        client = await self._get_client()

        try:
            logger.debug(f"RPC call to {self._current_rpc}: {method}")
            response = await client.post(self._current_rpc, json=payload)
            response.raise_for_status()

            result = response.json()

            if "error" in result:
                error = result["error"]
                raise NeoRPCError(
                    f"RPC error {error.get('code', 'unknown')}: {error.get('message', 'unknown error')}"
                )

            return result.get("result")

        except (httpx.TimeoutException, httpx.ConnectError, httpx.ReadError) as e:
            logger.error(f"Connection error with {self._current_rpc}: {e}")

            # Try fallback if enabled and we haven't already
            if retry_with_fallback and self._current_rpc != self.fallback_rpc_url:
                logger.info(f"Switching to fallback RPC: {self.fallback_rpc_url}")
                self._current_rpc = self.fallback_rpc_url
                # Recursive call with fallback disabled to prevent infinite loop
                return await self._rpc_call(method, params, retry_with_fallback=False)

            raise NeoConnectionError(
                f"Failed to connect to Neo RPC after timeout ({self.timeout}s)"
            ) from e

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error from RPC: {e}")
            raise NeoRPCError(f"HTTP {e.response.status_code}: {e.response.text}") from e

    async def connect_testnet(self) -> Dict[str, Any]:
        """
        Test connection to Neo N3 testnet and return network info.

        Returns:
            Dict with version and connection info

        Raises:
            NeoConnectionError: If connection fails
        """
        try:
            # Get version to verify connection
            version = await self._rpc_call("getversion")

            # Get block count to verify blockchain is responding
            block_count = await self._rpc_call("getblockcount")

            logger.info(f"Successfully connected to Neo N3 testnet at block {block_count}")

            return {
                "connected": True,
                "rpc_url": self._current_rpc,
                "version": version.get("useragent", "unknown"),
                "protocol": version.get("protocol", {}),
                "block_height": block_count - 1,  # Block height = block count - 1
                "network": version.get("network", "unknown")
            }

        except Exception as e:
            logger.error(f"Failed to connect to testnet: {e}")
            raise

    async def get_block_height(self) -> int:
        """
        Get current blockchain height.

        Returns:
            Current block height (block count - 1)

        Raises:
            NeoConnectionError: If connection fails
            NeoRPCError: If RPC call fails
        """
        block_count = await self._rpc_call("getblockcount")
        return block_count - 1

    async def get_balance(self, address: str) -> NeoAddress:
        """
        Get GAS and NEO balance for a specific address.

        Args:
            address: Neo N3 address (format: N...)

        Returns:
            NeoAddress with balance information

        Raises:
            NeoConnectionError: If connection fails
            NeoRPCError: If RPC call fails
        """
        try:
            # Use getnep17balances RPC method (requires TokensTracker plugin)
            # This is the most reliable way to get balances
            balances_result = await self._rpc_call("getnep17balances", [address])

            gas_balance = Decimal("0")
            neo_balance = Decimal("0")

            # Parse balances from result
            if balances_result and "balance" in balances_result:
                for balance in balances_result["balance"]:
                    # Normalize both hashes: remove 0x prefix and lowercase
                    asset_hash = balance.get("assethash", "").lower().replace("0x", "")
                    amount = balance.get("amount", "0")

                    # Normalize contract hashes for comparison (remove 0x prefix)
                    gas_contract_normalized = self.GAS_CONTRACT.lower().replace("0x", "")
                    neo_contract_normalized = self.NEO_CONTRACT.lower().replace("0x", "")

                    # Convert from smallest unit (GAS has 8 decimals, NEO has 0)
                    if asset_hash == gas_contract_normalized:
                        gas_balance = Decimal(amount) / Decimal("100000000")  # 8 decimals
                    elif asset_hash == neo_contract_normalized:
                        neo_balance = Decimal(amount)  # NEO is not divisible

            return NeoAddress(
                address=address,
                gas_balance=gas_balance,
                neo_balance=neo_balance
            )

        except NeoRPCError as e:
            # Only catch plugin-specific errors, re-raise genuine errors
            error_message = str(e).lower()
            if "unknown method" in error_message or "method not found" in error_message:
                # Plugin not available - return zero balances for demo purposes
                logger.warning(f"Could not fetch balances (plugin not available): {e}")
                return NeoAddress(
                    address=address,
                    gas_balance=Decimal("0"),
                    neo_balance=Decimal("0")
                )
            else:
                # Genuine error (network failure, invalid address, etc.) - re-raise
                logger.error(f"Failed to fetch balances for {address}: {e}")
                raise

    async def validate_address(self, address: str) -> bool:
        """
        Validate if an address is a valid Neo N3 address.

        Args:
            address: Address to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            result = await self._rpc_call("validateaddress", [address])
            return result.get("isvalid", False)
        except Exception as e:
            logger.error(f"Error validating address: {e}")
            return False

    async def get_block_by_height(self, height: int) -> Optional[Dict[str, Any]]:
        """
        Get block information by block height.

        Args:
            height: Block height

        Returns:
            Block data or None if not found
        """
        try:
            # verbose=1 returns JSON format (verbose=0 returns hex)
            block = await self._rpc_call("getblock", [height, 1])
            return block
        except Exception as e:
            logger.error(f"Error fetching block {height}: {e}")
            return None

    async def get_transaction(self, txid: str) -> Optional[Dict[str, Any]]:
        """
        Get transaction information by transaction ID.

        Args:
            txid: Transaction hash

        Returns:
            Transaction data or None if not found
        """
        try:
            # verbose=1 returns JSON format
            tx = await self._rpc_call("getrawtransaction", [txid, 1])
            return tx
        except Exception as e:
            logger.error(f"Error fetching transaction {txid}: {e}")
            return None

    async def __aenter__(self):
        """Context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        await self.close()
        return False

    def __repr__(self) -> str:
        return f"NeoService(rpc={self._current_rpc}, timeout={self.timeout}s)"


# Global service instance (singleton pattern)
_neo_service: Optional[NeoService] = None


async def get_neo_service() -> NeoService:
    """
    Get the global NeoService instance (thread-safe).

    Returns:
        NeoService singleton instance
    """
    global _neo_service

    # Fast path: if already initialized, return immediately
    if _neo_service is not None:
        return _neo_service

    # Slow path: acquire lock for initialization
    async with _neo_service_lock:
        # Double-check: another coroutine might have initialized it
        if _neo_service is None:
            _neo_service = NeoService()
        return _neo_service


async def close_neo_service():
    """Close the global NeoService instance (thread-safe)"""
    global _neo_service

    async with _neo_service_lock:
        if _neo_service is not None:
            await _neo_service.close()
            _neo_service = None
