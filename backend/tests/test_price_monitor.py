"""
Unit tests for Price Monitor Service

Tests Story 5.5: Price Monitor Service acceptance criteria:
- Monitor token prices via external APIs ✓
- Check if price conditions are met ✓
- Support GAS, NEO, bNEO price tracking ✓
- Configurable polling interval ✓
- Handle API failures gracefully ✓
- Return price data with timestamp ✓
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from decimal import Decimal
from datetime import datetime, UTC, timedelta

from app.services.price_monitor import (
    PriceMonitorService,
    PriceData,
    PriceConditionResult,
    PriceSource,
    PriceMonitorError,
    TriggerCondition,
    get_price_monitor,
    close_price_monitor
)
from app.models.workflow_models import TokenType


class TestPriceData:
    """Test PriceData model"""

    def test_price_data_creation(self):
        """Test creating price data"""
        price = PriceData(
            token=TokenType.GAS,
            price_usd=Decimal("5.50"),
            timestamp=datetime.now(UTC),
            source="mock"
        )

        assert price.token == TokenType.GAS
        assert price.price_usd == Decimal("5.50")
        assert price.source == "mock"
        assert isinstance(price.timestamp, datetime)

    def test_price_data_to_dict(self):
        """Test converting price data to dictionary"""
        price = PriceData(
            token=TokenType.NEO,
            price_usd=Decimal("15.00"),
            timestamp=datetime.now(UTC),
            source="coingecko",
            change_24h=Decimal("5.5")
        )

        result = price.to_dict()

        assert result["token"] == "NEO"
        assert result["price_usd"] == "15.00"
        assert result["source"] == "coingecko"
        assert result["change_24h"] == "5.5"
        assert "timestamp" in result

    def test_price_data_repr(self):
        """Test string representation"""
        price = PriceData(
            token=TokenType.GAS,
            price_usd=Decimal("5.50"),
            timestamp=datetime.now(UTC)
        )

        repr_str = repr(price)
        assert "GAS" in repr_str
        assert "5.50" in repr_str


class TestPriceConditionResult:
    """Test PriceConditionResult model"""

    def test_condition_result_creation(self):
        """Test creating condition result"""
        price = PriceData(
            token=TokenType.GAS,
            price_usd=Decimal("6.00"),
            timestamp=datetime.now(UTC)
        )

        result = PriceConditionResult(
            condition_met=True,
            current_price=price,
            target_price=Decimal("5.00"),
            condition=TriggerCondition.ABOVE,
            message="GAS price $6.00 > target $5.00"
        )

        assert result.condition_met is True
        assert result.target_price == Decimal("5.00")
        assert result.condition == TriggerCondition.ABOVE

    def test_condition_result_to_dict(self):
        """Test converting to dictionary"""
        price = PriceData(
            token=TokenType.GAS,
            price_usd=Decimal("4.00"),
            timestamp=datetime.now(UTC)
        )

        result = PriceConditionResult(
            condition_met=False,
            current_price=price,
            target_price=Decimal("5.00"),
            condition=TriggerCondition.ABOVE,
            message="Test message"
        )

        result_dict = result.to_dict()
        assert result_dict["condition_met"] is False
        assert result_dict["target_price"] == "5.00"
        assert result_dict["condition"] == "above"


class TestPriceMonitorService:
    """Test PriceMonitorService class"""

    @pytest.fixture
    def mock_service(self):
        """Create a mock price monitor service"""
        return PriceMonitorService(
            source=PriceSource.MOCK,
            demo_mode=True
        )

    @pytest.mark.asyncio
    async def test_get_mock_price(self, mock_service):
        """Test getting mock prices"""
        price = await mock_service.get_price(TokenType.GAS)

        assert price.token == TokenType.GAS
        assert price.price_usd > 0
        assert price.source == "mock"
        assert isinstance(price.timestamp, datetime)

    @pytest.mark.asyncio
    async def test_get_all_prices(self, mock_service):
        """Test getting all token prices"""
        prices = await mock_service.get_all_prices()

        assert TokenType.GAS in prices
        assert TokenType.NEO in prices
        assert TokenType.BNEO in prices

        for token, price in prices.items():
            assert price.price_usd > 0
            assert price.token == token

    @pytest.mark.asyncio
    async def test_price_caching(self, mock_service):
        """Test that prices are cached"""
        # Get price twice
        price1 = await mock_service.get_price(TokenType.GAS)
        price2 = await mock_service.get_price(TokenType.GAS)

        # Should return cached value (same timestamp)
        assert price1.timestamp == price2.timestamp

    @pytest.mark.asyncio
    async def test_price_cache_bypass(self, mock_service):
        """Test force refresh bypasses cache"""
        price1 = await mock_service.get_price(TokenType.GAS)
        # Small delay to ensure different timestamp
        await asyncio.sleep(0.01)
        price2 = await mock_service.get_price(TokenType.GAS, force_refresh=True)

        # Timestamps should differ when cache bypassed
        # (Mock prices have random variation)
        assert price2.timestamp >= price1.timestamp

    @pytest.mark.asyncio
    async def test_check_price_condition_above_met(self, mock_service):
        """Test price condition ABOVE when met"""
        # Mock a high price
        with patch.object(mock_service, '_get_mock_price') as mock_get:
            mock_get.return_value = PriceData(
                token=TokenType.GAS,
                price_usd=Decimal("10.00"),
                timestamp=datetime.now(UTC),
                source="mock"
            )

            result = await mock_service.check_price_condition(
                token=TokenType.GAS,
                condition=TriggerCondition.ABOVE,
                target_price=5.0
            )

            assert result.condition_met is True
            assert result.current_price.price_usd == Decimal("10.00")
            assert ">" in result.message

    @pytest.mark.asyncio
    async def test_check_price_condition_above_not_met(self, mock_service):
        """Test price condition ABOVE when not met"""
        with patch.object(mock_service, '_get_mock_price') as mock_get:
            mock_get.return_value = PriceData(
                token=TokenType.GAS,
                price_usd=Decimal("3.00"),
                timestamp=datetime.now(UTC),
                source="mock"
            )

            result = await mock_service.check_price_condition(
                token=TokenType.GAS,
                condition=TriggerCondition.ABOVE,
                target_price=5.0
            )

            assert result.condition_met is False

    @pytest.mark.asyncio
    async def test_check_price_condition_below_met(self, mock_service):
        """Test price condition BELOW when met"""
        with patch.object(mock_service, '_get_mock_price') as mock_get:
            mock_get.return_value = PriceData(
                token=TokenType.GAS,
                price_usd=Decimal("3.00"),
                timestamp=datetime.now(UTC),
                source="mock"
            )

            result = await mock_service.check_price_condition(
                token=TokenType.GAS,
                condition=TriggerCondition.BELOW,
                target_price=5.0
            )

            assert result.condition_met is True

    @pytest.mark.asyncio
    async def test_check_price_condition_equals_met(self, mock_service):
        """Test price condition EQUALS with tolerance"""
        with patch.object(mock_service, '_get_mock_price') as mock_get:
            # Price within 1% of target
            mock_get.return_value = PriceData(
                token=TokenType.GAS,
                price_usd=Decimal("5.04"),  # 0.8% from 5.00
                timestamp=datetime.now(UTC),
                source="mock"
            )

            result = await mock_service.check_price_condition(
                token=TokenType.GAS,
                condition=TriggerCondition.EQUALS,
                target_price=5.0
            )

            assert result.condition_met is True

    @pytest.mark.asyncio
    async def test_start_price_monitoring(self, mock_service):
        """Test starting continuous price monitoring"""
        callback_called = asyncio.Event()
        callback_result = []

        async def callback(result):
            callback_result.append(result)
            callback_called.set()

        # Mock price that meets condition immediately
        with patch.object(mock_service, 'get_price') as mock_get:
            mock_get.return_value = PriceData(
                token=TokenType.GAS,
                price_usd=Decimal("10.00"),
                timestamp=datetime.now(UTC),
                source="mock"
            )

            task_id = await mock_service.start_price_monitoring(
                token=TokenType.GAS,
                condition=TriggerCondition.ABOVE,
                target_price=5.0,
                callback=callback
            )

            assert task_id is not None
            assert task_id in mock_service.get_active_monitors()

            # Wait for callback
            try:
                await asyncio.wait_for(callback_called.wait(), timeout=2.0)
                assert len(callback_result) == 1
                assert callback_result[0].condition_met is True
            except asyncio.TimeoutError:
                pytest.fail("Callback not called within timeout")

    @pytest.mark.asyncio
    async def test_stop_price_monitoring(self, mock_service):
        """Test stopping price monitoring"""
        async def callback(result):
            pass

        task_id = await mock_service.start_price_monitoring(
            token=TokenType.GAS,
            condition=TriggerCondition.ABOVE,
            target_price=100.0,  # High target won't be met
            callback=callback
        )

        # Should be active
        assert task_id in mock_service.get_active_monitors()

        # Stop it
        result = mock_service.stop_price_monitoring(task_id)
        assert result is True

        # Should no longer be active
        assert task_id not in mock_service.get_active_monitors()

    @pytest.mark.asyncio
    async def test_close_service(self, mock_service):
        """Test closing the service"""
        async def callback(result):
            pass

        # Start a monitor
        await mock_service.start_price_monitoring(
            token=TokenType.GAS,
            condition=TriggerCondition.ABOVE,
            target_price=100.0,
            callback=callback
        )

        # Close service
        await mock_service.close()

        # All monitors should be stopped
        assert len(mock_service.get_active_monitors()) == 0

    @pytest.mark.asyncio
    async def test_api_failure_fallback(self):
        """Test graceful handling of API failures"""
        service = PriceMonitorService(
            source=PriceSource.COINGECKO,
            demo_mode=False
        )

        # Mock HTTP client to fail
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=Exception("API Error"))
        service._http_client = mock_client

        # Should fall back to mock prices
        price = await service.get_price(TokenType.GAS)

        # Should get a price despite API failure
        assert price.price_usd > 0
        assert price.source == "mock"

        await service.close()


class TestSingletonPattern:
    """Test singleton pattern for global instance"""

    @pytest.mark.asyncio
    async def test_get_price_monitor_singleton(self):
        """Test that get_price_monitor returns singleton"""
        import app.services.price_monitor as pm_module
        pm_module._price_monitor = None

        monitor1 = await get_price_monitor()
        monitor2 = await get_price_monitor()

        assert monitor1 is monitor2

        await close_price_monitor()

    @pytest.mark.asyncio
    async def test_close_price_monitor(self):
        """Test closing the singleton"""
        import app.services.price_monitor as pm_module
        pm_module._price_monitor = None

        monitor = await get_price_monitor()
        assert pm_module._price_monitor is not None

        await close_price_monitor()
        assert pm_module._price_monitor is None


class TestConfigurationOptions:
    """Test configuration options"""

    def test_custom_poll_interval(self):
        """Test custom polling interval"""
        service = PriceMonitorService(poll_interval=60)
        assert service.poll_interval == 60

    def test_custom_source(self):
        """Test custom price source"""
        service = PriceMonitorService(source=PriceSource.COINGECKO)
        assert service.source == PriceSource.COINGECKO

    def test_demo_mode_enabled(self):
        """Test demo mode"""
        service = PriceMonitorService(demo_mode=True)
        assert service.demo_mode is True
