"""
Screen Status Plugin for E-ink Display System
Displays status of all configured screens on the network
"""

from .base import ContentPlugin
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path


class ScreenStatusPlugin(ContentPlugin):
    """
    Plugin that displays the status of all configured e-ink displays

    Shows for each display:
    - Display name
    - Resolution and color mode
    - Online/offline status
    - Last successful update timestamp
    - Last error timestamp (if any)

    Configuration:
        server: DisplayServer instance (required)
        timeout: Seconds to wait when pinging displays (default: 3)
        title: Title shown at top (default: "Display Status")
        show_ip: Whether to show IP addresses (default: True)

    Example:
        plugins = {
            'screen_status': {
                'class': 'plugins.screen_status.ScreenStatusPlugin',
                'config': {
                    'server': server,  # Pass server instance
                    'timeout': 3,
                    'title': 'Display Status'
                }
            }
        }
    """

    VERSION = '1.0.0'
    DESCRIPTION = 'Display status dashboard for all e-ink screens'

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.server = config.get('server') if config else None
        self.timeout = config.get('timeout', 3) if config else 3
        self.title = config.get('title', 'Display Status') if config else 'Display Status'
        self.show_ip = config.get('show_ip', True) if config else True

    def get_description(self) -> str:
        return "Status dashboard showing all display states"

    def _load_font(self, size: int):
        """Load a font, falling back to default if needed"""
        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/System/Library/Fonts/Monaco.ttf",
        ]
        for path in font_paths:
            if Path(path).exists():
                try:
                    return ImageFont.truetype(path, size)
                except Exception:
                    continue
        return ImageFont.load_default()

    def _format_timestamp(self, dt: Optional[datetime]) -> str:
        """Format a datetime for display"""
        if dt is None:
            return "Never"
        if isinstance(dt, str):
            # Parse ISO format string
            try:
                dt = datetime.fromisoformat(dt)
            except ValueError:
                return dt
        return dt.strftime("%m/%d/%Y %I:%M %p")

    def _get_status_data(self) -> list:
        """Gather status data for all displays"""
        if not self.server:
            self.logger.warning("No server reference - cannot get display status")
            return []

        # Get live status (online/offline, latency)
        live_status = self.server.get_all_display_status(timeout=self.timeout)

        # Get update history (last success, last error)
        update_history = self.server.get_update_history()

        displays = []
        for name, status in live_status.items():
            history = update_history.get(name, {})

            display_info = {
                'name': name,
                'ip': status.get('ip', ''),
                'resolution': status.get('reported_resolution') or status.get('configured_resolution', ''),
                'mode': status.get('reported_mode') or status.get('configured_mode', ''),
                'online': status.get('online', False),
                'latency_ms': status.get('latency_ms'),
                'error': status.get('error'),
                'last_success': history.get('last_success'),
                'last_error': history.get('last_error'),
                'last_error_message': history.get('last_error_message'),
                'success_count': history.get('success_count', 0),
                'error_count': history.get('error_count', 0),
            }
            displays.append(display_info)

        # Sort by name
        displays.sort(key=lambda x: x['name'])
        return displays

    def generate(self, width: int, height: int, tricolor: bool = False,
                 grayscale: bool = False) -> Image.Image:
        """Generate status display image"""

        # Create white background
        image = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(image)

        # Calculate font sizes based on display size
        if width >= 600:
            title_size, name_size, detail_size = 28, 20, 16
        elif width >= 400:
            title_size, name_size, detail_size = 22, 16, 12
        else:
            title_size, name_size, detail_size = 18, 14, 10

        font_title = self._load_font(title_size)
        font_name = self._load_font(name_size)
        font_detail = self._load_font(detail_size)

        # Margins
        margin = 10
        y = margin

        # Draw title
        timestamp = datetime.now().strftime("%m/%d/%Y %I:%M %p")
        title_text = f"{self.title}"
        draw.text((margin, y), title_text, fill='black', font=font_title)

        # Draw timestamp on right
        ts_bbox = draw.textbbox((0, 0), timestamp, font=font_detail)
        ts_width = ts_bbox[2] - ts_bbox[0]
        draw.text((width - margin - ts_width, y + 5), timestamp, fill='black', font=font_detail)

        y += title_size + 10

        # Draw separator line
        draw.line([(margin, y), (width - margin, y)], fill='black', width=1)
        y += 10

        # Get display status data
        displays = self._get_status_data()

        if not displays:
            draw.text((margin, y), "No displays configured", fill='black', font=font_name)
            return image

        # Calculate space per display
        available_height = height - y - 40  # Leave room for summary
        display_height = min(available_height // len(displays), 80)

        # Draw each display
        for display in displays:
            if y + display_height > height - 40:
                # Out of space
                draw.text((margin, y), "...", fill='black', font=font_detail)
                break

            # Status indicator
            status_color = 'black' if display['online'] else ('red' if tricolor else 'black')
            indicator = "●" if display['online'] else "○"
            draw.text((margin, y), indicator, fill=status_color, font=font_name)

            # Display name and resolution/mode
            name_x = margin + 25
            mode_display = display['mode']
            if mode_display == 'BWR':
                mode_display = 'RED' if tricolor else 'BWR'

            name_text = f"{display['name']}: {display['resolution']} {mode_display}"
            draw.text((name_x, y), name_text, fill='black', font=font_name)

            # IP address (if enabled)
            if self.show_ip:
                ip_text = display['ip']
                ip_bbox = draw.textbbox((0, 0), ip_text, font=font_detail)
                ip_width = ip_bbox[2] - ip_bbox[0]
                draw.text((width - margin - ip_width, y + 2), ip_text,
                         fill='gray' if not tricolor and not grayscale else 'black',
                         font=font_detail)

            y += name_size + 4

            # Last success line
            success_text = f"Last Success: {self._format_timestamp(display['last_success'])}"
            draw.text((name_x, y), success_text, fill='black', font=font_detail)
            y += detail_size + 2

            # Last error line (if any)
            if display['last_error']:
                error_text = f"Last Error: {self._format_timestamp(display['last_error'])}"
                error_color = 'red' if tricolor else 'black'
                draw.text((name_x, y), error_text, fill=error_color, font=font_detail)
                y += detail_size + 2

            # Add spacing between displays
            y += 8

        # Draw separator before summary
        y = height - 35
        draw.line([(margin, y), (width - margin, y)], fill='black', width=1)
        y += 5

        # Summary line
        online_count = sum(1 for d in displays if d['online'])
        total_count = len(displays)
        summary = f"{total_count} configured | {online_count} online | {total_count - online_count} offline"
        draw.text((margin, y), summary, fill='black', font=font_detail)

        return image
