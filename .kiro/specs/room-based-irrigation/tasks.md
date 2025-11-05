# Implementation Plan - Room-Based Irrigation System

Complete redesign with room-based organization. Implementation in phases: backend first, then frontend.

## Phase 1: Backend Foundation

- [x] 1. Database schema and models
  - All v2 models created: Room, PumpV2, ZoneV2, WaterEvent, EnvironmentalSensor, SystemSettings
  - Association table event_zones_v2 for many-to-many relationship
  - _Requirements: Data persistence, room-based organization_

- [x] 2. Database initialization and connection





  - [x] 2.1 Create database.py with SQLAlchemy Base and engine setup


    - Configure SQLite connection to /data/irrigation_v2.db
    - Create session factory and dependency injection
    - _Requirements: 10.1, 10.5_
  - [x] 2.2 Create database initialization script


    - Implement create_tables() function
    - Add default SystemSettings row (id=1)
    - _Requirements: 10.5_

- [x] 3. FastAPI application setup




  - [x] 3.1 Create main.py with FastAPI app initialization


    - Configure CORS for Home Assistant Ingress
    - Add database startup/shutdown lifecycle
    - Include health check endpoint
    - _Requirements: 1.1_
  - [x] 3.2 Create Pydantic schemas for all models


    - Request schemas (Create/Update) for each model
    - Response schemas with relationships
    - _Requirements: API data validation_
-

- [x] 4. Home Assistant integration client




  - [x] 4.1 Create ha_client.py service


    - Implement get_entities() for entity discovery
    - Implement get_state() for reading entity values
    - Implement call_service() for switch/lock control
    - Use SUPERVISOR_TOKEN from environment

    - _Requirements: 3.4, 7.2, 9.4_
  - [x] 4.2 Add entity validation helpers

    - Verify entity exists before saving to database
    - _Requirements: 3.5_


## Phase 2: Core API Endpoints

- [x] 5. Rooms API


  - [x] 5.1 Create routers/rooms.py with CRUD endpoints


    - GET /api/rooms - List all rooms
    - POST /api/rooms - Create room
    - GET /api/rooms/{id} - Get room with relationships
    - PUT /api/rooms/{id} - Update room
    - DELETE /api/rooms/{id} - Delete room (cascade)
    - _Requirements: 2.1, 2.2, 2.3, 2.4_
  - [x] 5.2 Add room status calculation


    - GET /api/rooms/{id}/status - Current active events, pump states
    - _Requirements: 12.1, 12.2_

- [x] 6. Pumps API





  - [x] 6.1 Create routers/pumps.py with CRUD endpoints


    - GET /api/rooms/{room_id}/pumps - List pumps for room
    - POST /api/rooms/{room_id}/pumps - Create pump
    - PUT /api/pumps/{id} - Update pump
    - DELETE /api/pumps/{id} - Delete pump (cascade)
    - _Requirements: 2.1, 2.2, 2.3, 2.4_
  - [x] 6.2 Add pump status endpoint


    - GET /api/pumps/{id}/status - Lock state, active zone, queue length
    - _Requirements: 12.1, 12.2, 12.3_


- [x] 7. Zones API



  - [x] 7.1 Create routers/zones.py with CRUD endpoints


    - GET /api/pumps/{pump_id}/zones - List zones for pump
    - POST /api/pumps/{pump_id}/zones - Create zone
    - PUT /api/zones/{id} - Update zone
    - DELETE /api/zones/{id} - Delete zone
    - _Requirements: 3.1, 3.2, 3.3_
-

- [x] 8. Water Events API



  - [x] 8.1 Create routers/water_events.py with CRUD endpoints


    - GET /api/rooms/{room_id}/events - List events for room
    - POST /api/rooms/{room_id}/events - Create P1 or P2 event
    - PUT /api/events/{id} - Update event
    - DELETE /api/events/{id} - Delete event
    - _Requirements: 5.1, 5.2, 6.1, 6.2_
  - [x] 8.2 Implement zone assignment endpoints


    - POST /api/events/{id}/zones/{zone_id} - Assign zone to event
    - DELETE /api/events/{id}/zones/{zone_id} - Remove zone from event
    - _Requirements: Event-zone many-to-many relationship_
  - [x] 8.3 Add next run calculation endpoint


    - GET /api/events/{id}/next-run - Calculate next scheduled time
    - _Requirements: 11.1, 11.2_

- [x] 9. Sensors API




  - [x] 9.1 Create routers/sensors.py with CRUD endpoints


    - GET /api/rooms/{room_id}/sensors - List sensors for room
    - POST /api/rooms/{room_id}/sensors - Create sensor
    - PUT /api/sensors/{id} - Update sensor
    - DELETE /api/sensors/{id} - Delete sensor
    - _Requirements: Environmental monitoring_
  - [x] 9.2 Add sensor data endpoints


    - GET /api/sensors/{id}/current - Current value from HA
    - GET /api/sensors/{id}/history?duration=1h - Historical data from HA
    - _Requirements: Real-time and historical sensor data_

- [x] 10. Settings API





  - [x] 10.1 Create routers/settings.py


    - GET /api/settings - Get system settings
    - PUT /api/settings - Update system settings
    - _Requirements: 7.1, 7.2_
  - [x] 10.2 Add system management endpoints

    - POST /api/system/reset - Delete all data except settings
    - GET /api/system/health - System health check
    - _Requirements: System management_

## Phase 3: Execution Engine


- [x] 11. Pump queue processor



  - [x] 11.1 Create services/queue_processor.py


    - Implement in-memory queue per pump (dict of lists)
    - Add job to queue: add_job(pump_id, job)
    - Process queues every 1 second
    - _Requirements: 4.1, 4.2, 9.1_
  - [x] 11.2 Implement job execution logic


    - Check pump lock state via HA client
    - Execute first job if pump idle and queue not empty
    - Turn on pump lock → wait 5s → turn on zone switch
    - Wait for duration → turn off zone switch → wait 2s → turn off pump lock
    - _Requirements: 4.3, 4.4, 4.5, 9.2, 9.3, 9.4, 9.5_
  - [x] 11.3 Add error handling and logging


    - Handle HA API failures gracefully
    - Log all queue operations and job executions
    - _Requirements: Error handling_
-

- [x] 12. Event scheduler




  - [x] 12.1 Create services/scheduler.py


    - Run every 60 seconds using APScheduler
    - Load all enabled rooms and events from database
    - _Requirements: 8.1, 8.2_
  - [x] 12.2 Implement P1 event calculation

    - Get lights_on_entity value from HA
    - Add delay_minutes to calculate start time
    - Check if current time matches (within 60s window)
    - _Requirements: 5.3, 8.3_
  - [x] 12.3 Implement P2 event calculation

    - Parse time_of_day (HH:MM format)
    - Check if current time matches (within 60s window)
    - _Requirements: 6.3, 8.3_
  - [x] 12.4 Create execution jobs for matched events

    - For each zone assigned to event, create job
    - Add job to pump queue via queue_processor
    - _Requirements: 8.4, 8.5_

- [x] 13. Manual control API




  - [x] 13.1 Create routers/manual.py


    - POST /api/manual/run - Run zone manually with custom duration
    - POST /api/manual/stop - Emergency stop current operation
    - _Requirements: Manual control functionality_
  - [x] 13.2 Integrate with queue processor


    - Manual jobs bypass scheduler, go directly to queue
    - _Requirements: Manual control integration_

## Phase 4: Frontend Application
-

- [x] 14. Frontend project setup



  - [x] 14.1 Create frontend/ directory with Vue 3 + Vite


    - Initialize package.json with dependencies
    - Configure vite.config.js for production build
    - Setup Vue Router and Pinia
    - _Requirements: 1.1, 1.3_
  - [x] 14.2 Create API client service


    - Implement axios-based API wrapper
    - Handle authentication and error responses
    - _Requirements: Frontend-backend communication_
  - [x] 14.3 Create shared components


    - EntitySelector.vue - Searchable dropdown for HA entities
    - StatusBadge.vue - Status indicators
    - ConfirmDialog.vue - Confirmation dialogs
    - _Requirements: Reusable UI components_



- [x] 15. Dashboard view


  - [x] 15.1 Create views/Dashboard.vue


    - Display grid of room cards
    - Show room name, status, active events
    - Add "Create Room" button
    - _Requirements: 2.1, 2.2_
  - [x] 15.2 Implement auto-refresh


    - Poll room status every 5 seconds
    - _Requirements: 12.4_
-

- [x] 16. Room detail view



  - [x] 16.1 Create views/RoomDetail.vue


    - Display room info with edit button
    - Show pumps section with add button
    - Show zones section grouped by pump
    - Show water events section with add button
    - Show sensors section with add button
    - _Requirements: Room management interface_
  - [x] 16.2 Create components/PumpCard.vue


    - Display pump name, lock entity, status
    - Show zones list with edit/delete actions
    - Add zone button
    - _Requirements: 3.1_
  - [x] 16.3 Create components/EventCard.vue


    - Display event type (P1/P2), name, timing
    - Show assigned zones
    - Edit/delete actions
    - _Requirements: Event display_

- [x] 17. Room editor




  - [x] 17.1 Create components/RoomEditor.vue


    - Form for room name
    - Entity selectors for lights_on and lights_off
    - Enabled toggle
    - Save/cancel actions
    - _Requirements: 2.3, 2.4_
-

- [x] 18. Pump and zone editors



  - [x] 18.1 Create components/PumpEditor.vue


    - Form for pump name
    - Entity selector for lock entity
    - _Requirements: 2.3, 2.4_
  - [x] 18.2 Create components/ZoneEditor.vue


    - Form for zone name
    - Entity selector for switch entity
    - _Requirements: 3.2, 3.3_

- [x] 19. Water event editor




  - [x] 19.1 Create components/WaterEventEditor.vue


    - Event type selector (P1/P2)
    - Event name input
    - P1: delay_minutes input
    - P2: time_of_day input (HH:MM)
    - Run time input (seconds with helper for MM:SS)
    - Zone multi-select checkboxes
    - _Requirements: 5.1, 5.2, 6.1, 6.2_
-

- [x] 20. Sensor management



  - [x] 20.1 Create components/SensorEditor.vue


    - Form for sensor display name
    - Entity selector for sensor entity
    - Sensor type dropdown
    - Unit input (optional)
    - _Requirements: Sensor configuration_
  - [x] 20.2 Create components/SensorCard.vue


    - Display current value
    - Show historical graph with duration selector
    - _Requirements: Sensor display and graphs_

- [x] 21. Manual control interface




  - [x] 21.1 Create components/ManualControl.vue


    - Zone selector dropdown
    - Duration input (seconds)
    - Run button
    - Stop button
    - Progress indicator
    - _Requirements: Manual control UI_

- [x] 22. Settings view




  - [x] 22.1 Create views/Settings.vue


    - Form for pump_startup_delay_seconds
    - Form for zone_switch_delay_seconds
    - Form for scheduler_interval_seconds
    - Save button
    - _Requirements: 7.1, 7.2_
  - [x] 22.2 Add system reset functionality


    - "Delete All Data" button with confirmation
    - _Requirements: System reset_

## Phase 5: Integration and Deployment


- [x] 23. Backend startup integration



  - [x] 23.1 Update main.py with background tasks


    - Start scheduler on app startup
    - Start queue processor on app startup
    - Initialize database on first run
    - _Requirements: 8.1, 9.1_
  - [x] 23.2 Configure static file serving


    - Serve frontend build from /app/frontend/dist
    - Mount at root path
    - _Requirements: 1.1_


- [x] 24. Docker and deployment




  - [x] 24.1 Update Dockerfile


    - Install Node.js for frontend build
    - Copy and build frontend
    - Install Python dependencies
    - Configure entrypoint
    - _Requirements: Deployment_
  - [x] 24.2 Test run.sh script


    - Verify uvicorn starts correctly
    - Verify database initialization
    - _Requirements: Deployment_


- [x] 25. Documentation




  - [x] 25.1 Update README.md


    - Document room-based architecture
    - Add setup instructions
    - Include screenshots
    - _Requirements: Documentation_
  - [x] 25.2 Create API documentation


    - Add OpenAPI/Swagger docs to FastAPI
    - _Requirements: API documentation_

- [x] 26. Testing





  - [ ]* 26.1 Write backend unit tests
    - Test schedule calculation logic
    - Test queue operations
    - Test API endpoints
    - _Requirements: Testing_
  - [ ]* 26.2 Write integration tests
    - Test full event scheduling flow
    - Test manual control flow
    - _Requirements: Testing_
  - [ ]* 26.3 Manual testing checklist
    - Test all CRUD operations
    - Test scheduler with real HA entities
    - Test manual control
    - Test error scenarios
    - _Requirements: Testing_
