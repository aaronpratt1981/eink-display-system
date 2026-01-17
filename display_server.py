#!/usr/bin/env python3
"""
Generic E-ink Display Server
Manages multiple displays and content plugins
"""

import time
import logging
import importlib
import schedule
from pathlib import Path
from PIL import Image
import requests
from typing import Dict, Any, Optional
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Display:
    """Represents a physical e-ink display"""
    
    def __init__(self, name: str, ip: str, port: int, width: int, height: int, 
                 tricolor: bool = False):
        self.name = name
        self.ip = ip
        self.port = port
        self.width = width
        self.height = height
        self.tricolor = tricolor
        self.last_update = None
    
    def __repr__(self):
        colors = "BWR" if self.tricolor else "BW"
        return f"Display({self.name}, {self.width}x{self.height} {colors} @ {self.ip})"


class DisplayServer:
    """
    Main display server
    Manages displays and routes content from plugins
    """
    
    def __init__(self, output_dir: Path = None):
        self.displays: Dict[str, Display] = {}
        self.plugins: Dict[str, Any] = {}
        self.output_dir = output_dir or Path(__file__).parent / "output"
        self.output_dir.mkdir(exist_ok=True)
        
        logger.info("=" * 70)
        logger.info("E-ink Display Server - Plugin Architecture")
        logger.info("=" * 70)
    
    def register_display(self, name: str, ip: str, port: int, 
                        width: int, height: int, tricolor: bool = False):
        """Register a display"""
        display = Display(name, ip, port, width, height, tricolor)
        self.displays[name] = display
        logger.info(f"Registered display: {display}")
    
    def load_plugin(self, name: str, plugin_class: str, config: Dict = None):
        """
        Load a content plugin
        
        Args:
            name: Plugin instance name
            plugin_class: Python path to plugin class (e.g., 'plugins.weather.WeatherPlugin')
            config: Plugin configuration dictionary
        """
        try:
            # Import plugin module and class
            module_path, class_name = plugin_class.rsplit('.', 1)
            module = importlib.import_module(module_path)
            plugin_cls = getattr(module, class_name)
            
            # Instantiate plugin
            plugin = plugin_cls(config or {})
            self.plugins[name] = plugin
            
            logger.info(f"Loaded plugin: {name} ({plugin.get_name()})")
            
        except Exception as e:
            logger.error(f"Failed to load plugin {name}: {e}")
            raise
    
    def generate_content(self, plugin_name: str, display_name: str) -> Optional[Image.Image]:
        """
        Generate content from plugin for specific display
        
        Args:
            plugin_name: Name of plugin to use
            display_name: Name of display (for sizing)
            
        Returns:
            PIL Image or None if failed
        """
        if plugin_name not in self.plugins:
            logger.error(f"Plugin not found: {plugin_name}")
            return None
        
        if display_name not in self.displays:
            logger.error(f"Display not found: {display_name}")
            return None
        
        plugin = self.plugins[plugin_name]
        display = self.displays[display_name]
        
        try:
            logger.info(f"[{display.name}] Generating content from {plugin_name}...")
            
            # Check if update needed
            if not plugin.should_update():
                logger.info(f"[{display.name}] Plugin says no update needed")
                return None
            
            # Generate content
            image = plugin.generate(display.width, display.height, display.tricolor)
            
            if image.size != (display.width, display.height):
                logger.warning(f"Plugin returned wrong size: {image.size}, expected {display.width}x{display.height}")
                logger.info("Resizing image...")
                image = image.resize((display.width, display.height), Image.LANCZOS)
            
            # Save for debugging
            debug_path = self.output_dir / f"{display.name}_{plugin_name}.png"
            image.save(debug_path)
            logger.info(f"[{display.name}] Saved debug image: {debug_path}")
            
            return image
            
        except Exception as e:
            logger.error(f"[{display.name}] Error generating content: {e}", exc_info=True)
            return None
    
    def convert_to_binary(self, image: Image.Image, tricolor: bool = False) -> bytes:
        """
        Convert PIL image to binary format for e-ink display
        
        Args:
            image: PIL Image (RGB mode)
            tricolor: True to generate B/W/R data, False for B/W only
            
        Returns:
            Binary data ready to send to display
        """
        width, height = image.size
        pixels = image.load()
        
        if tricolor:
            # Create two buffers: black/white + red
            black_buffer = []
            red_buffer = []
            
            for y in range(height):
                for x in range(0, width, 8):
                    black_byte = 0
                    red_byte = 0
                    
                    for bit in range(8):
                        if x + bit < width:
                            r, g, b = pixels[x + bit, y]
                            
                            # Detect red
                            is_red = (r > 150 and r > g * 1.5 and r > b * 1.5)
                            
                            # Detect black
                            is_black = (r < 60 and g < 60 and b < 60)
                            
                            if is_black:
                                black_byte |= (1 << (7 - bit))
                            elif is_red:
                                red_byte |= (1 << (7 - bit))
                    
                    black_buffer.append(black_byte)
                    red_buffer.append(red_byte)
            
            return bytes(black_buffer + red_buffer)
        
        else:
            # Black and white only
            buffer = []
            
            for y in range(height):
                for x in range(0, width, 8):
                    byte = 0
                    
                    for bit in range(8):
                        if x + bit < width:
                            r, g, b = pixels[x + bit, y]
                            
                            # Black if dark
                            is_black = (r < 60 and g < 60 and b < 60)
                            
                            if is_black:
                                byte |= (1 << (7 - bit))
                    
                    buffer.append(byte)
            
            return bytes(buffer)
    
    def send_to_display(self, display_name: str, binary_data: bytes):
        """
        Send binary data to display via HTTP
        
        Args:
            display_name: Name of display
            binary_data: Binary image data
        """
        if display_name not in self.displays:
            logger.error(f"Display not found: {display_name}")
            return False
        
        display = self.displays[display_name]
        url = f"http://{display.ip}:{display.port}/update"
        
        try:
            logger.info(f"[{display.name}] Sending {len(binary_data)} bytes to {display.ip}...")
            
            response = requests.post(
                url,
                data=binary_data,
                headers={'Content-Type': 'application/octet-stream'},
                timeout=30
            )
            
            if response.status_code == 200:
                display.last_update = datetime.now()
                logger.info(f"[{display.name}] ✓ Update successful!")
                return True
            else:
                logger.error(f"[{display.name}] HTTP {response.status_code}: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"[{display.name}] Failed to connect: {e}")
            return False
    
    def update_display(self, display_name: str, plugin_name: str):
        """
        Complete update: generate content and send to display
        
        Args:
            display_name: Name of display to update
            plugin_name: Name of plugin to use for content
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"Updating {display_name} with {plugin_name}")
        logger.info(f"{'='*70}")
        
        # Generate content
        image = self.generate_content(plugin_name, display_name)
        if not image:
            logger.error(f"[{display_name}] Failed to generate content")
            return False
        
        # Convert to binary
        display = self.displays[display_name]
        binary_data = self.convert_to_binary(image, display.tricolor)
        
        # Save binary for debugging
        binary_path = self.output_dir / f"{display_name}_{plugin_name}.bin"
        with open(binary_path, 'wb') as f:
            f.write(binary_data)
        logger.info(f"[{display.name}] Saved binary: {binary_path}")
        
        # Send to display
        success = self.send_to_display(display_name, binary_data)
        
        logger.info(f"{'='*70}\n")
        return success
    
    def schedule_update(self, display_name: str, plugin_name: str, interval: str):
        """
        Schedule regular updates
        
        Args:
            display_name: Display to update
            plugin_name: Plugin to use
            interval: Schedule string (e.g., "10 minutes", "daily at 06:00")
        """
        def update_job():
            self.update_display(display_name, plugin_name)
        
        if "minutes" in interval:
            minutes = int(interval.split()[0])
            schedule.every(minutes).minutes.do(update_job)
            logger.info(f"Scheduled {display_name} <- {plugin_name} every {minutes} minutes")
            
        elif "hours" in interval:
            hours = int(interval.split()[0])
            schedule.every(hours).hours.do(update_job)
            logger.info(f"Scheduled {display_name} <- {plugin_name} every {hours} hours")
            
        elif "daily at" in interval:
            time_str = interval.split("at")[1].strip()
            schedule.every().day.at(time_str).do(update_job)
            logger.info(f"Scheduled {display_name} <- {plugin_name} daily at {time_str}")
        
        else:
            logger.error(f"Unknown schedule format: {interval}")
    
    def run(self):
        """Run the display server (blocking)"""
        logger.info("\n" + "="*70)
        logger.info("Display Server Running")
        logger.info(f"Displays: {len(self.displays)}")
        logger.info(f"Plugins: {len(self.plugins)}")
        logger.info("="*70 + "\n")
        
        # Run initial updates
        logger.info("Running initial updates...")
        schedule.run_all()
        
        # Main loop
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("\n\nShutting down...")
            self.cleanup()
    
    def cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up plugins...")
        for name, plugin in self.plugins.items():
            try:
                plugin.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up {name}: {e}")
        
        logger.info("Shutdown complete")


if __name__ == "__main__":
    # Example usage - real config comes from config.py
    server = DisplayServer()
    
    # Register displays
    server.register_display("living_room", "192.168.1.100", 8080, 648, 480, False)
    server.register_display("kitchen", "192.168.1.121", 8080, 800, 480, True)
    
    # Load plugins (would come from config)
    # server.load_plugin("weather", "plugins.weather.WeatherPlugin", {})
    # server.load_plugin("newspaper", "plugins.newspaper.NewspaperPlugin", {})
    
    # Schedule updates (would come from config)
    # server.schedule_update("living_room", "weather", "10 minutes")
    # server.schedule_update("kitchen", "newspaper", "daily at 06:00")
    
    # Run server
    # server.run()
    
    print("Display server loaded. Import and configure from config.py")
