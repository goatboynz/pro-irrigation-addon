# Install Pro-Irrigation in Home Assistant

Your add-on is now live on GitHub! Follow these steps to install it in Home Assistant.

## Repository URL
```
https://github.com/goatboynz/pro-irrigation-addon
```

## Installation Steps

### 1. Add Repository to Home Assistant

1. Open your Home Assistant instance
2. Navigate to **Settings** → **Add-ons** → **Add-on Store**
3. Click the **three-dot menu (⋮)** in the top right corner
4. Select **Repositories**
5. Paste this URL:
   ```
   https://github.com/goatboynz/pro-irrigation-addon
   ```
6. Click **Add**
7. Close the dialog

### 2. Install the Add-on

1. Refresh the Add-on Store page (F5 or reload)
2. Scroll down to find **"Pro-Irrigation"** in the list
3. Click on it
4. Click **Install**
5. Wait for installation to complete (5-10 minutes)

### 3. Configure and Start

1. After installation, go to the **Configuration** tab
2. Set `log_level` if desired (default: `info`)
3. Click **Save**
4. Go to the **Info** tab
5. Click **Start**
6. Wait for the add-on to start (30-60 seconds)

### 4. Enable Sidebar Access

1. Toggle **Show in sidebar** to ON
2. The add-on icon will appear in your Home Assistant sidebar
3. Click it to access the Pro-Irrigation interface

### 5. Verify Installation

Check the **Log** tab for successful startup:
```
============================================================
Pro-Irrigation Add-on - Startup Script
============================================================
Configuration:
  Log level: info
  Workers: 1
  Database path: /data/irrigation.db
  Port: 8000
============================================================
Starting FastAPI server...
INFO:     Started server process
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## Prerequisites

Before using the add-on, ensure you have:

### Required Entities

1. **Switch Entities**: One for each irrigation zone
   - Example: `switch.zone_1`, `switch.zone_2`

2. **Boolean Input Helpers**: One for each pump (acts as a lock)
   - Create via: Settings → Devices & Services → Helpers → Create Helper → Toggle
   - Example: `input_boolean.pump_1_lock`

### Optional (for Auto Mode)

Create these input helpers:
- `input_datetime.lights_on` - When lights turn on
- `input_datetime.lights_off` - When lights turn off
- `input_number.p1_start_delay` - Minutes after lights-on for P1
- `input_number.p2_start_delay` - Minutes after lights-on for P2 start
- `input_number.p2_end_buffer` - Minutes before lights-off for P2 end

## First Time Setup

### 1. Configure Global Settings (Optional)

1. Click **Settings** in the navigation menu
2. Select your input helpers from the dropdowns
3. Click **Save Settings**

### 2. Add Your First Pump

1. From the **Pumps Dashboard**, click **Add New Pump**
2. Enter a name (e.g., "Main Pump")
3. Select the lock entity (e.g., `input_boolean.pump_1_lock`)
4. Click **Create**

### 3. Add Zones

1. Click **Manage** on the pump card
2. Click **Add New Zone to this Pump**
3. Fill in the zone details:
   - Name: Descriptive name
   - Switch Entity: Select the switch
   - Mode: Auto or Manual
4. Configure schedule based on mode
5. Click **Save Zone**

## Troubleshooting

### Repository Not Appearing

- Verify the URL is correct
- Check that the repository is public
- Try removing and re-adding the repository
- Refresh the page

### Add-on Won't Install

- Check Home Assistant logs
- Verify your architecture is supported (aarch64, amd64, armv7)
- Ensure you have enough disk space
- Try restarting Home Assistant

### Add-on Won't Start

- Check the Log tab for errors
- Verify port 8000 is not in use
- Check disk space
- Try rebuilding the add-on

### Can't Access Interface

- Verify "Show in sidebar" is enabled
- Try accessing directly: `http://homeassistant.local:8000`
- Clear browser cache
- Check Ingress is enabled in config

## GitHub Repository

View the source code and documentation:
https://github.com/goatboynz/pro-irrigation-addon

## Support

- **GitHub Issues**: https://github.com/goatboynz/pro-irrigation-addon/issues
- **Home Assistant Community**: https://community.home-assistant.io/

## What's Next?

- Configure your pumps and zones
- Test the scheduling system
- Monitor operation via logs
- Share feedback on GitHub

---

**Repository**: https://github.com/goatboynz/pro-irrigation-addon  
**Version**: 1.0.0  
**Status**: ✓ Live and ready to install
