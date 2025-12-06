"""
API routes package
"""

from fastapi import APIRouter
from .v1 import router as v1_router
from .routes import health_router

# Create main API router
router = APIRouter(prefix="/api")

# Include versioned API
router.include_router(v1_router)

# Include non-versioned routes (for backward compatibility)
router.include_router(health_router)

__all__ = ["router"]
