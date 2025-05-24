# icon_helper.py - NEW FILE
"""
Icon Helper - Centralized icon management for the MP4 Looper application
"""

import os
import logging
from pathlib import Path
from paths import get_resource_path

class IconManager:
    """Manages application icons and provides easy access"""
    
    _instance = None
    _icon_path = None
    _icon_verified = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._load_icon_path()
    
    def _load_icon_path(self):
        """Load and verify the icon path once"""
        try:
            self._icon_path = get_resource_path("mp4_looper_icon.ico")
            
            # Verify the icon exists
            if os.path.exists(self._icon_path):
                self._icon_verified = True
                logging.debug(f"✅ Icon found: {self._icon_path}")
            else:
                self._icon_verified = False
                logging.warning(f"⚠️ Icon not found: {self._icon_path}")
                
        except Exception as e:
            logging.error(f"❌ Error loading icon: {e}")
            self._icon_verified = False
    
    def get_icon_path(self):
        """Get the path to the application icon"""
        return self._icon_path if self._icon_verified else None
    
    def is_icon_available(self):
        """Check if the icon is available"""
        return self._icon_verified
    
    def set_window_icon(self, window):
        """
        Set the icon for a Tkinter/CustomTkinter window
        
        Args:
            window: The window object (Tk, CTk, Toplevel, etc.)
            
        Returns:
            bool: True if icon was set successfully, False otherwise
        """
        if not self._icon_verified:
            logging.debug("Icon not available, skipping icon setting")
            return False
        
        try:
            window.iconbitmap(default=self._icon_path)
            logging.debug(f"✅ Icon set for window: {window.__class__.__name__}")
            return True
            
        except Exception as e:
            logging.debug(f"⚠️ Failed to set icon for {window.__class__.__name__}: {e}")
            return False


# Global instance
_icon_manager = None

def get_icon_manager():
    """Get the global icon manager instance"""
    global _icon_manager
    if _icon_manager is None:
        _icon_manager = IconManager()
    return _icon_manager

# Convenience functions for easy use
def get_app_icon_path():
    """Get the application icon path"""
    return get_icon_manager().get_icon_path()

def set_window_icon(window):
    """
    Set the MP4 Looper icon for any window
    
    Args:
        window: Tkinter/CustomTkinter window object
        
    Returns:
        bool: True if successful, False otherwise
        
    Example:
        import tkinter as tk
        from icon_helper import set_window_icon
        
        root = tk.Tk()
        set_window_icon(root)  # That's it!
    """
    return get_icon_manager().set_window_icon(window)

def is_icon_available():
    """Check if the application icon is available"""
    return get_icon_manager().is_icon_available()


# USAGE EXAMPLES:

# BEFORE (repeated in multiple files):
# try:
#     icon_path = get_resource_path("mp4_looper_icon.ico")
#     self.iconbitmap(default=icon_path)
#     logging.debug(f"Set auth dialog icon: {icon_path}")
# except Exception as e:
#     logging.debug(f"Could not set auth dialog icon: {e}")

# AFTER (one simple line):
# from icon_helper import set_window_icon
# set_window_icon(self)  # Done!