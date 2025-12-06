"""
Unit tests for Neo Execution Engine

Tests Story 5.1: Neo Execution Engine acceptance criteria:
- NeoExecutionEngine class created ✓
- Connects to testnet RPC ✓
- Signs transactions with demo wallet ✓
- Handles transaction confirmation ✓
- Returns transaction hash on success ✓
- Handles errors gracefully ✓
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from decimal import Decimal
from datetime import datetime, UTC

from app.services.execution_engine import (
    NeoExecutionEngine,
    TransactionResult,
    TransactionError,
    TransactionBroadcastError,
    TransactionConfirmationError,
    get_execution_engine,
    close_execution_engine
)
from app.services.neo_service import NeoRPCError, NeoConnectionError


class TestTransactionResult:
    """Test TransactionResult model"""

    def test_transaction_result_creation(self):
        """Test creating a transaction result"""
        result = TransactionResult(
            txid="0x1234567890abcdef",
            block_height=1000,
            confirmations=3,
            network_fee=Decimal("0.001"),
            system_fee=Decimal("0.002")
        )

        assert result.txid == "0x1234567890abcdef"
        assert result.block_height == 1000
        assert result.confirmations == 3
        assert result.network_fee == Decimal("0.001")
        assert result.system_fee == Decimal("0.002")
        assert isinstance(result.timestamp, datetime)

    def test_transaction_result_to_dict(self):
        """Test converting transaction result to dictionary"""
        result = TransactionResult(
            txid="0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
            block_height=500,
            confirmations=1
        )

        result_dict = result.to_dict()

        assert result_dict["txid"] == "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        assert result_dict["block_height"] == 500
        assert result_dict["confirmations"] == 1
        assert "timestamp" in result_dict

    def test_transaction_result_repr(self):
        """Test string representation"""
        result = TransactionResult(txid="0xtest", confirmations=2)
        repr_str = repr(result)

        assert "0xtest" in repr_str
        assert "confirmations=2" in repr_str


class TestNeoExecutionEngine:
    """Test NeoExecutionEngine class"""

    @pytest.fixture
    def mock_neo_service(self):
        """Create a mock NeoService"""
        service = AsyncMock()
        service.connect_testnet = AsyncMock(return_value={
            "connected": True,
            "block_height": 1000
        })
        service.get_block_height = AsyncMock(return_value=1000)
        service.get_transaction = AsyncMock(return_value=None)
        service._rpc_call = AsyncMock()
        service.close = AsyncMock()
        return service

    @pytest.fixture
    def mock_account(self):
        """Create a mock Neo account"""
        account = Mock()
        account.address = "NTest123456789012345678901234567"
        account.sign_tx = Mock()
        return account

    @pytest.fixture
    def engine(self, mock_neo_service, event_loop):
        """Create a NeoExecutionEngine with mocked dependencies"""
        with patch('app.services.execution_engine.NEO3_AVAILABLE', True):
            with patch('app.services.execution_engine.get_neo_service', return_value=mock_neo_service):
                with patch('app.services.execution_engine.NeoAccount') as mock_account_class:
                    # Mock Account.from_wif to return a mock account
                    mock_account = Mock()
                    mock_account.address = "NTest123456789012345678901234567"
                    mock_account_class.from_wif = Mock(return_value=mock_account)

                    engine = NeoExecutionEngine(neo_service=mock_neo_service)
                    event_loop.run_until_complete(engine._initialize())
                    yield engine

    @pytest.mark.asyncio
    async def test_engine_initialization(self, engine):
        """Test engine initializes correctly"""
        assert engine._initialized is True
        assert engine._address == "NTest123456789012345678901234567"
        assert engine._account is not None

    @pytest.mark.asyncio
    async def test_engine_initialization_wallet_error(self, mock_neo_service):
        """Test engine handles wallet loading errors"""
        with patch('app.services.execution_engine.NEO3_AVAILABLE', True):
            with patch('app.services.execution_engine.get_neo_service', return_value=mock_neo_service):
                with patch('app.services.execution_engine.NeoAccount') as mock_account_class:
                    mock_account_class.from_wif = Mock(side_effect=Exception("Invalid WIF"))

                    engine = NeoExecutionEngine(neo_service=mock_neo_service)

                    with pytest.raises(TransactionError) as exc_info:
                        await engine._initialize()

                    assert "Failed to load demo wallet" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_engine_initialization_connection_error(self, mock_neo_service):
        """Test engine handles RPC connection errors"""
        mock_neo_service.connect_testnet = AsyncMock(
            side_effect=NeoConnectionError("Connection failed")
        )

        with patch('app.services.execution_engine.NEO3_AVAILABLE', True):
            with patch('app.services.execution_engine.get_neo_service', return_value=mock_neo_service):
                with patch('app.services.execution_engine.NeoAccount') as mock_account_class:
                    mock_account = Mock()
                    mock_account.address = "NTest123456789012345678901234567"
                    mock_account_class.from_wif = Mock(return_value=mock_account)

                    engine = NeoExecutionEngine(neo_service=mock_neo_service)

                    with pytest.raises(NeoConnectionError) as exc_info:
                        await engine._initialize()

                    assert "Failed to connect to Neo N3 testnet" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_address(self, engine):
        """Test getting wallet address"""
        address = await engine.get_address()
        assert address == "NTest123456789012345678901234567"

    @pytest.mark.asyncio
    async def test_send_raw_transaction_success(self, engine, mock_neo_service):
        """Test successful transaction broadcast"""
        mock_neo_service._rpc_call = AsyncMock(return_value={
            "hash": "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
        })

        txid = await engine.send_raw_transaction("dGVzdF90cmFuc2FjdGlvbl9kYXRhXzEyMzQ1")

        assert txid == "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
        mock_neo_service._rpc_call.assert_called_once_with(
            "sendrawtransaction",
            ["dGVzdF90cmFuc2FjdGlvbl9kYXRhXzEyMzQ1"]
        )

    @pytest.mark.asyncio
    async def test_send_raw_transaction_already_exists(self, engine, mock_neo_service):
        """Test broadcast error when transaction already exists"""
        mock_neo_service._rpc_call = AsyncMock(
            side_effect=NeoRPCError("AlreadyExists")
        )

        with pytest.raises(TransactionBroadcastError) as exc_info:
            await engine.send_raw_transaction("dGVzdF90cmFuc2FjdGlvbl9kYXRhXzEyMzQ1")

        assert "already exists" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_send_raw_transaction_insufficient_funds(self, engine, mock_neo_service):
        """Test broadcast error for insufficient funds"""
        mock_neo_service._rpc_call = AsyncMock(
            side_effect=NeoRPCError("InsufficientFunds")
        )

        with pytest.raises(TransactionBroadcastError) as exc_info:
            await engine.send_raw_transaction("dGVzdF90cmFuc2FjdGlvbl9kYXRhXzEyMzQ1")

        assert "insufficient funds" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_send_raw_transaction_expired(self, engine, mock_neo_service):
        """Test broadcast error for expired transaction"""
        mock_neo_service._rpc_call = AsyncMock(
            side_effect=NeoRPCError("Expired")
        )

        with pytest.raises(TransactionBroadcastError) as exc_info:
            await engine.send_raw_transaction("dGVzdF90cmFuc2FjdGlvbl9kYXRhXzEyMzQ1")

        assert "expired" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_send_raw_transaction_invalid(self, engine, mock_neo_service):
        """Test broadcast error for invalid transaction"""
        mock_neo_service._rpc_call = AsyncMock(
            side_effect=NeoRPCError("Invalid transaction")
        )

        with pytest.raises(TransactionBroadcastError) as exc_info:
            await engine.send_raw_transaction("dGVzdF90cmFuc2FjdGlvbl9kYXRhXzEyMzQ1")

        assert "invalid" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_send_raw_transaction_memory_pool_full(self, engine, mock_neo_service):
        """Test broadcast error when memory pool is full"""
        mock_neo_service._rpc_call = AsyncMock(
            side_effect=NeoRPCError("OutOfMemory")
        )

        with pytest.raises(TransactionBroadcastError) as exc_info:
            await engine.send_raw_transaction("dGVzdF90cmFuc2FjdGlvbl9kYXRhXzEyMzQ1")

        assert "memory pool" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_wait_for_confirmation_immediate(self, engine, mock_neo_service):
        """Test waiting for confirmation when transaction is already confirmed"""
        # Mock transaction already in block
        mock_neo_service.get_transaction = AsyncMock(return_value={
            "blockheight": 995,
            "netfee": "100000000",  # 1 GAS
            "sysfee": "200000000"   # 2 GAS
        })
        mock_neo_service.get_block_height = AsyncMock(return_value=1000)

        result = await engine.wait_for_confirmation("0xtest123", min_confirmations=1)

        assert result.txid == "0xtest123"
        assert result.block_height == 995
        assert result.confirmations == 6  # (1000 - 995) + 1
        assert result.network_fee == Decimal("1.0")
        assert result.system_fee == Decimal("2.0")

    @pytest.mark.asyncio
    async def test_wait_for_confirmation_polling(self, engine, mock_neo_service):
        """Test waiting for confirmation with polling"""
        # First call: not in block yet
        # Second call: in block with 1 confirmation
        call_count = 0

        async def mock_get_transaction(txid):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return None  # Not yet in block
            else:
                return {
                    "blockheight": 999,
                    "netfee": "50000000",
                    "sysfee": "100000000"
                }

        mock_neo_service.get_transaction = mock_get_transaction
        mock_neo_service.get_block_height = AsyncMock(return_value=1000)

        result = await engine.wait_for_confirmation(
            "0xtest123",
            min_confirmations=1,
            poll_interval=0.1  # Fast polling for tests
        )

        assert result.txid == "0xtest123"
        assert result.block_height == 999
        assert result.confirmations == 2  # (1000 - 999) + 1
        assert call_count == 2  # Should have polled twice

    @pytest.mark.asyncio
    async def test_wait_for_confirmation_timeout(self, engine, mock_neo_service):
        """Test confirmation timeout"""
        # Always return None (never confirmed)
        mock_neo_service.get_transaction = AsyncMock(return_value=None)

        with pytest.raises(TransactionConfirmationError) as exc_info:
            await engine.wait_for_confirmation(
                "0xtest123",
                min_confirmations=1,
                timeout=1,  # 1 second timeout
                poll_interval=0.1
            )

        assert "timed out" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_wait_for_confirmation_network_error_retry(self, engine, mock_neo_service):
        """Test that network errors during confirmation are retried"""
        call_count = 0

        async def mock_get_transaction(txid):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise NeoConnectionError("Network error")
            else:
                return {
                    "blockheight": 999,
                    "netfee": "0",
                    "sysfee": "0"
                }

        mock_neo_service.get_transaction = mock_get_transaction
        mock_neo_service.get_block_height = AsyncMock(return_value=1000)

        result = await engine.wait_for_confirmation(
            "0xtest123",
            min_confirmations=1,
            poll_interval=0.1
        )

        assert result.txid == "0xtest123"
        assert call_count == 2  # Should have retried after network error

    @pytest.mark.asyncio
    async def test_wait_for_confirmation_min_confirmations(self, engine, mock_neo_service):
        """Test waiting for multiple confirmations"""
        call_count = 0

        mock_neo_service.get_transaction = AsyncMock(return_value={
            "blockheight": 997,  # Changed to 997 to require more polling
            "netfee": "0",
            "sysfee": "0"
        })

        # Track calls to get_block_height - simulate blockchain progressing
        async def track_calls():
            nonlocal call_count
            call_count += 1
            # First call: 998 (2 conf), second call: 999 (3 conf)
            # Confirmations = (current - 997) + 1
            return 997 + call_count

        mock_neo_service.get_block_height = track_calls

        result = await engine.wait_for_confirmation(
            "0xtest123",
            min_confirmations=3,
            poll_interval=0.05
        )

        assert result.confirmations >= 3
        # Should reach 3 confirmations on second call: (999 - 997) + 1 = 3
        assert call_count >= 2

    @pytest.mark.asyncio
    async def test_execute_transaction_with_confirmation(self, engine, mock_neo_service):
        """Test complete transaction execution with confirmation"""
        # Mock broadcast
        mock_neo_service._rpc_call = AsyncMock(return_value={
            "hash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        })

        # Mock confirmation
        mock_neo_service.get_transaction = AsyncMock(return_value={
            "blockheight": 999,
            "netfee": "100000000",
            "sysfee": "200000000"
        })
        mock_neo_service.get_block_height = AsyncMock(return_value=1000)

        result = await engine.execute_transaction(
            "dGVzdF90cmFuc2FjdGlvbl9kYXRhXzEyMzQ1",
            wait_for_confirmation=True,
            min_confirmations=1
        )

        assert result.txid == "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        assert result.block_height == 999
        assert result.confirmations >= 1

    @pytest.mark.asyncio
    async def test_execute_transaction_without_confirmation(self, engine, mock_neo_service):
        """Test transaction execution without waiting for confirmation"""
        mock_neo_service._rpc_call = AsyncMock(return_value={
            "hash": "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        })

        result = await engine.execute_transaction(
            "dGVzdF90cmFuc2FjdGlvbl9kYXRhXzEyMzQ1",
            wait_for_confirmation=False
        )

        assert result.txid == "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        assert result.confirmations == 0
        assert result.block_height is None

        # Should not have called get_transaction
        mock_neo_service.get_transaction.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_account(self, engine):
        """Test getting account for signing"""
        account = await engine.get_account()
        assert account is not None
        assert account.address == "NTest123456789012345678901234567"

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_neo_service):
        """Test using engine as context manager"""
        with patch('app.services.execution_engine.NEO3_AVAILABLE', True):
            with patch('app.services.execution_engine.get_neo_service', return_value=mock_neo_service):
                with patch('app.services.execution_engine.NeoAccount') as mock_account_class:
                    mock_account = Mock()
                    mock_account.address = "NTest123456789012345678901234567"
                    mock_account_class.from_wif = Mock(return_value=mock_account)

                    async with NeoExecutionEngine(neo_service=mock_neo_service) as engine:
                        assert engine._initialized is True
                        assert engine._address is not None

                    # After context exit, close should have been called
                    mock_neo_service.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_engine_close(self, engine, mock_neo_service):
        """Test closing the engine"""
        await engine.close()
        mock_neo_service.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_engine_repr(self, engine):
        """Test string representation"""
        repr_str = repr(engine)
        assert "NeoExecutionEngine" in repr_str
        assert "NTest123456789012345678901234567" in repr_str

    @pytest.mark.asyncio
    async def test_engine_repr_not_initialized(self, mock_neo_service):
        """Test string representation before initialization"""
        with patch('app.services.execution_engine.get_neo_service', return_value=mock_neo_service):
            engine = NeoExecutionEngine(neo_service=mock_neo_service)
            repr_str = repr(engine)
            assert "not initialized" in repr_str


class TestSingletonPattern:
    """Test singleton pattern for global engine instance"""

    @pytest.mark.asyncio
    async def test_get_execution_engine_singleton(self):
        """Test that get_execution_engine returns singleton"""
        with patch('app.services.execution_engine.NeoExecutionEngine') as mock_engine_class:
            mock_engine = AsyncMock()
            mock_engine_class.return_value = mock_engine

            # Clear singleton
            import app.services.execution_engine as engine_module
            engine_module._execution_engine = None

            # First call
            engine1 = await get_execution_engine()
            # Second call
            engine2 = await get_execution_engine()

            # Should be same instance
            assert engine1 is engine2
            # Constructor should only be called once
            assert mock_engine_class.call_count == 1

    @pytest.mark.asyncio
    async def test_close_execution_engine_singleton(self):
        """Test closing the singleton engine"""
        with patch('app.services.execution_engine.NeoExecutionEngine') as mock_engine_class:
            mock_engine = AsyncMock()
            mock_engine.close = AsyncMock()
            mock_engine_class.return_value = mock_engine

            # Clear singleton
            import app.services.execution_engine as engine_module
            engine_module._execution_engine = None

            # Create engine
            engine = await get_execution_engine()

            # Close it
            await close_execution_engine()

            # Should have called close
            mock_engine.close.assert_called_once()

            # Singleton should be cleared
            assert engine_module._execution_engine is None


class TestConfigurationOptions:
    """Test configuration options for execution engine"""

    @pytest.fixture
    def mock_neo_service(self):
        """Create a mock NeoService for this test class"""
        service = AsyncMock()
        service.connect_testnet = AsyncMock(return_value={
            "connected": True,
            "block_height": 1000
        })
        service.close = AsyncMock()
        return service

    @pytest.mark.asyncio
    async def test_custom_confirmation_settings(self, mock_neo_service):
        """Test custom confirmation timeout and interval"""
        with patch('app.services.execution_engine.get_neo_service', return_value=mock_neo_service):
            with patch('app.services.execution_engine.NeoAccount') as mock_account_class:
                mock_account = Mock()
                mock_account.address = "NTest123456789012345678901234567"
                mock_account_class.from_wif = Mock(return_value=mock_account)

                engine = NeoExecutionEngine(
                    neo_service=mock_neo_service,
                    confirmation_timeout=60,
                    poll_interval=5,
                    min_confirmations=3
                )

                assert engine.confirmation_timeout == 60
                assert engine.poll_interval == 5
                assert engine.min_confirmations == 3

    @pytest.mark.asyncio
    async def test_default_confirmation_settings(self, mock_neo_service):
        """Test default confirmation settings"""
        with patch('app.services.execution_engine.get_neo_service', return_value=mock_neo_service):
            engine = NeoExecutionEngine(neo_service=mock_neo_service)

            assert engine.confirmation_timeout == NeoExecutionEngine.DEFAULT_CONFIRMATION_TIMEOUT
            assert engine.poll_interval == NeoExecutionEngine.DEFAULT_POLL_INTERVAL
            assert engine.min_confirmations == NeoExecutionEngine.DEFAULT_MIN_CONFIRMATIONS
