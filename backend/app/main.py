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
    """Application lifespan manager - handles startup and shutdown"""
    # ========================================================================
    # STARTUP
    # ========================================================================
    logger.info("Starting Spica API...")

    # Initialize Neo RPC
    try:
        from app.services.neo_rpc import get_neo_rpc
        rpc = await get_neo_rpc()
        block_count = await rpc.get_block_count()
        logger.info(f"✓ Neo RPC connected, block height: {block_count}")
    except Exception as e:
        logger.warning(f"✗ Neo RPC initialization failed: {e}")

    # Initialize price monitor
    try:
        from app.services.price_monitor import get_price_monitor
        monitor = await get_price_monitor()
        logger.info(f"✓ Price monitor initialized, source: {monitor.source.value}")
    except Exception as e:
        logger.warning(f"✗ Price monitor initialization failed: {e}")

    # Initialize workflow scheduler
    try:
        from app.services.workflow_scheduler import get_workflow_scheduler
        scheduler = await get_workflow_scheduler()
        await scheduler.start()
        logger.info("✓ Workflow scheduler started")
    except Exception as e:
        logger.warning(f"✗ Scheduler initialization failed: {e}")

    # Initialize execution storage
    try:
        from app.services.execution_storage import get_execution_storage
        storage = await get_execution_storage()
        logger.info("✓ Execution storage initialized")
    except Exception as e:
        logger.warning(f"✗ Execution storage initialization failed: {e}")

    logger.info("✓ Spica API startup complete")

    yield

    # ========================================================================
    # SHUTDOWN
    # ========================================================================
    logger.info("Shutting down Spica API...")

    # Stop workflow scheduler
    try:
        from app.services.workflow_scheduler import get_workflow_scheduler
        scheduler = await get_workflow_scheduler()
        await scheduler.stop()
        logger.info("✓ Workflow scheduler stopped")
    except Exception as e:
        logger.error(f"✗ Error stopping scheduler: {e}")

    # Close price monitor
    try:
        from app.services.price_monitor import close_price_monitor
        await close_price_monitor()
        logger.info("✓ Price monitor closed")
    except Exception as e:
        logger.error(f"✗ Error closing price monitor: {e}")

    # Close Neo RPC
    try:
        from app.services.neo_rpc import close_neo_rpc
        await close_neo_rpc()
        logger.info("✓ Neo RPC closed")
    except Exception as e:
        logger.error(f"✗ Error closing Neo RPC: {e}")

    # Close execution storage
    try:
        from app.services.execution_storage import close_execution_storage
        await close_execution_storage()
        logger.info("✓ Execution storage closed")
    except Exception as e:
        logger.error(f"✗ Error closing execution storage: {e}")

    logger.info("✓ Spica API shutdown complete")


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
