# Implementation Plan - Room-Based Irrigation System

Complete redesign with room-based organization. Implementation in phases: backend first, then frontend.

- [-] 1. Database schema setup

- [x] 1.1 Create rooms, pumps, zones tables


- [ ] 1.2 Create water_events and event_zones tables  
- [ ] 1.3 Create environmental_sensors table
- [ ] 1.4 Create system_settings table

- [ ] 2. Rooms API
- [ ] 2.1 GET/POST/PUT/DELETE /api/rooms endpoints
- [ ] 2.2 Fetch lights schedule from HA entities

- [ ] 3. Pumps and Zones API
- [ ] 3.1 Pumps CRUD endpoints
- [ ] 3.2 Zones CRUD endpoints

- [ ] 4. Water Events API
- [ ] 4.1 P1/P2 events CRUD
- [ ] 4.2 Zone assignment logic

- [ ] 5. Sensors API
- [ ] 5.1 Sensors CRUD
- [ ] 5.2 Historical data from HA

- [ ] 6. Execution Engine
- [ ] 6.1 Pump/zone control with timing
- [ ] 6.2 Queue management
- [ ] 6.3 5-second pump delay, 2-second zone delay

- [ ] 7. Event Scheduler
- [ ] 7.1 Calculate P1/P2 times
- [ ] 7.2 60-second tick scheduler

- [ ] 8. Manual Control API
- [ ] 8.1 Manual run/stop endpoints

- [ ] 9. Settings API
- [ ] 9.1 Settings CRUD
- [ ] 9.2 Delete all data endpoint

- [ ] 10. Frontend - Dashboard
- [ ] 10.1 Room cards with status
- [ ] 10.2 Auto-refresh

- [ ] 11. Frontend - Room Detail
- [ ] 11.1 Pumps/zones display
- [ ] 11.2 Events panel
- [ ] 11.3 Sensors panel

- [ ] 12. Frontend - Event Editor
- [ ] 12.1 P1/P2 event forms
- [ ] 12.2 Zone selection

- [ ] 13. Frontend - Manual Control
- [ ] 13.1 Manual run dialog
- [ ] 13.2 Progress display

- [ ] 14. Frontend - Sensors
- [ ] 14.1 Sensor cards
- [ ] 14.2 Historical graphs

- [ ] 15. Frontend - Settings
- [ ] 15.1 Settings form
- [ ] 15.2 Delete all data

- [ ] 16. Testing and Documentation
- [ ] 16.1 Integration testing
- [ ] 16.2 Update docs
- [ ] 16.3 Deploy v2.0.0
