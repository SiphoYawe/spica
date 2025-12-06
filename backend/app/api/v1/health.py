"""
Health check endpoints for API v1
"""

from fastapi import APIRouter, Response, status
from typing import Optional
import time
import asyncio
from datetime import datetime, UTC
import logging

from app.models import (
    HealthCheckResponse,
    DetailedHealthResponse,
    ServiceStatus,
    ServiceStatusValue,
    HealthStatus,
)
from app.__version__ import __version__

logger = logging.getLogger(__name__)

router = APIRouter()


async def check_neo_rpc() -> ServiceStatus:
    """Check Neo RPC connectivity"""
    try:
        start_time = time.time()
        # TODO: Actually check Neo RPC when neo_service is implemented
        # For now, simulate a check
        await asyncio.sleep(0.05)  # Simulate network latency
        latency = (time.time() - start_time) * 1000

        return ServiceStatus(
            status=ServiceStatusValue.OK,
            message="Connected to Neo N3 testnet",
            latency_ms=round(latency, 2)
        )
    except Exception as e:
        logger.error(f"Neo RPC health check failed: {str(e)}", exc_info=True)
        return ServiceStatus(
            status=ServiceStatusValue.DOWN,
            message="Neo RPC service unavailable",
            latency_ms=None
        )


async def check_spoonos() -> ServiceStatus:
    """Check SpoonOS agent status"""
    try:
        start_time = time.time()
        # TODO: Actually check SpoonOS when agents are implemented
        # For now, simulate a check
        await asyncio.sleep(0.01)
        latency = (time.time() - start_time) * 1000

        return ServiceStatus(
            status=ServiceStatusValue.OK,
            message="SpoonOS agents ready",
            latency_ms=round(latency, 2)
        )
    except Exception as e:
        logger.error(f"SpoonOS health check failed: {str(e)}", exc_info=True)
        return ServiceStatus(
            status=ServiceStatusValue.DOWN,
            message="SpoonOS service unavailable",
            latency_ms=None
        )


@router.get(
    "/health",
    response_model=DetailedHealthResponse,
    summary="Detailed health check",
    description="Returns detailed health status of all system components",
    responses={
        200: {
            "description": "System is healthy",
            "model": DetailedHealthResponse
        },
        503: {
            "description": "System is unhealthy or degraded"
        }
    }
)
async def detailed_health(response: Response) -> DetailedHealthResponse:
    """
    Detailed health check endpoint that monitors all system components.

    Returns:
        DetailedHealthResponse with status of all services
    """
    # Check all services in parallel
    api_status = ServiceStatus(
        status=ServiceStatusValue.OK,
        message="API operational",
        latency_ms=None
    )

    neo_status, spoonos_status = await asyncio.gather(
        check_neo_rpc(),
        check_spoonos()
    )

    services = {
        "api": api_status,
        "neo_rpc": neo_status,
        "spoonos": spoonos_status
    }

    # Determine overall status
    statuses = [s.status for s in services.values()]
    if any(s == ServiceStatusValue.DOWN for s in statuses):
        overall_status = HealthStatus.UNHEALTHY
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    elif any(s == ServiceStatusValue.DEGRADED for s in statuses):
        overall_status = HealthStatus.DEGRADED
        response.status_code = status.HTTP_200_OK
    else:
        overall_status = HealthStatus.HEALTHY
        response.status_code = status.HTTP_200_OK

    return DetailedHealthResponse(
        status=overall_status,
        version=__version__,
        services=services,
        timestamp=datetime.now(UTC)
    )


@router.get(
    "/health/simple",
    response_model=HealthCheckResponse,
    summary="Simple health check",
    description="Returns basic health status for load balancers",
    responses={
        200: {
            "description": "Service is running",
            "model": HealthCheckResponse
        }
    }
)
async def simple_health() -> HealthCheckResponse:
    """
    Simple health check endpoint for load balancers and monitoring.

    This endpoint performs minimal checks and returns quickly.
    Use the /health endpoint for detailed status.

    Returns:
        HealthCheckResponse with basic status
    """
    return HealthCheckResponse(
        status=ServiceStatusValue.OK,
        service="Spica API",
        version=__version__,
        timestamp=datetime.now(UTC)
    )
