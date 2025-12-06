"""
Neo N3 Transaction Execution Engine

This module provides the execution engine for Neo N3 blockchain transactions.
It handles transaction building, signing, broadcasting, and confirmation polling.

Implements Story 5.1: Neo Execution Engine
"""

import asyncio
import logging
import base64
from typing import Optional, Dict, Any, List
from decimal import Decimal
from datetime import datetime, UTC

try:
    from neo3.wallet.account import Account as NeoAccount
    from neo3.core import types
    NEO3_AVAILABLE = True
except ImportError:
    NEO3_AVAILABLE = False
    NeoAccount = None
    types = None

import re
import base64

from app.config import settings
from app.services.neo_service import (
    NeoService,
    get_neo_service,
    NeoRPCError,
    NeoConnectionError
)

logger = logging.getLogger(__name__)

# Thread-safe singleton lock
_execution_engine_lock = asyncio.Lock()


class TransactionError(Exception):
    """Exception raised when transaction building/signing fails"""
    pass


class TransactionBroadcastError(Exception):
    """Exception raised when transaction broadcast fails"""
    pass


class TransactionConfirmationError(Exception):
    """Exception raised when transaction confirmation fails or times out"""
    pass


class TransactionResult:
    """Result of a transaction execution"""

    def __init__(
        self,
        txid: str,
        block_height: Optional[int] = None,
        confirmations: int = 0,
        network_fee: Optional[Decimal] = None,
        system_fee: Optional[Decimal] = None,
        timestamp: Optional[datetime] = None
    ):
        """
        Initialize transaction result.

        Args:
            txid: Transaction hash
            block_height: Block height where transaction was included
            confirmations: Number of confirmations
            network_fee: Network fee paid (in GAS)
            system_fee: System fee paid (in GAS)
            timestamp: Transaction timestamp
        """
        self.txid = txid
        self.block_height = block_height
        self.confirmations = confirmations
        self.network_fee = network_fee
        self.system_fee = system_fee
        self.timestamp = timestamp or datetime.now(UTC)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "txid": self.txid,
            "block_height": self.block_height,
            "confirmations": self.confirmations,
            "network_fee": str(self.network_fee) if self.network_fee else None,
            "system_fee": str(self.system_fee) if self.system_fee else None,
            "timestamp": self.timestamp.isoformat()
        }

    def __repr__(self) -> str:
        return f"TransactionResult(txid={self.txid}, confirmations={self.confirmations})"


class NeoExecutionEngine:
    """
    Execution engine for Neo N3 blockchain transactions.

    This engine provides the core functionality for executing workflow actions
    on the Neo N3 blockchain:
    - Connects to Neo N3 testnet via RPC
    - Loads and manages demo wallet for signing
    - Builds transactions for various operations
    - Signs transactions with wallet private key
    - Broadcasts transactions to the network
    - Polls for transaction confirmation

    Environment Variables Required:
    - DEMO_WALLET_WIF: Neo N3 wallet private key (WIF format)
    - NEO_TESTNET_RPC: Neo N3 RPC endpoint
    - NEO_RPC_TIMEOUT: Request timeout in seconds
    """

    # Confirmation settings
    DEFAULT_CONFIRMATION_TIMEOUT = 120  # seconds
    DEFAULT_POLL_INTERVAL = 2  # seconds
    DEFAULT_MIN_CONFIRMATIONS = 1

    # Gas token has 8 decimals in Neo N3
    GAS_DECIMALS = 8
    GAS_DIVISOR = Decimal(10 ** 8)  # 100000000

    # Neo N3 max transaction size
    MAX_TRANSACTION_SIZE = 102400  # bytes

    def __init__(
        self,
        neo_service: Optional[NeoService] = None,
        confirmation_timeout: Optional[int] = None,
        poll_interval: Optional[int] = None,
        min_confirmations: Optional[int] = None
    ):
        """
        Initialize Neo execution engine.

        Args:
            neo_service: Optional NeoService instance (will use global if not provided)
            confirmation_timeout: Max seconds to wait for confirmation (default: 120)
            poll_interval: Seconds between confirmation checks (default: 2)
            min_confirmations: Minimum confirmations required (default: 1)
        """
        self._neo_service = neo_service
        self._account: Optional[NeoAccount] = None
        self._address: Optional[str] = None
        self._initialized = False

        # Confirmation settings
        self.confirmation_timeout = confirmation_timeout or self.DEFAULT_CONFIRMATION_TIMEOUT
        self.poll_interval = poll_interval or self.DEFAULT_POLL_INTERVAL
        self.min_confirmations = min_confirmations or self.DEFAULT_MIN_CONFIRMATIONS

        logger.info("NeoExecutionEngine initialized")

    async def _initialize(self) -> None:
        """
        Initialize the execution engine (load wallet, connect to RPC).

        This is called automatically on first use.

        Raises:
            TransactionError: If wallet loading fails
            NeoConnectionError: If RPC connection fails
        """
        if self._initialized:
            return

        # Check if neo3 library is available
        if not NEO3_AVAILABLE:
            raise TransactionError(
                "neo3/neo-mamba library not available. "
                "Install neo-mamba to enable transaction execution."
            )

        # Load wallet from WIF
        try:
            wif = settings.demo_wallet_wif
            # Create account from WIF (blocking operation)
            loop = asyncio.get_event_loop()
            self._account = await loop.run_in_executor(
                None,
                NeoAccount.from_wif,
                wif
            )
            self._address = self._account.address
            logger.info(f"Wallet loaded successfully: {self._address}")
        except Exception as e:
            logger.error(f"Failed to load wallet from WIF: {e}")
            raise TransactionError(
                "Failed to load demo wallet. Check DEMO_WALLET_WIF configuration."
            ) from e

        # Get Neo service
        if self._neo_service is None:
            self._neo_service = await get_neo_service()

        # Test RPC connection
        try:
            await self._neo_service.connect_testnet()
        except Exception as e:
            logger.error(f"Failed to connect to Neo testnet: {e}")
            raise NeoConnectionError(
                "Failed to connect to Neo N3 testnet. Check NEO_TESTNET_RPC configuration."
            ) from e

        self._initialized = True
        logger.info("NeoExecutionEngine initialization complete")

    async def get_address(self) -> str:
        """
        Get the wallet address used for transaction signing.

        Returns:
            Neo N3 address (format: N...)
        """
        await self._initialize()
        return self._address

    async def send_raw_transaction(self, signed_tx_base64: str) -> str:
        """
        Broadcast a signed transaction to the network.

        Args:
            signed_tx_base64: Base64-encoded signed transaction

        Returns:
            Transaction hash (txid)

        Raises:
            TransactionBroadcastError: If broadcast fails
            NeoRPCError: If RPC returns an error
        """
        await self._initialize()

        # Validate transaction size
        try:
            decoded = base64.b64decode(signed_tx_base64)
            if len(decoded) > self.MAX_TRANSACTION_SIZE:
                raise TransactionBroadcastError(
                    f"Transaction size ({len(decoded)} bytes) exceeds "
                    f"maximum allowed ({self.MAX_TRANSACTION_SIZE} bytes)"
                )
            if len(decoded) == 0:
                raise TransactionBroadcastError(
                    "Transaction data is empty after base64 decoding"
                )
        except Exception as e:
            if isinstance(e, TransactionBroadcastError):
                raise
            raise TransactionBroadcastError(
                f"Invalid base64 transaction data: {e}"
            ) from e

        try:
            logger.info(f"Broadcasting transaction to Neo network ({len(decoded)} bytes)...")

            # Call sendrawtransaction RPC method
            result = await self._neo_service._rpc_call(
                "sendrawtransaction",
                [signed_tx_base64]
            )

            # Extract transaction hash from result
            if isinstance(result, dict) and "hash" in result:
                txid = result["hash"]
                # Remove 0x prefix if present
                txid = txid.replace("0x", "")

                # Validate hash format (64 hex characters for Neo N3)
                if not re.match(r'^[a-fA-F0-9]{64}$', txid):
                    raise TransactionBroadcastError(
                        f"Invalid transaction hash format received from RPC: {txid}"
                    )

                logger.info(f"Transaction broadcast successful: {txid}")
                return txid
            else:
                raise TransactionBroadcastError(
                    f"Unexpected sendrawtransaction response format: {result}"
                )

        except NeoRPCError as e:
            # Handle specific RPC errors with user-friendly messages
            error_msg = str(e).lower()

            if "alreadyexists" in error_msg or "already exists" in error_msg:
                raise TransactionBroadcastError(
                    "Transaction already exists in the blockchain"
                ) from e
            elif "insufficientfunds" in error_msg or "insufficient funds" in error_msg:
                raise TransactionBroadcastError(
                    "Insufficient funds to pay transaction fees"
                ) from e
            elif "expired" in error_msg:
                raise TransactionBroadcastError(
                    "Transaction has expired. Please try again."
                ) from e
            elif "invalid" in error_msg:
                raise TransactionBroadcastError(
                    "Invalid transaction format or signature"
                ) from e
            elif "outofmemory" in error_msg or "memory pool" in error_msg:
                raise TransactionBroadcastError(
                    "Network memory pool is full. Please try again later."
                ) from e
            else:
                raise TransactionBroadcastError(
                    f"Failed to broadcast transaction: {e}"
                ) from e

        except Exception as e:
            logger.error(f"Unexpected error broadcasting transaction: {e}")
            raise TransactionBroadcastError(
                f"Failed to broadcast transaction: {e}"
            ) from e

    async def wait_for_confirmation(
        self,
        txid: str,
        min_confirmations: Optional[int] = None,
        timeout: Optional[int] = None,
        poll_interval: Optional[int] = None
    ) -> TransactionResult:
        """
        Wait for transaction to be confirmed on the blockchain.

        This method polls the blockchain until the transaction is included
        in a block and has the required number of confirmations.

        Args:
            txid: Transaction hash to monitor
            min_confirmations: Minimum confirmations required (default: 1)
            timeout: Max seconds to wait (default: 120)
            poll_interval: Seconds between checks (default: 2)

        Returns:
            TransactionResult with confirmation details

        Raises:
            TransactionConfirmationError: If confirmation times out or fails
        """
        await self._initialize()

        # Use instance defaults if not specified
        min_confirmations = min_confirmations or self.min_confirmations
        timeout = timeout or self.confirmation_timeout
        poll_interval = poll_interval or self.poll_interval

        logger.info(
            f"Waiting for {min_confirmations} confirmation(s) for tx {txid} "
            f"(timeout: {timeout}s, interval: {poll_interval}s)"
        )

        start_time = asyncio.get_event_loop().time()
        attempts = 0

        while True:
            attempts += 1
            elapsed = asyncio.get_event_loop().time() - start_time

            # Check timeout
            if elapsed > timeout:
                raise TransactionConfirmationError(
                    f"Transaction confirmation timed out after {timeout}s "
                    f"({attempts} attempts). Transaction may still be pending."
                )

            try:
                # Get transaction from blockchain
                tx_data = await self._neo_service.get_transaction(txid)

                if tx_data is None:
                    # Transaction not yet in a block
                    logger.debug(
                        f"Transaction {txid} not yet confirmed "
                        f"(attempt {attempts}, elapsed {elapsed:.1f}s)"
                    )
                    await asyncio.sleep(poll_interval)
                    continue

                # Transaction found - check confirmations
                block_height = tx_data.get("blockheight")
                if block_height is None:
                    # In mempool but not yet in block
                    logger.debug(f"Transaction {txid} in mempool (attempt {attempts})")
                    await asyncio.sleep(poll_interval)
                    continue

                # Get current block height to calculate confirmations
                current_height = await self._neo_service.get_block_height()
                confirmations = (current_height - block_height) + 1

                logger.debug(
                    f"Transaction {txid} has {confirmations} confirmation(s) "
                    f"(block {block_height}, current {current_height})"
                )

                # Check if we have enough confirmations
                if confirmations >= min_confirmations:
                    # Extract fee information
                    network_fee = None
                    system_fee = None

                    if "netfee" in tx_data:
                        # Network fee in smallest unit (convert from 10^-8 GAS)
                        network_fee = Decimal(tx_data["netfee"]) / self.GAS_DIVISOR

                    if "sysfee" in tx_data:
                        # System fee in smallest unit (convert from 10^-8 GAS)
                        system_fee = Decimal(tx_data["sysfee"]) / self.GAS_DIVISOR

                    result = TransactionResult(
                        txid=txid,
                        block_height=block_height,
                        confirmations=confirmations,
                        network_fee=network_fee,
                        system_fee=system_fee,
                        timestamp=datetime.now(UTC)
                    )

                    logger.info(
                        f"Transaction {txid} confirmed! "
                        f"Block: {block_height}, Confirmations: {confirmations}, "
                        f"Fees: {network_fee or 0} GAS (net) + {system_fee or 0} GAS (sys)"
                    )

                    return result

                # Not enough confirmations yet
                await asyncio.sleep(poll_interval)

            except NeoConnectionError as e:
                # Network error - log and retry
                logger.warning(f"Network error checking transaction status: {e}")
                await asyncio.sleep(poll_interval)

            except Exception as e:
                logger.error(f"Unexpected error waiting for confirmation: {e}")
                raise TransactionConfirmationError(
                    f"Failed to check transaction confirmation: {e}"
                ) from e

    async def execute_transaction(
        self,
        signed_tx_base64: str,
        wait_for_confirmation: bool = True,
        min_confirmations: Optional[int] = None
    ) -> TransactionResult:
        """
        Execute a complete transaction: broadcast and optionally wait for confirmation.

        This is the high-level method for executing transactions. It:
        1. Broadcasts the signed transaction to the network
        2. Optionally waits for confirmation (default: True)
        3. Returns the transaction result

        Args:
            signed_tx_base64: Base64-encoded signed transaction
            wait_for_confirmation: Whether to wait for blockchain confirmation
            min_confirmations: Minimum confirmations required (default: 1)

        Returns:
            TransactionResult with execution details

        Raises:
            TransactionBroadcastError: If broadcast fails
            TransactionConfirmationError: If confirmation fails (when wait_for_confirmation=True)
        """
        await self._initialize()

        logger.info(f"Executing transaction (wait_for_confirmation={wait_for_confirmation})...")

        # Broadcast transaction
        txid = await self.send_raw_transaction(signed_tx_base64)

        # If not waiting for confirmation, return immediately
        if not wait_for_confirmation:
            return TransactionResult(
                txid=txid,
                confirmations=0,
                timestamp=datetime.now(UTC)
            )

        # Wait for confirmation
        result = await self.wait_for_confirmation(
            txid=txid,
            min_confirmations=min_confirmations
        )

        logger.info(f"Transaction execution complete: {txid}")
        return result

    async def get_account(self) -> NeoAccount:
        """
        Get the Neo account object for transaction signing.

        WARNING: This method exposes the account with private key.
        Only use internally for transaction building/signing.
        NEVER expose this in API responses.

        Returns:
            Neo account object with signing capabilities

        Raises:
            TransactionError: If wallet is not loaded
        """
        await self._initialize()

        if not self._account:
            raise TransactionError("Wallet account not available")

        return self._account

    async def close(self):
        """Close the execution engine and underlying connections"""
        if self._neo_service:
            await self._neo_service.close()

        logger.info("NeoExecutionEngine closed")

    async def __aenter__(self):
        """Context manager entry"""
        await self._initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        await self.close()
        return False

    def __repr__(self) -> str:
        """String representation"""
        address_display = self._address if self._initialized else "not initialized"
        return f"NeoExecutionEngine(address={address_display})"


# Global service instance (singleton pattern)
_execution_engine: Optional[NeoExecutionEngine] = None


async def get_execution_engine() -> NeoExecutionEngine:
    """
    Get the global NeoExecutionEngine instance (thread-safe).

    Returns:
        NeoExecutionEngine singleton instance
    """
    global _execution_engine

    # Fast path: if already initialized, return immediately
    if _execution_engine is not None:
        return _execution_engine

    # Slow path: acquire lock for initialization
    async with _execution_engine_lock:
        # Double-check: another coroutine might have initialized it
        if _execution_engine is None:
            _execution_engine = NeoExecutionEngine()
        return _execution_engine


async def close_execution_engine():
    """Close the global NeoExecutionEngine instance (thread-safe)"""
    global _execution_engine

    async with _execution_engine_lock:
        if _execution_engine is not None:
            await _execution_engine.close()
            _execution_engine = None
