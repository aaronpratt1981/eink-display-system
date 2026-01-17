# E-ink Display System - Plugin Architecture

Modular e-ink display system with plugin-based content generation. Display weather, news, calendars, photos, stocks, or create your own content plugins!

![Project Status](https://img.shields.io/badge/status-active-success.svg)
![Architecture](https://img.shields.io/badge/architecture-plugin--based-brightgreen.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## 🎯 Key Features

- **🔌 Plugin Architecture**: Add new content types without touching core code
- **📺 Any Content, Any Display**: Weather on kitchen display, calendar on office display
- **🔄 Content Rotation**: Multiple plugins on same display
- **🎨 7 Display Sizes**: 2.13" to 7.5" Waveshare screens supported
- **🔴 Tri-color Support**: Black/White/Red on Waveshare "B" displays
- **⚙️ Simple Configuration**: Everything in `config.py`
- **🚀 Community Plugins**: Easy to create and share

## 📐 Architecture

```
Display Server (main.py)
    ↓
Configuration (config.py)
    ↓
Plugins (plugins/)
    ├─ weather.py      → Weather data
    ├─ newspaper.py    → News front page
    ├─ calendar.py     → Google Calendar
    ├─ photo.py        → Photo frame
    ├─ stocks.py       → Stock ticker
    └─ your_plugin.py  → Your custom content!
    ↓
Generic Display (Pico 2 W)
    ↓
E-ink Screen (Waveshare)
```

## 🚀 Quick Start

### 1. Install on Your Raspberry Pi

```bash
git clone https://github.com/aaronpratt1981/eink-display-system.git
cd eink-display-system

python3 -m venv venv
source venv/bin/activate
pip install pillow requests schedule selenium

sudo apt-get install chromium  # For weather plugin
```

### 2. Configure

```bash
cp config_example.py config.py
nano config.py
```

**Define your displays:**
```python
displays = {
    'kitchen': {
        'ip': '192.168.1.100',
        'port': 8080,
        'width': 800,
        'height': 480,
        'tricolor': True  # If using red and not just black and white
    }
}
```

**Choose plugins:**
```python
plugins = {
    'newspaper': {
        'class': 'plugins.newspaper.NewspaperPlugin',
        'config': {}
    }
}
```

**Schedule updates:**
```python
schedule = {
    'kitchen': [
        ('newspaper', 'daily at 06:00')
    ]
}
```

### 3. Setup Pico Display

1. Flash MicroPython to Pico W
2. Upload `pico/display_800x480.py` or a file for another sized screen as `main.py`
3. Edit WiFi credentials in `main.py`
4. Reboot and note IP address

### 4. Run

```bash
python3 main.py
```

Done! Your display will update automatically. 🎉

## 📦 Available Plugins

| Plugin | Description | Config |
|--------|-------------|--------|
| **weather** | Current weather + forecast | `html_path` |
| **newspaper** | Daily newspaper front page | `url_template`, `cache_dir` |
| **calendar** | Google Calendar events | `calendar_ids`, `days_ahead` |
| **photo** | Photo frame with rotation | `photo_dir`, `mode` |
| **stocks** | Stock market ticker | `symbols` |

## 🔌 Creating Plugins

Create a plugin in 3 steps:

### 1. Create Plugin File

```python
# plugins/hello.py
from plugin_base import ContentPlugin
from PIL import Image, ImageDraw

class HelloWorldPlugin(ContentPlugin):
    def generate(self, width, height, tricolor=False):
        image = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(image)
        draw.text((50, 50), "Hello World!", fill='black')
        return image
```

### 2. Register in Config

```python
# config.py
plugins = {
    'hello': {
        'class': 'plugins.hello.HelloWorldPlugin',
        'config': {}
    }
}
```

### 3. Schedule It

```python
schedule = {
    'living_room': [('hello', 'every 5 minutes')]
}
```

**See [PLUGIN_GUIDE.md](PLUGIN_GUIDE.md) for complete documentation!**

## 🎨 Supported Displays

| Display | Resolution | Colors | Size | Best For |
|---------|------------|--------|------|----------|
| 7.5" B | 800 x 480 | ⚫⚪🔴 | 96KB* | Newspaper, Photos |
| 5.83" | 648 x 480 | ⚫⚪ | 39KB | Weather, Dashboard |
| 4.2" B | 400 x 300 | ⚫⚪🔴 | 30KB* | Calendar, Tasks |
| 3.7" | 480 x 280 | ⚫⚪ | 17KB | Status Board |
| 2.9" B | 296 x 128 | ⚫⚪🔴 | 9.5KB* | Compact Info |
| 2.66" B | 296 x 152 | ⚫⚪🔴 | 11KB* | Mini Display |
| 2.13" B | 250 x 122 | ⚫⚪🔴 | 7.8KB* | Tiny Status |

\* Tri-color (BWR) data size. B&W only is half.

## 💡 Example Use Cases

### Home Dashboard
```python
displays = {
    'kitchen': {
        'ip': '192.168.1.100',
        'width': 800,
        'height': 480,
        'tricolor': True
    },
    'bedroom': {
        'ip': '192.168.1.101',
        'width': 648,
        'height': 480,
        'tricolor': False
    }
}

schedule = {
    'kitchen': [
        ('newspaper', 'daily at 06:00'),
        ('calendar', 'every 1 hours')
    ],
    'bedroom': [
        ('weather', 'every 10 minutes'),
        ('photos', 'every 6 hours')
    ]
}
```

### Office Setup
```python
schedule = {
    'office': [
        ('weather', 'every 15 minutes'),
        ('stocks', 'every 15 minutes'),
        ('calendar', 'every 1 hours')
    ]
}
```

### Content Rotation
Multiple plugins on one display, alternating:

```python
schedule = {
    'living_room': [
        ('weather', 'every 10 minutes'),   # Updates 6x/hour
        ('calendar', 'every 1 hours'),     # Updates 1x/hour
        ('photos', 'every 6 hours')        # Updates 4x/day
    ]
}
```

## 🔧 Configuration Reference

### Display Configuration

```python
displays = {
    'display_name': {
        'ip': '192.168.1.XXX',      # Pico W IP address
        'port': 8080,                # Always 8080
        'width': 800,                # Display width in pixels
        'height': 480,               # Display height in pixels
        'tricolor': False            # True for "B" models with red
    }
}
```

### Plugin Configuration

```python
plugins = {
    'plugin_name': {
        'class': 'plugins.module.ClassName',
        'config': {
            'setting1': 'value1',
            'setting2': 'value2'
        }
    }
}
```

### Schedule Configuration

```python
schedule = {
    'display_name': [
        ('plugin_name', 'every 10 minutes'),
        ('plugin_name', 'every 1 hours'),
        ('plugin_name', 'daily at 06:00')
    ]
}
```

## 📚 Documentation

- **[PLUGIN_GUIDE.md](PLUGIN_GUIDE.md)** - Complete plugin development guide
- **[SETUP.md](docs/SETUP.md)** - Detailed installation guide
- **[DISPLAYS.md](docs/DISPLAYS.md)** - All display models


## 🐛 Troubleshooting

### Plugin not loading

```bash
# Check plugin file exists
ls -la plugins/

# Check class name matches
grep "class.*Plugin" plugins/your_plugin.py

# Test import
python3 -c "from plugins.your_plugin import YourPlugin"
```

### Display not updating

```bash
# Test Pico connectivity
ping 192.168.1.XXX
curl http://192.168.1.XXX:8080

# Check logs
python3 main.py  # Run in foreground
```

### Wrong image size

Plugins auto-adapt, but verify:
```python
def generate(self, width, height, tricolor=False):
    image = Image.new('RGB', (width, height), 'white')
    # width and height are passed correctly
    # Always return image sized exactly to width x height
```

## 🤝 Contributing

We love plugins! Share yours:

1. Create your plugin in `plugins/`
2. Document configuration in plugin docstring
3. Test on multiple display sizes
4. Submit PR with example config
5. Add to README

### Plugin Ideas

- 📊 System monitoring (CPU, memory, network)
- 🌡️ Home Assistant integration
- 📧 Email inbox summary
- 📝 Notion/Todoist integration
- 🎮 Game scores (ESPN API)
- 🚆 Transit times
- 🎵 Currently playing (Spotify)
- 📈 Crypto prices
- 🌙 Astronomy (moon phase, ISS)
- 🍕 Recipe of the day

## 📄 License

MIT License - see [LICENSE](LICENSE)

## 🙏 Acknowledgments

- [Waveshare](https://www.waveshare.com/) - E-paper displays
- [MicroPython](https://micropython.org/) - Pico firmware
- [Pillow](https://python-pillow.org/) - Image processing
- Community contributors!

## 🌟 Show Your Support

- ⭐ Star this repo
- 📸 Share your setup
- 🔌 Create plugins
- 🐛 Report bugs
- 💡 Suggest features

---

**Built with ❤️ for the e-ink community**

[Create an issue](https://github.com/aaronpratt1981/eink-display-system/issues) • [Plugin guide](PLUGIN_GUIDE.md)