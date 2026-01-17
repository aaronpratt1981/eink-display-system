"""
Base Plugin System for E-ink Display Content
Provides abstract base class for all content plugins
"""

from abc import ABC, abstractmethod
from PIL import Image
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class ContentPlugin(ABC):
    """
    Abstract base class for content plugins
    
    All content generators should inherit from this class and implement
    the generate() method to create images for e-ink displays.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize plugin with optional configuration
        
        Args:
            config: Dictionary of plugin-specific configuration
        """
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def generate(self, width: int, height: int, tricolor: bool = False,
                 grayscale: bool = False) -> Image.Image:
        """
        Generate content image for display

        Args:
            width: Display width in pixels
            height: Display height in pixels
            tricolor: Whether display supports red color (B/W/R)
            grayscale: Whether display supports 4-level grayscale
                       (white, light gray, dark gray, black)

        Returns:
            PIL Image in RGB mode (will be converted to display format by server)

        Notes:
            - For B&W displays: use black (0,0,0) and white (255,255,255)
            - For tricolor displays: also use red (255,0,0)
            - For grayscale displays: use shades of gray for best results
              The server will quantize to 4 levels automatically.

        Raises:
            Exception: If content generation fails
        """
        pass
    
    def should_update(self) -> bool:
        """
        Check if content needs updating
        
        Override this method to implement custom update logic
        (e.g., only update if data has changed)
        
        Returns:
            True if content should be regenerated, False otherwise
        """
        return True
    
    def cleanup(self):
        """
        Cleanup resources (optional)
        
        Override this method to cleanup any resources
        (e.g., close database connections, remove temp files)
        """
        pass
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get plugin information
        
        Returns:
            Dictionary with plugin metadata
        """
        return {
            'name': self.__class__.__name__,
            'version': getattr(self, 'VERSION', '1.0.0'),
            'description': getattr(self, 'DESCRIPTION', 'No description'),
            'author': getattr(self, 'AUTHOR', 'Unknown'),
            'config': self.config
        }


class PluginError(Exception):
    """Exception raised when plugin fails to generate content"""
    pass


class PluginRegistry:
    """
    Registry for managing content plugins
    
    Handles plugin discovery, instantiation, and lifecycle
    """
    
    def __init__(self):
        self.plugins: Dict[str, ContentPlugin] = {}
        self.logger = logging.getLogger('PluginRegistry')
    
    def register(self, name: str, plugin: ContentPlugin):
        """
        Register a plugin instance
        
        Args:
            name: Unique name for the plugin
            plugin: ContentPlugin instance
        """
        if name in self.plugins:
            self.logger.warning(f"Plugin '{name}' already registered, replacing...")
        
        self.plugins[name] = plugin
        self.logger.info(f"Registered plugin: {name} ({plugin.__class__.__name__})")
    
    def unregister(self, name: str):
        """
        Unregister and cleanup a plugin
        
        Args:
            name: Plugin name to unregister
        """
        if name in self.plugins:
            self.plugins[name].cleanup()
            del self.plugins[name]
            self.logger.info(f"Unregistered plugin: {name}")
    
    def get(self, name: str) -> Optional[ContentPlugin]:
        """
        Get plugin by name
        
        Args:
            name: Plugin name
            
        Returns:
            ContentPlugin instance or None if not found
        """
        return self.plugins.get(name)
    
    def list_plugins(self) -> Dict[str, Dict[str, Any]]:
        """
        List all registered plugins with their info
        
        Returns:
            Dictionary mapping plugin names to their info
        """
        return {
            name: plugin.get_info() 
            for name, plugin in self.plugins.items()
        }
    
    def cleanup_all(self):
        """Cleanup all registered plugins"""
        for name, plugin in self.plugins.items():
            try:
                plugin.cleanup()
            except Exception as e:
                self.logger.error(f"Error cleaning up plugin '{name}': {e}")
