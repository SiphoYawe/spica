"""
Demo wallet service for Neo N3 transactions.

This service manages a single demo wallet used for executing workflow transactions.
The wallet is loaded from a WIF (Wallet Import Format) private key stored in the
environment variable DEMO_WALLET_WIF.

CRITICAL SECURITY NOTES:
- NEVER log the WIF private key
- NEVER expose the WIF in API responses
- Only expose public address and balances
- This is for DEMO/TESTNET use only
"""

import logging
import asyncio
from typing import Optional
from decimal import Decimal
from datetime import datetime, UTC
from concurrent.futures import ThreadPoolExecutor

try:
    import base58
    BASE58_AVAILABLE = True
except ImportError:
    BASE58_AVAILABLE = False
    base58 = None

try:
    # Try importing neo-mamba (neo3 package)
    # neo-mamba 3.x API
    from neo3.wallet.account import Account as NeoAccount
    NEO_WALLET_AVAILABLE = True
except ImportError:
    # Fallback if neo3/neo-mamba not installed yet
    NEO_WALLET_AVAILABLE = False
    NeoAccount = None

from app.config import settings
from app.services.neo_service import NeoService, get_neo_service
from app.models.wallet_models import WalletInfo, WalletBalance

logger = logging.getLogger(__name__)


class WalletSecurityError(Exception):
    """Exception raised when wallet security is compromised"""
    pass


class WalletService:
    """
    Service for managing the demo wallet used for workflow execution.

    This service:
    - Loads wallet from WIF stored in environment
    - Provides wallet address and balances
    - NEVER exposes the private key/WIF

    Environment Variables Required:
    - DEMO_WALLET_WIF: Neo N3 wallet private key in WIF format
    """

    # Thread pool for blocking crypto operations
    _executor = ThreadPoolExecutor(max_workers=2)

    def __init__(self, neo_service: Optional[NeoService] = None):
        """
        Initialize wallet service.

        Args:
            neo_service: Optional NeoService instance (will use global if not provided)
        """
        self._neo_service = neo_service
        self._account = None  # Will be NeoAccount if neo3 available
        self._address: Optional[str] = None
        self._initialized = False

        # CRITICAL: Do NOT log the WIF
        logger.info("WalletService initializing (WIF loaded from environment)")

        if not NEO_WALLET_AVAILABLE:
            logger.warning("neo3/neo-mamba not installed - wallet features limited")

    def _load_wallet_sync(self) -> None:
        """
        Synchronous wallet loading (runs in thread pool).

        This method performs blocking crypto operations.

        Raises:
            WalletSecurityError: If WIF is invalid or cannot be loaded
        """
        if self._initialized:
            return

        if not NEO_WALLET_AVAILABLE:
            # Fallback: Decode WIF to get address (simplified for demo)
            # This won't allow transaction signing but allows address/balance display
            try:
                wif = settings.demo_wallet_wif
                # Use simplified WIF decode for address extraction
                # This is a fallback until neo-mamba is properly installed
                self._address = self._wif_to_address_fallback(wif)
                self._initialized = True
                logger.warning(f"Wallet loaded in fallback mode (neo3 not installed): {self._address}")
                return
            except Exception as e:
                raise WalletSecurityError(
                    "Failed to load wallet in fallback mode. Install neo-mamba package."
                ) from e

        try:
            # Load private key from WIF using neo3/neo-mamba
            # CRITICAL: Never log the WIF value
            wif = settings.demo_wallet_wif

            # Create account from WIF
            # neo-mamba 2.x requires password parameter, 3.x does not
            import inspect
            sig = inspect.signature(NeoAccount.from_wif)
            if 'password' in sig.parameters:
                # neo-mamba 2.x: requires password for encryption
                self._account = NeoAccount.from_wif(wif, password="")
            else:
                # neo-mamba 3.x: no password parameter
                self._account = NeoAccount.from_wif(wif)

            # Extract address (public - safe to store)
            self._address = self._account.address

            self._initialized = True
            logger.info(f"Demo wallet loaded successfully: {self._address}")

        except Exception as e:
            logger.error(f"Failed to load demo wallet from WIF: {e}")
            # Do NOT include WIF in error message
            raise WalletSecurityError(
                "Failed to load demo wallet. Check DEMO_WALLET_WIF environment variable."
            ) from e

    async def _load_wallet(self) -> None:
        """
        Load wallet from WIF in environment (async wrapper).

        This method runs blocking crypto operations in a thread pool.

        Raises:
            WalletSecurityError: If WIF is invalid or cannot be loaded
        """
        if self._initialized:
            return

        # Run blocking operations in thread pool
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self._executor, self._load_wallet_sync)

    def _wif_to_address_fallback(self, wif: str) -> str:
        """
        Fallback WIF to address conversion (simplified).

        This is used when neo3/neo-mamba is not installed.
        Only provides address extraction for balance display.
        Cannot be used for transaction signing.

        Args:
            wif: Wallet Import Format private key

        Returns:
            Neo N3 address (estimated)

        Note: This is a simplified fallback. Install neo-mamba for full functionality.
        """
        # For demo/development, return a placeholder that looks like a Neo address
        # In production, neo-mamba MUST be installed
        try:
            # Verify WIF format (starts with K or L, 52 characters)
            if not wif or len(wif) != 52 or not wif[0] in ['K', 'L']:
                raise ValueError("Invalid WIF format")

            # Optionally decode with base58 if available
            if BASE58_AVAILABLE:
                try:
                    decoded = base58.b58decode(wif)
                    if len(decoded) != 38:  # Standard WIF length
                        raise ValueError("Invalid WIF length after decode")
                except Exception:
                    pass  # Continue with hash-based approach

            # Return a deterministic address based on WIF hash (for demo purposes)
            # This won't match the real address, but allows testing without neo-mamba
            # Neo N3 addresses are 34 characters long
            import hashlib
            wif_hash = hashlib.sha256(wif.encode()).hexdigest()[:32]
            return f"N{wif_hash}"  # 33 characters total (N + 32 hex chars)
        except Exception as e:
            raise ValueError(f"Invalid WIF format: {e}")

    async def get_address(self) -> str:
        """
        Get the demo wallet address.

        Returns:
            Neo N3 address (format: N...)

        Raises:
            WalletSecurityError: If wallet cannot be loaded
        """
        await self._load_wallet()
        if not self._address:
            raise WalletSecurityError("Wallet address not available")
        return self._address

    async def get_wallet_info(self) -> WalletInfo:
        """
        Get comprehensive wallet information including balances.

        Returns:
            WalletInfo with address and token balances

        Raises:
            WalletSecurityError: If wallet cannot be loaded
        """
        await self._load_wallet()

        if not self._address:
            raise WalletSecurityError("Wallet not initialized")

        # Get Neo service
        if self._neo_service is None:
            self._neo_service = await get_neo_service()

        # Fetch balances from Neo blockchain
        try:
            neo_address = await self._neo_service.get_balance(self._address)

            # Build balance list
            balances = [
                WalletBalance(
                    token="GAS",
                    balance=neo_address.gas_balance,
                    decimals=8
                ),
                WalletBalance(
                    token="NEO",
                    balance=neo_address.neo_balance,
                    decimals=0
                )
            ]

            return WalletInfo(
                address=self._address,
                balances=balances,
                network="testnet",
                timestamp=datetime.now(UTC)
            )

        except Exception as e:
            logger.error(f"Failed to fetch wallet balances: {e}")
            # Return wallet info with zero balances on error
            return WalletInfo(
                address=self._address,
                balances=[
                    WalletBalance(token="GAS", balance=Decimal("0"), decimals=8),
                    WalletBalance(token="NEO", balance=Decimal("0"), decimals=0)
                ],
                network="testnet",
                timestamp=datetime.now(UTC)
            )

    async def get_balance(self, token: str = "GAS") -> Decimal:
        """
        Get balance for a specific token.

        Args:
            token: Token symbol (GAS or NEO)

        Returns:
            Token balance

        Raises:
            ValueError: If token is not supported
            WalletSecurityError: If wallet cannot be loaded
        """
        if token.upper() not in ["GAS", "NEO"]:
            raise ValueError(f"Unsupported token: {token}. Supported: GAS, NEO")

        wallet_info = await self.get_wallet_info()

        for balance in wallet_info.balances:
            if balance.token == token.upper():
                return balance.balance

        return Decimal("0")

    async def get_account(self):
        """
        Get the Neo account object for transaction signing.

        WARNING: This method exposes the account with private key.
        Only use internally for transaction signing.
        NEVER expose this in API responses.

        Returns:
            Neo account object

        Raises:
            WalletSecurityError: If wallet cannot be loaded
        """
        await self._load_wallet()

        if not self._account:
            raise WalletSecurityError("Wallet account not available")

        return self._account

    def __repr__(self) -> str:
        """String representation (safe - no sensitive data)"""
        address_display = self._address if self._initialized else "not loaded"
        return f"WalletService(address={address_display})"


# Global service instance (singleton) with thread safety
_wallet_service: Optional[WalletService] = None
_wallet_service_lock = asyncio.Lock()


async def get_wallet_service() -> WalletService:
    """
    Get the global WalletService instance (thread-safe singleton).

    Returns:
        WalletService singleton instance
    """
    global _wallet_service

    # Double-check locking pattern for thread-safe singleton
    if _wallet_service is None:
        async with _wallet_service_lock:
            # Check again inside the lock
            if _wallet_service is None:
                _wallet_service = WalletService()

    return _wallet_service
