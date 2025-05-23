# api_monitor_module/core/config_manager.py
"""
Configuration Manager - Handles all config and file paths for API monitoring
"""

import sys
import json
import logging
from datetime import datetime
from pathlib import Path

class ConfigManager:
    """Manages configuration and file paths for API monitoring"""
    
    def __init__(self, app_name, storage_path=None):
        self.app_name = app_name
        
        # Determine storage path - always next to script/exe
        if storage_path:
            self.storage_path = Path(storage_path)
        else:
            # Get the directory where the script/exe is located
            if getattr(sys, 'frozen', False):
                # Running as compiled executable
                app_dir = Path(sys.executable).parent
            else:
                # Running as script - get the main script directory
                if hasattr(sys, 'argv') and sys.argv[0]:
                    app_dir = Path(sys.argv[0]).parent
                else:
                    app_dir = Path.cwd()
            
            # Use a better folder name - simple and clean
            self.storage_path = app_dir / "monitoring_data"
        
        # Ensure storage directory exists
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # File paths
        self.config_file = self.storage_path / "config.json"
        self.stats_file = self.storage_path / "api_stats.json"
        self.rate_limits_file = self.storage_path / "rate_limits.json"
        self.archives_dir = self.storage_path / "archives"
        self.exports_dir = self.storage_path / "exports"
        
        # Create subdirectories
        self.archives_dir.mkdir(exist_ok=True)
        self.exports_dir.mkdir(exist_ok=True)
        
        # Log where we're storing data
        logging.info(f"📁 Monitoring data stored in: {self.storage_path}")
        
        # Load or create configuration
        self.config = self._load_or_create_config()
    
    def _load_or_create_config(self):
        """Load existing config or create default"""
        default_config = {
            "app_name": self.app_name,
            "version": "1.0.0",
            "created": datetime.now().isoformat(),
            "admin_emails": [],
            "retention": {
                "detailed_days": 30,
                "summary_months": 12,
                "auto_cleanup": True,
                "max_file_size_mb": 50
            },
            "ui": {
                "theme": "dark",
                "auto_refresh": False,
                "refresh_interval_seconds": 30,
                "default_window_size": [1000, 700],
                "remember_window_position": True
            },
            "tracking": {
                "enabled": True,
                "track_response_times": True,
                "track_user_activity": True,
                "enabled_apis": ["auth", "upload", "sheets", "drive"],
                "custom_metrics": {}
            },
            "rate_limits": {
                "global_enabled": True,
                "default_limits": {
                    "debug_upload": {"max_calls": 3, "window_minutes": 60},
                    "auth_operation": {"max_calls": 10, "window_minutes": 60},
                    "api_call": {"max_calls": 100, "window_minutes": 60}
                }
            },
            "alerts": {
                "enabled": False,
                "error_rate_threshold": 10.0,
                "response_time_threshold": 5000,
                "email_notifications": False
            }
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    existing_config = json.load(f)
                
                # Merge with defaults to add any new settings
                merged_config = self._merge_configs(default_config, existing_config)
                return merged_config
            except Exception as e:
                logging.error(f"Error loading config: {e}")
                return default_config
        else:
            # Create new config file
            self._save_config(default_config)
            return default_config
    
    def _merge_configs(self, default, existing):
        """Merge existing config with defaults to add new keys"""
        for key, value in default.items():
            if key not in existing:
                existing[key] = value
            elif isinstance(value, dict) and isinstance(existing[key], dict):
                existing[key] = self._merge_configs(value, existing[key])
        return existing
    
    def _save_config(self, config=None):
        """Save configuration to file"""
        if config is None:
            config = self.config
        
        try:
            # Update last modified
            config["last_modified"] = datetime.now().isoformat()
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            logging.debug(f"Config saved to {self.config_file}")
        except Exception as e:
            logging.error(f"Error saving config: {e}")
    
    def get(self, key_path, default=None):
        """
        Get configuration value using dot notation
        
        Args:
            key_path (str): Dot-separated path like 'retention.detailed_days'
            default: Default value if key not found
        
        Returns:
            Configuration value
        """
        keys = key_path.split('.')
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path, value, save=True):
        """
        Set configuration value using dot notation
        
        Args:
            key_path (str): Dot-separated path like 'retention.detailed_days'
            value: Value to set
            save (bool): Whether to save immediately
        """
        keys = key_path.split('.')
        config = self.config
        
        # Navigate to parent key
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        # Set the value
        config[keys[-1]] = value
        
        if save:
            self._save_config()
    
    def set_admin_emails(self, emails):
        """Set admin email addresses"""
        self.set('admin_emails', emails, save=True)
    
    def get_admin_emails(self):
        """Get admin email addresses"""
        return self.get('admin_emails', [])
    
    def is_admin(self, email):
        """Check if email is in admin list"""
        return email in self.get_admin_emails()
    
    def get_retention_config(self):
        """Get retention configuration"""
        return {
            'detailed_days': self.get('retention.detailed_days', 30),
            'summary_months': self.get('retention.summary_months', 12),
            'auto_cleanup': self.get('retention.auto_cleanup', True),
            'max_file_size_mb': self.get('retention.max_file_size_mb', 50)
        }
    
    def get_rate_limit_config(self, api_type):
        """Get rate limit configuration for specific API type"""
        default_limits = self.get('rate_limits.default_limits', {})
        
        if api_type in default_limits:
            return default_limits[api_type]
        
        # Return default rate limit
        return self.get('rate_limits.default_limits.api_call', {
            'max_calls': 100,
            'window_minutes': 60
        })
    
    def get_ui_config(self):
        """Get UI configuration"""
        return {
            'theme': self.get('ui.theme', 'dark'),
            'auto_refresh': self.get('ui.auto_refresh', False),
            'refresh_interval': self.get('ui.refresh_interval_seconds', 30),
            'window_size': self.get('ui.default_window_size', [1000, 700]),
            'remember_position': self.get('ui.remember_window_position', True)
        }
    
    def update_ui_config(self, **kwargs):
        """Update UI configuration"""
        for key, value in kwargs.items():
            self.set(f'ui.{key}', value, save=False)
        self._save_config()
    
    def get_file_paths(self):
        """Get all important file paths"""
        return {
            'storage_path': str(self.storage_path),
            'config_file': str(self.config_file),
            'stats_file': str(self.stats_file),
            'rate_limits_file': str(self.rate_limits_file),
            'archives_dir': str(self.archives_dir),
            'exports_dir': str(self.exports_dir)
        }
    
    def get_archive_file_path(self, year_month):
        """Get path for archive file (e.g., '2024-01')"""
        return self.archives_dir / f"{year_month}.json"
    
    def get_export_file_path(self, filename):
        """Get path for export file"""
        return self.exports_dir / filename
    
    def cleanup_config(self):
        """Clean up configuration (remove old temp settings, etc.)"""
        # Remove any temporary or invalid settings
        config_changed = False
        
        # Add any cleanup logic here
        # For example, removing old format settings
        
        if config_changed:
            self._save_config()
    
    def export_config(self, file_path):
        """Export configuration to a file"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logging.error(f"Error exporting config: {e}")
            return False
    
    def import_config(self, file_path):
        """Import configuration from a file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
            
            # Merge with current config
            self.config = self._merge_configs(self.config, imported_config)
            self._save_config()
            return True
        except Exception as e:
            logging.error(f"Error importing config: {e}")
            return False
    
    def reset_to_defaults(self):
        """Reset configuration to defaults"""
        # Backup current admin emails
        current_admins = self.get_admin_emails()
        
        # Reset to defaults
        self.config = self._load_or_create_config()
        
        # Restore admin emails
        self.set_admin_emails(current_admins)
        
        logging.info("Configuration reset to defaults")
    
    def get_storage_info(self):
        """Get information about storage usage"""
        try:
            total_size = 0
            file_count = 0
            
            for file_path in self.storage_path.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
                    file_count += 1
            
            return {
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'file_count': file_count,
                'storage_path': str(self.storage_path)
            }
        except Exception as e:
            logging.error(f"Error getting storage info: {e}")
            return {'error': str(e)}