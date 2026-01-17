#!/usr/bin/env python3
"""
Main Entry Point for E-ink Display Server
Loads configuration and starts the server
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from display_server import DisplayServer
import logging

logger = logging.getLogger(__name__)


def main():
    """Main entry point"""
    
    # Load configuration
    try:
        import config
        config.validate_config()
    except ImportError:
        logger.error("config.py not found! Copy config_example.py to config.py and customize it.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    
    # Create server
    server = DisplayServer(output_dir=config.server_config.get('output_dir'))
    
    # Register displays
    logger.info("\nRegistering displays...")
    for name, display_config in config.displays.items():
        server.register_display(
            name,
            display_config['ip'],
            display_config['port'],
            display_config['width'],
            display_config['height'],
            display_config.get('tricolor', False)
        )
    
    # Load plugins
    logger.info("\nLoading plugins...")
    for name, plugin_config in config.plugins.items():
        server.load_plugin(
            name,
            plugin_config['class'],
            plugin_config.get('config', {})
        )
    
    # Schedule updates
    logger.info("\nScheduling updates...")
    for display_name, plugin_schedules in config.schedule.items():
        for plugin_name, schedule_str in plugin_schedules:
            server.schedule_update(display_name, plugin_name, schedule_str)
    
    # Run server
    logger.info("\nStarting server...")
    server.run()


if __name__ == "__main__":
    main()
