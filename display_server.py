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
                 tricolor: bool = False, grayscale: bool = False):
        self.name = name
        self.ip = ip
        self.port = port
        self.width = width
        self.height = height
        self.tricolor = tricolor
        self.grayscale = grayscale
        self.last_update = None

        # Validate: tricolor and grayscale are mutually exclusive
        if tricolor and grayscale:
            raise ValueError(f"Display {name}: tricolor and grayscale are mutually exclusive")

    def __repr__(self):
        if self.tricolor:
            colors = "BWR"
        elif self.grayscale:
            colors = "GRAY"
        else:
            colors = "BW"
        return f"Display({self.name}, {self.width}x{self.height} {colors} @ {self.ip})"


class UpdateRecord:
    """Tracks update history for a display"""

    def __init__(self):
        self.last_attempt: Optional[datetime] = None
        self.last_success: Optional[datetime] = None
        self.last_error: Optional[datetime] = None
        self.last_error_message: Optional[str] = None
        self.success_count: int = 0
        self.error_count: int = 0

    def record_success(self):
        """Record a successful update"""
        now = datetime.now()
        self.last_attempt = now
        self.last_success = now
        self.success_count += 1

    def record_error(self, error_message: str):
        """Record a failed update"""
        now = datetime.now()
        self.last_attempt = now
        self.last_error = now
        self.last_error_message = error_message
        self.error_count += 1

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'last_attempt': self.last_attempt.isoformat() if self.last_attempt else None,
            'last_success': self.last_success.isoformat() if self.last_success else None,
            'last_error': self.last_error.isoformat() if self.last_error else None,
            'last_error_message': self.last_error_message,
            'success_count': self.success_count,
            'error_count': self.error_count
        }


class DisplayServer:
    """
    Main display server
    Manages displays and routes content from plugins
    """

    def __init__(self, output_dir: Path = None):
        self.displays: Dict[str, Display] = {}
        self.plugins: Dict[str, Any] = {}
        self.update_history: Dict[str, UpdateRecord] = {}
        self.output_dir = output_dir or Path(__file__).parent / "output"
        self.output_dir.mkdir(exist_ok=True)

        logger.info("=" * 70)
        logger.info("E-ink Display Server - Plugin Architecture")
        logger.info("=" * 70)
    
    def register_display(self, name: str, ip: str, port: int,
                        width: int, height: int, tricolor: bool = False,
                        grayscale: bool = False):
        """Register a display"""
        display = Display(name, ip, port, width, height, tricolor, grayscale)
        self.displays[name] = display
        self.update_history[name] = UpdateRecord()
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
            image = plugin.generate(display.width, display.height, display.tricolor,
                                    display.grayscale)
            
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

    def convert_to_grayscale(self, image: Image.Image) -> bytes:
        """
        Convert PIL image to 4-level grayscale binary format

        Args:
            image: PIL Image (RGB mode)

        Returns:
            Binary data with 2 bits per pixel (4 pixels per byte)
            Levels: 0b00=white, 0b01=light gray, 0b10=dark gray, 0b11=black
        """
        # Convert to grayscale
        gray = image.convert('L')
        width, height = gray.size
        pixels = gray.load()

        buffer = []
        for y in range(height):
            for x in range(0, width, 4):  # 4 pixels per byte
                byte = 0
                for i in range(4):
                    if x + i < width:
                        brightness = pixels[x + i, y]
                        # Map to 4 levels (2 bits)
                        if brightness > 192:
                            level = 0b00  # White
                        elif brightness > 128:
                            level = 0b01  # Light gray
                        elif brightness > 64:
                            level = 0b10  # Dark gray
                        else:
                            level = 0b11  # Black
                        byte |= (level << (6 - i * 2))
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
        history = self.update_history[display_name]
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
                history.record_success()
                logger.info(f"[{display.name}] ✓ Update successful!")
                return True
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                history.record_error(error_msg)
                logger.error(f"[{display.name}] {error_msg}")
                return False

        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            history.record_error(error_msg)
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
        
        # Convert to binary format based on display type
        display = self.displays[display_name]
        if display.grayscale:
            binary_data = self.convert_to_grayscale(image)
        else:
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

    def get_update_history(self, display_name: str = None) -> Dict:
        """
        Get update history for one or all displays

        Args:
            display_name: Optional display name. If None, returns all.

        Returns:
            Dictionary with update history
        """
        if display_name:
            if display_name in self.update_history:
                return {display_name: self.update_history[display_name].to_dict()}
            return {}
        return {name: record.to_dict() for name, record in self.update_history.items()}

    def query_display_status(self, display_name: str, timeout: float = 3.0) -> Dict:
        """
        Query a display's current status via HTTP GET

        Args:
            display_name: Name of display to query
            timeout: Connection timeout in seconds

        Returns:
            Dictionary with online status, resolution, color mode, latency
        """
        if display_name not in self.displays:
            return {'error': 'Display not found'}

        display = self.displays[display_name]
        url = f"http://{display.ip}:{display.port}/"

        result = {
            'name': display_name,
            'ip': display.ip,
            'port': display.port,
            'configured_resolution': f"{display.width}x{display.height}",
            'configured_mode': 'GRAY' if display.grayscale else ('BWR' if display.tricolor else 'BW'),
            'online': False,
            'reported_resolution': None,
            'reported_mode': None,
            'latency_ms': None,
            'error': None
        }

        try:
            import time
            start = time.time()
            response = requests.get(url, timeout=timeout)
            latency = (time.time() - start) * 1000

            if response.status_code == 200:
                result['online'] = True
                result['latency_ms'] = round(latency, 1)

                # Parse response: "EINK 800x480 BWR"
                text = response.text.strip()
                if text.startswith('EINK '):
                    parts = text.split()
                    if len(parts) >= 3:
                        result['reported_resolution'] = parts[1]
                        result['reported_mode'] = parts[2]
            else:
                result['error'] = f"HTTP {response.status_code}"

        except requests.exceptions.Timeout:
            result['error'] = "Timeout"
        except requests.exceptions.ConnectionError:
            result['error'] = "Connection refused"
        except Exception as e:
            result['error'] = str(e)

        return result

    def get_all_display_status(self, timeout: float = 3.0) -> Dict[str, Dict]:
        """
        Query status of all configured displays

        Args:
            timeout: Connection timeout per display

        Returns:
            Dictionary mapping display names to their status
        """
        return {name: self.query_display_status(name, timeout)
                for name in self.displays}

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
