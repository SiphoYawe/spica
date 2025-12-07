"""
Neo RPC Service

Provides async HTTP JSON-RPC interface to Neo N3 blockchain with:
- Connection pooling via httpx.AsyncClient
- Type-safe method signatures
- Automatic decimal adjustment for token balances
- Transaction confirmation polling
- Error handling with custom exceptions
- Singleton pattern for global instance management

Verified against:
- /neo-dev-portal/docs/n3/reference/rpc/latest-version/api.md
- Neo N3 RPC API specification
"""

import asyncio
import httpx
from decimal import Decimal
from typing import Dict, List, Optional, Any
from app.config import settings
from app.services.contract_registry import get_contract_registry


class NeoRPCError(Exception):
    """
    Neo RPC error with code and message.

    Raised when the JSON-RPC response contains an error field.
    """

    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(f"Neo RPC Error {code}: {message}")


class NeoRPCService:
    """
    Neo N3 JSON-RPC client with connection pooling and type-safe methods.

    Implements:
    - Block & network queries (getblockcount, getversion, etc.)
    - Account balance queries (getnep17balances)
    - Contract invocation (invokefunction, invokescript)
    - Transaction operations (sendrawtransaction, getrawtransaction)
    - Transaction confirmation polling (wait_for_confirmation)
    - Address validation (validateaddress)

    Connection Management:
    - Lazy initialization of httpx.AsyncClient
    - Connection reuse across requests
    - Proper cleanup with close()

    Error Handling:
    - Raises NeoRPCError for RPC-level errors
    - Raises httpx exceptions for network errors
    - Validates response structure
    """

    def __init__(self, rpc_url: Optional[str] = None):
        """
        Initialize Neo RPC service.

        Args:
            rpc_url: Optional RPC endpoint URL.
                     If None, uses settings.neo_rpc_url based on configured network.
        """
        self.rpc_url = rpc_url or settings.neo_rpc_url
        self._client: Optional[httpx.AsyncClient] = None
        self._request_id = 0
        self.registry = get_contract_registry()

    def _get_client(self) -> httpx.AsyncClient:
        """
        Get or create httpx AsyncClient with connection pooling.

        Returns:
            httpx.AsyncClient instance with 60-second timeout
        """
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(settings.neo_rpc_timeout),
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
            )
        return self._client

    async def close(self) -> None:
        """
        Close the HTTP client and release resources.

        Call this when shutting down the service to ensure proper cleanup.
        """
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def _call(self, method: str, params: Optional[List[Any]] = None) -> Any:
        """
        Make JSON-RPC 2.0 call to Neo node.

        Args:
            method: RPC method name (e.g., "getblockcount")
            params: Optional list of method parameters

        Returns:
            Response result field

        Raises:
            NeoRPCError: If RPC returns error
            httpx.HTTPError: If network request fails
        """
        self._request_id += 1

        payload = {
            "jsonrpc": "2.0",
            "id": self._request_id,
            "method": method,
            "params": params or []
        }

        client = self._get_client()
        response = await client.post(self.rpc_url, json=payload)
        response.raise_for_status()

        data = response.json()

        # Check for RPC error
        if "error" in data:
            error = data["error"]
            raise NeoRPCError(
                code=error.get("code", -1),
                message=error.get("message", "Unknown RPC error")
            )

        return data.get("result")

    # Block & Network Methods

    async def get_block_count(self) -> int:
        """
        Get current block height.

        Returns:
            Current block count (height + 1)

        RPC: getblockcount
        """
        result = await self._call("getblockcount")
        return int(result)

    async def get_best_block_hash(self) -> str:
        """
        Get hash of the most recent block.

        Returns:
            Block hash as hex string (0x-prefixed)

        RPC: getbestblockhash
        """
        result = await self._call("getbestblockhash")
        return str(result)

    async def get_version(self) -> Dict[str, Any]:
        """
        Get Neo node version information.

        Returns:
            Dict with keys:
            - tcpport: int
            - wsport: int
            - nonce: int
            - useragent: str
            - protocol: Dict with network, validatorscount, msperblock, etc.

        RPC: getversion
        """
        result = await self._call("getversion")
        return result

    # Account Methods

    async def get_nep17_balances(self, address: str) -> Dict[str, Decimal]:
        """
        Get all NEP-17 token balances for an address.

        Args:
            address: Neo N3 address (e.g., "NXV7ZhHiyM1aHXwpVsRZC6BwNFP2jghXAq")

        Returns:
            Dict mapping token contract hash to decimal-adjusted balance.
            Example: {"0xd2a4cff31913016155e38e474a2c06d08be276cf": Decimal("10.5")}

        RPC: getnep17balances
        """
        result = await self._call("getnep17balances", [address])

        balances = {}
        if result and "balance" in result:
            for item in result["balance"]:
                asset_hash = item["assethash"]
                amount = item["amount"]

                # Get decimals for this token (default to 8 if unknown)
                # Neo native contracts use specific decimals
                decimals = 8
                if asset_hash == self.registry.get_native_hash("GAS"):
                    decimals = self.registry.get_decimals("GAS")
                elif asset_hash == self.registry.get_native_hash("NEO"):
                    decimals = self.registry.get_decimals("NEO")

                # Adjust for decimals
                adjusted_balance = Decimal(amount) / Decimal(10 ** decimals)
                balances[asset_hash] = adjusted_balance

        return balances

    async def get_gas_balance(self, address: str) -> Decimal:
        """
        Get GAS balance for an address.

        Args:
            address: Neo N3 address

        Returns:
            GAS balance as Decimal (adjusted for 8 decimals)
            Returns Decimal("0") if no GAS balance

        RPC: getnep17balances (filtered for GAS)
        """
        balances = await self.get_nep17_balances(address)
        gas_hash = self.registry.get_native_hash("GAS")
        return balances.get(gas_hash, Decimal("0"))

    async def get_neo_balance(self, address: str) -> int:
        """
        Get NEO balance for an address.

        Args:
            address: Neo N3 address

        Returns:
            NEO balance as integer (NEO is indivisible)
            Returns 0 if no NEO balance

        RPC: getnep17balances (filtered for NEO)
        """
        balances = await self.get_nep17_balances(address)
        neo_hash = self.registry.get_native_hash("NEO")
        balance = balances.get(neo_hash, Decimal("0"))
        return int(balance)

    # Contract Methods

    async def invoke_function(
        self,
        script_hash: str,
        operation: str,
        params: Optional[List[Dict]] = None,
        signers: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Invoke a smart contract function (read-only, no transaction).

        Args:
            script_hash: Contract script hash (0x-prefixed)
            operation: Function name to invoke
            params: Optional list of parameters in Neo RPC format:
                    [{"type": "String", "value": "hello"}, ...]
            signers: Optional list of signers for script verification:
                    [{"account": "0x...", "scopes": "CalledByEntry"}, ...]

        Returns:
            Dict with keys:
            - script: str (base64 encoded script)
            - state: str ("HALT" or "FAULT")
            - gasconsumed: str
            - stack: List[Dict] (return values)
            - exception: Optional[str]

        RPC: invokefunction
        """
        rpc_params = [script_hash, operation, params or []]
        if signers:
            rpc_params.append(signers)

        result = await self._call("invokefunction", rpc_params)
        return result

    async def invoke_script(
        self,
        script_base64: str,
        signers: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Invoke a script (read-only, no transaction).

        Args:
            script_base64: Base64-encoded Neo VM script
            signers: Optional list of signers for script verification

        Returns:
            Dict with same structure as invoke_function

        RPC: invokescript
        """
        rpc_params = [script_base64]
        if signers:
            rpc_params.append(signers)

        result = await self._call("invokescript", rpc_params)
        return result

    # Transaction Methods

    async def send_raw_transaction(self, tx_base64: str) -> str:
        """
        Broadcast a signed transaction to the network.

        Args:
            tx_base64: Base64-encoded signed transaction

        Returns:
            Transaction hash (0x-prefixed)

        Raises:
            NeoRPCError: If transaction is invalid or rejected

        RPC: sendrawtransaction
        """
        result = await self._call("sendrawtransaction", [tx_base64])

        # Result is dict with "hash" key
        if isinstance(result, dict) and "hash" in result:
            return result["hash"]

        # Some nodes return just the hash string
        return str(result)

    async def get_raw_transaction(
        self,
        tx_hash: str,
        verbose: bool = True
    ) -> Dict[str, Any]:
        """
        Get transaction details by hash.

        Args:
            tx_hash: Transaction hash (0x-prefixed)
            verbose: If True, return JSON object. If False, return hex string.

        Returns:
            If verbose=True: Dict with transaction details (size, version, script, etc.)
            If verbose=False: Hex string of raw transaction

        RPC: getrawtransaction
        """
        result = await self._call("getrawtransaction", [tx_hash, 1 if verbose else 0])
        return result

    async def get_application_log(self, tx_hash: str) -> Dict[str, Any]:
        """
        Get application execution log for a transaction.

        Args:
            tx_hash: Transaction hash (0x-prefixed)

        Returns:
            Dict with keys:
            - txid: str
            - executions: List[Dict] with:
              - trigger: str ("Application")
              - vmstate: str ("HALT" or "FAULT")
              - gasconsumed: str
              - stack: List[Dict] (return values)
              - notifications: List[Dict] (emitted events)

        Raises:
            NeoRPCError: If transaction not found or not confirmed

        RPC: getapplicationlog
        """
        result = await self._call("getapplicationlog", [tx_hash])
        return result

    async def calculate_network_fee(self, tx_base64: str) -> int:
        """
        Calculate network fee for a transaction.

        Args:
            tx_base64: Base64-encoded transaction (signed or unsigned)

        Returns:
            Network fee in GAS smallest units (10^-8 GAS)

        RPC: calculatenetworkfee
        """
        result = await self._call("calculatenetworkfee", [tx_base64])

        # Result is dict with "networkfee" key
        if isinstance(result, dict) and "networkfee" in result:
            return int(result["networkfee"])

        return int(result)

    # Transaction Confirmation

    async def wait_for_confirmation(
        self,
        tx_hash: str,
        timeout: int = 60,
        poll_interval: float = 2.0
    ) -> Dict[str, Any]:
        """
        Poll for transaction confirmation until HALT or FAULT.

        Continuously checks getapplicationlog until:
        - Transaction is confirmed (HALT state)
        - Transaction failed (FAULT state)
        - Timeout is reached

        Args:
            tx_hash: Transaction hash to monitor
            timeout: Maximum seconds to wait (default 60)
            poll_interval: Seconds between polls (default 2.0)

        Returns:
            Application log dict (same as get_application_log)

        Raises:
            TimeoutError: If transaction not confirmed within timeout
            NeoRPCError: If RPC call fails
        """
        start_time = asyncio.get_event_loop().time()

        while True:
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed >= timeout:
                raise TimeoutError(
                    f"Transaction {tx_hash} not confirmed within {timeout} seconds"
                )

            try:
                app_log = await self.get_application_log(tx_hash)

                # Check if execution is complete
                if app_log and "executions" in app_log and len(app_log["executions"]) > 0:
                    execution = app_log["executions"][0]
                    vm_state = execution.get("vmstate")

                    if vm_state in ["HALT", "FAULT"]:
                        return app_log

            except NeoRPCError as e:
                # Transaction not yet confirmed - continue polling
                # Common error codes:
                # - Unknown transaction/item (not in blockchain yet)
                if "Unknown" not in e.message:
                    raise

            # Wait before next poll
            await asyncio.sleep(poll_interval)

    # Validation

    async def validate_address(self, address: str) -> bool:
        """
        Validate Neo N3 address format.

        Args:
            address: Address string to validate

        Returns:
            True if valid Neo N3 address, False otherwise

        RPC: validateaddress
        """
        result = await self._call("validateaddress", [address])

        # Result is dict with "isvalid" boolean
        if isinstance(result, dict):
            return result.get("isvalid", False)

        return False


# Singleton Pattern for Global Instance Management

_neo_rpc_instance: Optional[NeoRPCService] = None


async def get_neo_rpc() -> NeoRPCService:
    """
    Get global NeoRPCService singleton instance.

    Creates instance on first call, reuses for subsequent calls.
    Enables connection pooling across the application.

    Returns:
        NeoRPCService instance configured from settings

    Usage:
        rpc = await get_neo_rpc()
        block_count = await rpc.get_block_count()
    """
    global _neo_rpc_instance

    if _neo_rpc_instance is None:
        _neo_rpc_instance = NeoRPCService()

    return _neo_rpc_instance


async def close_neo_rpc() -> None:
    """
    Close global NeoRPCService instance and release resources.

    Call this during application shutdown to ensure proper cleanup.

    Usage:
        await close_neo_rpc()
    """
    global _neo_rpc_instance

    if _neo_rpc_instance is not None:
        await _neo_rpc_instance.close()
        _neo_rpc_instance = None
