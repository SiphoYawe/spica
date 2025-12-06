"""
API v1 routes package
"""

from fastapi import APIRouter
from .health import router as health_router
from .wallet import router as wallet_router

# Create main v1 router
router = APIRouter(prefix="/v1")

# Include sub-routers
router.include_router(health_router, tags=["health"])
router.include_router(wallet_router, tags=["wallet"])

__all__ = ["router"]
