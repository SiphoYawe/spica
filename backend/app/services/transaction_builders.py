"""
Transaction builders for Neo N3 blockchain operations.

This module implements transaction builders for different workflow actions:
- SwapTransactionBuilder: Build swap transactions for Flamingo DEX
- StakeTransactionBuilder: Build staking transactions for Flamingo
- TransferTransactionBuilder: Build NEP-17 token transfer transactions

Implements Stories 5.2, 5.3, and 5.4
"""

import logging
import asyncio
import base64
from typing import Optional, Dict, Any
from decimal import Decimal
from datetime import datetime, UTC

try:
    from neo3.wallet.account import Account as NeoAccount
    from neo3.core import types
    from neo3.contracts import vm
    from neo3.core.cryptography import hash as neo_hash
    NEO3_AVAILABLE = True
except ImportError:
    NEO3_AVAILABLE = False
    NeoAccount = None
    types = None
    vm = None
    neo_hash = None

from app.config import settings
from app.services.execution_engine import (
    NeoExecutionEngine,
    get_execution_engine,
    TransactionResult,
    TransactionError
)
from app.services.neo_service import NeoService, get_neo_service
from app.models.workflow_models import (
    SwapAction,
    StakeAction,
    TransferAction,
    TokenType
)

logger = logging.getLogger(__name__)


# ============================================================================
# Contract Hashes (Neo N3 Testnet)
# ============================================================================

class ContractHashes:
    """Neo N3 contract hashes for testnet"""

    # Native tokens (same on mainnet and testnet)
    GAS = "0xd2a4cff31913016155e38e474a2c06d08be276cf"
    NEO = "0xef4073a0f2b305a38ec4050e4d3d28bc40ea63f5"

    # Flamingo DEX contracts (MOCK for hackathon - replace with real testnet hashes)
    # These are placeholder hashes for demo purposes
    FLAMINGO_SWAP_ROUTER = "0x1111111111111111111111111111111111111111"
    FLAMINGO_STAKE_POOL = "0x2222222222222222222222222222222222222222"

    # bNEO token contract (configurable via environment)
    BNEO = "0x48c40d4666f93408be1bef038b6722404d9a4c2a"  # Example testnet hash

    @classmethod
    def get_token_hash(cls, token: TokenType) -> str:
        """Get contract hash for a token type"""
        mapping = {
            TokenType.GAS: cls.GAS,
            TokenType.NEO: cls.NEO,
            TokenType.BNEO: cls.BNEO
        }
        return mapping[token]

    @classmethod
    def get_token_decimals(cls, token: TokenType) -> int:
        """Get decimals for a token type"""
        mapping = {
            TokenType.GAS: 8,
            TokenType.NEO: 0,
            TokenType.BNEO: 8
        }
        return mapping[token]


# ============================================================================
# Base Transaction Builder
# ============================================================================

class BaseTransactionBuilder:
    """Base class for all transaction builders"""

    def __init__(
        self,
        execution_engine: Optional[NeoExecutionEngine] = None,
        neo_service: Optional[NeoService] = None,
        demo_mode: bool = True
    ):
        """
        Initialize transaction builder.

        Args:
            execution_engine: Optional execution engine instance
            neo_service: Optional Neo service instance
            demo_mode: Enable demo mode (simulated transactions)
        """
        self._execution_engine = execution_engine
        self._neo_service = neo_service
        self.demo_mode = demo_mode

        if demo_mode:
            logger.info(f"{self.__class__.__name__} initialized in DEMO mode")
        else:
            logger.info(f"{self.__class__.__name__} initialized in LIVE mode")

    async def _get_execution_engine(self) -> NeoExecutionEngine:
        """Get or create execution engine instance"""
        if self._execution_engine is None:
            self._execution_engine = await get_execution_engine()
        return self._execution_engine

    async def _get_neo_service(self) -> NeoService:
        """Get or create Neo service instance"""
        if self._neo_service is None:
            self._neo_service = await get_neo_service()
        return self._neo_service

    async def _get_wallet_address(self) -> str:
        """Get the wallet address for the transaction"""
        engine = await self._get_execution_engine()
        return await engine.get_address()

    async def _validate_balance(
        self,
        token: TokenType,
        required_amount: Decimal
    ) -> bool:
        """
        Validate that wallet has sufficient balance.

        Args:
            token: Token type to check
            required_amount: Required amount

        Returns:
            True if balance is sufficient

        Raises:
            TransactionError: If balance is insufficient and not in demo mode
        """
        try:
            neo_service = await self._get_neo_service()
            address = await self._get_wallet_address()

            # Get balance from blockchain
            balance_info = await neo_service.get_balance(address)

            # Get current balance for the token
            if token == TokenType.GAS:
                current_balance = balance_info.gas_balance
            elif token == TokenType.NEO:
                current_balance = balance_info.neo_balance
            else:
                # For bNEO and other tokens, we'd need to query the contract
                logger.warning(f"Balance check for {token} not fully implemented, assuming sufficient")
                return True

            sufficient = current_balance >= required_amount

            if not sufficient:
                logger.warning(
                    f"Insufficient balance: have {current_balance} {token.value}, "
                    f"need {required_amount} {token.value}"
                )
                # In demo mode, log warning but allow to proceed
                if self.demo_mode:
                    logger.warning("Demo mode: proceeding despite insufficient balance")
                    return True
                else:
                    return False

            return True

        except Exception as e:
            logger.error(f"Error checking balance: {e}")
            # In demo mode, proceed anyway
            if self.demo_mode:
                logger.warning("Demo mode: skipping balance validation due to error")
                return True
            return False

    def _create_demo_transaction_result(
        self,
        operation: str,
        details: Dict[str, Any]
    ) -> TransactionResult:
        """
        Create a simulated transaction result for demo mode.

        Args:
            operation: Operation name
            details: Operation details

        Returns:
            Simulated TransactionResult
        """
        # Generate a fake but realistic-looking transaction hash
        import hashlib
        import secrets

        # Create deterministic but unique-looking hash
        hash_input = f"{operation}_{datetime.now(UTC).isoformat()}_{secrets.token_hex(8)}"
        fake_txid = hashlib.sha256(hash_input.encode()).hexdigest()[:64]

        logger.info(
            f"DEMO MODE: Simulated {operation} transaction\n"
            f"  Details: {details}\n"
            f"  Fake TXID: {fake_txid}"
        )

        return TransactionResult(
            txid=fake_txid,
            block_height=1234567,  # Fake block height
            confirmations=1,
            network_fee=Decimal("0.001"),  # Typical network fee
            system_fee=Decimal("0.01"),   # Typical system fee
            timestamp=datetime.now(UTC)
        )


# ============================================================================
# Story 5.2: Swap Transaction Builder
# ============================================================================

class SwapTransactionBuilder(BaseTransactionBuilder):
    """
    Build swap transactions for Flamingo DEX.

    Implements Story 5.2: Swap Transaction Builder

    Acceptance Criteria:
    - Build Flamingo swap invocation script
    - Support GAS ↔ bNEO swaps
    - Calculate expected output with slippage
    - Execute transaction on testnet
    - Return transaction hash
    - Handle swap failure
    """

    DEFAULT_SLIPPAGE_TOLERANCE = Decimal("0.01")  # 1%

    async def build_and_execute(
        self,
        action: SwapAction,
        slippage_tolerance: Optional[Decimal] = None
    ) -> TransactionResult:
        """
        Build and execute a swap transaction.

        Args:
            action: SwapAction specification
            slippage_tolerance: Maximum acceptable slippage (default: 1%)

        Returns:
            TransactionResult with swap transaction details

        Raises:
            TransactionError: If swap building or execution fails
        """
        slippage = slippage_tolerance or self.DEFAULT_SLIPPAGE_TOLERANCE

        # Determine swap amount
        if action.amount is not None:
            swap_amount = Decimal(str(action.amount))
        elif action.percentage is not None:
            # Calculate amount from percentage of balance
            neo_service = await self._get_neo_service()
            address = await self._get_wallet_address()
            balance_info = await neo_service.get_balance(address)

            if action.from_token == TokenType.GAS:
                balance = balance_info.gas_balance
            elif action.from_token == TokenType.NEO:
                balance = balance_info.neo_balance
            else:
                # For other tokens, use placeholder in demo mode
                balance = Decimal("100")

            swap_amount = balance * (Decimal(str(action.percentage)) / Decimal("100"))
        else:
            raise TransactionError("Swap action must specify either amount or percentage")

        logger.info(
            f"Building swap transaction: {swap_amount} {action.from_token.value} → "
            f"{action.to_token.value} (slippage: {slippage * 100}%)"
        )

        # Validate balance
        if not await self._validate_balance(action.from_token, swap_amount):
            raise TransactionError(
                f"Insufficient {action.from_token.value} balance for swap"
            )

        # Calculate expected output with slippage
        expected_output = await self._calculate_swap_output(
            action.from_token,
            action.to_token,
            swap_amount
        )
        min_output = expected_output * (Decimal("1") - slippage)

        logger.info(
            f"Expected output: {expected_output} {action.to_token.value} "
            f"(min with slippage: {min_output})"
        )

        # Demo mode: return simulated transaction
        if self.demo_mode:
            return self._create_demo_transaction_result(
                "swap",
                {
                    "from_token": action.from_token.value,
                    "to_token": action.to_token.value,
                    "from_amount": str(swap_amount),
                    "expected_output": str(expected_output),
                    "min_output": str(min_output),
                    "slippage_tolerance": str(slippage * 100) + "%"
                }
            )

        # Live mode: build and execute real transaction
        try:
            script = await self._build_swap_script(
                action.from_token,
                action.to_token,
                swap_amount,
                min_output
            )

            # Sign and execute transaction
            engine = await self._get_execution_engine()
            signed_tx = await self._sign_transaction(script, engine)

            result = await engine.execute_transaction(
                signed_tx,
                wait_for_confirmation=True
            )

            logger.info(f"Swap transaction executed successfully: {result.txid}")
            return result

        except Exception as e:
            logger.error(f"Swap transaction failed: {e}")
            raise TransactionError(f"Failed to execute swap: {e}") from e

    async def _calculate_swap_output(
        self,
        from_token: TokenType,
        to_token: TokenType,
        amount: Decimal
    ) -> Decimal:
        """
        Calculate expected swap output amount.

        In production, this would query the DEX for current pool prices.
        For demo, we use mock prices.

        Args:
            from_token: Source token
            to_token: Destination token
            amount: Amount to swap

        Returns:
            Expected output amount
        """
        # Mock exchange rates for demo (in production, query Flamingo DEX)
        mock_prices = {
            TokenType.GAS: Decimal("5.0"),   # $5 per GAS
            TokenType.NEO: Decimal("15.0"),  # $15 per NEO
            TokenType.BNEO: Decimal("14.5")  # $14.5 per bNEO (slight discount)
        }

        from_value = amount * mock_prices[from_token]
        output_amount = from_value / mock_prices[to_token]

        # Apply 0.3% swap fee (typical for AMMs)
        output_amount = output_amount * Decimal("0.997")

        return output_amount

    async def _build_swap_script(
        self,
        from_token: TokenType,
        to_token: TokenType,
        amount: Decimal,
        min_output: Decimal
    ) -> bytes:
        """
        Build Neo N3 VM script for swap transaction.

        This creates a script that calls the Flamingo swap router contract.

        Args:
            from_token: Source token
            to_token: Destination token
            amount: Amount to swap
            min_output: Minimum acceptable output

        Returns:
            Compiled VM script bytes
        """
        if not NEO3_AVAILABLE:
            raise TransactionError("neo3 library not available for script building")

        # Get contract hashes
        from_hash = ContractHashes.get_token_hash(from_token)
        to_hash = ContractHashes.get_token_hash(to_token)
        router_hash = ContractHashes.FLAMINGO_SWAP_ROUTER

        # Convert amount to contract units (with decimals)
        from_decimals = ContractHashes.get_token_decimals(from_token)
        amount_units = int(amount * (Decimal(10) ** from_decimals))

        to_decimals = ContractHashes.get_token_decimals(to_token)
        min_output_units = int(min_output * (Decimal(10) ** to_decimals))

        # Get wallet address
        address = await self._get_wallet_address()

        # Build script (pseudo-code - actual implementation would use neo3.contracts.vm)
        # This is a simplified example
        logger.info(
            f"Building swap script: router={router_hash}, "
            f"from={from_hash}, to={to_hash}, amount={amount_units}"
        )

        # For hackathon demo, return a placeholder script
        # In production, this would be a proper VM script calling Flamingo
        script = b'\x00' * 100  # Placeholder script

        return script

    async def _sign_transaction(
        self,
        script: bytes,
        engine: NeoExecutionEngine
    ) -> str:
        """
        Sign transaction script and return base64-encoded signed transaction.

        Args:
            script: VM script bytes
            engine: Execution engine with wallet

        Returns:
            Base64-encoded signed transaction
        """
        # This is a placeholder - actual implementation would:
        # 1. Create Transaction object with script
        # 2. Set network fee and system fee
        # 3. Add witnesses (signatures)
        # 4. Serialize and encode to base64

        # For demo, return a mock signed transaction
        signed_tx = base64.b64encode(script).decode('ascii')
        return signed_tx


# ============================================================================
# Story 5.3: Stake Transaction Builder
# ============================================================================

class StakeTransactionBuilder(BaseTransactionBuilder):
    """
    Build staking transactions for Flamingo.

    Implements Story 5.3: Stake Transaction Builder

    Acceptance Criteria:
    - Build Flamingo stake invocation script
    - Support bNEO staking
    - Execute transaction on testnet
    - Return transaction hash
    - Handle stake failure
    - Verify stake amount
    """

    async def build_and_execute(
        self,
        action: StakeAction
    ) -> TransactionResult:
        """
        Build and execute a staking transaction.

        Args:
            action: StakeAction specification

        Returns:
            TransactionResult with stake transaction details

        Raises:
            TransactionError: If staking building or execution fails
        """
        # Determine stake amount
        if action.amount is not None:
            stake_amount = Decimal(str(action.amount))
        elif action.percentage is not None:
            # Calculate amount from percentage of balance
            neo_service = await self._get_neo_service()
            address = await self._get_wallet_address()
            balance_info = await neo_service.get_balance(address)

            if action.token == TokenType.NEO:
                balance = balance_info.neo_balance
            elif action.token == TokenType.GAS:
                balance = balance_info.gas_balance
            else:
                # For bNEO and other tokens, use placeholder in demo mode
                balance = Decimal("100")

            stake_amount = balance * (Decimal(str(action.percentage)) / Decimal("100"))
        else:
            raise TransactionError("Stake action must specify either amount or percentage")

        logger.info(
            f"Building stake transaction: {stake_amount} {action.token.value}"
        )

        # Validate balance
        if not await self._validate_balance(action.token, stake_amount):
            raise TransactionError(
                f"Insufficient {action.token.value} balance for staking"
            )

        # Verify stake amount (must be positive and not dust)
        min_stake = Decimal("0.01")
        if stake_amount < min_stake:
            raise TransactionError(
                f"Stake amount too small: {stake_amount} < {min_stake} {action.token.value}"
            )

        # Demo mode: return simulated transaction
        if self.demo_mode:
            return self._create_demo_transaction_result(
                "stake",
                {
                    "token": action.token.value,
                    "amount": str(stake_amount),
                    "stake_pool": ContractHashes.FLAMINGO_STAKE_POOL
                }
            )

        # Live mode: build and execute real transaction
        try:
            script = await self._build_stake_script(action.token, stake_amount)

            # Sign and execute transaction
            engine = await self._get_execution_engine()
            signed_tx = await self._sign_transaction(script, engine)

            result = await engine.execute_transaction(
                signed_tx,
                wait_for_confirmation=True
            )

            logger.info(f"Stake transaction executed successfully: {result.txid}")
            return result

        except Exception as e:
            logger.error(f"Stake transaction failed: {e}")
            raise TransactionError(f"Failed to execute stake: {e}") from e

    async def _build_stake_script(
        self,
        token: TokenType,
        amount: Decimal
    ) -> bytes:
        """
        Build Neo N3 VM script for staking transaction.

        Args:
            token: Token to stake
            amount: Amount to stake

        Returns:
            Compiled VM script bytes
        """
        if not NEO3_AVAILABLE:
            raise TransactionError("neo3 library not available for script building")

        # Get contract hashes
        token_hash = ContractHashes.get_token_hash(token)
        pool_hash = ContractHashes.FLAMINGO_STAKE_POOL

        # Convert amount to contract units
        decimals = ContractHashes.get_token_decimals(token)
        amount_units = int(amount * (Decimal(10) ** decimals))

        # Get wallet address
        address = await self._get_wallet_address()

        logger.info(
            f"Building stake script: pool={pool_hash}, "
            f"token={token_hash}, amount={amount_units}"
        )

        # For hackathon demo, return a placeholder script
        script = b'\x00' * 80  # Placeholder script

        return script

    async def _sign_transaction(
        self,
        script: bytes,
        engine: NeoExecutionEngine
    ) -> str:
        """Sign transaction and return base64-encoded signed transaction"""
        # Placeholder - same pattern as swap builder
        signed_tx = base64.b64encode(script).decode('ascii')
        return signed_tx


# ============================================================================
# Story 5.4: Transfer Transaction Builder
# ============================================================================

class TransferTransactionBuilder(BaseTransactionBuilder):
    """
    Build NEP-17 token transfer transactions.

    Implements Story 5.4: Transfer Transaction Builder

    Acceptance Criteria:
    - Build NEP-17 transfer script
    - Support GAS, NEO, bNEO transfers
    - Validate recipient address format
    - Execute transaction on testnet
    - Return transaction hash
    - Handle insufficient balance
    """

    async def build_and_execute(
        self,
        action: TransferAction
    ) -> TransactionResult:
        """
        Build and execute a transfer transaction.

        Args:
            action: TransferAction specification

        Returns:
            TransactionResult with transfer transaction details

        Raises:
            TransactionError: If transfer building or execution fails
        """
        # Determine transfer amount
        if action.amount is not None:
            transfer_amount = Decimal(str(action.amount))
        elif action.percentage is not None:
            # Calculate amount from percentage of balance
            neo_service = await self._get_neo_service()
            address = await self._get_wallet_address()
            balance_info = await neo_service.get_balance(address)

            if action.token == TokenType.GAS:
                balance = balance_info.gas_balance
            elif action.token == TokenType.NEO:
                balance = balance_info.neo_balance
            else:
                # For bNEO and other tokens, use placeholder in demo mode
                balance = Decimal("100")

            transfer_amount = balance * (Decimal(str(action.percentage)) / Decimal("100"))
        else:
            raise TransactionError("Transfer action must specify either amount or percentage")

        logger.info(
            f"Building transfer transaction: {transfer_amount} {action.token.value} → {action.to_address}"
        )

        # Validate recipient address format
        await self._validate_recipient_address(action.to_address)

        # Validate balance
        if not await self._validate_balance(action.token, transfer_amount):
            raise TransactionError(
                f"Insufficient {action.token.value} balance for transfer"
            )

        # Demo mode: return simulated transaction
        if self.demo_mode:
            return self._create_demo_transaction_result(
                "transfer",
                {
                    "token": action.token.value,
                    "amount": str(transfer_amount),
                    "to_address": action.to_address,
                    "token_contract": ContractHashes.get_token_hash(action.token)
                }
            )

        # Live mode: build and execute real transaction
        try:
            script = await self._build_transfer_script(
                action.token,
                transfer_amount,
                action.to_address
            )

            # Sign and execute transaction
            engine = await self._get_execution_engine()
            signed_tx = await self._sign_transaction(script, engine)

            result = await engine.execute_transaction(
                signed_tx,
                wait_for_confirmation=True
            )

            logger.info(f"Transfer transaction executed successfully: {result.txid}")
            return result

        except Exception as e:
            logger.error(f"Transfer transaction failed: {e}")
            raise TransactionError(f"Failed to execute transfer: {e}") from e

    async def _validate_recipient_address(self, address: str) -> None:
        """
        Validate recipient address format.

        Args:
            address: Neo N3 address to validate

        Raises:
            TransactionError: If address format is invalid
        """
        # Basic format validation (already done in Pydantic model)
        if not address.startswith('N') or len(address) != 34:
            raise TransactionError(
                f"Invalid Neo N3 address format: {address}"
            )

        # Additional validation via RPC (if available)
        try:
            neo_service = await self._get_neo_service()
            is_valid = await neo_service.validate_address(address)

            if not is_valid:
                raise TransactionError(
                    f"Address failed RPC validation: {address}"
                )

            logger.info(f"Recipient address validated: {address}")

        except Exception as e:
            # In demo mode, log warning but continue
            if self.demo_mode:
                logger.warning(f"Could not validate address via RPC (demo mode): {e}")
            else:
                raise TransactionError(f"Address validation failed: {e}") from e

    async def _build_transfer_script(
        self,
        token: TokenType,
        amount: Decimal,
        to_address: str
    ) -> bytes:
        """
        Build Neo N3 VM script for NEP-17 transfer.

        This creates a script that calls the 'transfer' method of the token contract.

        Args:
            token: Token to transfer
            amount: Amount to transfer
            to_address: Recipient address

        Returns:
            Compiled VM script bytes
        """
        if not NEO3_AVAILABLE:
            raise TransactionError("neo3 library not available for script building")

        # Get contract hash
        token_hash = ContractHashes.get_token_hash(token)

        # Convert amount to contract units
        decimals = ContractHashes.get_token_decimals(token)
        amount_units = int(amount * (Decimal(10) ** decimals))

        # Get sender address
        from_address = await self._get_wallet_address()

        logger.info(
            f"Building transfer script: token={token_hash}, "
            f"from={from_address}, to={to_address}, amount={amount_units}"
        )

        # For hackathon demo, return a placeholder script
        # In production, this would build a proper NEP-17 transfer script:
        # - Convert addresses to script hashes
        # - Call token.transfer(from, to, amount, data)
        # - Add necessary witnesses

        script = b'\x00' * 90  # Placeholder script

        return script

    async def _sign_transaction(
        self,
        script: bytes,
        engine: NeoExecutionEngine
    ) -> str:
        """Sign transaction and return base64-encoded signed transaction"""
        # Placeholder - same pattern as other builders
        signed_tx = base64.b64encode(script).decode('ascii')
        return signed_tx


# ============================================================================
# Factory Functions
# ============================================================================

async def get_swap_builder(demo_mode: bool = True) -> SwapTransactionBuilder:
    """
    Get a SwapTransactionBuilder instance.

    Args:
        demo_mode: Enable demo mode (default: True for hackathon)

    Returns:
        SwapTransactionBuilder instance
    """
    return SwapTransactionBuilder(demo_mode=demo_mode)


async def get_stake_builder(demo_mode: bool = True) -> StakeTransactionBuilder:
    """
    Get a StakeTransactionBuilder instance.

    Args:
        demo_mode: Enable demo mode (default: True for hackathon)

    Returns:
        StakeTransactionBuilder instance
    """
    return StakeTransactionBuilder(demo_mode=demo_mode)


async def get_transfer_builder(demo_mode: bool = True) -> TransferTransactionBuilder:
    """
    Get a TransferTransactionBuilder instance.

    Args:
        demo_mode: Enable demo mode (default: True for hackathon)

    Returns:
        TransferTransactionBuilder instance
    """
    return TransferTransactionBuilder(demo_mode=demo_mode)
