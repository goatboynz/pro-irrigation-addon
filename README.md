# Pro-Irrigation v2 - Room-Based System

A complete redesign of the irrigation management system, now organized around grow rooms for simpler, more intuitive operation. Built as a Home Assistant add-on with a modern web interface.

## What's New in v2

- **Room-Based Organization**: Everything organized by grow rooms instead of individual zones
- **Simplified Scheduling**: P1 and P2 events configured at the room level
- **Manual Controls**: Easy manual pump/zone operation with custom durations
- **Environmental Monitoring**: Track soil RH, EC, and more with historical graphs
- **Better Timing**: Configurable pump startup and zone switch delays
- **Queue Management**: Intelligent pump queue prevents conflicts and ensures sequential execution

## Quick Start

### Installation

1. Add this repository to Home Assistant:
   ```
   https://github.com/goatboynz/pro-irrigation-addon
   ```

2. Install "Pro-Irrigation v2"

3. Start the add-on

4. Enable "Show in sidebar" to access from Home Assistant menu

### First Steps

1. **Create a Room**
   - Name it (e.g., "Flower Room 1")
   - Select lights-on entity (input_datetime or sensor)
   - Select lights-off entity (input_datetime or sensor)
   - Enable the room

2. **Add a Pump**
   - Name it (e.g., "Main Pump")
   - Select lock entity (input_boolean that prevents simultaneous zone operation)

3. **Add Zones**
   - Name each zone (e.g., "Front Left", "Back Right")
   - Select switch entity that controls the zone valve
   - Zones are automatically associated with their pump

4. **Configure Water Events**
   - **P1 Events**: Primary watering after lights turn on
     - Set delay in minutes (e.g., 30 minutes after lights on)
     - Set run time in seconds (e.g., 82 for 1min 22sec)
   - **P2 Events**: Secondary waterings at specific times
     - Set time of day in HH:MM format (e.g., 14:00, 18:00)
     - Set run time in seconds
   - Assign events to specific zones (multi-select)

5. **Add Sensors** (Optional)
   - Soil moisture, EC, temperature, humidity, etc.
   - View real-time values
   - Historical graphs with configurable time ranges

## Features

### Room Management
- Create multiple grow rooms with independent configurations
- Each room has its own lights schedule
- Centralized water event management per room
- Enable/disable rooms without deleting configuration

### Water Events
- **P1 Events**: Primary watering triggered by lights-on event
  - Configurable delay after lights turn on
  - Ideal for first watering of the day
- **P2 Events**: Secondary waterings at specific times
  - Set exact time of day (HH:MM format)
  - Perfect for mid-day or evening waterings
- Run times in seconds for precise control
- Assign events to multiple zones
- Events automatically calculate next run time

### Pump Queue System
- Each pump maintains its own execution queue
- Prevents multiple zones from running simultaneously on the same pump
- First-in-first-out (FIFO) execution order
- Automatic pump lock management
- Configurable startup and shutdown delays

### Manual Control
- Run any zone manually with custom duration
- Emergency stop functionality
- Jobs added directly to pump queue
- Bypasses scheduler for immediate execution

### Environmental Monitoring
- Add multiple sensors per room
- Real-time value display
- Historical graphs with time range selection:
  - 1 hour
  - 6 hours
  - 24 hours
  - 7 days
- Support for various sensor types:
  - Soil moisture (RH)
  - Electrical conductivity (EC)
  - Temperature
  - Humidity
  - Custom sensors

### System Settings
- **Pump Startup Delay**: Time to wait after activating pump lock before turning on zone (default: 5 seconds)
- **Zone Switch Delay**: Time to wait after turning off zone before deactivating pump lock (default: 2 seconds)
- **Scheduler Interval**: How often the scheduler checks for events (default: 60 seconds)
- **System Reset**: Delete all data and start fresh (preserves settings)

## Architecture

### Hierarchical Structure

```
Rooms
  ├── Pumps
  │   └── Zones
  ├── Water Events (P1/P2)
  │   └── Assigned Zones
  └── Environmental Sensors
```

### Component Overview

**Backend (Python/FastAPI)**
- RESTful API for all operations
- SQLite database for persistent storage
- Scheduler engine (runs every 60 seconds)
- Queue processor (runs every 1 second)
- Home Assistant API integration

**Frontend (Vue.js)**
- Modern single-page application
- Real-time status updates
- Responsive design for mobile and desktop
- Integrated with Home Assistant Ingress

**Background Services**
- **Scheduler**: Evaluates all water events and creates execution jobs
- **Queue Processor**: Manages pump queues and executes jobs sequentially
- **HA Client**: Communicates with Home Assistant API for entity control and state

### Execution Flow

1. **Scheduler** checks all enabled rooms and water events every 60 seconds
2. When an event is due, **Scheduler** creates execution jobs for assigned zones
3. Jobs are added to the appropriate **Pump Queue**
4. **Queue Processor** checks each pump's queue every 1 second
5. If pump is idle and queue has jobs, **Queue Processor** executes the first job:
   - Turn on pump lock
   - Wait for pump startup delay (5s)
   - Turn on zone switch
   - Wait for duration
   - Turn off zone switch
   - Wait for zone switch delay (2s)
   - Turn off pump lock
6. Process repeats for next job in queue

## System Requirements

### Home Assistant
- Home Assistant OS or Supervised
- Version 2023.1 or later recommended

### Required Entities
- **Switch entities** for zone control (e.g., `switch.zone_1`)
- **Input boolean entities** for pump locks (e.g., `input_boolean.pump_1_lock`)

### Optional Entities
- **Input datetime entities** for lights schedule (e.g., `input_datetime.lights_on`)
- **Sensor entities** for environmental monitoring (e.g., `sensor.soil_moisture`)

### Hardware
- Raspberry Pi 3 or better (for Home Assistant)
- Adequate storage for database and logs

## API Documentation

The system provides a comprehensive REST API. Access the interactive API documentation at:

- **Swagger UI**: `http://your-homeassistant:8000/docs`
- **ReDoc**: `http://your-homeassistant:8000/redoc`

### Key API Endpoints

**Rooms**
- `GET /api/rooms` - List all rooms
- `POST /api/rooms` - Create room
- `GET /api/rooms/{id}` - Get room details
- `PUT /api/rooms/{id}` - Update room
- `DELETE /api/rooms/{id}` - Delete room
- `GET /api/rooms/{id}/status` - Get room status

**Pumps**
- `GET /api/rooms/{room_id}/pumps` - List pumps for room
- `POST /api/rooms/{room_id}/pumps` - Create pump
- `PUT /api/pumps/{id}` - Update pump
- `DELETE /api/pumps/{id}` - Delete pump
- `GET /api/pumps/{id}/status` - Get pump status

**Zones**
- `GET /api/pumps/{pump_id}/zones` - List zones for pump
- `POST /api/pumps/{pump_id}/zones` - Create zone
- `PUT /api/zones/{id}` - Update zone
- `DELETE /api/zones/{id}` - Delete zone

**Water Events**
- `GET /api/rooms/{room_id}/events` - List events for room
- `POST /api/rooms/{room_id}/events` - Create event
- `PUT /api/events/{id}` - Update event
- `DELETE /api/events/{id}` - Delete event
- `POST /api/events/{id}/zones/{zone_id}` - Assign zone to event
- `DELETE /api/events/{id}/zones/{zone_id}` - Remove zone from event

**Sensors**
- `GET /api/rooms/{room_id}/sensors` - List sensors for room
- `POST /api/rooms/{room_id}/sensors` - Create sensor
- `PUT /api/sensors/{id}` - Update sensor
- `DELETE /api/sensors/{id}` - Delete sensor
- `GET /api/sensors/{id}/current` - Get current sensor value
- `GET /api/sensors/{id}/history` - Get historical sensor data

**Manual Control**
- `POST /api/manual/run` - Run zone manually
- `POST /api/manual/stop` - Emergency stop

**Settings**
- `GET /api/settings` - Get system settings
- `PUT /api/settings` - Update system settings
- `POST /api/system/reset` - Reset all data

## Troubleshooting

### Zones Not Running

1. Check that the room is enabled
2. Verify water events are configured correctly
3. Check that zones are assigned to events
4. Verify Home Assistant entities are accessible
5. Check logs for scheduler errors

### Pump Lock Issues

1. Ensure pump lock entity exists in Home Assistant
2. Verify entity is an `input_boolean`
3. Check that lock entity is not stuck in "on" state
4. Review queue processor logs

### Scheduler Not Triggering

1. Verify lights-on/lights-off entities are correct
2. Check that current time matches event schedule
3. Ensure scheduler interval is set correctly (default: 60s)
4. Review scheduler logs for calculation errors

### Frontend Not Loading

1. Verify add-on is running
2. Check that Ingress is enabled
3. Clear browser cache
4. Check add-on logs for errors

### Entity Not Found

1. Ensure entity exists in Home Assistant
2. Verify entity ID is spelled correctly
3. Check that entity is not disabled
4. Restart Home Assistant if entity was recently created

## Development

### Project Structure

```
.
├── backend/
│   ├── main.py                 # FastAPI application
│   ├── models/                 # Database models
│   ├── routers/                # API endpoints
│   ├── services/               # Background services
│   └── schemas.py              # Pydantic schemas
├── frontend/
│   ├── src/
│   │   ├── components/         # Vue components
│   │   ├── views/              # Page views
│   │   └── services/           # API client
│   └── package.json
├── data/                       # Database storage
├── Dockerfile                  # Container build
└── config.yaml                 # HA add-on config
```

### Building Locally

```bash
# Build Docker image
docker build -t pro-irrigation:dev .

# Run locally
docker run -p 8000:8000 \
  -v $(pwd)/data:/data \
  -e SUPERVISOR_TOKEN=your_token \
  pro-irrigation:dev
```

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## Support

- **GitHub**: https://github.com/goatboynz/pro-irrigation-addon
- **Issues**: https://github.com/goatboynz/pro-irrigation-addon/issues
- **Discussions**: https://github.com/goatboynz/pro-irrigation-addon/discussions

## Version History

### 2.0.0 (Current)
- Complete redesign with room-based architecture
- New Vue.js frontend
- FastAPI backend
- Scheduler and queue processor
- Environmental monitoring
- Manual control interface

### 1.0.0 (Deprecated)
- Original zone-based system
- Node-RED flows
- Basic scheduling

## License

MIT License - See LICENSE file for details

## Credits

Developed for Home Assistant community by goatboynz
