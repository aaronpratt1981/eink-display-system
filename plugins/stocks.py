"""
Stock Ticker Plugin
Displays stock market information
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from .base import ContentPlugin


class StockTickerPlugin(ContentPlugin):
    """
    Stock market ticker plugin
    
    Displays real-time stock prices and changes
    Can show multiple stocks with color coding
    
    Configuration:
        - symbols: List of stock symbols to display
        - show_charts: Show mini price charts (default: False)
        - update_interval: Minutes between updates (default: 15)
    """
    
    def __init__(self, config=None):
        super().__init__(config)
        
        self.symbols = config.get('symbols', ['AAPL', 'GOOGL', 'MSFT', 'TSLA'])
        self.show_charts = config.get('show_charts', False)
        
        # TODO: Add actual stock API integration (Alpha Vantage, Yahoo Finance, etc.)
        # For now, this is a mock implementation
    
    def get_description(self):
        return f"Stock ticker ({len(self.symbols)} symbols)"
    
    def fetch_stock_data(self):
        """
        Fetch stock data from API
        
        TODO: Implement actual API integration
        For now, returns mock data
        """
        # Mock data for demonstration
        import random
        
        stocks = []
        for symbol in self.symbols:
            price = random.uniform(100, 500)
            change = random.uniform(-10, 10)
            change_pct = (change / price) * 100
            
            stocks.append({
                'symbol': symbol,
                'price': price,
                'change': change,
                'change_pct': change_pct
            })
        
        return stocks
    
    def generate(self, width, height, tricolor=False):
        """Generate stock ticker display"""
        # Create white background
        image = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(image)
        
        # Try to load fonts
        try:
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
            symbol_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
            price_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 28)
            info_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
        except:
            title_font = ImageFont.load_default()
            symbol_font = ImageFont.load_default()
            price_font = ImageFont.load_default()
            info_font = ImageFont.load_default()
        
        # Draw title
        title = "Stock Market"
        draw.text((20, 20), title, fill='black', font=title_font)
        
        # Draw timestamp
        timestamp = datetime.now().strftime('%I:%M %p')
        draw.text((width - 150, 30), timestamp, fill='black', font=info_font)
        
        # Draw line under title
        draw.line([(20, 80), (width - 20, 80)], fill='black', width=2)
        
        # Fetch stock data
        stocks = self.fetch_stock_data()
        
        # Calculate layout
        y = 110
        row_height = (height - y - 40) // len(stocks)
        
        for stock in stocks:
            symbol = stock['symbol']
            price = stock['price']
            change = stock['change']
            change_pct = stock['change_pct']
            
            # Determine color (red for losses, black/green for gains)
            if tricolor and change < 0:
                color = 'red'
            else:
                color = 'black'
            
            # Draw symbol
            draw.text((30, y), symbol, fill='black', font=symbol_font)
            
            # Draw price
            price_text = f"${price:.2f}"
            draw.text((180, y), price_text, fill='black', font=price_font)
            
            # Draw change
            change_text = f"{change:+.2f} ({change_pct:+.2f}%)"
            draw.text((350, y), change_text, fill=color, font=price_font)
            
            # Draw separator line
            if stock != stocks[-1]:
                line_y = y + row_height - 10
                draw.line([(40, line_y), (width - 40, line_y)], fill='lightgray', width=1)
            
            y += row_height
        
        # Draw footer
        footer_text = "Market data delayed 15 minutes"
        draw.text((20, height - 30), footer_text, fill='gray', font=info_font)
        
        return image


# Example configuration for config.py:
"""
plugins = {
    'stocks': {
        'class': 'plugins.stocks.StockTickerPlugin',
        'config': {
            'symbols': ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN', 'NVDA'],
            'show_charts': False
        }
    }
}

# Schedule to update every 15 minutes during market hours
schedule = {
    'office': [
        ('stocks', 'every 15 minutes')
    ]
}
"""
