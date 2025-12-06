"""
Tests for transaction builders.

Tests Stories 5.2, 5.3, and 5.4:
- SwapTransactionBuilder
- StakeTransactionBuilder
- TransferTransactionBuilder
"""

import pytest
import asyncio
from decimal import Decimal
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from app.services.transaction_builders import (
    SwapTransactionBuilder,
    StakeTransactionBuilder,
    TransferTransactionBuilder,
    ContractHashes,
    get_swap_builder,
    get_stake_builder,
    get_transfer_builder
)
from app.services.execution_engine import TransactionResult, TransactionError
from app.services.neo_service import NeoAddress
from app.models.workflow_models import (
    SwapAction,
    StakeAction,
    TransferAction,
    TokenType
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_execution_engine():
    """Mock execution engine"""
    engine = AsyncMock()
    engine.get_address.return_value = "NTestWalletAddress1234567890abc"
    engine.execute_transaction.return_value = TransactionResult(
        txid="0xabcd1234" + "0" * 56,  # 64-char hex
        block_height=1234567,
        confirmations=1,
        network_fee=Decimal("0.001"),
        system_fee=Decimal("0.01")
    )
    return engine


@pytest.fixture
def mock_neo_service():
    """Mock Neo service"""
    service = AsyncMock()
    service.get_balance.return_value = NeoAddress(
        address="NTestWalletAddress1234567890abc",
        gas_balance=Decimal("100"),
        neo_balance=Decimal("50")
    )
    service.validate_address.return_value = True
    return service


# ============================================================================
# Story 5.2: Swap Transaction Builder Tests
# ============================================================================

class TestSwapTransactionBuilder:
    """Test SwapTransactionBuilder (Story 5.2)"""

    @pytest.mark.asyncio
    async def test_swap_builder_initialization(self):
        """Test swap builder can be initialized"""
        builder = SwapTransactionBuilder(demo_mode=True)
        assert builder.demo_mode is True
        assert builder.DEFAULT_SLIPPAGE_TOLERANCE == Decimal("0.01")

    @pytest.mark.asyncio
    async def test_swap_with_fixed_amount_demo_mode(
        self,
        mock_execution_engine,
        mock_neo_service
    ):
        """Test swap with fixed amount in demo mode"""
        # Arrange
        action = SwapAction(
            type="swap",
            from_token=TokenType.GAS,
            to_token=TokenType.NEO,
            amount=10.0
        )

        builder = SwapTransactionBuilder(
            execution_engine=mock_execution_engine,
            neo_service=mock_neo_service,
            demo_mode=True
        )

        # Act
        result = await builder.build_and_execute(action)

        # Assert
        assert result.txid is not None
        assert len(result.txid) == 64
        assert result.block_height == 1234567
        assert result.confirmations == 1

    @pytest.mark.asyncio
    async def test_swap_with_percentage_demo_mode(
        self,
        mock_execution_engine,
        mock_neo_service
    ):
        """Test swap with percentage in demo mode"""
        # Arrange
        action = SwapAction(
            type="swap",
            from_token=TokenType.GAS,
            to_token=TokenType.BNEO,
            percentage=25.0
        )

        builder = SwapTransactionBuilder(
            execution_engine=mock_execution_engine,
            neo_service=mock_neo_service,
            demo_mode=True
        )

        # Act
        result = await builder.build_and_execute(action)

        # Assert
        assert result.txid is not None
        # Verify balance was queried (called twice: once for amount calculation, once for validation)
        assert mock_neo_service.get_balance.call_count >= 1

    @pytest.mark.asyncio
    async def test_swap_calculates_expected_output(
        self,
        mock_execution_engine,
        mock_neo_service
    ):
        """Test swap calculates expected output with slippage"""
        # Arrange
        action = SwapAction(
            type="swap",
            from_token=TokenType.GAS,
            to_token=TokenType.NEO,
            amount=10.0
        )

        builder = SwapTransactionBuilder(
            execution_engine=mock_execution_engine,
            neo_service=mock_neo_service,
            demo_mode=True
        )

        # Act
        expected_output = await builder._calculate_swap_output(
            TokenType.GAS,
            TokenType.NEO,
            Decimal("10")
        )

        # Assert
        # GAS = $5, NEO = $15, so 10 GAS = $50 = 3.33 NEO
        # With 0.3% fee: 3.33 * 0.997 = ~3.32
        assert expected_output > Decimal("3.3")
        assert expected_output < Decimal("3.4")

    @pytest.mark.asyncio
    async def test_swap_with_custom_slippage(
        self,
        mock_execution_engine,
        mock_neo_service
    ):
        """Test swap with custom slippage tolerance"""
        # Arrange
        action = SwapAction(
            type="swap",
            from_token=TokenType.NEO,
            to_token=TokenType.GAS,
            amount=5.0
        )

        builder = SwapTransactionBuilder(
            execution_engine=mock_execution_engine,
            neo_service=mock_neo_service,
            demo_mode=True
        )

        # Act
        result = await builder.build_and_execute(
            action,
            slippage_tolerance=Decimal("0.05")  # 5% slippage
        )

        # Assert
        assert result.txid is not None

    @pytest.mark.asyncio
    async def test_swap_validates_balance_demo_mode(
        self,
        mock_execution_engine,
        mock_neo_service
    ):
        """Test swap proceeds in demo mode even with insufficient balance"""
        # Arrange - set low balance
        mock_neo_service.get_balance.return_value = NeoAddress(
            address="NTest",
            gas_balance=Decimal("1"),  # Only 1 GAS
            neo_balance=Decimal("0")
        )

        action = SwapAction(
            type="swap",
            from_token=TokenType.GAS,
            to_token=TokenType.NEO,
            amount=100.0  # Trying to swap 100 GAS
        )

        builder = SwapTransactionBuilder(
            execution_engine=mock_execution_engine,
            neo_service=mock_neo_service,
            demo_mode=True  # Demo mode allows this to proceed
        )

        # Act - should succeed in demo mode even with low balance
        result = await builder.build_and_execute(action)

        # Assert
        assert result.txid is not None

    @pytest.mark.asyncio
    async def test_swap_validates_balance_strict_mode(
        self,
        mock_execution_engine,
        mock_neo_service
    ):
        """Test swap fails in live mode with insufficient balance"""
        # Arrange - set low balance
        mock_neo_service.get_balance.return_value = NeoAddress(
            address="NTest",
            gas_balance=Decimal("1"),  # Only 1 GAS
            neo_balance=Decimal("0")
        )

        action = SwapAction(
            type="swap",
            from_token=TokenType.GAS,
            to_token=TokenType.NEO,
            amount=100.0
        )

        builder = SwapTransactionBuilder(
            execution_engine=mock_execution_engine,
            neo_service=mock_neo_service,
            demo_mode=False  # Live mode - strict validation
        )

        # Act & Assert
        with pytest.raises(TransactionError, match="Insufficient.*balance"):
            await builder.build_and_execute(action)

    @pytest.mark.asyncio
    async def test_swap_requires_amount_or_percentage(
        self,
        mock_execution_engine,
        mock_neo_service
    ):
        """Test swap fails if neither amount nor percentage specified"""
        # Arrange - create action with neither amount nor percentage
        # This should fail at model validation level
        with pytest.raises(ValueError):
            action = SwapAction(
                type="swap",
                from_token=TokenType.GAS,
                to_token=TokenType.NEO
            )


# ============================================================================
# Story 5.3: Stake Transaction Builder Tests
# ============================================================================

class TestStakeTransactionBuilder:
    """Test StakeTransactionBuilder (Story 5.3)"""

    @pytest.mark.asyncio
    async def test_stake_builder_initialization(self):
        """Test stake builder can be initialized"""
        builder = StakeTransactionBuilder(demo_mode=True)
        assert builder.demo_mode is True

    @pytest.mark.asyncio
    async def test_stake_with_fixed_amount_demo_mode(
        self,
        mock_execution_engine,
        mock_neo_service
    ):
        """Test stake with fixed amount in demo mode"""
        # Arrange
        action = StakeAction(
            type="stake",
            token=TokenType.BNEO,
            amount=50.0
        )

        builder = StakeTransactionBuilder(
            execution_engine=mock_execution_engine,
            neo_service=mock_neo_service,
            demo_mode=True
        )

        # Act
        result = await builder.build_and_execute(action)

        # Assert
        assert result.txid is not None
        assert len(result.txid) == 64
        assert result.confirmations == 1

    @pytest.mark.asyncio
    async def test_stake_with_percentage_demo_mode(
        self,
        mock_execution_engine,
        mock_neo_service
    ):
        """Test stake with percentage in demo mode"""
        # Arrange
        action = StakeAction(
            type="stake",
            token=TokenType.NEO,
            percentage=50.0
        )

        builder = StakeTransactionBuilder(
            execution_engine=mock_execution_engine,
            neo_service=mock_neo_service,
            demo_mode=True
        )

        # Act
        result = await builder.build_and_execute(action)

        # Assert
        assert result.txid is not None
        # Verify balance was queried (called at least once)
        assert mock_neo_service.get_balance.call_count >= 1

    @pytest.mark.asyncio
    async def test_stake_validates_minimum_amount(
        self,
        mock_execution_engine,
        mock_neo_service
    ):
        """Test stake validates minimum amount (no dust)"""
        # Arrange - stake amount below minimum
        action = StakeAction(
            type="stake",
            token=TokenType.BNEO,
            amount=0.001  # Below minimum
        )

        builder = StakeTransactionBuilder(
            execution_engine=mock_execution_engine,
            neo_service=mock_neo_service,
            demo_mode=True
        )

        # Act & Assert
        with pytest.raises(TransactionError, match="too small"):
            await builder.build_and_execute(action)

    @pytest.mark.asyncio
    async def test_stake_validates_balance_demo_mode(
        self,
        mock_execution_engine,
        mock_neo_service
    ):
        """Test stake proceeds in demo mode even with insufficient balance"""
        # Arrange - set low balance
        mock_neo_service.get_balance.return_value = NeoAddress(
            address="NTest",
            gas_balance=Decimal("1"),
            neo_balance=Decimal("5")
        )

        action = StakeAction(
            type="stake",
            token=TokenType.NEO,
            amount=100.0  # More than balance
        )

        builder = StakeTransactionBuilder(
            execution_engine=mock_execution_engine,
            neo_service=mock_neo_service,
            demo_mode=True  # Demo mode allows this
        )

        # Act - should succeed in demo mode
        result = await builder.build_and_execute(action)

        # Assert
        assert result.txid is not None

    @pytest.mark.asyncio
    async def test_stake_supports_different_tokens(
        self,
        mock_execution_engine,
        mock_neo_service
    ):
        """Test stake supports different token types"""
        # Test each supported token
        for token in [TokenType.NEO, TokenType.BNEO, TokenType.GAS]:
            action = StakeAction(
                type="stake",
                token=token,
                amount=10.0
            )

            builder = StakeTransactionBuilder(
                execution_engine=mock_execution_engine,
                neo_service=mock_neo_service,
                demo_mode=True
            )

            result = await builder.build_and_execute(action)
            assert result.txid is not None


# ============================================================================
# Story 5.4: Transfer Transaction Builder Tests
# ============================================================================

class TestTransferTransactionBuilder:
    """Test TransferTransactionBuilder (Story 5.4)"""

    @pytest.mark.asyncio
    async def test_transfer_builder_initialization(self):
        """Test transfer builder can be initialized"""
        builder = TransferTransactionBuilder(demo_mode=True)
        assert builder.demo_mode is True

    @pytest.mark.asyncio
    async def test_transfer_with_fixed_amount_demo_mode(
        self,
        mock_execution_engine,
        mock_neo_service
    ):
        """Test transfer with fixed amount in demo mode"""
        # Arrange
        action = TransferAction(
            type="transfer",
            token=TokenType.GAS,
            to_address="NVfJmhP28Q9qva9Tdtpt3af4H1a3cp7Lih",
            amount=25.0
        )

        builder = TransferTransactionBuilder(
            execution_engine=mock_execution_engine,
            neo_service=mock_neo_service,
            demo_mode=True
        )

        # Act
        result = await builder.build_and_execute(action)

        # Assert
        assert result.txid is not None
        assert len(result.txid) == 64

    @pytest.mark.asyncio
    async def test_transfer_with_percentage_demo_mode(
        self,
        mock_execution_engine,
        mock_neo_service
    ):
        """Test transfer with percentage in demo mode"""
        # Arrange
        action = TransferAction(
            type="transfer",
            token=TokenType.NEO,
            to_address="NVfJmhP28Q9qva9Tdtpt3af4H1a3cp7Lih",
            percentage=75.0
        )

        builder = TransferTransactionBuilder(
            execution_engine=mock_execution_engine,
            neo_service=mock_neo_service,
            demo_mode=True
        )

        # Act
        result = await builder.build_and_execute(action)

        # Assert
        assert result.txid is not None
        # Verify balance was queried
        mock_neo_service.get_balance.assert_called()

    @pytest.mark.asyncio
    async def test_transfer_validates_recipient_address_format(
        self,
        mock_execution_engine,
        mock_neo_service
    ):
        """Test transfer validates recipient address format"""
        # Arrange - invalid address (should fail at Pydantic level)
        with pytest.raises(ValueError):
            action = TransferAction(
                type="transfer",
                token=TokenType.GAS,
                to_address="InvalidAddress",  # Not Neo N3 format
                amount=10.0
            )

    @pytest.mark.asyncio
    async def test_transfer_validates_recipient_address_via_rpc(
        self,
        mock_execution_engine,
        mock_neo_service
    ):
        """Test transfer validates recipient address via RPC"""
        # Arrange
        action = TransferAction(
            type="transfer",
            token=TokenType.GAS,
            to_address="NVfJmhP28Q9qva9Tdtpt3af4H1a3cp7Lih",
            amount=10.0
        )

        builder = TransferTransactionBuilder(
            execution_engine=mock_execution_engine,
            neo_service=mock_neo_service,
            demo_mode=True
        )

        # Act
        result = await builder.build_and_execute(action)

        # Assert
        assert result.txid is not None
        # Verify address validation was called
        mock_neo_service.validate_address.assert_called_with(action.to_address)

    @pytest.mark.asyncio
    async def test_transfer_handles_invalid_address_from_rpc(
        self,
        mock_execution_engine,
        mock_neo_service
    ):
        """Test transfer handles invalid address from RPC"""
        # Arrange - RPC says address is invalid
        mock_neo_service.validate_address.return_value = False

        action = TransferAction(
            type="transfer",
            token=TokenType.GAS,
            to_address="NVfJmhP28Q9qva9Tdtpt3af4H1a3cp7Lih",
            amount=10.0
        )

        builder = TransferTransactionBuilder(
            execution_engine=mock_execution_engine,
            neo_service=mock_neo_service,
            demo_mode=True  # Demo mode - should log warning but continue
        )

        # Act - in demo mode, should proceed despite invalid address
        result = await builder.build_and_execute(action)

        # Assert
        assert result.txid is not None

    @pytest.mark.asyncio
    async def test_transfer_validates_balance_demo_mode(
        self,
        mock_execution_engine,
        mock_neo_service
    ):
        """Test transfer proceeds in demo mode even with insufficient balance"""
        # Arrange - low balance
        mock_neo_service.get_balance.return_value = NeoAddress(
            address="NTest",
            gas_balance=Decimal("5"),
            neo_balance=Decimal("0")
        )

        action = TransferAction(
            type="transfer",
            token=TokenType.GAS,
            to_address="NVfJmhP28Q9qva9Tdtpt3af4H1a3cp7Lih",
            amount=100.0  # More than balance
        )

        builder = TransferTransactionBuilder(
            execution_engine=mock_execution_engine,
            neo_service=mock_neo_service,
            demo_mode=True  # Demo mode allows this
        )

        # Act - should succeed in demo mode
        result = await builder.build_and_execute(action)

        # Assert
        assert result.txid is not None

    @pytest.mark.asyncio
    async def test_transfer_supports_all_token_types(
        self,
        mock_execution_engine,
        mock_neo_service
    ):
        """Test transfer supports GAS, NEO, and bNEO"""
        # Test each token type
        for token in [TokenType.GAS, TokenType.NEO, TokenType.BNEO]:
            action = TransferAction(
                type="transfer",
                token=token,
                to_address="NVfJmhP28Q9qva9Tdtpt3af4H1a3cp7Lih",
                amount=10.0
            )

            builder = TransferTransactionBuilder(
                execution_engine=mock_execution_engine,
                neo_service=mock_neo_service,
                demo_mode=True
            )

            result = await builder.build_and_execute(action)
            assert result.txid is not None


# ============================================================================
# Contract Hashes Tests
# ============================================================================

class TestContractHashes:
    """Test ContractHashes utility class"""

    def test_get_token_hash(self):
        """Test getting token contract hashes"""
        assert ContractHashes.get_token_hash(TokenType.GAS) == ContractHashes.GAS
        assert ContractHashes.get_token_hash(TokenType.NEO) == ContractHashes.NEO
        assert ContractHashes.get_token_hash(TokenType.BNEO) == ContractHashes.BNEO

    def test_get_token_decimals(self):
        """Test getting token decimals"""
        assert ContractHashes.get_token_decimals(TokenType.GAS) == 8
        assert ContractHashes.get_token_decimals(TokenType.NEO) == 0
        assert ContractHashes.get_token_decimals(TokenType.BNEO) == 8

    def test_gas_hash_format(self):
        """Test GAS contract hash is valid format"""
        assert ContractHashes.GAS.startswith("0x")
        assert len(ContractHashes.GAS) == 42  # 0x + 40 hex chars

    def test_neo_hash_format(self):
        """Test NEO contract hash is valid format"""
        assert ContractHashes.NEO.startswith("0x")
        assert len(ContractHashes.NEO) == 42


# ============================================================================
# Factory Function Tests
# ============================================================================

class TestFactoryFunctions:
    """Test factory functions for builders"""

    @pytest.mark.asyncio
    async def test_get_swap_builder(self):
        """Test get_swap_builder factory"""
        builder = await get_swap_builder(demo_mode=True)
        assert isinstance(builder, SwapTransactionBuilder)
        assert builder.demo_mode is True

    @pytest.mark.asyncio
    async def test_get_stake_builder(self):
        """Test get_stake_builder factory"""
        builder = await get_stake_builder(demo_mode=False)
        assert isinstance(builder, StakeTransactionBuilder)
        assert builder.demo_mode is False

    @pytest.mark.asyncio
    async def test_get_transfer_builder(self):
        """Test get_transfer_builder factory"""
        builder = await get_transfer_builder(demo_mode=True)
        assert isinstance(builder, TransferTransactionBuilder)
        assert builder.demo_mode is True


# ============================================================================
# Integration Tests
# ============================================================================

class TestTransactionBuildersIntegration:
    """Integration tests for transaction builders"""

    @pytest.mark.asyncio
    async def test_swap_to_stake_workflow(
        self,
        mock_execution_engine,
        mock_neo_service
    ):
        """Test complete workflow: swap then stake"""
        # Step 1: Swap GAS to bNEO
        swap_action = SwapAction(
            type="swap",
            from_token=TokenType.GAS,
            to_token=TokenType.BNEO,
            amount=50.0
        )

        swap_builder = SwapTransactionBuilder(
            execution_engine=mock_execution_engine,
            neo_service=mock_neo_service,
            demo_mode=True
        )

        swap_result = await swap_builder.build_and_execute(swap_action)
        assert swap_result.txid is not None

        # Step 2: Stake the bNEO
        stake_action = StakeAction(
            type="stake",
            token=TokenType.BNEO,
            amount=50.0
        )

        stake_builder = StakeTransactionBuilder(
            execution_engine=mock_execution_engine,
            neo_service=mock_neo_service,
            demo_mode=True
        )

        stake_result = await stake_builder.build_and_execute(stake_action)
        assert stake_result.txid is not None

        # Verify two different transactions
        assert swap_result.txid != stake_result.txid

    @pytest.mark.asyncio
    async def test_multiple_transfers(
        self,
        mock_execution_engine,
        mock_neo_service
    ):
        """Test multiple sequential transfers"""
        addresses = [
            "NVfJmhP28Q9qva9Tdtpt3af4H1a3cp7Lih",
            "NYxb4fSZVKAz8YsgaPK2WkT3KcAE9b3Vag",
            "NZs2zXSPuuv9ZF6TDGSWT1RBmE8rfGj7UW"
        ]

        builder = TransferTransactionBuilder(
            execution_engine=mock_execution_engine,
            neo_service=mock_neo_service,
            demo_mode=True
        )

        txids = []
        for address in addresses:
            action = TransferAction(
                type="transfer",
                token=TokenType.GAS,
                to_address=address,
                amount=10.0
            )

            result = await builder.build_and_execute(action)
            txids.append(result.txid)

        # Verify all transactions succeeded and have unique txids
        assert len(txids) == 3
        assert len(set(txids)) == 3  # All unique


# ============================================================================
# Error Handling Tests
# ============================================================================

class TestErrorHandling:
    """Test error handling in transaction builders"""

    @pytest.mark.asyncio
    async def test_swap_handles_network_error(
        self,
        mock_execution_engine,
        mock_neo_service
    ):
        """Test swap handles network errors gracefully"""
        # Arrange - make balance query fail
        mock_neo_service.get_balance.side_effect = Exception("Network error")

        action = SwapAction(
            type="swap",
            from_token=TokenType.GAS,
            to_token=TokenType.NEO,
            percentage=50.0
        )

        builder = SwapTransactionBuilder(
            execution_engine=mock_execution_engine,
            neo_service=mock_neo_service,
            demo_mode=True
        )

        # Act & Assert
        with pytest.raises(Exception):
            await builder.build_and_execute(action)

    @pytest.mark.asyncio
    async def test_transfer_handles_address_validation_error(
        self,
        mock_execution_engine,
        mock_neo_service
    ):
        """Test transfer handles address validation errors"""
        # Arrange - make address validation fail
        mock_neo_service.validate_address.side_effect = Exception("RPC error")

        action = TransferAction(
            type="transfer",
            token=TokenType.GAS,
            to_address="NVfJmhP28Q9qva9Tdtpt3af4H1a3cp7Lih",
            amount=10.0
        )

        builder = TransferTransactionBuilder(
            execution_engine=mock_execution_engine,
            neo_service=mock_neo_service,
            demo_mode=True  # Demo mode should handle this gracefully
        )

        # Act - should succeed in demo mode despite validation error
        result = await builder.build_and_execute(action)

        # Assert
        assert result.txid is not None
