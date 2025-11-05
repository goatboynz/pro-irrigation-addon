# Pro-Irrigation Add-on

Professional irrigation management system for Home Assistant that provides centralized control of irrigation pumps and zones through an intuitive web interface.

## Overview

The Pro-Irrigation Add-on replaces complex Node-RED flows and dozens of input helpers with a single, professional interface. Built around a "Pumps → Zones" hierarchy that matches your physical irrigation hardware, it provides intelligent scheduling with built-in safety mechanisms to prevent pump conflicts.

## Features

- **Pump Management**: Organize irrigation zones by physical pump hardware
- **Intelligent Scheduling**: 
  - Auto Mode: Automatically calculates irrigation times based on your lighting schedule
  - Manual Mode: Specify exact irrigation times with precision control
- **Queue Management**: Prevents multiple zones on the same pump from running simultaneously
- **Home Assistant Integration**: 
  - Embedded UI via Ingress (accessible from sidebar)
  - Controls Home Assistant switch entities
  - Discovers and uses existing input helpers
- **Real-time Monitoring**: Live pump and zone status updates
- **Persistent Configuration**: All settings stored in SQLite database

## Installation

### Method 1: Add Repository to Home Assistant

1. Navigate to **Settings** → **Add-ons** → **Add-on Store** in Home Assistant
2. Click the three-dot menu (⋮) in the top right corner
3. Select **Repositories**
4. Add this repository URL: `https://github.com/goatboynz/pro-irrigation-addon`
5. Click **Add**
6. Find "Pro-Irrigation" in the add-on store
7. Click on it and select **Install**
8. Wait for the installation to complete (this may take several minutes)

### Method 2: Manual Installation

1. Copy the add-on files to your Home Assistant add-ons directory:
   ```
   /addons/pro-irrigation/
   ```
2. Restart Home Assistant
3. Navigate to **Settings** → **Add-ons** → **Add-on Store**
4. Refresh the page
5. Find "Pro-Irrigation" in the local add-ons section
6. Click **Install**

### Starting the Add-on

1. After installation, click **Start**
2. Enable **Start on boot** if you want the add-on to start automatically
3. Enable **Watchdog** to automatically restart the add-on if it crashes
4. Click **Show in sidebar** to add quick access to the Home Assistant menu

## Configuration

### Add-on Configuration

The add-on can be configured through the Configuration tab:

```yaml
log_level: info
```

**Configuration Options:**

- `log_level` (optional): Set logging verbosity
  - `debug`: Detailed debugging information
  - `info`: General informational messages (default)
  - `warning`: Warning messages only
  - `error`: Error messages only

### Prerequisites

Before using the add-on, ensure you have:

1. **Switch Entities**: One switch entity for each irrigation zone (e.g., `switch.zone_1`, `switch.zone_2`)
2. **Lock Entities**: One boolean input helper for each pump to act as a lock (e.g., `input_boolean.pump_1_lock`)

### Optional: Auto Mode Prerequisites

If you plan to use Auto Mode scheduling, create these input helpers:

1. **Lights On Time**: `input_datetime.lights_on` - When your lights turn on
2. **Lights Off Time**: `input_datetime.lights_off` - When your lights turn off
3. **P1 Start Delay**: `input_number.p1_start_delay` - Minutes after lights-on to start first irrigation
4. **P2 Start Delay**: `input_number.p2_start_delay` - Minutes after lights-on to start P2 events
5. **P2 End Buffer**: `input_number.p2_end_buffer` - Minutes before lights-off to stop P2 events

## Usage Guide

### Initial Setup

#### 1. Configure Global Settings (Optional for Auto Mode)

1. Click **Settings** in the navigation menu
2. Select your input helpers from the dropdowns:
   - Lights On Entity
   - Lights Off Entity
   - P1 Start Delay Entity
   - P2 Start Delay Entity
   - P2 End Buffer Entity
3. Add any feed schedule notes in the text area
4. Click **Save Settings**

#### 2. Add Your First Pump

1. From the **Pumps Dashboard**, click **Add New Pump**
2. Enter a name for your pump (e.g., "Main Pump", "Greenhouse Pump")
3. Select the lock entity for this pump (e.g., `input_boolean.pump_1_lock`)
4. Click **Create**

#### 3. Add Zones to Your Pump

1. Click **Manage** on the pump card
2. Click **Add New Zone to this Pump**
3. Fill in the zone details:
   - **Name**: Descriptive name (e.g., "Tomatoes", "Lettuce Bed 1")
   - **Switch Entity**: Select the switch that controls this zone
   - **Mode**: Choose Auto or Manual

**For Auto Mode:**
- **P1 Duration**: How long (in seconds) the first irrigation runs
- **P2 Event Count**: Number of additional irrigations throughout the day
- **P2 Duration**: How long (in seconds) each P2 irrigation runs

**For Manual Mode:**
- **P1 Events**: List of times in format `HH:MM.SS` (one per line)
  - Example: `08:30.120` means 8:30 AM for 120 seconds
- **P2 Events**: List of times in format `HH:MM.SS` (one per line)

4. Click **Save Zone**

### Understanding Scheduling Modes

#### Auto Mode

Auto Mode automatically calculates irrigation times based on your lighting schedule:

- **P1 Event**: Runs once per day at `lights_on + p1_start_delay`
- **P2 Events**: Distributed evenly between `lights_on + p2_start_delay` and `lights_off - p2_end_buffer`

Example:
- Lights on: 6:00 AM
- Lights off: 10:00 PM
- P1 delay: 30 minutes
- P2 delay: 60 minutes
- P2 buffer: 60 minutes
- P2 count: 3

Result:
- P1: 6:30 AM
- P2: 7:00 AM, 1:40 PM, 8:20 PM

#### Manual Mode

Manual Mode gives you precise control over irrigation times. Enter times in `HH:MM.SS` format where:
- `HH`: Hour (00-23)
- `MM`: Minute (00-59)
- `SS`: Duration in seconds

Example:
```
08:00.300
12:30.180
18:45.240
```

### Monitoring Your System

#### Pump Status Indicators

- **Idle**: Pump is not running, no zones queued
- **Running**: Pump is actively irrigating a zone (zone name shown)
- **Queued**: Pump has zones waiting to run

#### Zone Information

Each zone displays:
- **Name**: Zone identifier
- **Mode**: Auto or Manual badge
- **Next Run**: When the zone will next execute
- **Status**: Enabled or Disabled

### Managing Your System

#### Editing Zones

1. Navigate to the Zone Manager for the pump
2. Click the **Edit** button on the zone
3. Modify settings as needed
4. Click **Save Zone**

#### Deleting Zones

1. Navigate to the Zone Manager for the pump
2. Click the **Delete** button on the zone
3. Confirm the deletion

#### Enabling/Disabling Zones

1. Edit the zone
2. Toggle the **Enabled** checkbox
3. Save the zone

Disabled zones will not execute but retain their configuration.

#### Deleting Pumps

1. From the Pumps Dashboard, click **Manage** on the pump
2. Click **Delete Pump** (if available)
3. Confirm the deletion

Note: Deleting a pump will also delete all associated zones.

## How It Works

### Scheduler Engine

The scheduler runs every 60 seconds and:
1. Loads all enabled zones from the database
2. Retrieves current global settings from Home Assistant
3. Calculates scheduled times for each zone
4. Creates execution jobs for zones that should run now
5. Adds jobs to the appropriate pump queue

### Queue Processor

The queue processor runs every 1 second and:
1. Checks each pump's lock status
2. If a pump is idle and has queued jobs:
   - Locks the pump
   - Turns on the zone switch
   - Waits for the specified duration
   - Turns off the zone switch
   - Unlocks the pump
3. Processes the next job in the queue

### Safety Mechanisms

- **Pump Locks**: Prevent multiple zones on the same pump from running simultaneously
- **Queue System**: Ensures zones run in the order they were scheduled
- **Timeout Protection**: Automatically unlocks stuck pumps after 5 minutes
- **Error Handling**: Continues operation even if individual zones fail

## Troubleshooting

### Add-on Won't Start

**Check the logs:**
1. Go to the add-on page
2. Click the **Log** tab
3. Look for error messages

**Common issues:**
- Database corruption: Delete `/data/irrigation.db` and restart
- Port conflict: Ensure port 8000 is not in use by another add-on

### Zones Not Running

**Verify zone configuration:**
1. Check that the zone is **Enabled**
2. Verify the switch entity exists and is correct
3. Check the next run time is in the future

**Check global settings (Auto Mode):**
1. Ensure all required input helpers are configured
2. Verify the input helper values are reasonable
3. Check that lights-on time is before lights-off time

**Check pump lock:**
1. Verify the pump lock entity exists
2. Manually check if the lock is stuck "on"
3. Manually turn off the lock if needed

### Switch Not Responding

**Verify Home Assistant connection:**
1. Check that Home Assistant is running
2. Verify the switch entity exists in Home Assistant
3. Test the switch manually in Home Assistant

**Check entity permissions:**
- Ensure the add-on has permission to control switches

### Incorrect Schedule Times

**For Auto Mode:**
1. Verify global settings are configured correctly
2. Check input helper values in Home Assistant
3. Review the calculation logic in the design document

**For Manual Mode:**
1. Verify time format is correct: `HH:MM.SS`
2. Check for typos in the event list
3. Ensure times are in 24-hour format

### Database Issues

**Reset the database:**
1. Stop the add-on
2. Access the add-on's file system or use SSH
3. Delete `/data/irrigation.db`
4. Restart the add-on
5. Reconfigure your pumps and zones

**Backup the database:**
- The database is located at `/data/irrigation.db`
- Copy this file to back up your configuration

### UI Not Loading

**Clear browser cache:**
1. Hard refresh the page (Ctrl+Shift+R or Cmd+Shift+R)
2. Clear browser cache for Home Assistant
3. Try a different browser

**Check Ingress:**
1. Verify Ingress is enabled in config.yaml
2. Restart the add-on
3. Check Home Assistant logs for Ingress errors

### Performance Issues

**Reduce polling frequency:**
- The system polls every 5 seconds by default
- This is configurable in the frontend code if needed

**Optimize zone count:**
- The system is tested with up to 100 zones
- Consider splitting very large systems across multiple instances

## Advanced Configuration

### Environment Variables

The following environment variables can be set in the Dockerfile or run.sh:

- `LOG_LEVEL`: Override the log level (debug, info, warning, error)
- `WORKERS`: Number of uvicorn workers (default: 1, do not change)
- `DATABASE_PATH`: Path to SQLite database (default: /data/irrigation.db)

### Database Schema

The database uses SQLite with three main tables:
- `pumps`: Pump configurations
- `zones`: Zone configurations and schedules
- `global_settings`: System-wide settings

Direct database access is not recommended but can be done via SQLite tools.

## Development

### Project Structure

```
pro-irrigation-addon/
├── backend/              # Python FastAPI backend
│   ├── main.py          # Application entry point
│   ├── models/          # Database models and schemas
│   ├── services/        # Business logic services
│   ├── routers/         # API route handlers
│   └── tests/           # Backend tests
├── frontend/            # Vue.js frontend application
│   ├── src/
│   │   ├── components/  # Vue components
│   │   ├── views/       # Page views
│   │   ├── services/    # API client
│   │   ├── stores/      # Pinia state management
│   │   └── router/      # Vue Router configuration
│   └── package.json
├── data/                # Persistent data directory
├── config.yaml          # Home Assistant add-on configuration
├── Dockerfile           # Multi-stage Docker build
└── run.sh              # Startup script
```

### Backend Development

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

The frontend dev server will proxy API requests to the backend.

### Running Tests

**Backend tests:**
```bash
cd backend
pytest
```

**Frontend tests:**
```bash
cd frontend
npm run test
```

### Building the Add-on

```bash
docker build -t pro-irrigation:latest .
```

## API Documentation

The REST API is documented at `/api/docs` when the add-on is running. Access it at:
```
http://homeassistant.local:8000/api/docs
```

## Support

For issues, feature requests, or questions:
- GitHub Issues: https://github.com/goatboynz/pro-irrigation-addon/issues
- Home Assistant Community: https://community.home-assistant.io/

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - See LICENSE file for details

## Acknowledgments

Built for the Home Assistant community with ❤️
