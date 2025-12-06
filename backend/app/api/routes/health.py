"""
Root-level health check endpoint (non-versioned)
Provides backward compatibility and simple health checks
"""

from fastapi import APIRouter
from datetime import datetime, UTC

from app.models import HealthCheckResponse, ServiceStatusValue
from app.__version__ import __version__

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="Root health check",
    description="Simple health check at /api/health for backward compatibility",
    tags=["health"]
)
async def root_health() -> HealthCheckResponse:
    """
    Root-level health check endpoint.

    This endpoint is available at /api/health for quick health checks.
    For detailed health information, use /api/v1/health

    Returns:
        HealthCheckResponse with basic status
    """
    return HealthCheckResponse(
        status=ServiceStatusValue.OK,
        service="Spica API",
        version=__version__,
        timestamp=datetime.now(UTC)
    )
