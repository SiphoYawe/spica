"""
API v1 routes package
"""

from fastapi import APIRouter
from .health import router as health_router
from .wallet import router as wallet_router
from .workflow import router as workflow_router
from .deploy import router as deploy_router

# Create main v1 router
router = APIRouter(prefix="/v1")

# Include sub-routers
router.include_router(health_router, tags=["health"])
router.include_router(wallet_router, tags=["wallet"])
router.include_router(workflow_router, tags=["workflow"])
router.include_router(deploy_router, tags=["deployment"])

__all__ = ["router"]
