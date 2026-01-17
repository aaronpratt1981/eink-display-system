# Plugin Plan: Screen Status Display

A plugin that queries all configured e-ink displays on the network and renders their status information to a single display.

**Status: IMPLEMENTED**

---

## Overview

This plugin:
1. Accesses the DisplayServer to get display configurations and update history
2. Queries each Pico's HTTP endpoint to check connectivity
3. Renders a status dashboard showing all displays with update history
4. Displays on a designated screen

---

## Implementation Summary

### Components Modified/Created

| Component | Changes |
|-----------|---------|
| `waveshare-screens/*.py` | Standardized GET response: `EINK {width}x{height} {mode}` |
| `display_server.py` | Added `UpdateRecord` class and update tracking |
| `display_server.py` | Added `query_display_status()` and `get_all_display_status()` |
| `display_server.py` | Added `get_update_history()` method |
| `plugins/screen_status.py` | New plugin file |

### Firmware GET Response Format

All firmware files now return a standardized response:
```
EINK 800x480 BWR
```

Where mode is:
- `BWR` - Tri-color (Black/White/Red)
- `GRAY` - 4-level grayscale
- `BW` - Black and white only

### Update Tracking

The server tracks for each display:
- `last_attempt` - When last update was attempted
- `last_success` - When last successful update occurred
- `last_error` - When last error occurred
- `last_error_message` - Error details
- `success_count` - Total successful updates
- `error_count` - Total failed updates

### Display Output Format

```
┌────────────────────────────────────────┐
│  Display Status          1/17 3:45 PM  │
├────────────────────────────────────────┤
│  ● kitchen: 800x480 RED   192.168.1.100│
│    Last Success: 1/17/2026 3:30 PM     │
│                                        │
│  ● office: 480x280 GRAY   192.168.1.101│
│    Last Success: 1/17/2026 3:30 PM     │
│                                        │
│  ○ bedroom: 400x300 BWR   192.168.1.102│
│    Last Success: 1/15/2026 10:00 AM    │
│    Last Error: 1/17/2026 3:30 PM       │
├────────────────────────────────────────┤
│  3 configured | 2 online | 1 offline   │
└────────────────────────────────────────┘
```

---

## Configuration

```python
# In config.py

# The server instance must be passed to the plugin
plugins = {
    'screen_status': {
        'class': 'plugins.screen_status.ScreenStatusPlugin',
        'config': {
            'server': server,       # Required: DisplayServer instance
            'timeout': 3,           # Seconds per display ping (default: 3)
            'show_ip': True,        # Show IP addresses (default: True)
            'title': 'Display Status'  # Header title
        }
    }
}

schedule = {
    'status_display': [
        ('screen_status', 'every 30 minutes')
    ]
}
```

---

## Features Implemented

- [x] Display name from config
- [x] IP address (configurable)
- [x] Online/offline status with visual indicator (●/○)
- [x] Resolution from live query or config
- [x] Color mode (BW/BWR/GRAY, shown as RED on tri-color displays)
- [x] Last successful update timestamp
- [x] Last error timestamp
- [x] Summary: total configured, online count, offline count
- [x] Timestamp of status check
- [x] Responsive layout for different screen sizes
- [x] Red highlighting for errors/offline on tri-color displays

---

## Technical Details

### How Status is Gathered

1. **Live status**: `server.get_all_display_status()` pings each display
   - Makes HTTP GET request with timeout
   - Parses `EINK {res} {mode}` response
   - Measures latency
   - Returns online/offline status

2. **Update history**: `server.get_update_history()` returns stored records
   - Timestamps for last success/error
   - Error messages
   - Counts

### Data Flow

```
Plugin.generate()
    ↓
server.get_all_display_status()  →  HTTP GET to each Pico
    ↓
server.get_update_history()      →  In-memory update records
    ↓
Combine data, render image
    ↓
Return PIL Image
```

---

## Testing Checklist

- [ ] Test with no displays configured
- [ ] Test with 1 display (online)
- [ ] Test with 1 display (offline)
- [ ] Test with multiple displays (mixed online/offline)
- [ ] Test rendering on different screen sizes (250x122 to 800x480)
- [ ] Test with slow/unresponsive display
- [ ] Verify red highlighting works on tri-color displays
- [ ] Verify grayscale rendering

---

## Future Enhancements

- Track historical uptime percentage
- Parallel display queries for faster status gathering
- Show Pico memory usage (requires firmware changes)
- Alert notifications when displays go offline
- Pagination for many displays
- Group displays by location/room
