# Installation Guide

This guide will help you install Pro-Irrigation v2 as a Home Assistant add-on.

## Prerequisites

- Home Assistant OS or Supervised installation
- Home Assistant version 2023.1 or later
- Switch entities for zone control
- Input boolean entities for pump locks

## Installation Methods

### Method 1: Add Repository to Home Assistant (Recommended)

1. **Add the Repository**
   - Open Home Assistant
   - Navigate to **Settings** → **Add-ons** → **Add-on Store**
   - Click the **⋮** (three dots) in the top right corner
   - Select **Repositories**
   - Add this URL:
     ```
     https://github.com/goatboynz/pro-irrigation-addon
     ```
   - Click **Add**

2. **Install the Add-on**
   - Refresh the Add-on Store page
   - Find "Pro-Irrigation v2" in the list
   - Click on it
   - Click **Install**
   - Wait for the installation to complete (this may take several minutes)

3. **Configure the Add-on**
   - After installation, go to the **Configuration** tab
   - Set your preferred log level (default: info)
   - Click **Save**

4. **Start the Add-on**
   - Go to the **Info** tab
   - Click **Start**
   - Wait for the add-on to start (check the logs for "Startup complete")

5. **Enable in Sidebar**
   - Toggle **Show in sidebar** to ON
   - The add-on will now appear in your Home Assistant sidebar

6. **Access the Interface**
   - Click on "Pro-Irrigation" in the sidebar
   - You should see the dashboard

### Method 2: Manual Installation (Advanced)

If you want to install from a local copy:

1. **Clone the Repository**
   ```bash
   cd /addons
   git clone https://github.com/goatboynz/pro-irrigation-addon.git
   ```

2. **Follow steps 2-6 from Method 1**

## Initial Setup

After installation, you need to configure your irrigation system:

### 1. Create Required Home Assistant Entities

Before using the add-on, create these entities in Home Assistant:

**Pump Lock Entities** (one per pump):
```yaml
# configuration.yaml
input_boolean:
  pump_1_lock:
    name: Pump 1 Lock
    icon: mdi:lock
  pump_2_lock:
    name: Pump 2 Lock
    icon: mdi:lock
```

**Lights Schedule Entities** (optional, for P1 events):
```yaml
input_datetime:
  lights_on:
    name: Lights On Time
    has_date: false
    has_time: true
  lights_off:
    name: Lights Off Time
    has_date: false
    has_time: true
```

Restart Home Assistant after adding these entities.

### 2. Configure Your First Room

1. Open Pro-Irrigation from the sidebar
2. Click **Add Room**
3. Fill in the details:
   - **Name**: e.g., "Flower Room 1"
   - **Lights On Entity**: Select your lights-on entity (optional)
   - **Lights Off Entity**: Select your lights-off entity (optional)
   - **Enabled**: Toggle ON
4. Click **Save**

### 3. Add a Pump

1. Click on your room to view details
2. In the Pumps section, click **Add Pump**
3. Fill in the details:
   - **Name**: e.g., "Main Pump"
   - **Lock Entity**: Select the input_boolean for this pump
   - **Enabled**: Toggle ON
4. Click **Save**

### 4. Add Zones

1. Click **Manage** on your pump
2. Click **Add Zone**
3. Fill in the details:
   - **Name**: e.g., "Front Left"
   - **Switch Entity**: Select the switch that controls this zone
   - **Enabled**: Toggle ON
4. Click **Save**
5. Repeat for all zones on this pump

### 5. Configure Water Events

1. Go back to the room detail view
2. In the Water Events section, click **Add Event**
3. For a P1 event (after lights on):
   - **Type**: P1
   - **Name**: e.g., "Morning Water"
   - **Delay (minutes)**: e.g., 30 (runs 30 minutes after lights turn on)
   - **Run Time (seconds)**: e.g., 82 (1 minute 22 seconds)
   - **Zones**: Select which zones should run
   - **Enabled**: Toggle ON
4. For a P2 event (specific time):
   - **Type**: P2
   - **Name**: e.g., "Afternoon Water"
   - **Time of Day**: e.g., 14:00
   - **Run Time (seconds)**: e.g., 82
   - **Zones**: Select which zones should run
   - **Enabled**: Toggle ON
5. Click **Save**

### 6. Add Sensors (Optional)

1. In the room detail view, go to the Sensors section
2. Click **Add Sensor**
3. Fill in the details:
   - **Sensor Entity**: Select your sensor (e.g., soil moisture)
   - **Display Name**: e.g., "Soil Moisture - Front"
   - **Sensor Type**: e.g., "moisture"
   - **Unit**: e.g., "%"
   - **Enabled**: Toggle ON
4. Click **Save**

## Verification

To verify everything is working:

1. **Check the Dashboard**: You should see your room with pump status
2. **Check Room Detail**: Click on your room to see all configured entities
3. **Test Manual Control**: Try running a zone manually to verify connectivity
4. **Check Logs**: Go to Settings → Add-ons → Pro-Irrigation v2 → Log tab

## Troubleshooting

### Add-on Won't Start

1. Check the logs for error messages
2. Verify the /data directory is writable
3. Ensure no port conflicts on port 8000

### Can't See Entities

1. Verify entities exist in Home Assistant
2. Check entity IDs are spelled correctly
3. Restart Home Assistant if entities were just created

### Zones Not Running

1. Verify the room is enabled
2. Check that water events are enabled
3. Ensure zones are assigned to events
4. Verify switch entities are accessible
5. Check scheduler logs

### Frontend Not Loading

1. Clear browser cache
2. Try a different browser
3. Check add-on logs for errors
4. Verify Ingress is enabled

## Updating

To update to a new version:

1. Go to Settings → Add-ons → Pro-Irrigation v2
2. If an update is available, you'll see an **Update** button
3. Click **Update**
4. Wait for the update to complete
5. Restart the add-on

## Uninstalling

To remove the add-on:

1. Go to Settings → Add-ons → Pro-Irrigation v2
2. Click **Uninstall**
3. Confirm the uninstallation

Note: This will delete all configuration data. Export any important data first.

## Support

- **GitHub Issues**: https://github.com/goatboynz/pro-irrigation-addon/issues
- **Discussions**: https://github.com/goatboynz/pro-irrigation-addon/discussions
- **Documentation**: See README.md

## Next Steps

- Configure system settings (pump delays, scheduler interval)
- Set up environmental monitoring
- Create backup schedules
- Explore manual control features
