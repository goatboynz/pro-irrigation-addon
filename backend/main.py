"""
Pro-Irrigation Add-on Main Application

This is the main entry point for the FastAPI backend application.
It initializes the database, sets up the API routes, and configures
middleware for CORS and error handling. It also manages the lifecycle
of the scheduler engine and queue processor.
"""

import logging
import os
import signal
import sys
from datetime import datetime
from contextlib import asynccontextmanager
from queue import Queue
from typing import Dict

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from .models.database import init_db, get_db, check_db_health
from .models.schemas import HealthResponse, SystemStatusResponse
from .models.pump import Pump
from .models.zone import Zone

# Import routers
from .routers import pumps, zones, entities, settings

# Import services
from .services.ha_client import HomeAssistantClient
from .services.scheduler import SchedulerEngine
from .services.queue_processor import QueueProcessor

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
log_dir = os.getenv("LOG_DIR", "/data/logs")

# Create log directory if it doesn't exist
os.makedirs(log_dir, exist_ok=True)

# Configure logging with both console and file handlers
from logging.handlers import RotatingFileHandler

# Create formatters
detailed_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
)
simple_formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s'
)

# Console handler (simple format)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(log_level)
console_handler.setFormatter(simple_formatter)

# File handler with rotation (detailed format)
file_handler = RotatingFileHandler(
    os.path.join(log_dir, 'pro-irrigation.log'),
    maxBytes=10 * 1024 * 1024,  # 10 MB
    backupCount=5
)
file_handler.setLevel(log_level)
file_handler.setFormatter(detailed_formatter)

# Error file handler (errors only)
error_handler = RotatingFileHandler(
    os.path.join(log_dir, 'pro-irrigation-errors.log'),
    maxBytes=10 * 1024 * 1024,  # 10 MB
    backupCount=5
)
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(detailed_formatter)

# Configure root logger
logging.basicConfig(
    level=log_level,
    handlers=[console_handler, file_handler, error_handler]
)

logger = logging.getLogger(__name__)
logger.info(f"Logging configured: level={log_level}, log_dir={log_dir}")

# Global instances for scheduler and queue processor
scheduler_engine: SchedulerEngine = None
queue_processor: QueueProcessor = None
pump_queues: Dict[int, Queue] = {}
ha_client: HomeAssistantClient = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for application startup and shutdown.
    
    This function runs on application startup to initialize the database,
    start the scheduler engine and queue processor, and on shutdown to
    perform cleanup and graceful shutdown of all services.
    """
    global scheduler_engine, queue_processor, pump_queues, ha_client
    
    # ========================================================================
    # STARTUP
    # ========================================================================
    logger.info("=" * 70)
    logger.info("Starting Pro-Irrigation Add-on v1.0.0")
    logger.info("=" * 70)
    
    try:
        # Step 1: Initialize database
        logger.info("Initializing database...")
        init_db()
        logger.info("✓ Database initialized successfully")
        
        # Step 2: Initialize Home Assistant client
        logger.info("Initializing Home Assistant client...")
        supervisor_token = os.getenv("SUPERVISOR_TOKEN")
        if not supervisor_token:
            logger.warning("SUPERVISOR_TOKEN not found, using default for development")
            supervisor_token = "dev_token"
        
        ha_client = HomeAssistantClient(supervisor_token)
        logger.info("✓ Home Assistant client initialized")
        
        # Step 3: Initialize pump queues (shared between scheduler and processor)
        logger.info("Initializing pump queues...")
        pump_queues = {}
        logger.info("✓ Pump queues initialized")
        
        # Step 4: Initialize and start scheduler engine
        logger.info("Starting scheduler engine...")
        scheduler_engine = SchedulerEngine(ha_client, pump_queues)
        scheduler_engine.start()
        logger.info("✓ Scheduler engine started (60-second interval)")
        
        # Step 5: Initialize and start queue processor
        logger.info("Starting queue processor...")
        queue_processor = QueueProcessor(ha_client, pump_queues)
        queue_processor.start()
        logger.info("✓ Queue processor started (1-second interval)")
        
        logger.info("=" * 70)
        logger.info("Pro-Irrigation Add-on startup complete")
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"Failed to start Pro-Irrigation Add-on: {str(e)}", exc_info=True)
        raise
    
    yield
    
    # ========================================================================
    # SHUTDOWN
    # ========================================================================
    logger.info("=" * 70)
    logger.info("Shutting down Pro-Irrigation Add-on")
    logger.info("=" * 70)
    
    try:
        # Stop queue processor first to prevent new job execution
        if queue_processor:
            logger.info("Stopping queue processor...")
            queue_processor.stop()
            logger.info("✓ Queue processor stopped")
        
        # Stop scheduler engine to prevent new jobs from being created
        if scheduler_engine:
            logger.info("Stopping scheduler engine...")
            scheduler_engine.stop()
            logger.info("✓ Scheduler engine stopped")
        
        logger.info("=" * 70)
        logger.info("Pro-Irrigation Add-on shutdown complete")
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}", exc_info=True)


# Create FastAPI application
app = FastAPI(
    title="Pro-Irrigation Add-on API",
    description="REST API for Pro-Irrigation Home Assistant Add-on",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS middleware
# Allow all origins since the frontend is served through Home Assistant Ingress
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(pumps.router)
app.include_router(zones.router)
app.include_router(entities.router)
app.include_router(settings.router)

# Serve frontend static files
# The frontend is built to backend/static directory
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
    logger.info(f"Serving frontend static files from {static_dir}")
else:
    logger.warning(f"Static directory not found: {static_dir}")


# ============================================================================
# Health Check and System Status Endpoints
# ============================================================================

@app.get("/api/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """
    Health check endpoint.
    
    Returns the health status of the application and database connection.
    This endpoint can be used by monitoring systems to verify the service
    is running correctly.
    
    Returns:
        HealthResponse: Health status information
    """
    db_healthy = check_db_health()
    
    return HealthResponse(
        status="healthy" if db_healthy else "unhealthy",
        database="connected" if db_healthy else "disconnected",
        timestamp=datetime.now()
    )


@app.get("/api/status", response_model=SystemStatusResponse, tags=["System"])
async def system_status(db: Session = Depends(get_db)):
    """
    System status endpoint.
    
    Returns overall system status including database health and
    statistics about pumps and zones.
    
    Args:
        db: Database session (injected)
    
    Returns:
        SystemStatusResponse: System status information
    """
    try:
        db_healthy = check_db_health()
        
        # Get statistics
        total_pumps = db.query(Pump).count()
        total_zones = db.query(Zone).count()
        enabled_zones = db.query(Zone).filter(Zone.enabled == True).count()
        
        return SystemStatusResponse(
            status="operational" if db_healthy else "degraded",
            database_healthy=db_healthy,
            total_pumps=total_pumps,
            total_zones=total_zones,
            enabled_zones=enabled_zones,
            timestamp=datetime.now()
        )
    
    except Exception as e:
        logger.error(f"Error getting system status: {str(e)}")
        return SystemStatusResponse(
            status="error",
            database_healthy=False,
            total_pumps=0,
            total_zones=0,
            enabled_zones=0,
            timestamp=datetime.now()
        )


# ============================================================================
# Error Handlers
# ============================================================================

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError

from .exceptions import (
    ProIrrigationException,
    DatabaseException,
    HomeAssistantException,
    ValidationException,
    SchedulerException,
    QueueProcessorException,
    ConfigurationException
)
from .services.ha_client import HomeAssistantAPIError


@app.exception_handler(ProIrrigationException)
async def pro_irrigation_exception_handler(request: Request, exc: ProIrrigationException):
    """
    Handler for custom Pro-Irrigation exceptions.
    
    Returns structured error responses with appropriate HTTP status codes.
    """
    logger.error(
        f"Pro-Irrigation error: {exc.message}",
        extra={"details": exc.details, "path": request.url.path}
    )
    
    # Determine status code based on exception type
    status_code = 500
    if isinstance(exc, ValidationException):
        status_code = 400
    elif isinstance(exc, ConfigurationException):
        status_code = 400
    elif isinstance(exc, HomeAssistantException):
        status_code = 502
    elif isinstance(exc, DatabaseException):
        status_code = 500
    
    return JSONResponse(
        status_code=status_code,
        content={
            "error": exc.__class__.__name__,
            "message": exc.message,
            "details": exc.details
        }
    )


@app.exception_handler(HomeAssistantAPIError)
async def ha_api_error_handler(request: Request, exc: HomeAssistantAPIError):
    """
    Handler for Home Assistant API errors.
    
    Returns 502 Bad Gateway when Home Assistant communication fails.
    """
    logger.error(
        f"Home Assistant API error: {str(exc)}",
        extra={"path": request.url.path}
    )
    
    return JSONResponse(
        status_code=502,
        content={
            "error": "HomeAssistantAPIError",
            "message": "Failed to communicate with Home Assistant",
            "details": {"error": str(exc)}
        }
    )


@app.exception_handler(SQLAlchemyError)
async def database_error_handler(request: Request, exc: SQLAlchemyError):
    """
    Handler for SQLAlchemy database errors.
    
    Logs the error and returns a generic database error response.
    """
    logger.error(
        f"Database error: {str(exc)}",
        extra={"path": request.url.path},
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "DatabaseError",
            "message": "A database error occurred",
            "details": {"error": str(exc)}
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    """
    Handler for Pydantic request validation errors.
    
    Returns detailed validation error information to help clients fix requests.
    """
    logger.warning(
        f"Request validation error: {str(exc)}",
        extra={"path": request.url.path, "errors": exc.errors()}
    )
    
    return JSONResponse(
        status_code=422,
        content={
            "error": "ValidationError",
            "message": "Request validation failed",
            "details": {"errors": exc.errors()}
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Handler for FastAPI HTTP exceptions.
    
    Logs the error and returns the exception's status code and detail.
    """
    log_level = logging.WARNING if exc.status_code < 500 else logging.ERROR
    logger.log(
        log_level,
        f"HTTP {exc.status_code}: {exc.detail}",
        extra={"path": request.url.path, "status_code": exc.status_code}
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTPException",
            "message": exc.detail,
            "details": {}
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for unhandled errors.
    
    Logs the error with full traceback and returns a generic error response.
    This is the last resort handler for unexpected errors.
    """
    logger.critical(
        f"Unhandled exception: {str(exc)}",
        extra={"path": request.url.path, "exception_type": type(exc).__name__},
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred",
            "details": {"error": str(exc), "type": type(exc).__name__}
        }
    )


# ============================================================================
# Root Endpoint
# ============================================================================

@app.get("/", tags=["System"])
async def root():
    """
    Root endpoint.
    
    Returns basic API information.
    """
    return {
        "name": "Pro-Irrigation Add-on API",
        "version": "1.0.0",
        "status": "running"
    }


def signal_handler(signum, frame):
    """
    Signal handler for graceful shutdown.
    
    Handles SIGINT (Ctrl+C) and SIGTERM signals to ensure proper cleanup
    of scheduler and queue processor before exiting.
    """
    signal_name = signal.Signals(signum).name
    logger.info(f"Received signal {signal_name}, initiating graceful shutdown...")
    
    # The lifespan context manager will handle cleanup
    # Just exit gracefully
    sys.exit(0)


if __name__ == "__main__":
    import uvicorn
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("Signal handlers registered for graceful shutdown")
    
    # Run the application
    # In production, this will be run by the run.sh script
    try:
        uvicorn.run(
            "backend.main:app",
            host="0.0.0.0",
            port=8000,
            reload=False,
            log_level=log_level.lower()
        )
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Application error: {str(e)}", exc_info=True)
        sys.exit(1)
