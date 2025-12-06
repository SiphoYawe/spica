"""
Pydantic models for API request/response schemas
"""

from typing import Optional, Dict, Any, List
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, UTC


class HealthStatus(str, Enum):
    """Overall system health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ServiceStatusValue(str, Enum):
    """Individual service status values"""
    OK = "ok"
    DEGRADED = "degraded"
    DOWN = "down"


class BaseResponse(BaseModel):
    """Base response model for all API endpoints"""
    success: bool = Field(..., description="Indicates if the request was successful")
    message: Optional[str] = Field(None, description="Optional message for additional context")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Response timestamp")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Operation completed successfully",
                "timestamp": "2025-12-06T00:00:00.000000"
            }
        }
    )


class ErrorDetail(BaseModel):
    """Detailed error information"""
    code: str = Field(..., description="Error code for programmatic handling")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[str] = Field(None, description="Additional error details")
    retry: bool = Field(False, description="Whether the request can be retried")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid input provided",
                "details": "Field 'amount' must be positive",
                "retry": False
            }
        }
    )


class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = Field(False, description="Always false for errors")
    error: ErrorDetail = Field(..., description="Error details")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Error timestamp")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": False,
                "error": {
                    "code": "NEO_RPC_TIMEOUT",
                    "message": "Unable to connect to Neo network. Please try again.",
                    "details": "RPC timeout after 60s",
                    "retry": True
                },
                "timestamp": "2025-12-06T00:00:00.000000"
            }
        }
    )


class HealthCheckResponse(BaseModel):
    """Basic health check response"""
    status: ServiceStatusValue = Field(..., description="Overall service status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Health check timestamp")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "ok",
                "service": "Spica API",
                "version": "0.1.0",
                "timestamp": "2025-12-06T00:00:00.000000"
            }
        }
    )


class ServiceStatus(BaseModel):
    """Individual service status"""
    status: ServiceStatusValue = Field(..., description="Service status: 'ok', 'degraded', 'down'")
    message: Optional[str] = Field(None, description="Optional status message")
    latency_ms: Optional[float] = Field(None, ge=0.0, description="Service latency in milliseconds")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "ok",
                "message": "Service operational",
                "latency_ms": 45.2
            }
        }
    )


class DetailedHealthResponse(BaseModel):
    """Detailed health check with service status"""
    status: HealthStatus = Field(..., description="Overall system status")
    version: str = Field(..., description="API version")
    services: Dict[str, ServiceStatus] = Field(
        default_factory=dict,
        description="Status of dependent services"
    )
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC), description="Health check timestamp")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "version": "0.1.0",
                "services": {
                    "api": {
                        "status": "ok",
                        "message": "API operational",
                        "latency_ms": 2.1
                    },
                    "neo_rpc": {
                        "status": "ok",
                        "message": "Connected to Neo N3 testnet",
                        "latency_ms": 150.5
                    },
                    "spoonos": {
                        "status": "ok",
                        "message": "SpoonOS agents ready",
                        "latency_ms": 5.3
                    }
                },
                "timestamp": "2025-12-06T00:00:00.000000"
            }
        }
    )


class DataResponse(BaseResponse):
    """Response model with data payload"""
    data: Optional[Any] = Field(None, description="Response data payload")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "Data retrieved successfully",
                "data": {"key": "value"},
                "timestamp": "2025-12-06T00:00:00.000000"
            }
        }
    )


class PaginatedResponse(BaseResponse):
    """Paginated response model"""
    data: List[Any] = Field(default_factory=list, description="List of items")
    total: int = Field(..., ge=0, description="Total number of items")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, le=100, description="Items per page")
    total_pages: int = Field(..., ge=0, description="Total number of pages")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "data": [{"id": 1}, {"id": 2}],
                "total": 100,
                "page": 1,
                "page_size": 10,
                "total_pages": 10,
                "timestamp": "2025-12-06T00:00:00.000000"
            }
        }
    )
