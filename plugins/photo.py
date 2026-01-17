"""
Photo Frame Plugin
Displays photos from a directory with optional rotation
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import random
from .base import ContentPlugin, PluginError


class PhotoFramePlugin(ContentPlugin):
    """
    Digital photo frame plugin
    
    Displays photos from a directory
    Can rotate through photos or show random selection
    
    Configuration:
        - photo_dir: Path to directory containing photos
        - mode: 'sequential' or 'random' (default: sequential)
        - show_caption: Show filename as caption (default: True)
        - fit_mode: 'contain' or 'cover' (default: contain)
    """
    
    def __init__(self, config=None):
        super().__init__(config)
        
        photo_dir = config.get('photo_dir', 'photos')
        self.photo_dir = Path(photo_dir)
        
        if not self.photo_dir.exists():
            raise PluginError(f"Photo directory not found: {self.photo_dir}")
        
        self.mode = config.get('mode', 'sequential')
        self.show_caption = config.get('show_caption', True)
        self.fit_mode = config.get('fit_mode', 'contain')
        
        # Get list of image files
        self.photos = []
        for ext in ['*.jpg', '*.jpeg', '*.png', '*.gif']:
            self.photos.extend(self.photo_dir.glob(ext))
            self.photos.extend(self.photo_dir.glob(ext.upper()))
        
        if not self.photos:
            raise PluginError(f"No photos found in {self.photo_dir}")
        
        self.photos.sort()
        self.current_index = 0
        
        print(f"Loaded {len(self.photos)} photos from {self.photo_dir}")
    
    def get_description(self):
        return f"Photo frame ({len(self.photos)} photos)"
    
    def get_next_photo(self):
        """Get next photo path"""
        if self.mode == 'random':
            return random.choice(self.photos)
        else:
            photo = self.photos[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.photos)
            return photo
    
    def fit_image(self, image, width, height):
        """Fit image to display size"""
        img_width, img_height = image.size
        
        if self.fit_mode == 'cover':
            # Crop to fill entire display
            scale = max(width / img_width, height / img_height)
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            
            resized = image.resize((new_width, new_height), Image.LANCZOS)
            
            # Center crop
            left = (new_width - width) // 2
            top = (new_height - height) // 2
            return resized.crop((left, top, left + width, top + height))
        
        else:
            # Contain - fit within display with borders
            scale = min(width / img_width, height / img_height)
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            
            resized = image.resize((new_width, new_height), Image.LANCZOS)
            
            # Create white background and paste centered
            canvas = Image.new('RGB', (width, height), 'white')
            x = (width - new_width) // 2
            y = (height - new_height) // 2
            canvas.paste(resized, (x, y))
            
            return canvas
    
    def generate(self, width, height, tricolor=False):
        """Generate photo frame display"""
        # Get next photo
        photo_path = self.get_next_photo()
        print(f"Displaying: {photo_path.name}")
        
        # Load and fit image
        photo = Image.open(photo_path)
        photo = photo.convert('RGB')
        photo = self.fit_image(photo, width, height)
        
        # Add caption if enabled
        if self.show_caption:
            draw = ImageDraw.Draw(photo)
            
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
            except:
                font = ImageFont.load_default()
            
            # Draw caption background
            caption = photo_path.stem
            bbox = draw.textbbox((0, 0), caption, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # White rectangle at bottom
            padding = 10
            draw.rectangle(
                [(0, height - text_height - padding * 2), (width, height)],
                fill='white'
            )
            
            # Centered text
            x = (width - text_width) // 2
            y = height - text_height - padding
            draw.text((x, y), caption, fill='black', font=font)
        
        return photo


# Example configuration for config.py:
"""
plugins = {
    'photos': {
        'class': 'plugins.photo.PhotoFramePlugin',
        'config': {
            'photo_dir': '/home/pi/photos',
            'mode': 'random',
            'show_caption': True,
            'fit_mode': 'contain'
        }
    }
}

# Schedule to rotate every 6 hours
schedule = {
    'kitchen': [
        ('photos', 'every 6 hours')
    ]
}
"""
