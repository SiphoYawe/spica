"""
Spica - AI-Powered DeFi Workflow Builder for Neo N3
FastAPI application entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from datetime import datetime, UTC
import logging

from app.api import router as api_router
from app.__version__ import __version__

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info("Starting Spica backend...")
    # TODO: Initialize SpoonOS agents, schedulers, etc.
    yield
    logger.info("Shutting down Spica backend...")
    # TODO: Cleanup resources


app = FastAPI(
    title="Spica API",
    description="AI-Powered DeFi Workflow Builder for Neo N3",
    version=__version__,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://frontend:5173",   # Docker container
        "http://localhost:3000",  # Alternative dev server
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "Accept",
        "X-Requested-With",
        # x402 payment headers
        "X-PAYMENT-REQUEST",
        "X-PAYMENT",
        "X-PAYMENT-SIGNATURE",
    ],
    expose_headers=[
        "X-PAYMENT-REQUEST",  # Expose x402 headers to frontend
    ]
)

# Include API routes
app.include_router(api_router)


@app.get("/")
async def root():
    """
    Root endpoint - basic service information

    Returns basic service status and metadata.
    Use /api/health for detailed health checks.
    """
    return {
        "status": "ok",
        "service": "Spica API",
        "version": __version__,
        "timestamp": datetime.now(UTC).isoformat(),
        "docs": "/docs",
        "health": "/api/health"
    }


@app.get("/health")
async def legacy_health():
    """
    Legacy health check endpoint (for backward compatibility)

    Redirects to /api/health
    Use /api/v1/health for detailed status
    """
    return {
        "status": "healthy",
        "message": "Use /api/health or /api/v1/health for detailed status",
        "timestamp": datetime.now(UTC).isoformat()
    }
