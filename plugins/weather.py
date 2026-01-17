"""
Weather Plugin
Displays current weather conditions using HTML rendering
"""

from pathlib import Path
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from .base import ContentPlugin, PluginError


class WeatherPlugin(ContentPlugin):
    """
    Weather display plugin
    
    Renders weather-display.html using Chrome/Selenium
    Shows current conditions, temperature, and forecast
    """
    
    def __init__(self, config=None):
        super().__init__(config)
        
        # Get HTML template path
        self.html_path = Path(config.get('html_path', 'weather-display.html'))
        if not self.html_path.exists():
            raise PluginError(f"Weather HTML not found: {self.html_path}")
        
        self.driver = None
    
    def get_description(self):
        return "Current weather conditions with forecast"
    
    def setup_driver(self):
        """Setup Chrome driver for rendering"""
        if self.driver:
            return self.driver
        
        chrome_options = Options()
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        
        # Try to find chromium
        for browser_path in ['/usr/bin/chromium', '/usr/bin/chromium-browser', '/usr/bin/google-chrome']:
            if Path(browser_path).exists():
                chrome_options.binary_location = browser_path
                break
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            return self.driver
        except Exception as e:
            raise PluginError(f"Failed to setup Chrome: {e}")
    
    def generate(self, width, height, tricolor=False):
        """Generate weather display"""
        driver = self.setup_driver()
        
        # Set window size
        driver.set_window_size(width, height)
        
        # Load HTML
        driver.get(f'file://{self.html_path.absolute()}')
        
        # Wait for rendering
        import time
        time.sleep(2)
        
        # Capture screenshot
        screenshot_bytes = driver.get_screenshot_as_png()
        
        # Convert to PIL Image
        from io import BytesIO
        image = Image.open(BytesIO(screenshot_bytes))
        
        # Ensure correct size
        if image.size != (width, height):
            image = image.resize((width, height), Image.LANCZOS)
        
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        return image
    
    def cleanup(self):
        """Cleanup Chrome driver"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
