from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, Optional, Sequence

from .constants import SOLANA_SERVICE_NAME
from .service import SolanaService
from .swap import SolanaSwapTool
from .transfer import SolanaTransferTool
from .wallet import wallet_provider

logger = logging.getLogger(__name__)


def _runtime_get_service(runtime: Any, service_type: str) -> Optional[Any]:
    if runtime is None:
        return None

    for attr in ("get_service", "getService", "get"):
        getter = getattr(runtime, attr, None)
        if callable(getter):
            try:
                service = getter(service_type)
            except TypeError:
                continue
            if service:
                return service

    services_attr = getattr(runtime, "services", None)
    if isinstance(services_attr, dict):
        return services_attr.get(service_type)

    return None


async def _wait_for_service(runtime: Any, service_type: str, *, poll_interval: float = 1.0, log_prefix: str = "runtime") -> Optional[Any]:
    while True:
        service = _runtime_get_service(runtime, service_type)
        if service is not None:
            logger.info("%s acquired %s service", log_prefix, service_type)
            return service

        logger.debug("%s waiting for %s service...", log_prefix, service_type)
        await asyncio.sleep(poll_interval)

async def _noop_init(*_args: Any, **_kwargs: Any) -> None:
    """Default no-op init used when callers do not supply an init hook."""

@dataclass(frozen=True)
class ProviderDefinition:
    """Define a provider entry compatible with the TypeScript plugin schema."""

    name: str
    description: str
    getter: Callable[..., Awaitable[Dict[str, Any]]]
    dynamic: bool = True

    async def get(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        return await self.getter(*args, **kwargs)


@dataclass(frozen=True)
class PluginManifest:

    name: str
    description: str
    actions: Sequence[Any] = field(default_factory=list)
    evaluators: Sequence[Any] = field(default_factory=list)
    providers: Sequence[ProviderDefinition] = field(default_factory=list)
    services: Sequence[Any] = field(default_factory=list)
    init: Callable[..., Awaitable[None]] = field(default=_noop_init)

    async def initialize(self, context: Any = None, runtime: Any = None) -> None:
        await self.init(context, runtime)

    def to_dict(self) -> Dict[str, Any]:
        """Return the manifest as a plain dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "actions": list(self.actions),
            "evaluators": list(self.evaluators),
            "providers": list(self.providers),
            "services": list(self.services),
            "init": self.init,
        }

async def init_plugin(_context: Any = None, runtime: Any = None) -> None:
    """Initialise Solana plugin behaviour with the provided runtime."""
    if runtime is None:
        logger.warning("Solana plugin init called without runtime; skipping registration")
        return

    logger.info("Solana plugin initialising")

    async def _register_with_trader_chain() -> None:
        try:
            trader_chain_service = await _wait_for_service(
                runtime,
                service_type="TRADER_CHAIN",
                poll_interval=1.0,
                log_prefix="solana",
            )
        except Exception as exc:  # pylint: disable=broad-except
            logger.warning("Failed to acquire TRADER_CHAIN service: %s", exc)
            return

        if trader_chain_service is None:
            logger.warning("TRADER_CHAIN service unavailable")
            return

        register_fn: Optional[Callable[[Dict[str, Any]], Any]] = None
        for attr in ("register_chain", "registerChain"):
            candidate = getattr(trader_chain_service, attr, None)
            if callable(candidate):
                register_fn = candidate
                break

        if register_fn is None:
            logger.warning("TRADER_CHAIN service does not expose a register_chain method")
            return

        details = {
            "name": "Solana services",
            "chain": "solana",
            "service": SOLANA_SERVICE_NAME,
        }

        try:
            maybe_coro = register_fn(details)
            if hasattr(maybe_coro, "__await__"):
                await maybe_coro  # type: ignore[func-returns-value]
            logger.info("Solana plugin registered with TRADER_CHAIN service")
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Failed to register Solana chain with trader service: %s", exc)

    asyncio.create_task(
        _register_with_trader_chain(),
        name="solana-register-trader-chain",
    )

solana_plugin = PluginManifest(
    name=SOLANA_SERVICE_NAME,
    description="Solana Plugin for SpoonAI (Python port)",
    actions=[
        SolanaTransferTool(),
        SolanaSwapTool(),
    ],
    evaluators=[],
    providers=[
        ProviderDefinition(
            name="solana-wallet",
            description="Access Solana wallet information and balances.",
            getter=wallet_provider,
            dynamic=True,
        )
    ],
    services=[SolanaService],
    init=init_plugin,
)


__all__ = [
    "PluginManifest",
    "ProviderDefinition",
    "solana_plugin",
    "wallet_provider",
    "init_plugin",
]
