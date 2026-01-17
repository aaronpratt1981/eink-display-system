"""
Plugins Package
Contains all content generation plugins for e-ink displays
"""

from .base import ContentPlugin, PluginError, PluginRegistry

__all__ = ['ContentPlugin', 'PluginError', 'PluginRegistry']
