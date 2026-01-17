# Complete Setup Guide - Plugin-Based E-ink Display System

Detailed setup instructions for the modular plugin-based e-ink display system.

## 📋 Table of Contents

1. [Hardware Requirements](#hardware-requirements)
2. [Raspberry Pi Setup](#raspberry-pi-setup)
3. [Pico W Setup](#pico-w-setup)
4. [Configuration](#configuration)
5. [Running the System](#running-the-system)
6. [Adding Plugins](#adding-plugins)
7. [Troubleshooting](#troubleshooting)

## 🔧 Hardware Requirements

### Required Components

- **Raspberry Pi** (3B+, 4, or 5) with Raspberry Pi OS
- **1-7 Raspberry Pi Pico W** (one per display)
- **1-7 Waveshare E-ink displays** (any supported size)
- **MicroSD card** (8GB+ for Pi)
- **Power supplies** (USB-C for Pi, micro-USB for Pico W)
- **WiFi network**

### Supported Displays

| Display | Resolution | Pico Firmware |
|---------|------------|---------------|
| 7.5" B | 800 x 480 | `display_800x480.py` |
| 5.83" | 648 x 480 | `display_648x480.py` |
| 4.2" B | 400 x 300 | (create from template) |
| Others | Various | (create from template) |

## 🥧 Raspberry Pi Setup

### Step 1: Install Raspberry Pi OS

1. Download [Raspberry Pi Imager](https://www.raspberrypi.com/software/)
2. Flash **Raspberry Pi OS (64-bit)** to SD card
3. **Configure during imaging:**
   - Enable SSH
   - Set WiFi credentials
   - Set username and password
4. Insert SD card and boot Pi

### Step 2: Initial Configuration

```bash
# Connect via SSH
ssh pi@raspberrypi.local

# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install required packages
sudo apt-get install -y git python3-pip python3-venv chromium
```

### Step 3: Clone Repository

```bash
# Clone repository
cd ~
git clone https://github.com/YOUR_USERNAME/eink-display-system.git
cd eink-display-system

# Verify files
ls -la
# Should see: main.py, display_server.py, config_example.py, plugins/, pico/
```

### Step 4: Setup Python Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install pillow requests schedule selenium

# Verify installation
python3 -c "import PIL; print('✓ Pillow installed')"
python3 -c "import selenium; print('✓ Selenium installed')"
```

### Step 5: Create Configuration

```bash
# Copy example config
cp config_example.py config.py

# Edit configuration
nano config.py
```

**Example configuration:**

```python
displays = {
    'kitchen': {
        'ip': '192.168.1.121',      # Change to your Pico IP
        'port': 8080,
        'width': 800,
        'height': 480,
        'tricolor': True
    },
    'living_room': {
        'ip': '192.168.1.100',      # Change to your Pico IP
        'port': 8080,
        'width': 648,
        'height': 480,
        'tricolor': False
    }
}

plugins = {
    'weather': {
        'class': 'plugins.weather.WeatherPlugin',
        'config': {
            'html_path': 'weather-display.html'
        }
    },
    'newspaper': {
        'class': 'plugins.newspaper.NewspaperPlugin',
        'config': {}
    }
}

schedule = {
    'living_room': [
        ('weather', 'every 10 minutes')
    ],
    'kitchen': [
        ('newspaper', 'daily at 06:00')
    ]
}
```

Save and exit (Ctrl+O, Enter, Ctrl+X).

### Step 6: Test Configuration

```bash
# Test config file
python3 config.py

# Should see:
# ✓ Configuration valid
# Displays configured: ...
# Plugins loaded: ...
# Schedules: ...
```

### Step 7: Test Server (Optional)

```bash
# Run server in foreground (for testing)
python3 main.py

# Watch for:
# - Displays registered
# - Plugins loaded
# - Schedules created
# - Initial updates

# Press Ctrl+C to stop
```

### Step 8: Install as System Service

```bash
# Get your username
whoami
# Remember this for next step

# Create service file
sudo nano /etc/systemd/system/eink-displays.service
```

Paste this content (**replace YOUR_USERNAME**):

```ini
[Unit]
Description=E-ink Display Server
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/home/YOUR_USERNAME/eink-display-system
ExecStart=/home/YOUR_USERNAME/eink-display-system/venv/bin/python3 /home/YOUR_USERNAME/eink-display-system/main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Save and enable:

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service
sudo systemctl enable eink-displays

# Start service
sudo systemctl start eink-displays

# Check status
sudo systemctl status eink-displays

# View logs
sudo journalctl -u eink-displays -f
```

**Raspberry Pi setup complete!** ✅

## 📟 Pico W Setup

### Step 1: Flash MicroPython

1. **Download MicroPython** for Pico W:
   - Visit: https://micropython.org/download/RPI_PICO_W/
   - Download latest `.uf2` file

2. **Flash to Pico:**
   - Hold BOOTSEL button on Pico
   - Connect Pico to computer via USB
   - Release BOOTSEL button
   - Pico appears as USB drive
   - Copy `.uf2` file to the drive
   - Pico reboots automatically

### Step 2: Install Thonny IDE

```bash
# On your computer (not Pi)
# Download from: https://thonny.org/

# Or on Pi:
sudo apt-get install thonny
```

### Step 3: Upload Firmware

1. **Open Thonny**
2. **Connect Pico** via USB
3. **Select interpreter:** 
   - Bottom right → "MicroPython (Raspberry Pi Pico)"
4. **Open firmware file:**
   - For 800x480: Open `pico/display_800x480.py`
   - For 648x480: Open `pico/display_648x480.py`

5. **Configure WiFi:**
   ```python
   SSID = "your_network_name"      # ← Change this
   PASSWORD = "your_password"       # ← Change this
   STATIC_IP = "192.168.1.121"     # ← Change this
   ```

6. **Save to Pico:**
   - File → Save as...
   - Select "Raspberry Pi Pico"
   - Save as `main.py` (important!)

7. **Reboot Pico:** 
   - Press Ctrl+D in Thonny
   - Or unplug and replug USB

8. **Note IP address** from serial output:
   ```
   Network Configuration:
     IP Address: 192.168.1.121    ← Remember this
   ```

9. **Update `config.py` on Pi** with this IP address

### Step 4: Verify Display Works

```bash
# From Raspberry Pi, test connection
curl http://192.168.1.121:8080

# Should see:
# Generic E-ink Display (800x480)
# POST to /update
```

**Pico setup complete!** ✅

Repeat for each additional display.

## ⚙️ Configuration

### Display Configuration

Each display needs:

```python
'display_name': {
    'ip': '192.168.1.XXX',      # Pico's static IP
    'port': 8080,                # Always 8080
    'width': 800,                # Display width
    'height': 480,               # Display height
    'tricolor': True             # True for "B" models
}
```

### Plugin Configuration

Built-in plugins:

#### Weather Plugin

```python
'weather': {
    'class': 'plugins.weather.WeatherPlugin',
    'config': {
        'html_path': 'weather-display.html'  # Path to HTML template
    }
}
```

Requires `weather-display.html` file in project directory.

#### Newspaper Plugin

```python
'newspaper': {
    'class': 'plugins.newspaper.NewspaperPlugin',
    'config': {
        'url_template': 'https://.../{date}/...',
        'cache_dir': 'output/cache'
    }
}
```

Downloads newspaper from URL (default: Indianapolis Star).

#### Calendar Plugin

```python
'calendar': {
    'class': 'plugins.calendar.CalendarPlugin',
    'config': {
        'calendar_ids': ['primary'],
        'days_ahead': 7,
        'max_events': 10
    }
}
```

Currently shows mock data (Google Calendar API integration needed).

#### Photo Plugin

```python
'photos': {
    'class': 'plugins.photo.PhotoFramePlugin',
    'config': {
        'photo_dir': '/home/pi/photos',
        'mode': 'random',           # or 'sequential'
        'show_caption': True,
        'fit_mode': 'contain'       # or 'cover'
    }
}
```

Displays photos from directory.

#### Stock Ticker Plugin

```python
'stocks': {
    'class': 'plugins.stocks.StockTickerPlugin',
    'config': {
        'symbols': ['AAPL', 'GOOGL', 'MSFT', 'TSLA']
    }
}
```

Currently shows mock data (API integration needed).

### Schedule Configuration

Schedule format:

```python
schedule = {
    'display_name': [
        ('plugin_name', 'schedule_string'),
        # Can have multiple
    ]
}
```

Schedule strings:

- `'every 10 minutes'` - Every N minutes
- `'every 1 hours'` - Every N hours  
- `'daily at 06:00'` - Specific time (24-hour format)

**Examples:**

```python
# Single plugin per display
schedule = {
    'kitchen': [('newspaper', 'daily at 06:00')]
}

# Multiple plugins (content rotation)
schedule = {
    'living_room': [
        ('weather', 'every 10 minutes'),
        ('calendar', 'every 1 hours')
    ]
}

# Multiple updates per day
schedule = {
    'kitchen': [
        ('newspaper', 'daily at 06:00'),
        ('newspaper', 'daily at 18:00')
    ]
}
```

## 🚀 Running the System

### Manual Start

```bash
cd ~/eink-display-system
source venv/bin/activate
python3 main.py
```

### Service Control

```bash
# Start
sudo systemctl start eink-displays

# Stop
sudo systemctl stop eink-displays

# Restart
sudo systemctl restart eink-displays

# Status
sudo systemctl status eink-displays

# View logs
sudo journalctl -u eink-displays -f

# Disable auto-start
sudo systemctl disable eink-displays

# Enable auto-start
sudo systemctl enable eink-displays
```

### Testing Changes

```bash
# Stop service
sudo systemctl stop eink-displays

# Run manually to see output
cd ~/eink-display-system
source venv/bin/activate
python3 main.py

# When done testing, restart service
sudo systemctl start eink-displays
```

## 🔌 Adding Plugins

See **[PLUGIN_GUIDE.md](PLUGIN_GUIDE.md)** for complete guide.

**Quick example:**

```python
# plugins/hello.py
from .base import ContentPlugin
from PIL import Image, ImageDraw

class HelloPlugin(ContentPlugin):
    def generate(self, width, height, tricolor=False):
        image = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(image)
        draw.text((50, 50), "Hello World!", fill='black')
        return image
```

Add to `config.py`:

```python
plugins['hello'] = {
    'class': 'plugins.hello.HelloPlugin',
    'config': {}
}

schedule['living_room'].append(('hello', 'every 5 minutes'))
```

## 🔧 Troubleshooting

### Pi Can't Connect to Pico

```bash
# Ping test
ping 192.168.1.121

# If fails:
# 1. Check Pico serial output for IP
# 2. Verify WiFi credentials in Pico's main.py
# 3. Ensure same network
# 4. Try rebooting Pico
```

### Display Not Updating

```bash
# Check service status
sudo systemctl status eink-displays

# View logs for errors
sudo journalctl -u eink-displays -n 50

# Test Pico directly
curl http://192.168.1.121:8080
```

### Plugin Not Loading

```bash
# Check plugin exists
ls -la plugins/

# Test import
python3 -c "from plugins.weather import WeatherPlugin; print('OK')"

# Check config.py syntax
python3 config.py
```

### Image Quality Issues

Adjust brightness/contrast in plugin or use image editing before display.

### Service Won't Start

```bash
# Check service file
sudo cat /etc/systemd/system/eink-displays.service

# Verify paths match your username
# Verify venv path is correct

# Reload after changes
sudo systemctl daemon-reload
sudo systemctl restart eink-displays
```

## 📊 System Monitoring

### Check Display Updates

```bash
# View real-time logs
sudo journalctl -u eink-displays -f

# Look for:
# - "Updating [display] with [plugin]"
# - "✓ Update successful!"
```

### Debug Mode

```bash
# Stop service and run manually
sudo systemctl stop eink-displays
cd ~/eink-display-system
source venv/bin/activate
python3 main.py

# See all output in real-time
# Press Ctrl+C to stop
```

### Memory Usage

```bash
# On Raspberry Pi
free -h

# On Pico (via Thonny serial)
import gc
gc.mem_free()
```

## 📚 Next Steps

- **[Create custom plugins](PLUGIN_GUIDE.md)** - Build your own content
- **[Migrate old system](MIGRATION_GUIDE.md)** - Upgrade from unified server
- **Add more displays** - Scale to 7 displays
- **Optimize schedules** - Fine-tune update frequency
- **Share plugins** - Contribute back!

---

**Setup complete!** Your e-ink display system is ready! 🎉

Need help? Check the guides or open an issue on GitHub.
