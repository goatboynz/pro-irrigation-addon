"""
FastAPI application for v2 room-based irrigation system.

This module provides:
- FastAPI application initialization
- CORS configuration for Home Assistant Ingress
- Database lifecycle management
- Health check endpoint
- Static file serving for frontend
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

from backend.models.database import create_tables, engine
from backend.models.v2_settings import SystemSettings
from backend.models.database import SessionLocal
from backend.routers import rooms, pumps, zones, water_events, sensors, settings, manual, ha_entities
from backend.services.scheduler import get_scheduler
from backend.services.queue_processor import get_queue_processor


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.
    
    Startup:
        - Create database tables if they don't exist
        - Initialize default SystemSettings if not present
        - Start queue processor background task
        - Start scheduler background task
    
    Shutdown:
        - Stop scheduler
        - Stop queue processor
        - Close database connections
    """
    # Startup
    print("Starting up irrigation system...")
    
    # Create all tables
    create_tables()
    print("Database tables created/verified")
    
    # Initialize default SystemSettings if not exists
    db = SessionLocal()
    try:
        settings = db.query(SystemSettings).filter(SystemSettings.id == 1).first()
        if not settings:
            default_settings = SystemSettings(
                id=1,
                pump_startup_delay_seconds=5,
                zone_switch_delay_seconds=2,
                scheduler_interval_seconds=60
            )
            db.add(default_settings)
            db.commit()
            print("Default system settings initialized")
        else:
            print("System settings already exist")
    finally:
        db.close()
    
    # Start background tasks
    print("Starting background tasks...")
    
    # Start queue processor
    queue_processor = get_queue_processor()
    await queue_processor.start()
    print("Queue processor started")
    
    # Start scheduler
    scheduler = get_scheduler()
    await scheduler.start()
    print("Scheduler started")
    
    print("Startup complete")
    
    yield
    
    # Shutdown
    print("Shutting down irrigation system...")
    
    # Stop background tasks
    print("Stopping background tasks...")
    scheduler = get_scheduler()
    await scheduler.stop()
    print("Scheduler stopped")
    
    queue_processor = get_queue_processor()
    await queue_processor.stop()
    print("Queue processor stopped")
    
    # Close database
    engine.dispose()
    print("Shutdown complete")


# Create FastAPI application with comprehensive API documentation
app = FastAPI(
    title="Room-Based Irrigation System API",
    description="""
## Overview

The Room-Based Irrigation System provides a comprehensive API for managing irrigation in grow rooms.
The system is organized hierarchically: Rooms contain Pumps, Pumps contain Zones, and Rooms have Water Events
that are assigned to specific Zones.

## Architecture

```
Rooms
  ├── Pumps
  │   └── Zones
  ├── Water Events (P1/P2)
  │   └── Assigned Zones
  └── Environmental Sensors
```

## Key Concepts

### Rooms
Rooms represent physical grow spaces with their own lighting schedules. Each room can have multiple pumps,
water events, and environmental sensors.

### Pumps
Pumps supply water to zones. Each pump has a lock entity (input_boolean) that prevents multiple zones
from running simultaneously. Pumps maintain a queue of execution jobs.

### Zones
Zones are individual irrigation areas controlled by switch entities. Each zone belongs to a pump and
can be assigned to multiple water events.

### Water Events
Water events define when irrigation should occur:
- **P1 Events**: Triggered after lights turn on (with configurable delay)
- **P2 Events**: Triggered at specific times of day

### Execution Flow

1. Scheduler checks for due events every 60 seconds
2. When event is due, jobs are created for assigned zones
3. Jobs are added to the pump's queue
4. Queue processor executes jobs sequentially:
   - Turn on pump lock
   - Wait for pump startup delay (default: 5s)
   - Turn on zone switch
   - Wait for duration
   - Turn off zone switch
   - Wait for zone switch delay (default: 2s)
   - Turn off pump lock

## Authentication

This API is designed to run as a Home Assistant add-on and uses Home Assistant's authentication
via Ingress. No additional authentication is required when accessed through Home Assistant.

## Rate Limiting

No rate limiting is currently implemented. Use responsibly.

## Error Handling

All endpoints return standard HTTP status codes:
- 200: Success
- 201: Created
- 400: Bad Request (validation error)
- 404: Not Found
- 500: Internal Server Error

Error responses include a detail message explaining the issue.
    """,
    version="2.0.0",
    lifespan=lifespan,
    contact={
        "name": "Pro-Irrigation Support",
        "url": "https://github.com/goatboynz/pro-irrigation-addon",
    },
    license_info={
        "name": "MIT License",
        "url": "https://github.com/goatboynz/pro-irrigation-addon/blob/main/LICENSE",
    },
    openapi_tags=[
        {
            "name": "Rooms",
            "description": "Operations for managing grow rooms. Rooms are the top-level organizational unit.",
        },
        {
            "name": "Pumps",
            "description": "Operations for managing pumps. Each pump belongs to a room and contains zones.",
        },
        {
            "name": "Zones",
            "description": "Operations for managing irrigation zones. Each zone belongs to a pump.",
        },
        {
            "name": "Water Events",
            "description": "Operations for managing water events (P1 and P2). Events are assigned to zones.",
        },
        {
            "name": "Sensors",
            "description": "Operations for managing environmental sensors and retrieving sensor data.",
        },
        {
            "name": "Settings",
            "description": "Operations for managing system settings and configuration.",
        },
        {
            "name": "Manual Control",
            "description": "Operations for manual zone control and emergency stop.",
        },
        {
            "name": "System",
            "description": "System health and information endpoints.",
        },
    ],
)

# Configure CORS for Home Assistant Ingress
# Home Assistant Ingress requires permissive CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for HA Ingress compatibility
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Include routers
app.include_router(rooms.router)
app.include_router(pumps.router)
app.include_router(zones.router)
app.include_router(water_events.router)
app.include_router(sensors.router)
app.include_router(settings.router)
app.include_router(manual.router)
app.include_router(ha_entities.router)


@app.get("/health", tags=["System"])
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        dict: Status information about the system
    """
    return {
        "status": "healthy",
        "service": "room-based-irrigation",
        "version": "2.0.0"
    }


@app.get("/api", tags=["System"])
async def root():
    """
    API root endpoint with information.
    
    Returns:
        dict: Welcome message and API documentation link
    """
    return {
        "message": "Room-Based Irrigation System API",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/health"
    }


# Mount static files for frontend (serve from /app/frontend/dist)
# This should be done last, after all API routes are registered
frontend_dist_path = "/app/frontend/dist"
if os.path.exists(frontend_dist_path):
    app.mount("/", StaticFiles(directory=frontend_dist_path, html=True), name="frontend")
    print(f"Frontend static files mounted from {frontend_dist_path}")
else:
    print(f"Warning: Frontend dist directory not found at {frontend_dist_path}")
