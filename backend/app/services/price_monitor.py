"""
Price Monitor Service for Spica Workflows

This module implements Story 5.5: Price Monitor Service

The PriceMonitorService provides:
- Real-time price monitoring for Neo N3 tokens
- Price trigger evaluation for workflow conditions
- Mock price feeds for demo mode
- Configurable polling intervals

Acceptance Criteria:
- Monitor token prices via external APIs
- Check if price conditions are met
- Support GAS, NEO, bNEO price tracking
- Configurable polling interval
- Handle API failures gracefully
- Return price data with timestamp
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List, Callable, Awaitable
from decimal import Decimal
from datetime import datetime, UTC, timedelta
from dataclasses import dataclass, field
from enum import Enum
import httpx

from app.config import settings
from app.models.workflow_models import TokenType

logger = logging.getLogger(__name__)


# ============================================================================
# Enums (must be defined before dataclasses that use them)
# ============================================================================

class PriceSource(Enum):
    """Available price data sources."""
    MOCK = "mock"
    COINGECKO = "coingecko"
    FLAMINGO = "flamingo"


class TriggerCondition(str, Enum):
    """Price trigger conditions for monitoring."""
    ABOVE = "above"
    BELOW = "below"
    EQUALS = "equals"


# ============================================================================
# Price Data Models
# ============================================================================

@dataclass
class PriceData:
    """Token price information with metadata."""
    token: TokenType
    price_usd: Decimal
    timestamp: datetime
    source: str = "mock"
    change_24h: Optional[Decimal] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "token": self.token.value,
            "price_usd": str(self.price_usd),
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "change_24h": str(self.change_24h) if self.change_24h else None
        }

    def __repr__(self) -> str:
        return f"PriceData({self.token.value}=${self.price_usd}, source={self.source})"


@dataclass
class PriceConditionResult:
    """Result of evaluating a price condition."""
    condition_met: bool
    current_price: PriceData
    target_price: Decimal
    condition: TriggerCondition
    message: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "condition_met": self.condition_met,
            "current_price": self.current_price.to_dict(),
            "target_price": str(self.target_price),
            "condition": self.condition.value,
            "message": self.message
        }


# ============================================================================
# Price Monitor Service
# ============================================================================

class PriceMonitorService:
    """
    Service for monitoring token prices and evaluating trigger conditions.

    Implements Story 5.5: Price Monitor Service

    Features:
    - Multi-source price fetching (mock, CoinGecko, Flamingo DEX)
    - Configurable polling intervals
    - Price caching to reduce API calls
    - Graceful error handling with fallbacks

    Usage:
        ```python
        monitor = PriceMonitorService()

        # Get current price
        price = await monitor.get_price(TokenType.GAS)
        print(f"GAS price: ${price.price_usd}")

        # Check if condition is met
        result = await monitor.check_price_condition(
            token=TokenType.GAS,
            condition=TriggerCondition.ABOVE,
            target_price=5.0
        )
        if result.condition_met:
            print("Price trigger activated!")
        ```
    """

    # CoinGecko token IDs for Neo ecosystem
    COINGECKO_IDS = {
        TokenType.GAS: "gas",
        TokenType.NEO: "neo",
        TokenType.BNEO: "neo"  # bNEO tracks NEO price
    }

    # Default polling interval (seconds)
    DEFAULT_POLL_INTERVAL = 30

    # Price cache TTL (seconds) - Task 2.1: Changed to 60 seconds
    CACHE_TTL = 60

    def __init__(
        self,
        source: PriceSource = PriceSource.MOCK,
        poll_interval: int = DEFAULT_POLL_INTERVAL,
        demo_mode: bool = None
    ):
        """
        Initialize the price monitor service.

        Args:
            source: Price data source to use
            poll_interval: Seconds between price updates
            demo_mode: Enable demo mode with mock prices
        """
        self.source = source
        self.poll_interval = poll_interval
        self.demo_mode = demo_mode if demo_mode is not None else settings.spica_demo_mode

        # Price cache: token -> (price_data, fetch_time)
        self._cache: Dict[TokenType, tuple[PriceData, datetime]] = {}

        # Active monitoring tasks
        self._monitoring_tasks: Dict[str, asyncio.Task] = {}

        # HTTP client for external APIs
        self._http_client: Optional[httpx.AsyncClient] = None

        if self.demo_mode:
            logger.info("PriceMonitorService initialized in DEMO mode (using mock prices)")
        else:
            logger.info(f"PriceMonitorService initialized with source: {source.value}")

    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=10.0)
        return self._http_client

    async def close(self):
        """Close the service and cleanup resources."""
        # Cancel monitoring tasks
        for task in self._monitoring_tasks.values():
            task.cancel()
        self._monitoring_tasks.clear()

        # Close HTTP client
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

        logger.info("PriceMonitorService closed")

    # ========================================================================
    # Price Fetching
    # ========================================================================

    async def get_price(self, token: TokenType, force_refresh: bool = False) -> PriceData:
        """
        Get current price for a token.

        Args:
            token: Token to get price for
            force_refresh: Bypass cache and fetch fresh data

        Returns:
            PriceData with current price

        Raises:
            PriceMonitorError: If price fetching fails
        """
        # Check cache first (unless force refresh)
        if not force_refresh and token in self._cache:
            cached_price, fetch_time = self._cache[token]
            cache_age = (datetime.now(UTC) - fetch_time).total_seconds()
            if cache_age < self.CACHE_TTL:
                logger.debug(f"Using cached price for {token.value}: ${cached_price.price_usd}")
                return cached_price

        # Fetch fresh price
        try:
            if self.demo_mode or self.source == PriceSource.MOCK:
                price_data = await self._get_mock_price(token)
            elif self.source == PriceSource.COINGECKO:
                price_data = await self._get_coingecko_price(token)
            elif self.source == PriceSource.FLAMINGO:
                price_data = await self._get_flamingo_price(token)
            else:
                price_data = await self._get_mock_price(token)

            # Update cache
            self._cache[token] = (price_data, datetime.now(UTC))

            logger.info(f"Fetched price for {token.value}: ${price_data.price_usd}")
            return price_data

        except Exception as e:
            logger.error(f"Error fetching price for {token.value}: {e}")
            # Return cached price if available (even if stale)
            if token in self._cache:
                logger.warning(f"Using stale cached price for {token.value}")
                return self._cache[token][0]
            raise PriceMonitorError(f"Failed to get price for {token.value}: {e}") from e

    async def get_all_prices(self, force_refresh: bool = False) -> Dict[TokenType, PriceData]:
        """
        Get prices for all supported tokens.

        Args:
            force_refresh: Bypass cache

        Returns:
            Dictionary of token to price data
        """
        prices = {}
        for token in [TokenType.GAS, TokenType.NEO, TokenType.BNEO]:
            try:
                prices[token] = await self.get_price(token, force_refresh)
            except Exception as e:
                logger.error(f"Failed to get price for {token.value}: {e}")
        return prices

    async def _get_mock_price(self, token: TokenType) -> PriceData:
        """Get mock price for demo mode."""
        # Realistic mock prices with slight variations
        import random
        base_prices = {
            TokenType.GAS: Decimal("5.50"),
            TokenType.NEO: Decimal("15.00"),
            TokenType.BNEO: Decimal("14.50")
        }

        base = base_prices.get(token, Decimal("1.0"))
        # Add ±5% random variation
        variation = Decimal(str(random.uniform(-0.05, 0.05)))
        price = base * (Decimal("1") + variation)

        return PriceData(
            token=token,
            price_usd=price.quantize(Decimal("0.01")),
            timestamp=datetime.now(UTC),
            source="mock",
            change_24h=Decimal(str(random.uniform(-10, 10))).quantize(Decimal("0.01"))
        )

    async def _get_coingecko_price(self, token: TokenType) -> PriceData:
        """Fetch price from CoinGecko API."""
        client = await self._get_http_client()
        coin_id = self.COINGECKO_IDS.get(token, "gas")

        try:
            response = await client.get(
                f"https://api.coingecko.com/api/v3/simple/price",
                params={
                    "ids": coin_id,
                    "vs_currencies": "usd",
                    "include_24hr_change": "true"
                }
            )
            response.raise_for_status()
            data = response.json()

            if coin_id not in data:
                raise PriceMonitorError(f"No data for {coin_id} from CoinGecko")

            price_usd = Decimal(str(data[coin_id]["usd"]))
            change_24h = data[coin_id].get("usd_24h_change")
            if change_24h is not None:
                change_24h = Decimal(str(change_24h)).quantize(Decimal("0.01"))

            return PriceData(
                token=token,
                price_usd=price_usd,
                timestamp=datetime.now(UTC),
                source="coingecko",
                change_24h=change_24h
            )

        except Exception as e:
            logger.error(f"CoinGecko API error: {e}")
            # Fallback to mock
            logger.warning("Falling back to mock prices")
            return await self._get_mock_price(token)

    async def _get_flamingo_price(self, token: TokenType) -> PriceData:
        """
        Fetch price from Flamingo DEX pool reserves.

        Task 2.2: Real Flamingo DEX Price Feed Implementation

        Calculates price based on pool reserve ratios by querying
        the Flamingo swap router's getAmountsOut function.

        Process:
        1. Query router for how much GAS you'd get for 1 token
        2. Get GAS price in USD from CoinGecko
        3. Calculate token price: (GAS amount) * (GAS USD price)

        Falls back to CoinGecko on error.
        """
        from app.services.neo_rpc import get_neo_rpc
        from app.services.contract_registry import get_contract_registry

        registry = get_contract_registry()

        try:
            rpc = await get_neo_rpc()

            # Get contract hashes
            token_hash = registry.get_token_hash(token.value)
            gas_hash = registry.get_native_hash("GAS")
            router_hash = registry.get_flamingo_hash("SWAP_ROUTER")

            # Prepare amount: 1 token in smallest units
            decimals = registry.get_decimals(token.value)
            one_token = 10 ** decimals  # 1 token in smallest units

            # Query Flamingo Router: getAmountsOut(amountIn, path)
            # Returns array of amounts for each token in path
            # path = [token_in, token_out] = [our_token, GAS]
            result = await rpc.invoke_function(
                router_hash,
                "getAmountsOut",
                [
                    {"type": "Integer", "value": str(one_token)},
                    {"type": "Array", "value": [
                        {"type": "Hash160", "value": token_hash},
                        {"type": "Hash160", "value": gas_hash}
                    ]}
                ]
            )

            # Check if invocation succeeded
            if result.get("state") != "HALT":
                logger.warning(f"Flamingo getAmountsOut failed: {result.get('exception')}")
                logger.info("Falling back to CoinGecko for price data")
                return await self._get_coingecko_price(token)

            # Parse output - get GAS amount from stack
            stack = result.get("stack", [])
            if stack and len(stack) > 0:
                # getAmountsOut returns an array of amounts
                # stack[0] is the array, we want the last element (output amount)
                amounts_array = stack[0].get("value", [])
                if amounts_array and len(amounts_array) > 1:
                    # Last element is the GAS output amount
                    gas_output = amounts_array[-1]
                    gas_amount_raw = int(gas_output.get("value", 0))

                    # Convert from smallest units to GAS (8 decimals)
                    gas_amount = Decimal(str(gas_amount_raw)) / Decimal(10 ** 8)

                    # Get GAS price in USD from CoinGecko as reference
                    gas_price_data = await self._get_coingecko_price(TokenType.GAS)

                    # Calculate token price: (GAS amount) * (GAS USD price)
                    token_price_usd = gas_amount * gas_price_data.price_usd

                    logger.info(
                        f"Flamingo price for {token.value}: "
                        f"{gas_amount} GAS * ${gas_price_data.price_usd} = ${token_price_usd}"
                    )

                    return PriceData(
                        token=token,
                        price_usd=token_price_usd.quantize(Decimal("0.01")),
                        timestamp=datetime.now(UTC),
                        source="flamingo",
                        change_24h=None  # DEX doesn't provide 24h change
                    )

            # If we couldn't parse the result, fall back
            logger.warning("Could not parse Flamingo getAmountsOut response")
            return await self._get_coingecko_price(token)

        except Exception as e:
            logger.error(f"Flamingo price fetch error for {token.value}: {e}")
            logger.info("Falling back to CoinGecko for price data")
            return await self._get_coingecko_price(token)  # Fallback

    # ========================================================================
    # Condition Evaluation
    # ========================================================================

    async def check_price_condition(
        self,
        token: TokenType,
        condition: TriggerCondition,
        target_price: float
    ) -> PriceConditionResult:
        """
        Check if a price condition is met.

        Args:
            token: Token to check
            condition: Comparison condition (ABOVE, BELOW, EQUALS)
            target_price: Target price threshold

        Returns:
            PriceConditionResult indicating if condition is met
        """
        current_price = await self.get_price(token)
        target = Decimal(str(target_price))

        if condition == TriggerCondition.ABOVE:
            condition_met = current_price.price_usd > target
            comparison = ">" if condition_met else "≤"
        elif condition == TriggerCondition.BELOW:
            condition_met = current_price.price_usd < target
            comparison = "<" if condition_met else "≥"
        elif condition == TriggerCondition.EQUALS:
            # Allow 1% tolerance for equals
            tolerance = target * Decimal("0.01")
            condition_met = abs(current_price.price_usd - target) <= tolerance
            comparison = "≈" if condition_met else "≠"
        else:
            condition_met = False
            comparison = "?"

        message = (
            f"{token.value} price ${current_price.price_usd} {comparison} "
            f"target ${target}"
        )

        logger.info(f"Price condition check: {message} (met={condition_met})")

        return PriceConditionResult(
            condition_met=condition_met,
            current_price=current_price,
            target_price=target,
            condition=condition,
            message=message
        )

    # ========================================================================
    # Continuous Monitoring
    # ========================================================================

    async def start_price_monitoring(
        self,
        token: TokenType,
        condition: TriggerCondition,
        target_price: float,
        callback: Callable[[PriceConditionResult], Awaitable[None]],
        monitoring_id: Optional[str] = None
    ) -> str:
        """
        Start continuous price monitoring with callback on condition met.

        Args:
            token: Token to monitor
            condition: Trigger condition
            target_price: Target price
            callback: Async function called when condition is met
            monitoring_id: Optional ID for the monitoring task

        Returns:
            Monitoring task ID
        """
        task_id = monitoring_id or f"monitor_{token.value}_{datetime.now(UTC).timestamp()}"

        async def monitor_loop():
            logger.info(
                f"Starting price monitor {task_id}: "
                f"{token.value} {condition.value} ${target_price}"
            )
            while True:
                try:
                    result = await self.check_price_condition(
                        token, condition, target_price
                    )
                    if result.condition_met:
                        logger.info(f"Price condition met for {task_id}")
                        await callback(result)
                        # Stop monitoring after condition is met
                        break

                    await asyncio.sleep(self.poll_interval)

                except asyncio.CancelledError:
                    logger.info(f"Price monitor {task_id} cancelled")
                    break
                except Exception as e:
                    logger.error(f"Error in price monitor {task_id}: {e}")
                    await asyncio.sleep(self.poll_interval)

        task = asyncio.create_task(monitor_loop())
        self._monitoring_tasks[task_id] = task

        return task_id

    def stop_price_monitoring(self, task_id: str) -> bool:
        """
        Stop a price monitoring task.

        Args:
            task_id: ID of the monitoring task

        Returns:
            True if task was found and cancelled
        """
        if task_id in self._monitoring_tasks:
            self._monitoring_tasks[task_id].cancel()
            del self._monitoring_tasks[task_id]
            logger.info(f"Stopped price monitor: {task_id}")
            return True
        return False

    def get_active_monitors(self) -> List[str]:
        """Get list of active monitoring task IDs."""
        return list(self._monitoring_tasks.keys())


# ============================================================================
# Exception Classes
# ============================================================================

class PriceMonitorError(Exception):
    """Exception raised when price monitoring fails."""
    pass


# ============================================================================
# Singleton Instance
# ============================================================================

_price_monitor: Optional[PriceMonitorService] = None
_price_monitor_lock = asyncio.Lock()


async def get_price_monitor() -> PriceMonitorService:
    """
    Get the global PriceMonitorService instance (thread-safe).

    Returns:
        PriceMonitorService singleton
    """
    global _price_monitor

    if _price_monitor is not None:
        return _price_monitor

    async with _price_monitor_lock:
        if _price_monitor is None:
            # Task 2.1: Use CoinGecko by default when not in demo mode
            _price_monitor = PriceMonitorService(source=PriceSource.COINGECKO)
        return _price_monitor


async def close_price_monitor():
    """Close the global PriceMonitorService instance."""
    global _price_monitor

    async with _price_monitor_lock:
        if _price_monitor is not None:
            await _price_monitor.close()
            _price_monitor = None
