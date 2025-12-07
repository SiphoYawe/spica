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
import os
from typing import Optional, Dict, Any
from decimal import Decimal
from datetime import datetime, UTC

try:
    from neo3.wallet.account import Account as NeoAccount
    from neo3.core import types
    from neo3.contracts import vm
    from neo3.contracts.vm import ScriptBuilder
    from neo3.vm import opcode
    from neo3.core.cryptography import hash as neo_hash
    from neo3.network import payloads
    NEO3_AVAILABLE = True
except ImportError:
    NEO3_AVAILABLE = False
    NeoAccount = None
    types = None
    vm = None
    ScriptBuilder = None
    opcode = None
    neo_hash = None
    payloads = None

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
        """Get contract hash for a token type using registry"""
        from app.services.contract_registry import get_contract_registry
        registry = get_contract_registry()
        return registry.get_token_hash(token.value)

    @classmethod
    def get_token_decimals(cls, token: TokenType) -> int:
        """Get decimals for a token type using registry"""
        from app.services.contract_registry import get_contract_registry
        registry = get_contract_registry()
        return registry.get_decimals(token.value)


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

    def _address_to_script_hash(self, address: str) -> str:
        """
        Convert Neo N3 address to script hash (big-endian hex).

        Args:
            address: Neo N3 address (e.g., NXXXxxxXXX...)

        Returns:
            Script hash as hex string with 0x prefix
        """
        if not NEO3_AVAILABLE or NeoAccount is None:
            raise TransactionError("neo3 library not available for address conversion")

        script_hash = NeoAccount.address_to_script_hash(address)
        return str(script_hash)

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

    async def _sign_transaction(
        self,
        script: bytes,
        signer_address: str,
        signer_wif: Optional[str] = None
    ) -> str:
        """
        Create and sign a Neo N3 transaction.

        Args:
            script: Neo VM script bytes
            signer_address: Address of the signer
            signer_wif: WIF private key (from env if not provided)

        Returns:
            Base64-encoded signed transaction
        """
        if not NEO3_AVAILABLE or payloads is None:
            raise TransactionError("neo3 library not available for transaction signing")

        from app.services.neo_rpc import get_neo_rpc

        rpc = await get_neo_rpc()

        # Get current block height for validity window
        block_height = await rpc.get_block_count()

        # Load account from WIF
        wif = signer_wif or settings.demo_wallet_wif
        if not wif:
            raise TransactionError("No wallet WIF configured")

        signer_account = NeoAccount.from_wif(wif)

        # Create transaction
        tx = payloads.Transaction(
            version=0,
            nonce=int.from_bytes(os.urandom(4), 'little'),
            system_fee=0,  # Will be calculated
            network_fee=0,  # Will be calculated
            valid_until_block=block_height + 5760,  # ~1 day
            attributes=[],
            signers=[
                payloads.Signer(
                    account=signer_account.script_hash,
                    scope=payloads.WitnessScope.CALLED_BY_ENTRY
                )
            ],
            script=script,
            witnesses=[]
        )

        # Calculate system fee via test invoke
        script_base64 = base64.b64encode(script).decode()
        invoke_result = await rpc.invoke_script(
            script_base64,
            [{"account": str(signer_account.script_hash), "scopes": "CalledByEntry"}]
        )

        if invoke_result.get("state") != "HALT":
            raise TransactionError(f"Script execution failed: {invoke_result.get('exception')}")

        system_fee = int(invoke_result["gasconsumed"])
        tx.system_fee = system_fee + 100000  # Add small buffer

        # Calculate network fee
        unsigned_tx_base64 = base64.b64encode(tx.to_array()).decode()
        network_fee = await rpc.calculate_network_fee(unsigned_tx_base64)
        tx.network_fee = network_fee

        # Sign transaction
        tx_hash = tx.hash()
        signature = signer_account.sign(tx_hash.to_array())

        # Create witness
        invocation_script_builder = ScriptBuilder()
        invocation_script_builder.emit_push(signature)

        verification_script = signer_account.contract.script

        tx.witnesses = [
            payloads.Witness(
                invocation_script=invocation_script_builder.to_array(),
                verification_script=verification_script
            )
        ]

        # Serialize to base64
        return base64.b64encode(tx.to_array()).decode()

    async def _broadcast_transaction(self, signed_tx: str) -> str:
        """
        Broadcast signed transaction to network.

        Args:
            signed_tx: Base64-encoded signed transaction

        Returns:
            Transaction hash
        """
        from app.services.neo_rpc import get_neo_rpc
        rpc = await get_neo_rpc()

        return await rpc.send_raw_transaction(signed_tx)

    async def _execute_transaction(
        self,
        script: bytes,
        signer_address: str,
        wait_confirmation: bool = True
    ) -> TransactionResult:
        """
        Sign, broadcast, and optionally wait for confirmation.

        Returns:
            TransactionResult with txid, block_height, etc.
        """
        from app.services.neo_rpc import get_neo_rpc
        rpc = await get_neo_rpc()

        # Sign
        signed_tx = await self._sign_transaction(script, signer_address)

        # Broadcast
        tx_hash = await self._broadcast_transaction(signed_tx)
        logger.info(f"Transaction broadcast: {tx_hash}")

        if wait_confirmation:
            # Wait for confirmation
            app_log = await rpc.wait_for_confirmation(tx_hash)

            # Extract details from log
            execution = app_log["executions"][0]
            gas_consumed = Decimal(execution["gasconsumed"]) / Decimal(10 ** 8)

            # Get transaction details
            tx_info = await rpc.get_raw_transaction(tx_hash)

            return TransactionResult(
                txid=tx_hash,
                block_height=tx_info.get("blockindex"),
                confirmations=tx_info.get("confirmations", 1),
                network_fee=Decimal(tx_info.get("netfee", 0)) / Decimal(10 ** 8),
                system_fee=Decimal(tx_info.get("sysfee", 0)) / Decimal(10 ** 8),
                timestamp=datetime.now(UTC)
            )
        else:
            return TransactionResult(
                txid=tx_hash,
                timestamp=datetime.now(UTC)
            )

    async def _get_token_balance(
        self,
        token: TokenType,
        address: str
    ) -> Decimal:
        """
        Get token balance for address.

        Args:
            token: Token type
            address: Neo N3 address

        Returns:
            Balance as Decimal
        """
        from app.services.neo_rpc import get_neo_rpc
        from app.services.contract_registry import get_contract_registry

        try:
            rpc = await get_neo_rpc()
            registry = get_contract_registry()

            if token == TokenType.GAS:
                return await rpc.get_gas_balance(address)
            elif token == TokenType.NEO:
                return Decimal(await rpc.get_neo_balance(address))
            else:
                # For bNEO and other tokens, query via balanceOf
                token_hash = registry.get_token_hash(token.value)
                decimals = registry.get_decimals(token.value)

                result = await rpc.invoke_function(
                    token_hash,
                    "balanceOf",
                    [{"type": "Hash160", "value": self._address_to_script_hash(address)}]
                )

                if result.get("state") == "HALT" and result.get("stack"):
                    balance_int = int(result["stack"][0].get("value", 0))
                    return Decimal(balance_int) / Decimal(10 ** decimals)

                return Decimal(0)

        except Exception as e:
            logger.warning(f"Failed to get balance for {token}: {e}")
            return Decimal(0)


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
            # Get user address
            user_address = await self._get_wallet_address()

            # Build script
            script = await self._build_swap_script(
                action.from_token,
                action.to_token,
                swap_amount,
                min_output,
                user_address
            )

            # Execute transaction (sign, broadcast, confirm)
            result = await self._execute_transaction(
                script,
                user_address,
                wait_confirmation=True
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
        Calculate expected swap output using Flamingo DEX.
        Queries the Router contract for expected output.
        """
        from app.services.neo_rpc import get_neo_rpc
        from app.services.contract_registry import get_contract_registry

        registry = get_contract_registry()

        from_hash = registry.get_token_hash(from_token.value)
        to_hash = registry.get_token_hash(to_token.value)
        router_hash = registry.get_flamingo_hash("SWAP_ROUTER")

        from_decimals = registry.get_decimals(from_token.value)
        to_decimals = registry.get_decimals(to_token.value)
        amount_int = int(amount * Decimal(10 ** from_decimals))

        try:
            rpc = await get_neo_rpc()

            # Call getAmountsOut on router
            result = await rpc.invoke_function(
                router_hash,
                "getAmountsOut",
                [
                    {"type": "Integer", "value": str(amount_int)},
                    {"type": "Array", "value": [
                        {"type": "Hash160", "value": from_hash},
                        {"type": "Hash160", "value": to_hash}
                    ]}
                ]
            )

            if result.get("state") != "HALT":
                logger.warning(f"getAmountsOut failed: {result.get('exception')}")
                # Fallback to mock calculation
                return await self._calculate_swap_output_mock(from_token, to_token, amount)

            # Parse output amount from stack
            stack = result.get("stack", [])
            if stack and stack[0].get("value"):
                amounts = stack[0]["value"]
                output_amount = int(amounts[-1]["value"])  # Last amount in path
                return Decimal(output_amount) / Decimal(10 ** to_decimals)

            # Fallback to mock
            return await self._calculate_swap_output_mock(from_token, to_token, amount)

        except Exception as e:
            logger.warning(f"Failed to query DEX for swap output: {e}")
            return await self._calculate_swap_output_mock(from_token, to_token, amount)

    async def _calculate_swap_output_mock(
        self,
        from_token: TokenType,
        to_token: TokenType,
        amount: Decimal
    ) -> Decimal:
        """Fallback mock calculation for swap output."""
        mock_prices = {
            TokenType.GAS: Decimal("5.0"),
            TokenType.NEO: Decimal("15.0"),
            TokenType.BNEO: Decimal("14.5")
        }

        from_value = amount * mock_prices.get(from_token, Decimal("1"))
        output_amount = from_value / mock_prices.get(to_token, Decimal("1"))

        # Apply 0.3% swap fee
        output_amount = output_amount * Decimal("0.997")

        return output_amount

    async def _build_swap_script(
        self,
        from_token: TokenType,
        to_token: TokenType,
        amount: Decimal,
        min_output: Decimal,
        user_address: str = None
    ) -> bytes:
        """
        Build Neo VM script for Flamingo DEX swap.

        Flamingo swap uses the Router contract:
        - Approve token spending
        - Call swap method with path and amounts
        """
        if not NEO3_AVAILABLE:
            raise TransactionError("neo3 library not available for script building")

        from app.services.contract_registry import get_contract_registry
        from datetime import datetime

        registry = get_contract_registry()

        # Get contract hashes
        from_hash = registry.get_token_hash(from_token.value)
        to_hash = registry.get_token_hash(to_token.value)
        router_hash = registry.get_flamingo_hash("SWAP_ROUTER")

        # Get decimals and convert amounts
        from_decimals = registry.get_decimals(from_token.value)
        to_decimals = registry.get_decimals(to_token.value)

        amount_int = int(amount * Decimal(10 ** from_decimals))
        min_output_int = int(min_output * Decimal(10 ** to_decimals))

        # Get user address if not provided
        if user_address is None:
            user_address = await self._get_wallet_address()

        user_hash = self._address_to_script_hash(user_address)

        sb = ScriptBuilder()

        # Step 1: Approve Router to spend from_token
        # transfer(from, router, amount, "approve")
        sb.emit_push(b"approve")  # data = "approve" signals approval
        sb.emit_push(amount_int)
        sb.emit_push(types.UInt160.from_string(router_hash[2:]).to_array())
        sb.emit_push(types.UInt160.from_string(user_hash[2:]).to_array())
        sb.emit_contract_call(
            types.UInt160.from_string(from_hash[2:]),
            "transfer"
        )
        sb.emit(opcode.OpCode.ASSERT)

        # Step 2: Call Router swap
        # swapTokenInForTokenOut(sender, amountIn, amountOutMin, path, deadline)
        deadline = int((datetime.utcnow().timestamp() + 600) * 1000)  # 10 min

        # Build path array [from_token, to_token]
        path_from = types.UInt160.from_string(from_hash[2:])
        path_to = types.UInt160.from_string(to_hash[2:])

        # Push swap parameters (reverse order for stack)
        sb.emit_push(deadline)

        # Pack path array
        sb.emit_push(path_to.to_array())
        sb.emit_push(path_from.to_array())
        sb.emit_push(2)  # Array length
        sb.emit(opcode.OpCode.PACK)

        sb.emit_push(min_output_int)
        sb.emit_push(amount_int)
        sb.emit_push(types.UInt160.from_string(user_hash[2:]).to_array())

        sb.emit_contract_call(
            types.UInt160.from_string(router_hash[2:]),
            "swapTokenInForTokenOut"
        )

        logger.info(
            f"Built Flamingo swap script:\n"
            f"  Router: {router_hash}\n"
            f"  Path: {from_token.value} ({from_hash}) -> {to_token.value} ({to_hash})\n"
            f"  Amount: {amount_int} units\n"
            f"  Min Output: {min_output_int} units\n"
            f"  Deadline: {deadline}"
        )

        return sb.to_array()


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
            user_address = await self._get_wallet_address()

            script = await self._build_stake_script(
                action.token,
                stake_amount,
                user_address
            )

            result = await self._execute_transaction(
                script,
                user_address,
                wait_confirmation=True
            )

            logger.info(f"Stake transaction executed successfully: {result.txid}")
            return result

        except Exception as e:
            logger.error(f"Stake transaction failed: {e}")
            raise TransactionError(f"Failed to execute stake: {e}") from e

    async def _build_stake_script(
        self,
        token: TokenType,
        amount: Decimal,
        user_address: str = None
    ) -> bytes:
        """
        Build Neo VM script for Flamingo staking.

        For bNEO staking:
        1. Transfer bNEO to staking pool
        2. Pool automatically mints reward tokens

        Args:
            token: Token to stake (bNEO)
            amount: Amount to stake
            user_address: User's Neo address

        Returns:
            Compiled Neo VM script bytes
        """
        if not NEO3_AVAILABLE:
            raise TransactionError("neo3 library not available for script building")

        from app.services.contract_registry import get_contract_registry

        registry = get_contract_registry()

        # Get contract hashes
        token_hash = registry.get_token_hash(token.value)
        pool_hash = registry.get_flamingo_hash("FLUND_TOKEN")  # FLUND pool for bNEO staking

        decimals = registry.get_decimals(token.value)
        amount_int = int(amount * Decimal(10 ** decimals))

        # Get user address if not provided
        if user_address is None:
            user_address = await self._get_wallet_address()

        user_hash = self._address_to_script_hash(user_address)

        sb = ScriptBuilder()

        # Transfer token to pool (stake)
        # The pool contract handles staking on receiving transfer
        # data parameter indicates staking operation
        sb.emit_push(b"stake")  # data parameter indicates staking
        sb.emit_push(amount_int)
        sb.emit_push(types.UInt160.from_string(pool_hash[2:]).to_array())
        sb.emit_push(types.UInt160.from_string(user_hash[2:]).to_array())
        sb.emit_contract_call(
            types.UInt160.from_string(token_hash[2:]),
            "transfer"
        )
        sb.emit(opcode.OpCode.ASSERT)

        logger.info(
            f"Built stake script: pool={pool_hash}, "
            f"token={token_hash}, amount={amount_int}, user={user_address}"
        )

        return sb.to_array()


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
            from_address = await self._get_wallet_address()

            script = await self._build_transfer_script(
                action.token,
                transfer_amount,
                action.to_address
            )

            result = await self._execute_transaction(
                script,
                from_address,
                wait_confirmation=True
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

        NEP-17 transfer call:
        - Contract: Token contract hash
        - Method: "transfer"
        - Args: [from (Hash160), to (Hash160), amount (Integer), data (Any)]

        Args:
            token: Token to transfer
            amount: Amount to transfer
            to_address: Recipient address

        Returns:
            Compiled VM script bytes
        """
        if not NEO3_AVAILABLE:
            raise TransactionError("neo3 library not available for script building")

        if ScriptBuilder is None or opcode is None:
            raise TransactionError("neo3 ScriptBuilder or opcode not available")

        from app.services.contract_registry import get_contract_registry

        registry = get_contract_registry()

        # Get contract hash and decimals
        token_hash = registry.get_token_hash(token.value)
        decimals = registry.get_decimals(token.value)

        # Convert amount to integer (handle decimals)
        amount_int = int(amount * Decimal(10 ** decimals))

        # Get sender address
        from_address = await self._get_wallet_address()

        # Convert addresses to script hashes
        from_hash = types.UInt160.from_string(
            self._address_to_script_hash(from_address)[2:]  # Remove 0x prefix
        )
        to_hash = types.UInt160.from_string(
            self._address_to_script_hash(to_address)[2:]  # Remove 0x prefix
        )
        contract_hash = types.UInt160.from_string(token_hash[2:])  # Remove 0x prefix

        logger.info(
            f"Building NEP-17 transfer script:\n"
            f"  Token: {token.value} ({token_hash})\n"
            f"  From: {from_address} (hash: {from_hash})\n"
            f"  To: {to_address} (hash: {to_hash})\n"
            f"  Amount: {amount} ({amount_int} units with {decimals} decimals)"
        )

        # Build script
        sb = ScriptBuilder()

        # Push arguments in reverse order (stack-based)
        sb.emit_push(None)                      # data parameter (null)
        sb.emit_push(amount_int)                # amount
        sb.emit_push(to_hash.to_array())        # to address
        sb.emit_push(from_hash.to_array())      # from address

        # Call contract method
        sb.emit_contract_call(contract_hash, "transfer")

        # Assert result is true
        sb.emit(opcode.OpCode.ASSERT)

        script_bytes = sb.to_array()
        logger.info(f"Generated NEP-17 transfer script: {len(script_bytes)} bytes")

        return script_bytes


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
