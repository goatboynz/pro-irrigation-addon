# Quick Start Guide

Get up and running with Pro-Irrigation v2 in 5 minutes!

## Installation (2 minutes)

1. **Add Repository**
   - Settings → Add-ons → Add-on Store → ⋮ → Repositories
   - Add: `https://github.com/goatboynz/pro-irrigation-addon`

2. **Install Add-on**
   - Find "Pro-Irrigation v2" in store
   - Click Install → Start
   - Enable "Show in sidebar"

## Setup (3 minutes)

### Step 1: Create Pump Lock Entity

Add to your `configuration.yaml`:

```yaml
input_boolean:
  pump_1_lock:
    name: Pump 1 Lock
    icon: mdi:lock
```

Restart Home Assistant.

### Step 2: Create Your First Room

1. Open Pro-Irrigation from sidebar
2. Click **Add Room**
3. Enter name: "My Room"
4. Click **Save**

### Step 3: Add a Pump

1. Click on your room
2. Click **Add Pump**
3. Name: "Main Pump"
4. Lock Entity: `input_boolean.pump_1_lock`
5. Click **Save**

### Step 4: Add a Zone

1. Click **Manage** on your pump
2. Click **Add Zone**
3. Name: "Zone 1"
4. Switch Entity: Select your zone switch
5. Click **Save**

### Step 5: Create Water Event

1. Go back to room view
2. Click **Add Event**
3. Type: P2
4. Name: "Test Water"
5. Time: 14:00
6. Run Time: 60 seconds
7. Select your zone
8. Click **Save**

## Test It!

### Manual Test

1. Go to room detail
2. Find your zone
3. Click **Run Manually**
4. Enter duration: 10 seconds
5. Click **Run**
6. Watch your zone activate!

### Scheduled Test

Wait until 14:00 (or change the time to now + 2 minutes) and watch it run automatically!

## What's Next?

- Add more zones
- Create P1 events (after lights on)
- Add environmental sensors
- Configure system settings
- Set up multiple rooms

## Need Help?

- Full docs: See README.md
- Installation: See INSTALL.md
- Issues: https://github.com/goatboynz/pro-irrigation-addon/issues

## Common Commands

**View Logs:**
Settings → Add-ons → Pro-Irrigation v2 → Log

**Restart Add-on:**
Settings → Add-ons → Pro-Irrigation v2 → Restart

**Update Add-on:**
Settings → Add-ons → Pro-Irrigation v2 → Update (when available)

## Tips

- Start with one room and expand
- Test manual control before scheduling
- Use descriptive names for zones
- Check logs if something doesn't work
- Enable rooms/pumps/zones after configuration

## Troubleshooting

**Zone won't run?**
- Check room is enabled
- Check event is enabled
- Check zone is assigned to event
- Verify switch entity exists

**Can't see entities?**
- Restart Home Assistant
- Check entity IDs are correct
- Verify entities exist in Developer Tools

**Frontend won't load?**
- Clear browser cache
- Check add-on logs
- Restart add-on

---

That's it! You're ready to automate your irrigation. 🌱
