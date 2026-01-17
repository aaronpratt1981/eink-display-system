# Plugin Development Guide

Complete guide to creating custom content plugins for the e-ink display system.

## 🎯 Overview

Plugins are Python classes that generate content images for displays. They're completely independent and reusable across any display size.

## 📐 Plugin Architecture

```
Your Plugin (Python class)
    ↓
Generates PIL Image (RGB)
    ↓
Display Server converts to binary
    ↓
Sends to Pico display
    ↓
Displayed on e-ink screen
```

**Key principle:** Plugins are display-agnostic. They adapt to any size!

## 🚀 Quick Start: Hello World Plugin

### Step 1: Create Plugin File

```python
# plugins/hello.py

from .base import ContentPlugin
from PIL import Image, ImageDraw, ImageFont


class HelloWorldPlugin(ContentPlugin):
    """Simple Hello World plugin"""
    
    def get_description(self):
        return "Hello World display"
    
    def generate(self, width, height, tricolor=False):
        """Generate content image"""
        # Create white background
        image = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(image)
        
        # Draw text
        text = "Hello, E-ink World!"
        
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
        except:
            font = ImageFont.load_default()
        
        # Center text
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        
        draw.text((x, y), text, fill='black', font=font)
        
        return image
```

### Step 2: Register in Config

```python
# config.py

plugins = {
    'hello': {
        'class': 'plugins.hello.HelloWorldPlugin',
        'config': {}
    }
}

schedule = {
    'living_room': [
        ('hello', 'every 5 minutes')
    ]
}
```

### Step 3: Test It

```bash
python3 main.py
```

That's it! Your plugin is live! 🎉

## 📚 Plugin API Reference

### Base Class

All plugins inherit from `ContentPlugin`:

```python
from .base import ContentPlugin

class MyPlugin(ContentPlugin):
    def __init__(self, config=None):
        super().__init__(config)
        # Your initialization
    
    def generate(self, width, height, tricolor=False):
        # Must return PIL Image (RGB mode)
        pass
    
    def get_description(self):
        # Return short description
        return "My plugin"
    
    def should_update(self):
        # Return True if content needs updating
        return True
    
    def cleanup(self):
        # Cleanup resources when plugin unloads
        pass
```

### Required Methods

#### `generate(width, height, tricolor=False) -> Image`

**Generate content image**

Parameters:
- `width` (int): Display width in pixels
- `height` (int): Display height in pixels  
- `tricolor` (bool): True if display supports red color

Returns:
- PIL Image object in RGB mode, sized exactly to width × height

Example:
```python
def generate(self, width, height, tricolor=False):
    image = Image.new('RGB', (width, height), 'white')
    # ... draw content ...
    return image
```

### Optional Methods

#### `get_description() -> str`

Return human-readable plugin description.

```python
def get_description(self):
    return "Weather forecast with current conditions"
```

#### `should_update() -> bool`

Return whether content needs regenerating. Use for caching or rate limiting.

```python
def should_update(self):
    # Only update once per day
    today = datetime.now().date()
    if self.last_update == today:
        return False
    return True
```

#### `cleanup()`

Cleanup resources when plugin is unloaded.

```python
def cleanup(self):
    if self.database:
        self.database.close()
    if self.api_client:
        self.api_client.disconnect()
```

## 🎨 Working with PIL (Pillow)

### Basic Image Creation

```python
from PIL import Image, ImageDraw, ImageFont

# Create blank image
image = Image.new('RGB', (width, height), 'white')

# Get drawing context
draw = ImageDraw.Draw(image)
```

### Drawing Text

```python
# Load font
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
except:
    font = ImageFont.load_default()

# Draw text
draw.text((x, y), "Hello", fill='black', font=font)

# Center text
bbox = draw.textbbox((0, 0), text, font=font)
text_width = bbox[2] - bbox[0]
text_height = bbox[3] - bbox[1]
x = (width - text_width) // 2
y = (height - text_height) // 2
draw.text((x, y), text, fill='black', font=font)
```

### Drawing Shapes

```python
# Rectangle
draw.rectangle([(x1, y1), (x2, y2)], fill='white', outline='black', width=2)

# Circle
draw.ellipse([(x1, y1), (x2, y2)], fill='white', outline='black')

# Line
draw.line([(x1, y1), (x2, y2)], fill='black', width=3)

# Polygon
points = [(x1, y1), (x2, y2), (x3, y3)]
draw.polygon(points, fill='white', outline='black')
```

### Loading Images

```python
# Load from file
photo = Image.open('photo.jpg')

# Resize
photo = photo.resize((400, 300), Image.LANCZOS)

# Paste onto canvas
canvas = Image.new('RGB', (width, height), 'white')
canvas.paste(photo, (x, y))
```

### Colors for E-ink

```python
# For B&W displays:
'white' or (255, 255, 255)  # White
'black' or (0, 0, 0)         # Black

# For tri-color displays (with red):
'white' or (255, 255, 255)  # White
'black' or (0, 0, 0)         # Black
'red' or (255, 0, 0)         # Red
```

## 🔧 Plugin Configuration

Pass configuration through config.py:

```python
# config.py
plugins = {
    'weather': {
        'class': 'plugins.weather.WeatherPlugin',
        'config': {
            'location': 'Indianapolis, IN',
            'units': 'imperial',
            'api_key': 'your_key_here'
        }
    }
}
```

Access in plugin:

```python
class WeatherPlugin(ContentPlugin):
    def __init__(self, config=None):
        super().__init__(config)
        
        self.location = config.get('location', 'Indianapolis, IN')
        self.units = config.get('units', 'imperial')
        self.api_key = config.get('api_key')
        
        if not self.api_key:
            raise PluginConfigError("API key required")
```

## 📦 Example Plugins

### Time & Date Display

```python
class ClockPlugin(ContentPlugin):
    def generate(self, width, height, tricolor=False):
        from datetime import datetime
        
        image = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(image)
        
        # Get current time
        now = datetime.now()
        time_str = now.strftime('%I:%M %p')
        date_str = now.strftime('%A, %B %d, %Y')
        
        # Draw time (large)
        font_large = ImageFont.truetype("arial.ttf", 120)
        bbox = draw.textbbox((0, 0), time_str, font=font_large)
        x = (width - (bbox[2] - bbox[0])) // 2
        draw.text((x, height//3), time_str, fill='black', font=font_large)
        
        # Draw date (small)
        font_small = ImageFont.truetype("arial.ttf", 32)
        bbox = draw.textbbox((0, 0), date_str, font=font_small)
        x = (width - (bbox[2] - bbox[0])) // 2
        draw.text((x, height*2//3), date_str, fill='black', font=font_small)
        
        return image
```

### Weather from API

```python
class WeatherAPIPlugin(ContentPlugin):
    def __init__(self, config):
        super().__init__(config)
        self.api_key = config['api_key']
        self.location = config.get('location', 'Indianapolis')
    
    def fetch_weather(self):
        import requests
        url = f"https://api.openweathermap.org/data/2.5/weather"
        params = {'q': self.location, 'appid': self.api_key, 'units': 'imperial'}
        response = requests.get(url, params=params)
        return response.json()
    
    def generate(self, width, height, tricolor=False):
        data = self.fetch_weather()
        
        image = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(image)
        
        # Draw weather info
        temp = data['main']['temp']
        description = data['weather'][0]['description']
        
        font = ImageFont.truetype("arial.ttf", 48)
        draw.text((50, 50), f"{temp}°F", fill='black', font=font)
        draw.text((50, 120), description.title(), fill='black', font=font)
        
        return image
```

### RSS Feed Reader

```python
class RSSFeedPlugin(ContentPlugin):
    def __init__(self, config):
        super().__init__(config)
        self.feed_url = config['feed_url']
    
    def fetch_feed(self):
        import feedparser
        return feedparser.parse(self.feed_url)
    
    def generate(self, width, height, tricolor=False):
        feed = self.fetch_feed()
        
        image = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(image)
        
        font_title = ImageFont.truetype("arial.ttf", 28)
        font_item = ImageFont.truetype("arial.ttf", 20)
        
        # Draw feed title
        draw.text((20, 20), feed.feed.title, fill='black', font=font_title)
        
        # Draw items
        y = 70
        for entry in feed.entries[:10]:
            draw.text((20, y), entry.title, fill='black', font=font_item)
            y += 35
        
        return image
```

### To-Do List

```python
class TodoPlugin(ContentPlugin):
    def __init__(self, config):
        super().__init__(config)
        self.todo_file = Path(config.get('todo_file', 'todos.txt'))
    
    def load_todos(self):
        if self.todo_file.exists():
            return self.todo_file.read_text().strip().split('\n')
        return []
    
    def generate(self, width, height, tricolor=False):
        todos = self.load_todos()
        
        image = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(image)
        
        font_title = ImageFont.truetype("arial.ttf", 36)
        font_item = ImageFont.truetype("arial.ttf", 24)
        
        # Title
        draw.text((20, 20), "To-Do List", fill='black', font=font_title)
        
        # Items
        y = 80
        for todo in todos:
            # Checkbox
            draw.rectangle([(20, y), (40, y+20)], outline='black', width=2)
            
            # Text
            color = 'red' if tricolor and '!' in todo else 'black'
            draw.text((50, y), todo, fill=color, font=font_item)
            
            y += 35
        
        return image
```

## 🧪 Testing Plugins

### Manual Test

```python
# test_plugin.py

from plugins.my_plugin import MyPlugin
from PIL import Image

# Create plugin
plugin = MyPlugin({'setting': 'value'})

# Generate for different sizes
for width, height in [(648, 480), (800, 480), (400, 300)]:
    image = plugin.generate(width, height, tricolor=True)
    image.save(f"test_{width}x{height}.png")
    print(f"✓ Generated {width}x{height}")

print("Check test_*.png files")
```

### Integration Test

```bash
# Add to config.py temporarily
python3 main.py

# Watch logs
sudo journalctl -u eink-displays -f
```

## 🎯 Best Practices

### 1. Handle Missing Data Gracefully

```python
def generate(self, width, height, tricolor=False):
    try:
        data = self.fetch_data()
    except Exception as e:
        # Show error message on display
        return self.generate_error_image(width, height, str(e))
```

### 2. Cache Expensive Operations

```python
def should_update(self):
    if self.cache_valid():
        return False
    return True

def generate(self, width, height, tricolor=False):
    if self.cached_image:
        return self.cached_image
    # ... generate ...
    self.cached_image = image
    return image
```

### 3. Make Sizes Responsive

```python
def generate(self, width, height, tricolor=False):
    # Adapt font size to display
    if width > 600:
        font_size = 48
    elif width > 400:
        font_size = 32
    else:
        font_size = 24
    
    font = ImageFont.truetype("arial.ttf", font_size)
```

### 4. Use Configuration

```python
class MyPlugin(ContentPlugin):
    def __init__(self, config):
        super().__init__(config)
        
        # Provide defaults
        self.refresh_interval = config.get('refresh_interval', 60)
        self.show_icons = config.get('show_icons', True)
        self.color_scheme = config.get('color_scheme', 'default')
```

### 5. Document Configuration

```python
class MyPlugin(ContentPlugin):
    """
    My awesome plugin
    
    Configuration:
        - api_key: Required API key
        - refresh_interval: Minutes between updates (default: 60)
        - show_icons: Show weather icons (default: True)
        - location: City name (default: "Indianapolis")
    
    Example:
        plugins = {
            'my_plugin': {
                'class': 'plugins.myplugin.MyPlugin',
                'config': {
                    'api_key': 'your_key',
                    'refresh_interval': 30,
                    'location': 'New York'
                }
            }
        }
    """
```

## 🐛 Debugging

### Enable Debug Output

```python
def generate(self, width, height, tricolor=False):
    print(f"[MyPlugin] Generating {width}x{height}")
    print(f"[MyPlugin] Config: {self.config}")
    
    # ... generate ...
    
    print(f"[MyPlugin] Generated successfully")
    return image
```

### Save Debug Images

```python
def generate(self, width, height, tricolor=False):
    image = Image.new('RGB', (width, height), 'white')
    # ... draw ...
    
    # Save for inspection
    debug_path = Path('debug') / f'{self.get_name()}_{width}x{height}.png'
    debug_path.parent.mkdir(exist_ok=True)
    image.save(debug_path)
    print(f"Debug image: {debug_path}")
    
    return image
```

### Test Without Hardware

```python
# Just generate and save images
plugin = MyPlugin({})
image = plugin.generate(800, 480)
image.save('test.png')
```

## 📚 Resources

- **PIL Documentation**: https://pillow.readthedocs.io/
- **Font Locations**: `/usr/share/fonts/truetype/`
- **Example Plugins**: See `plugins/` directory
- **Plugin Base**: See `plugins/base.py`

## 🤝 Sharing Plugins

Want to share your plugin?

1. **Document it well** - Add docstring with config options
2. **Test on multiple displays** - Try different sizes
3. **Add example config** - Show how to use it
4. **Submit PR** - Add to plugins/ directory
5. **Update README** - Add to plugin list

---

**Happy plugin development!** 🚀

Need help? Open an issue or check existing plugins for examples.
