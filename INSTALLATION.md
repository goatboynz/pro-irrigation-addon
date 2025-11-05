# Installation and Testing Guide

This guide provides detailed instructions for installing, testing, and verifying the Pro-Irrigation Add-on.

## Prerequisites

### Home Assistant Requirements

- Home Assistant OS or Supervised installation
- Home Assistant version 2023.1 or later
- Access to the Home Assistant add-on store
- SSH access (optional, for advanced troubleshooting)

### Hardware Requirements

- Minimum 512MB RAM available for the add-on
- 100MB free disk space
- Network connectivity to Home Assistant

### Entity Requirements

Before installing, ensure you have:

1. **Switch Entities**: One for each irrigation zone
   - Example: `switch.zone_1`, `switch.zone_2`, etc.
   - These control your physical irrigation valves

2. **Boolean Input Helpers**: One for each pump (acts as a lock)
   - Create via: Settings → Devices & Services → Helpers → Create Helper → Toggle
   - Example: `input_boolean.pump_1_lock`, `input_boolean.pump_2_lock`

3. **Optional - For Auto Mode**:
   - `input_datetime.lights_on` - When lights turn on
   - `input_datetime.lights_off` - When lights turn off
   - `input_number.p1_start_delay` - Minutes after lights-on for P1
   - `input_number.p2_start_delay` - Minutes after lights-on for P2 start
   - `input_number.p2_end_buffer` - Minutes before lights-off for P2 end

## Installation Methods

### Method 1: Install from Repository (Recommended)

1. **Add the Repository**:
   - Navigate to **Settings** → **Add-ons** → **Add-on Store**
   - Click the three-dot menu (⋮) in the top right
   - Select **Repositories**
   - Add: `https://github.com/goatboynz/pro-irrigation-addon`
   - Click **Add**

2. **Install the Add-on**:
   - Refresh the add-on store page
   - Find "Pro-Irrigation" in the list
   - Click on it
   - Click **Install**
   - Wait for installation to complete (5-10 minutes)

3. **Configure the Add-on**:
   - Go to the **Configuration** tab
   - Set `log_level` if desired (default: `info`)
   - Click **Save**

4. **Start the Add-on**:
   - Go to the **Info** tab
   - Click **Start**
   - Wait for the add-on to start (30-60 seconds)
   - Check the **Log** tab for any errors

5. **Enable Sidebar Access**:
   - Toggle **Show in sidebar** to ON
   - The add-on will appear in your Home Assistant sidebar

### Method 2: Manual Installation (Development)

1. **Access Home Assistant File System**:
   - Via SSH, Samba share, or File Editor add-on
   - Navigate to `/addons/` directory

2. **Copy Add-on Files**:
   ```bash
   # Create directory
   mkdir -p /addons/pro-irrigation
   
   # Copy all files to this directory
   # Include: backend/, frontend/, config.yaml, Dockerfile, run.sh, etc.
   ```

3. **Restart Home Assistant**:
   - Settings → System → Restart Home Assistant
   - Wait for restart to complete

4. **Install from Local Add-ons**:
   - Navigate to **Settings** → **Add-ons** → **Add-on Store**
   - Scroll to **Local add-ons** section
   - Find "Pro-Irrigation"
   - Click **Install**

5. **Follow steps 3-5 from Method 1**

## Testing the Installation

### 1. Verify Add-on is Running

**Check Status**:
- Go to Settings → Add-ons → Pro-Irrigation
- Status should show "Running"
- Uptime should be increasing

**Check Logs**:
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
Database will be created at /data/irrigation.db
Starting FastAPI server...
============================================================
INFO:     Started server process [X]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 2. Access the Web Interface

**Via Sidebar**:
- Click "Pro-Irrigation" in the Home Assistant sidebar
- The interface should load within 2-3 seconds
- You should see the Pumps Dashboard (empty initially)

**Via Direct URL** (if Ingress fails):
- Navigate to: `http://homeassistant.local:8000`
- Note: This bypasses authentication

### 3. Test API Endpoints

**Health Check**:
```bash
curl http://homeassistant.local:8000/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2025-11-05T12:00:00Z"
}
```

**API Documentation**:
- Navigate to: `http://homeassistant.local:8000/api/docs`
- Interactive API documentation should load

### 4. Test Basic Functionality

**Create a Test Pump**:
1. Click **Add New Pump**
2. Enter name: "Test Pump"
3. Select a boolean input helper for the lock
4. Click **Create**
5. Verify the pump card appears

**Create a Test Zone**:
1. Click **Manage** on the test pump
2. Click **Add New Zone to this Pump**
3. Enter name: "Test Zone"
4. Select a switch entity
5. Choose **Manual** mode
6. Enter P1 event: `12:00.60` (noon for 60 seconds)
7. Click **Save Zone**
8. Verify the zone appears in the list

**Verify Entity Discovery**:
1. When creating a zone, click the switch entity dropdown
2. Verify your switch entities appear
3. Try searching/filtering entities

### 5. Test Scheduling (Optional)

**Manual Mode Test**:
1. Create a zone with a manual schedule for 2-3 minutes in the future
2. Wait for the scheduled time
3. Verify the switch turns on
4. Verify it turns off after the duration
5. Check the pump lock was used correctly

**Auto Mode Test** (requires global settings):
1. Configure global settings with test values
2. Create a zone in Auto mode
3. Check the "Next Run" time is calculated correctly
4. Wait for execution and verify

## Verifying Ingress Integration

### Check Ingress Configuration

1. **Verify config.yaml**:
   ```yaml
   ingress: true
   ingress_port: 8000
   panel_icon: mdi:sprinkler-variant
   panel_title: Pro-Irrigation
   ```

2. **Check Add-on Info**:
   - Go to Settings → Add-ons → Pro-Irrigation → Info
   - "Ingress" should show as "Enabled"

3. **Test Sidebar Access**:
   - Enable "Show in sidebar"
   - Click the sidebar icon
   - URL should be: `http://homeassistant.local/api/hassio_ingress/...`

### Troubleshooting Ingress

**Ingress Not Working**:
1. Restart the add-on
2. Clear browser cache
3. Try a different browser
4. Check Home Assistant logs for Ingress errors

**Sidebar Icon Not Appearing**:
1. Verify "Show in sidebar" is enabled
2. Refresh the Home Assistant page
3. Check if the icon appears after a few seconds

## Testing the Docker Build

### Local Build Test

1. **Build the Image**:
   ```bash
   ./build.sh
   ```

2. **Run Locally**:
   ```bash
   docker run -p 8000:8000 -v $(pwd)/data:/data pro-irrigation:latest
   ```

3. **Test Access**:
   - Navigate to: `http://localhost:8000`
   - Verify the interface loads

4. **Check Logs**:
   ```bash
   docker logs <container_id>
   ```

### Multi-Architecture Build

**Build for ARM64**:
```bash
./build.sh --platform linux/arm64 --tag pro-irrigation:arm64
```

**Build for ARMv7**:
```bash
./build.sh --platform linux/arm/v7 --tag pro-irrigation:armv7
```

**Build for AMD64**:
```bash
./build.sh --platform linux/amd64 --tag pro-irrigation:amd64
```

## Database Verification

### Check Database Creation

1. **Access Add-on File System**:
   - Via SSH or File Editor
   - Navigate to `/data/irrigation.db`

2. **Verify Database**:
   ```bash
   sqlite3 /data/irrigation.db ".tables"
   ```
   
   Expected output:
   ```
   global_settings  pumps  zones
   ```

3. **Check Data**:
   ```bash
   sqlite3 /data/irrigation.db "SELECT * FROM pumps;"
   ```

### Backup Database

```bash
cp /data/irrigation.db /backup/irrigation.db.backup
```

## Performance Testing

### Response Time Test

```bash
# Test API response time
time curl http://homeassistant.local:8000/api/health
```

Expected: < 200ms

### Load Test (Optional)

```bash
# Install Apache Bench
apt-get install apache2-utils

# Run load test
ab -n 1000 -c 10 http://homeassistant.local:8000/api/health
```

### Memory Usage

```bash
# Check container memory usage
docker stats <container_id>
```

Expected: < 200MB under normal operation

## Common Issues and Solutions

### Issue: Add-on Won't Start

**Check**:
1. View logs for error messages
2. Verify port 8000 is not in use
3. Check disk space availability
4. Verify Home Assistant version compatibility

**Solution**:
```bash
# Restart the add-on
# Or rebuild the add-on
# Or check system resources
```

### Issue: Database Errors

**Check**:
1. Verify `/data` directory is writable
2. Check disk space
3. Look for corruption errors in logs

**Solution**:
```bash
# Stop add-on
# Delete /data/irrigation.db
# Start add-on (will recreate database)
```

### Issue: Entities Not Discovered

**Check**:
1. Verify entities exist in Home Assistant
2. Check entity naming (must be switch.*, input_boolean.*, etc.)
3. Verify Home Assistant API is accessible

**Solution**:
- Restart Home Assistant
- Restart the add-on
- Check entity permissions

### Issue: Zones Not Executing

**Check**:
1. Verify zone is enabled
2. Check next run time is in the future
3. Verify switch entity is correct
4. Check pump lock is not stuck

**Solution**:
- Manually test the switch in Home Assistant
- Check scheduler logs
- Verify global settings (for Auto mode)

## Uninstallation

### Complete Removal

1. **Stop the Add-on**:
   - Settings → Add-ons → Pro-Irrigation
   - Click **Stop**

2. **Uninstall**:
   - Click **Uninstall**
   - Confirm the action

3. **Remove Data** (optional):
   - Via SSH: `rm -rf /data/irrigation.db`
   - This deletes all configuration

4. **Remove Repository** (optional):
   - Settings → Add-ons → Add-on Store
   - Three-dot menu → Repositories
   - Remove the repository URL

## Next Steps

After successful installation and testing:

1. **Configure Your System**:
   - Add all your pumps
   - Configure all zones
   - Set up global settings

2. **Monitor Operation**:
   - Check logs regularly
   - Verify zones execute as expected
   - Monitor pump status

3. **Optimize Settings**:
   - Adjust timing parameters
   - Fine-tune schedules
   - Enable/disable zones as needed

4. **Backup Configuration**:
   - Regularly backup `/data/irrigation.db`
   - Document your configuration

## Support

If you encounter issues:

1. Check the logs first
2. Review the troubleshooting section in README.md
3. Search existing GitHub issues
4. Create a new issue with:
   - Home Assistant version
   - Add-on version
   - Log output
   - Steps to reproduce

## Additional Resources

- **API Documentation**: http://homeassistant.local:8000/api/docs
- **GitHub Repository**: https://github.com/goatboynz/pro-irrigation-addon
- **Home Assistant Community**: https://community.home-assistant.io/
