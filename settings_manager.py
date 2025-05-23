# settings_manager.py - FIXED VERSION
import os
import sys
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

class SettingsManager:
    """Centralized settings management for MP4 Looper - FIXED VERSION"""
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern - only one settings manager"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # Initialize attributes here to avoid __init__ issues
            cls._instance._initialized = False
            cls._instance.settings = {}  # FIX: Initialize settings here
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.settings_file = self._get_settings_file_path()
            self.settings = self._load_settings()  # This will now work
            self._initialized = True
            logging.debug(f"Settings manager initialized: {self.settings_file}")
    
    def _get_settings_file_path(self) -> Path:
        """Get the settings file path based on whether we're running as exe or script"""
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            app_dir = Path(sys.executable).parent
        else:
            # Running as script - get the directory of THIS file
            app_dir = Path(__file__).parent
        
        return app_dir / "looper_settings.json"
    
    def _get_default_settings(self) -> Dict[str, Any]:
        """Default settings structure"""
        return {
            "version": "1.1.0",
            "created": "2025-05-22",
            
            # UI Settings
            "ui": {
                "output_folder": str(Path.cwd()),
                "music_folder": "",
                "loop_duration": "3600",  # 1 hour default
                "window_geometry": "900x900",
                "window_position": None
            },
            
            # Google Sheets Settings  
            "sheets": {
                "sheet_url": "",
                "sheet_preset": "Reggae",
                "auto_validate": True
            },
            
            # Processing Settings
            "processing": {
                "use_default_song_count": True,
                "default_song_count": "5",
                "fade_audio": True,
                "export_timestamp": True,
                "auto_upload": False,
                "hardware_acceleration": True
            },
            
            # Advanced Settings
            "advanced": {
                "debug_logging": False,
                "auto_cleanup": True,
                "backup_settings": True,
                "check_updates": True
            }
        }
    
    def _load_settings(self) -> Dict[str, Any]:
        """Load settings from file or create defaults"""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                
                # Merge with defaults to ensure all keys exist
                default_settings = self._get_default_settings()
                merged_settings = self._deep_merge(default_settings, loaded_settings)
                
                logging.info(f"Settings loaded from: {self.settings_file}")
                return merged_settings
                
            except Exception as e:
                logging.error(f"Error loading settings: {e}")
                logging.info("Using default settings")
                return self._get_default_settings()
        else:
            # Create new settings file
            default_settings = self._get_default_settings()
            self._save_settings(default_settings)
            logging.info(f"Created new settings file: {self.settings_file}")
            return default_settings
    
    def _deep_merge(self, default: Dict, loaded: Dict) -> Dict:
        """Deep merge loaded settings with defaults"""
        result = default.copy()
        
        for key, value in loaded.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _save_settings(self, settings: Optional[Dict] = None):
        """Save settings to file"""
        if settings is None:
            settings = self.settings
        
        try:
            # Create backup if enabled
            if self.get("advanced.backup_settings", True) and self.settings_file.exists():
                backup_file = self.settings_file.with_suffix('.json.backup')
                import shutil
                shutil.copy2(self.settings_file, backup_file)
            
            # Save settings
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            
            logging.debug(f"Settings saved to: {self.settings_file}")
            
        except Exception as e:
            logging.error(f"Error saving settings: {e}")
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """Get setting value using dot notation"""
        keys = key_path.split('.')
        value = self.settings
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any, save: bool = True):
        """Set setting value using dot notation"""
        keys = key_path.split('.')
        settings_ref = self.settings
        
        # Navigate to parent key
        for key in keys[:-1]:
            if key not in settings_ref:
                settings_ref[key] = {}
            settings_ref = settings_ref[key]
        
        # Set the value
        settings_ref[keys[-1]] = value
        
        if save:
            self._save_settings()
        
        logging.debug(f"Setting updated: {key_path} = {value}")
    
    def update_section(self, section: str, updates: Dict[str, Any], save: bool = True):
        """Update multiple settings in a section"""
        if section not in self.settings:
            self.settings[section] = {}
        
        self.settings[section].update(updates)
        
        if save:
            self._save_settings()
        
        logging.debug(f"Section '{section}' updated with {len(updates)} settings")
    
    def get_ui_settings(self) -> Dict[str, Any]:
        """Get all UI-related settings"""
        return self.settings.get('ui', {})
    
    def get_processing_settings(self) -> Dict[str, Any]:
        """Get all processing-related settings"""
        return self.settings.get('processing', {})
    
    def get_sheets_settings(self) -> Dict[str, Any]:
        """Get all Google Sheets-related settings"""
        return self.settings.get('sheets', {})
    
    def get_all_settings(self) -> Dict[str, Any]:
        """Get a copy of all settings"""
        return self.settings.copy()
    
    def validate_settings(self) -> bool:
        """Validate current settings structure"""
        try:
            # Check required top-level sections
            required_sections = ['ui', 'sheets', 'processing', 'advanced']
            
            for section in required_sections:
                if section not in self.settings:
                    logging.warning(f"Missing section: {section}")
                    return False
            
            return True
            
        except Exception as e:
            logging.error(f"Settings validation error: {e}")
            return False


# Global settings instance
_settings_manager = None

def get_settings() -> SettingsManager:
    """Get the global settings manager instance"""
    global _settings_manager
    if _settings_manager is None:
        _settings_manager = SettingsManager()
    return _settings_manager


# Convenience functions for quick access
def get_setting(key_path: str, default: Any = None) -> Any:
    """Quick access to get a setting"""
    return get_settings().get(key_path, default)

def set_setting(key_path: str, value: Any, save: bool = True):
    """Quick access to set a setting"""
    return get_settings().set(key_path, value, save)