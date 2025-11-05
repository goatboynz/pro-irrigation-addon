# Implementation Plan

- [x] 1. Set up project structure and Home Assistant add-on configuration





  - Create directory structure for add-on (backend/, frontend/, data/)
  - Write config.yaml with add-on metadata, ingress configuration, and schema
  - Write Dockerfile with multi-stage build for frontend and backend
  - Create run.sh script to start both frontend server and backend API
  - _Requirements: 1.1, 1.2_


- [x] 2. Implement database models and initialization




  - [x] 2.1 Create SQLAlchemy database models


    - Write Pump model with id, name, lock_entity, timestamps, and zones relationship
    - Write Zone model with all fields (pump_id, name, switch_entity, mode, auto/manual parameters, enabled flag)
    - Write GlobalSettings model with entity references and feed_notes
    - Implement database.py with engine creation and session management
    - _Requirements: 10.2, 10.3, 10.4_

  - [x] 2.2 Create database initialization and migration logic

    - Write init_db() function to create tables on first run
    - Implement database connection with /data/irrigation.db path
    - Add database health check function
    - _Requirements: 10.1, 10.5_

- [x] 3. Implement Home Assistant API client




  - [x] 3.1 Create HomeAssistantClient class


    - Implement __init__ with supervisor token and base URL configuration
    - Write get_entities() method to discover entities by type (switch, input_datetime, input_number, input_boolean)
    - Write get_state() method to retrieve entity state
    - Write call_service() method for generic service calls
    - Implement turn_on() and turn_off() convenience methods
    - Add error handling and retry logic for API failures
    - _Requirements: 3.4, 7.3, 8.2, 9.3, 9.4, 9.5, 9.6_

- [x] 4. Implement schedule calculation logic



  - [x] 4.1 Create schedule calculator service


    - Write calculate_auto_schedule() function implementing P1/P2 algorithm
    - Implement P1 calculation: lights_on + p1_start_delay
    - Implement P2 calculation: distribute events between p2_start and p2_end
    - Write parse_manual_schedule() function to parse HH:MM.SS format
    - Add validation for manual schedule format
    - _Requirements: 5.3, 5.4, 5.5, 5.6, 6.3, 6.4, 6.5_
  - [x] 4.2 Implement next run time calculation


    - Write get_next_run_time() function for a zone
    - Handle both auto and manual mode calculations
    - Return None if no upcoming events scheduled
    - _Requirements: 11.2_
-

- [x] 5. Implement Scheduler Engine



  - [x] 5.1 Create scheduler service with APScheduler


    - Initialize APScheduler with 60-second interval job
    - Write scheduler_tick() main function
    - Implement logic to load all enabled zones from database
    - Add logic to retrieve global settings from Home Assistant
    - _Requirements: 8.1, 8.2, 8.3_
  - [x] 5.2 Implement job creation and queue management


    - Write logic to calculate scheduled times for each zone
    - Implement time matching logic (within 60-second window)
    - Create ExecutionJob data structure with zone_id, switch_entity, duration
    - Add jobs to appropriate pump queues (in-memory queue per pump)
    - _Requirements: 8.4, 8.5, 9.1_

- [x] 6. Implement Pump Queue Processor



  - [x] 6.1 Create queue processor service


    - Initialize queue processor with 1-second interval
    - Create in-memory queue dictionary (pump_id -> Queue)
    - Write processor_tick() main function
    - _Requirements: 9.1_
  - [x] 6.2 Implement queue execution logic


    - Write logic to check each pump's lock status via Home Assistant
    - Implement job execution: lock pump, turn on switch, wait duration, turn off switch, unlock pump
    - Add error handling for switch control failures
    - Implement timeout mechanism for stuck locks (5-minute timeout)
    - Add logging for all queue operations
    - _Requirements: 4.3, 4.4, 4.5, 9.2, 9.3, 9.4, 9.5, 9.6_


- [x] 7. Implement FastAPI backend REST API




  - [x] 7.1 Create main FastAPI application


    - Initialize FastAPI app with CORS middleware
    - Set up database dependency injection
    - Add health check endpoint (GET /api/health)
    - Add system status endpoint (GET /api/status)
    - _Requirements: 1.1_
  - [x] 7.2 Implement Pump API endpoints


    - Write GET /api/pumps endpoint to list all pumps with status
    - Write POST /api/pumps endpoint to create new pump
    - Write GET /api/pumps/{id} endpoint for pump details
    - Write PUT /api/pumps/{id} endpoint to update pump
    - Write DELETE /api/pumps/{id} endpoint to delete pump
    - Write GET /api/pumps/{id}/status endpoint for real-time status
    - Implement status calculation (idle/running/queued) by checking queue processor state
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 12.1, 12.2, 12.3_
  - [x] 7.3 Implement Zone API endpoints


    - Write GET /api/pumps/{pump_id}/zones endpoint to list zones
    - Write POST /api/pumps/{pump_id}/zones endpoint to create zone
    - Write GET /api/zones/{id} endpoint for zone details
    - Write PUT /api/zones/{id} endpoint to update zone
    - Write DELETE /api/zones/{id} endpoint to delete zone
    - Write GET /api/zones/{id}/next-run endpoint using calculator service
    - _Requirements: 3.1, 3.2, 3.3, 11.1, 11.2_
  - [x] 7.4 Implement Entity Discovery API endpoints


    - Write GET /api/ha/entities endpoint with type query parameter
    - Implement filtering by entity type (switch, input_datetime, input_number, input_boolean)
    - Return entity list with id, friendly_name, and state
    - _Requirements: 3.4, 7.3_
  - [x] 7.5 Implement Global Settings API endpoints


    - Write GET /api/settings endpoint to retrieve settings
    - Write PUT /api/settings endpoint to update settings
    - Create default settings row if none exists
    - _Requirements: 7.1, 7.4, 7.5_
  - [x] 7.6 Create Pydantic schemas for request/response validation


    - Write PumpCreate, PumpUpdate, PumpResponse schemas
    - Write ZoneCreate, ZoneUpdate, ZoneResponse schemas
    - Write GlobalSettingsUpdate, GlobalSettingsResponse schemas
    - Write EntityResponse schema
    - Add validation rules for all fields
    - _Requirements: 3.5, 6.5_

- [x] 8. Implement Vue.js frontend application




  - [x] 8.1 Set up Vue.js project with Vite


    - Initialize Vue 3 project with Vite
    - Install dependencies (vue-router, pinia, axios)
    - Configure Vite build to output to backend/static directory
    - Set up proxy configuration for API calls during development
    - _Requirements: 1.1, 1.3_
  - [x] 8.2 Create API service client


    - Write IrrigationAPI class with axios
    - Implement all API methods (getPumps, createPump, getZones, createZone, etc.)
    - Add error handling and toast notifications
    - Configure base URL for production (relative paths for Ingress)
    - _Requirements: 1.1_
  - [x] 8.3 Create Pinia store for state management


    - Create irrigation store with state for pumps, zones, settings
    - Implement actions for CRUD operations
    - Add getters for computed values (pump status, next run times)
    - Implement real-time status polling (every 5 seconds)
    - _Requirements: 1.4, 12.4_
  - [x] 8.4 Implement router and navigation


    - Set up Vue Router with routes for dashboard, zone manager, settings
    - Create route guards if needed
    - Implement navigation between views
    - _Requirements: 1.2_

- [x] 9. Implement Pumps Dashboard view




  - [x] 9.1 Create PumpCard component


    - Display pump name, status badge, and active zone name
    - Show queue length indicator
    - Add "Manage" button that navigates to zone manager
    - Style with Home Assistant design patterns
    - _Requirements: 2.1, 2.2, 12.1, 12.2, 12.3_
  - [x] 9.2 Create PumpsDashboard view


    - Display grid of PumpCard components
    - Add "Add New Pump" button with modal/dialog
    - Implement pump creation form (name input, lock entity selector)
    - Load pumps on mount and refresh on interval
    - _Requirements: 2.1, 2.3, 2.4, 2.5_

- [x] 10. Implement Zone Manager view






  - [x] 10.1 Create ZoneListItem component

    - Display zone name, mode badge (Auto/Manual), and next run time
    - Add edit and delete buttons
    - Show enabled/disabled status
    - _Requirements: 3.1, 11.1, 11.3, 11.4_

  - [x] 10.2 Create ZoneManager view

    - Display list of ZoneListItem components for selected pump
    - Add "Add New Zone to this Pump" button
    - Implement zone deletion with confirmation
    - Show pump name in header
    - _Requirements: 3.1, 3.2_

- [x] 11. Implement Zone Editor component





  - [x] 11.1 Create EntitySelector component


    - Implement searchable dropdown using native select or custom component
    - Load entities from API on mount
    - Filter entities as user types
    - Display entity friendly names
    - _Requirements: 3.4, 3.5_

  - [x] 11.2 Create ZoneEditor form component

    - Add zone name text input
    - Add EntitySelector for switch entity selection
    - Add mode toggle (Auto/Manual) with radio buttons or switch
    - _Requirements: 3.3, 5.1, 6.1_
  - [x] 11.3 Implement Auto Mode fields

    - Show P1 duration input (seconds)
    - Show P2 event count input (number)
    - Show P2 duration input (seconds)
    - Conditionally display when Auto mode selected
    - _Requirements: 5.2_
  - [x] 11.4 Implement Manual Mode fields

    - Show P1 event list textarea with format hint (HH:MM.SS)
    - Show P2 event list textarea with format hint
    - Add format validation and error messages
    - Conditionally display when Manual mode selected
    - _Requirements: 6.2, 6.3_
  - [x] 11.5 Implement form submission and validation


    - Add save button that calls create or update API
    - Implement client-side validation for required fields
    - Show validation errors inline
    - Close editor and refresh zone list on success
    - _Requirements: 3.3, 3.5, 6.5_


- [x] 12. Implement Global Settings view




  - [x] 12.1 Create GlobalSettings component


    - Add EntitySelector for lights_on_entity (input_datetime)
    - Add EntitySelector for lights_off_entity (input_datetime)
    - Add EntitySelector for p1_delay_entity (input_number)
    - Add EntitySelector for p2_delay_entity (input_number)
    - Add EntitySelector for p2_buffer_entity (input_number)
    - Add textarea for feed_notes
    - _Requirements: 7.1, 7.2, 7.5_
  - [x] 12.2 Implement settings form submission


    - Add save button that calls update settings API
    - Show success/error notifications
    - Load current settings on mount
    - _Requirements: 7.4_
-

- [x] 13. Implement application startup and lifecycle



  - [x] 13.1 Create main application entry point



    - Write main.py that initializes database, starts FastAPI, starts scheduler, starts queue processor
    - Implement graceful shutdown handlers
    - Add logging configuration
    - _Requirements: 10.5_

  - [x] 13.2 Create run.sh startup script

    - Start backend FastAPI server on port 8000
    - Serve frontend static files from FastAPI
    - Configure uvicorn with appropriate workers
    - _Requirements: 1.1, 1.2_




- [x] 14. Add error handling and logging







  - [x] 14.1 Implement backend error handling

    - Add try-catch blocks in all API endpoints
    - Implement custom exception handlers for FastAPI
    - Add logging for all errors with appropriate levels
    - Return proper HTTP status codes and error messages
    - _Requirements: 8.1, 9.2_


  - [ ] 14.2 Implement frontend error handling
    - Add global error handler for API failures
    - Implement toast notification system for errors
    - Add loading states for all async operations

    - Handle network timeouts with retry logic
    - _Requirements: 1.1_


- [x] 15. Implement status monitoring and real-time updates




  - [x] 15.1 Add status polling in frontend


    - Implement interval-based polling (every 5 seconds) for pump status
    - Update pump cards with latest status
    - Update zone next run times
    - _Requirements: 11.5, 12.4_


  - [x] 15.2 Implement backend status calculation


    - Write get_pump_status() function that checks queue processor state
    - Determine if pump is idle, running (with active zone), or has queued jobs
    - Cache status for performance (1-second cache)
    - _Requirements: 12.1, 12.2, 12.3_

- [x] 16. Add styling and UI polish





  - [x] 16.1 Implement Home Assistant-compatible styling


    - Create CSS variables matching HA theme colors
    - Style all components with HA design patterns
    - Ensure responsive design for mobile devices
    - Add loading spinners and skeleton screens
    - _Requirements: 1.1, 1.3_
  - [x] 16.2 Add icons and visual indicators




    - Add pump status icons (idle, running, queued)
    - Add mode badges for zones (Auto/Manual)
    - Add enabled/disabled indicators
    - Use Material Design Icons (mdi) consistent with HA
    - _Requirements: 2.2, 11.3, 11.4_

- [x] 17. Write tests for core functionality










  - [x] 17.1 Write backend unit tests





    - Test schedule calculation logic (auto mode algorithm)
    - Test manual schedule parsing
    - Test database models and relationships
    - Test API endpoint handlers
    - _Requirements: 5.3, 5.4, 5.5, 5.6, 6.4_
  - [ ]* 17.2 Write frontend component tests
    - Test PumpCard rendering and interactions
    - Test ZoneEditor form validation
    - Test EntitySelector filtering
    - Test API service methods


    --_Requirements: 3.4, 6.5_

  - [ ]* 17.3 Write integration tests
    - Test full pump creation flow
    - Test zone creation with auto mode
    - Test zone creation with manual mode
    - Test global settings update
    - _Requirements: 2.4, 3.3, 7.4_
-

- [x] 18. Create documentation and deployment files






  - [x] 18.1 Write README.md

    - Add installation instructions
    - Document configuration options
    - Add usage guide with screenshots
    - Include troubleshooting section
    - _Requirements: 1.1_

  - [x] 18.2 Create CHANGELOG.md

    - Document initial release features
    - Add version numbering
    - _Requirements: 1.1_

  - [x] 18.3 Finalize add-on configuration

    - Review and test config.yaml
    - Verify Dockerfile builds correctly
    - Test add-on installation in Home Assistant
    - Verify Ingress integration works
    - _Requirements: 1.1, 1.2_
