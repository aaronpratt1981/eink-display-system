"""
Calendar Plugin
Displays upcoming events from Google Calendar
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta
from .base import ContentPlugin


class CalendarPlugin(ContentPlugin):
    """
    Google Calendar display plugin
    
    Shows upcoming events for the next 7 days
    Can be configured with specific calendars
    
    Configuration:
        - calendar_ids: List of Google Calendar IDs
        - days_ahead: Number of days to show (default: 7)
        - max_events: Maximum events to display (default: 10)
    """
    
    def __init__(self, config=None):
        super().__init__(config)
        
        self.calendar_ids = config.get('calendar_ids', ['primary'])
        self.days_ahead = config.get('days_ahead', 7)
        self.max_events = config.get('max_events', 10)
        
        # TODO: Add Google Calendar API authentication
        # For now, this is a mock implementation
    
    def get_description(self):
        return f"Calendar events for next {self.days_ahead} days"
    
    def fetch_events(self):
        """
        Fetch events from Google Calendar
        
        TODO: Implement actual Google Calendar API integration
        For now, returns mock data
        """
        # Mock events for demonstration
        events = [
            {'date': datetime.now() + timedelta(days=0), 'time': '09:00', 'title': 'Team Meeting'},
            {'date': datetime.now() + timedelta(days=0), 'time': '14:00', 'title': 'Doctor Appointment'},
            {'date': datetime.now() + timedelta(days=1), 'time': '10:30', 'title': 'Project Review'},
            {'date': datetime.now() + timedelta(days=2), 'time': '15:00', 'title': 'Dentist'},
            {'date': datetime.now() + timedelta(days=3), 'time': '11:00', 'title': 'Lunch with Sarah'},
            {'date': datetime.now() + timedelta(days=5), 'time': '09:00', 'title': 'Flight to NYC'},
        ]
        return events[:self.max_events]
    
    def generate(self, width, height, tricolor=False, grayscale=False):
        """Generate calendar display"""
        # Create white background
        image = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(image)
        
        # Try to load fonts
        try:
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
            date_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
            event_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
        except:
            title_font = ImageFont.load_default()
            date_font = ImageFont.load_default()
            event_font = ImageFont.load_default()
        
        # Draw title
        title = f"Calendar - Next {self.days_ahead} Days"
        draw.text((20, 20), title, fill='black', font=title_font)
        
        # Draw line under title
        draw.line([(20, 70), (width - 20, 70)], fill='black', width=2)
        
        # Fetch events
        events = self.fetch_events()
        
        # Draw events
        y = 90
        last_date = None
        
        for event in events:
            event_date = event['date'].strftime('%A, %B %d')
            
            # Draw date header if new day
            if event_date != last_date:
                draw.text((20, y), event_date, fill='black', font=date_font)
                y += 35
                last_date = event_date
            
            # Draw event
            time_str = event['time']
            title_str = event['title']
            
            # Use red for today's events if tricolor
            color = 'red' if tricolor and event['date'].date() == datetime.now().date() else 'black'
            
            draw.text((40, y), f"{time_str}", fill=color, font=event_font)
            draw.text((120, y), f"{title_str}", fill=color, font=event_font)
            
            y += 30
            
            # Stop if we run out of space
            if y > height - 40:
                break
        
        # Draw footer
        footer_text = f"Updated: {datetime.now().strftime('%I:%M %p')}"
        draw.text((20, height - 30), footer_text, fill='black', font=event_font)
        
        return image


# Example configuration for config.py:
"""
plugins = {
    'calendar': {
        'class': 'plugins.calendar.CalendarPlugin',
        'config': {
            'calendar_ids': ['primary', 'family@group.calendar.google.com'],
            'days_ahead': 7,
            'max_events': 15
        }
    }
}
"""
