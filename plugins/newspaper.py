"""
Newspaper Plugin
Downloads and displays newspaper front page
"""

from pathlib import Path
from PIL import Image
from datetime import datetime
import requests
from .base import ContentPlugin, PluginError


class NewspaperPlugin(ContentPlugin):
    """
    Newspaper front page plugin
    
    Downloads Indianapolis Star front page and processes for display
    Automatically resizes and rotates for landscape display
    """
    
    def __init__(self, config=None):
        super().__init__(config)
        
        # URL template for newspaper
        self.url_template = config.get(
            'url_template',
            'https://d2dr22b2lm4tvw.cloudfront.net/in_is/{date}/front-page-large.jpg'
        )
        
        self.cache_dir = Path(config.get('cache_dir', 'output/cache'))
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.last_download_date = None
        self.cached_image = None
    
    def get_description(self):
        return "Indianapolis Star newspaper front page"
    
    def should_update(self):
        """Only update once per day"""
        today = datetime.now().date()
        if self.last_download_date == today and self.cached_image:
            return False
        return True
    
    def download_newspaper(self):
        """Download today's newspaper"""
        date_str = datetime.now().strftime('%Y-%m-%d')
        url = self.url_template.format(date=date_str)
        
        try:
            print(f"Downloading newspaper: {url}")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Save to cache
            cache_path = self.cache_dir / f"newspaper_{date_str}.jpg"
            with open(cache_path, 'wb') as f:
                f.write(response.content)
            
            print(f"Downloaded {len(response.content)} bytes")
            
            # Load as image
            image = Image.open(cache_path)
            self.last_download_date = datetime.now().date()
            self.cached_image = image
            
            return image
            
        except Exception as e:
            raise PluginError(f"Failed to download newspaper: {e}")
    
    def process_newspaper(self, image, target_width, target_height):
        """
        Process newspaper for display
        
        Steps:
        1. Resize to target_height pixels wide (for rotation)
        2. Crop to target_width pixels tall
        3. Rotate 90° clockwise (portrait → landscape)
        4. Result is target_width x target_height landscape
        """
        # Step 1: Resize width to match display height (will become width after rotation)
        aspect_ratio = image.height / image.width
        new_height = int(target_height * aspect_ratio)
        image_resized = image.resize((target_height, new_height), Image.LANCZOS)
        print(f"Resized to: {image_resized.size}")
        
        # Step 2: Crop to target width (will become height after rotation)
        crop_height = min(target_width, image_resized.height)
        image_cropped = image_resized.crop((0, 0, target_height, crop_height))
        print(f"Cropped to: {image_cropped.size}")
        
        # Step 3: Rotate 90° clockwise
        image_rotated = image_cropped.rotate(-90, expand=True)
        print(f"Rotated to: {image_rotated.size}")
        
        # Convert to RGB
        if image_rotated.mode != 'RGB':
            image_rotated = image_rotated.convert('RGB')
        
        return image_rotated
    
    def generate(self, width, height, tricolor=False):
        """Generate newspaper display"""
        # Download if needed
        if not self.cached_image or self.should_update():
            image = self.download_newspaper()
        else:
            print("Using cached newspaper")
            image = self.cached_image
        
        # Process for display
        processed = self.process_newspaper(image, width, height)
        
        return processed
    
    def cleanup(self):
        """Cleanup cached images"""
        self.cached_image = None
