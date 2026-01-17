# Display Firmware Guide - All 7 Sizes

Complete guide for all Pico display firmwares with auto B&W/tri-color detection.

## 🎯 Auto-Detection Feature

**ALL firmwares automatically detect whether the server sends:**
- ✅ **B&W only** - Half the data size
- ✅ **Tri-color (BWR)** - Full data size with red channel

**You don't need different firmwares for B&W vs tri-color!**

## 📟 All 7 Display Firmwares

| Display | Resolution | File | Data Size |
|---------|------------|------|-----------|
| 7.5" B | 800 x 480 | `display_800x480.py` | 48KB (B&W) or 96KB (BWR) |
| 5.83" | 648 x 480 | `display_648x480.py` | 39KB (B&W) |
| 4.2" B | 400 x 300 | `display_400x300.py` | 15KB (B&W) or 30KB (BWR) |
| 3.7" | 480 x 280 | `display_480x280.py` | 17KB (B&W) |
| 2.9" B | 296 x 128 | `display_296x128.py` | 4.7KB (B&W) or 9.5KB (BWR) |
| 2.66" B | 296 x 152 | `display_296x152.py` | 5.6KB (B&W) or 11.2KB (BWR) |
| 2.13" B | 250 x 122 | `display_250x122.py` | 3.8KB (B&W) or 7.6KB (BWR) |

## 🔧 How Auto-Detection Works

When the server sends data, the Pico firmware:

1. **Receives data** from HTTP POST
2. **Checks size:**
   ```python
   is_bw = (len(data) == width * height / 8)        # B&W only
   is_bwr = (len(data) == width * height / 8 * 2)   # Tri-color
   ```
3. **Handles accordingly:**
   - **B&W mode:** Uses all data for black/white, writes white to red channel
   - **Tri-color mode:** Uses first half for B&W, second half for red

**Example for 800x480 display:**
- Server sends **48,000 bytes** → Pico displays B&W
- Server sends **96,000 bytes** → Pico displays tri-color
- Same firmware handles both!

## 📝 Setup Instructions

### 1. Choose Your Display Size

Pick the firmware file that matches your display resolution:
- 800x480 → `display_800x480.py`
- 648x480 → `display_648x480.py`
- etc.

### 2. Edit WiFi Settings

Open the file and update these lines:

```python
SSID = "YOUR_WIFI_SSID"          # ← Your network name
PASSWORD = "YOUR_WIFI_PASSWORD"  # ← Your password
STATIC_IP = "192.168.1.XXX"      # ← Unique IP for this display
```

**Important:** Each Pico needs a unique IP!

Suggested IPs:
- Display 1: `192.168.1.100`
- Display 2: `192.168.1.101`
- Display 3: `192.168.1.102`
- etc.

### 3. Upload to Pico

1. **Open Thonny IDE**
2. **Connect Pico** via USB
3. **Open firmware file** for your display size
4. **Save to Pico** as `main.py` (important!)
5. **Reboot** Pico (Ctrl+D or unplug/replug)

### 4. Note IP Address

Watch serial output for:
```
✓ 192.168.1.100:8080 | 800x480
```

Write this down!

### 5. Update Server Config

On Raspberry Pi, edit `config.py`:

```python
displays = {
    'kitchen': {
        'ip': '192.168.1.100',    # ← IP from step 4
        'port': 8080,
        'width': 800,              # ← Match your display
        'height': 480,
        'tricolor': True           # ← True for "B" models
    }
}
```

## 🎨 B&W vs Tri-color Configuration

### On the Server (config.py)

**For "B" model displays (can show red):**
```python
displays = {
    'kitchen': {
        'ip': '192.168.1.100',
        'tricolor': True    # ← Server will send red data
    }
}
```

**For regular displays (B&W only):**
```python
displays = {
    'living_room': {
        'ip': '192.168.1.101',
        'tricolor': False   # ← Server sends B&W only
    }
}
```

### The Pico Automatically Adapts!

- If server sends 48KB → Pico displays B&W
- If server sends 96KB → Pico displays tri-color
- **No firmware change needed!**

## ✅ Verification

Test your setup:

```bash
# From Raspberry Pi, test connection
curl http://192.168.1.100:8080

# Should see:
# Generic E-ink (800x480)
# B&W: 48000B or BWR: 96000B
# POST to /update
```

## 🔄 Switching Between B&W and Tri-color

**Want to switch from B&W to tri-color?**

1. **Edit server config.py:**
   ```python
   'tricolor': False  →  'tricolor': True
   ```

2. **Restart server:**
   ```bash
   sudo systemctl restart eink-displays
   ```

3. **Pico automatically detects and displays tri-color!**

No firmware change needed! 🎉

## 📏 Display Sizes Reference

### Large Displays (Good for Photos/Newspaper)
- **7.5" B** (800x480) - Largest, great for newspaper
- **5.83"** (648x480) - Good size for weather/dashboard

### Medium Displays (Good for Dashboards/Calendar)
- **4.2" B** (400x300) - Nice medium size
- **3.7"** (480x280) - Landscape format

### Small Displays (Good for Status/Compact Info)
- **2.9" B** (296x128) - Compact info
- **2.66" B** (296x152) - Slightly taller
- **2.13" B** (250x122) - Smallest

## 🔌 Pin Connections

**All displays use the same wiring:**

```
Display → Pico W
─────────────────
BUSY → GP13 (Pin 17)
RST  → GP12 (Pin 16)
DC   → GP8  (Pin 11)
CS   → GP9  (Pin 12)
CLK  → GP10 (Pin 14)
DIN  → GP11 (Pin 15)
GND  → GND  (Pin 38)
VCC  → 3V3  (Pin 36)  ⚠️ 3.3V ONLY!
```

## 💡 Tips

### Memory Considerations

**B&W mode uses less memory:**
- 800x480 B&W: 48KB ✅ Fits easily
- 800x480 BWR: 96KB ⚠️ Tight on Pico W

If you get memory errors on large displays, use B&W mode:
```python
'tricolor': False  # in config.py
```

### Multiple Displays

You can mix and match:
```python
displays = {
    'kitchen': {
        'ip': '192.168.1.100',
        'width': 800,
        'height': 480,
        'tricolor': True    # ← Tri-color
    },
    'living_room': {
        'ip': '192.168.1.101',
        'width': 648,
        'height': 480,
        'tricolor': False   # ← B&W only
    }
}
```

Each Pico automatically handles what it receives!

### Testing

After uploading firmware:

1. **Serial monitor** (Thonny) shows:
   - WiFi connection
   - IP address
   - Server status

2. **Test HTTP:**
   ```bash
   curl http://PICO_IP:8080
   ```

3. **Send test update** from server:
   ```bash
   python3 main.py
   ```

## 🐛 Troubleshooting

### "Invalid size" error

**Problem:** Pico receives wrong data size

**Check:**
```python
# In config.py on Pi:
'width': 800,    # Must match actual display!
'height': 480,
```

### Display shows garbage

**Possible causes:**
1. Wrong firmware for display size
2. Wrong resolution in config.py
3. Corrupted transfer

**Solution:** Re-upload correct firmware

### Memory error on Pico

**Problem:** `OUT OF MEMORY`

**Solution:** Use B&W mode instead of tri-color:
```python
'tricolor': False  # in config.py
```

### Display doesn't update

**Check:**
1. Pico IP is correct in config.py
2. Same WiFi network
3. No firewall blocking port 8080
4. Pico shows "Server running" in serial

## 📊 Feature Matrix

| Feature | All Firmwares |
|---------|---------------|
| Auto B&W detection | ✅ |
| Auto tri-color detection | ✅ |
| HTTP server | ✅ |
| Static IP | ✅ |
| Deep sleep after update | ✅ |
| Memory optimization | ✅ |
| Error handling | ✅ |
| Serial logging | ✅ |

## 🎯 Summary

✅ **One firmware per display size**
✅ **Automatically detects B&W vs tri-color**
✅ **Same wiring for all displays**
✅ **Easy to configure**
✅ **Works with any plugin**

Just pick the right size, configure WiFi, and upload! 🚀

---

**Questions?** Check SETUP.md for complete installation guide!
