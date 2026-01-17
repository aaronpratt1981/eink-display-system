"""
Configuration File for E-ink Display Server
Define displays, plugins, and schedules here
"""

from pathlib import Path

# =============================================================================
# DISPLAY CONFIGURATION
# =============================================================================

displays = {
    # Display name: configuration
    'living_room': {
        'ip': '192.168.1.100',
        'port': 8080,
        'width': 648,
        'height': 480,
        'tricolor': False  # B&W only
    },
    
    'kitchen': {
        'ip': '192.168.1.121',
        'port': 8080,
        'width': 800,
        'height': 480,
        'tricolor': True  # Supports red (7.5" B model)
    },
    
    # Add more displays as needed
    # 'office': {
    #     'ip': '192.168.1.102',
    #     'port': 8080,
    #     'width': 400,
    #     'height': 300,
    #     'tricolor': True
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
    
    print("✓ Configuration valid")
    return True


if __name__ == "__main__":
    # Test configuration
    validate_config()
    
    print("\nDisplays configured:")
    for name, config in displays.items():
        colors = "BWR" if config['tricolor'] else "BW"
        print(f"  • {name}: {config['width']}x{config['height']} {colors} @ {config['ip']}")
    
    print("\nPlugins loaded:")
    for name, config in plugins.items():
        print(f"  • {name}: {config['class']}")
    
    print("\nSchedules:")
    for display, plugin_list in schedule.items():
        print(f"  {display}:")
        for plugin, sched in plugin_list:
            print(f"    - {plugin}: {sched}")
