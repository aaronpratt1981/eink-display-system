"""
Configuration File for E-ink Display Server
Define displays, plugins, and schedules here
"""

from pathlib import Path

# =============================================================================
# DISPLAY CONFIGURATION
# =============================================================================
#
# Display options:
#   - tricolor: True for B/W/Red displays (e.g., 7.5" B model)
#   - grayscale: True for 4-level grayscale displays (e.g., 2.7", 3.7", 4.2")
#   - Note: tricolor and grayscale are mutually exclusive
#   - If both are False, display receives B&W data
#   - Grayscale displays can also receive B&W data (set grayscale: False)
#

displays = {
    # Display name: configuration
    'living_room': {
        'ip': '192.168.1.100',
        'port': 8080,
        'width': 648,
        'height': 480,
        'tricolor': False,  # B&W only
        'grayscale': False
    },

    'kitchen': {
        'ip': '192.168.1.121',
        'port': 8080,
        'width': 800,
        'height': 480,
        'tricolor': True,  # Supports red (7.5" B model)
        'grayscale': False
    },

    # Example: 4-level grayscale display (3.7")
    # 'office': {
    #     'ip': '192.168.1.102',
    #     'port': 8080,
    #     'width': 480,
    #     'height': 280,
    #     'tricolor': False,
    #     'grayscale': True  # 4-level grayscale (white, light gray, dark gray, black)
    # },

    # Example: Grayscale display in B&W mode (for simpler content)
    # 'hallway': {
    #     'ip': '192.168.1.103',
    #     'port': 8080,
    #     'width': 480,
    #     'height': 280,
    #     'tricolor': False,
    #     'grayscale': False  # Send B&W to grayscale-capable display
    # },
}


# =============================================================================
# PLUGIN CONFIGURATION
# =============================================================================

plugins = {
    # Plugin name: configuration
    'weather': {
        'class': 'plugins.weather.WeatherPlugin',
        'config': {
            'html_path': 'weather-display.html'
        }
    },
    
    'newspaper': {
        'class': 'plugins.newspaper.NewspaperPlugin',
        'config': {
            'url_template': 'https://d2dr22b2lm4tvw.cloudfront.net/in_is/{date}/front-page-large.jpg',
            'cache_dir': 'output/cache'
        }
    },
    
    'calendar': {
        'class': 'plugins.calendar.CalendarPlugin',
        'config': {
            'calendar_ids': ['primary'],
            'days_ahead': 7,
            'max_events': 10
        }
    },
    
    'photos': {
        'class': 'plugins.photo.PhotoFramePlugin',
        'config': {
            'photo_dir': 'photos',
            'mode': 'random',
            'show_caption': True,
            'fit_mode': 'contain'
        }
    },
    
    'stocks': {
        'class': 'plugins.stocks.StockTickerPlugin',
        'config': {
            'symbols': ['AAPL', 'GOOGL', 'MSFT', 'TSLA']
        }
    },
}


# =============================================================================
# SCHEDULE CONFIGURATION
# =============================================================================

schedule = {
    # Display name: list of (plugin_name, schedule_string) tuples
    
    'living_room': [
        ('weather', 'every 10 minutes'),
        # Can add multiple plugins that rotate
        # ('calendar', 'every 1 hours'),
    ],
    
    'kitchen': [
        ('newspaper', 'daily at 06:00'),
        ('newspaper', 'every 6 hours'),  # Also update every 6 hours
    ],
    
    # Example: Multi-content rotation
    # 'office': [
    #     ('weather', 'every 15 minutes'),
    #     ('stocks', 'every 15 minutes'),
    #     ('calendar', 'every 1 hours'),
    # ],
}


# =============================================================================
# SERVER CONFIGURATION
# =============================================================================

server_config = {
    'output_dir': Path('output'),
    'log_level': 'INFO',
}


# =============================================================================
# HELPER FUNCTIONS (Optional)
# =============================================================================

def validate_config():
    """Validate configuration"""
    # Check all scheduled displays exist
    for display_name in schedule.keys():
        if display_name not in displays:
            raise ValueError(f"Display '{display_name}' in schedule but not defined")

    # Check all scheduled plugins exist
    for display_name, plugin_list in schedule.items():
        for plugin_name, _ in plugin_list:
            if plugin_name not in plugins:
                raise ValueError(f"Plugin '{plugin_name}' in schedule but not defined")

    # Check tricolor and grayscale are mutually exclusive
    for display_name, config in displays.items():
        if config.get('tricolor', False) and config.get('grayscale', False):
            raise ValueError(f"Display '{display_name}': tricolor and grayscale are mutually exclusive")

    print("✓ Configuration valid")
    return True


if __name__ == "__main__":
    # Test configuration
    validate_config()

    print("\nDisplays configured:")
    for name, config in displays.items():
        if config.get('tricolor', False):
            colors = "BWR"
        elif config.get('grayscale', False):
            colors = "GRAY"
        else:
            colors = "BW"
        print(f"  • {name}: {config['width']}x{config['height']} {colors} @ {config['ip']}")
    
    print("\nPlugins loaded:")
    for name, config in plugins.items():
        print(f"  • {name}: {config['class']}")
    
    print("\nSchedules:")
    for display, plugin_list in schedule.items():
        print(f"  {display}:")
        for plugin, sched in plugin_list:
            print(f"    - {plugin}: {sched}")
