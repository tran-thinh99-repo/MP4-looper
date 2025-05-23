# paths.py - Updated with standardized path resolution

import os
import sys
import logging
import shutil
from tkinter import messagebox
from pathlib import Path

class PathManager:
    """Centralized path management for the application"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._base_path = None
            self._app_directory = None
            self._is_frozen = getattr(sys, 'frozen', False)
            self._initialize_paths()
            self._initialized = True
            logging.debug(f"Path manager initialized - Base: {self._base_path}")
    
    def _initialize_paths(self):
        """Initialize application paths based on execution context"""
        if self._is_frozen:
            # Running as compiled executable (PyInstaller)
            self._app_directory = Path(sys.executable).parent
            
            # For frozen apps, use a permanent data location
            app_data_dir = Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
            self._base_path = app_data_dir / "MP4Looper"
        else:
            # Running as script
            try:
                # Get the directory of the main script
                if hasattr(sys, 'argv') and sys.argv[0]:
                    self._app_directory = Path(sys.argv[0]).resolve().parent
                else:
                    self._app_directory = Path(__file__).resolve().parent
                
                self._base_path = self._app_directory
                
            except (NameError, AttributeError):
                # Fallback to current working directory
                self._app_directory = Path.cwd()
                self._base_path = self._app_directory
        
        # Ensure base path exists
        self._base_path.mkdir(parents=True, exist_ok=True)
        
        logging.info(f"Application directory: {self._app_directory}")
        logging.info(f"Data storage path: {self._base_path}")
    
    @property
    def is_frozen(self) -> bool:
        """Check if running as compiled executable"""
        return self._is_frozen
    
    @property
    def app_directory(self) -> Path:
        """Get the application directory (where exe/script is located)"""
        return self._app_directory
    
    @property
    def base_path(self) -> Path:
        """Get the base data storage path"""
        return self._base_path
    
    def get_resource_path(self, relative_path: str) -> Path:
        """Get absolute path to resource, works for dev and PyInstaller"""
        try:
            if self._is_frozen and hasattr(sys, '_MEIPASS'):
                # PyInstaller creates a temp folder and stores path in _MEIPASS
                base_path = Path(sys._MEIPASS)
            else:
                # Use the application directory
                base_path = self._app_directory
            
            return base_path / relative_path
            
        except Exception as e:
            logging.error(f"Error getting resource path for {relative_path}: {e}")
            # Fallback to application directory
            return self._app_directory / relative_path
    
    def get_config_path(self, filename: str) -> Path:
        """Get path for configuration files"""
        return self._base_path / filename
    
    def get_logs_path(self, filename: str = "debug.log") -> Path:
        """Get path for log files"""
        return self._base_path / filename
    
    def get_temp_path(self, filename: str = None) -> Path:
        """Get path for temporary files"""
        temp_dir = self._base_path / "temp"
        temp_dir.mkdir(exist_ok=True)
        
        if filename:
            return temp_dir / filename
        return temp_dir
    
    def get_cache_path(self, filename: str = None) -> Path:
        """Get path for cache files"""
        cache_dir = self._base_path / "cache"
        cache_dir.mkdir(exist_ok=True)
        
        if filename:
            return cache_dir / filename
        return cache_dir
    
    def get_backup_path(self, filename: str = None) -> Path:
        """Get path for backup files"""
        backup_dir = self._base_path / "backups"
        backup_dir.mkdir(exist_ok=True)
        
        if filename:
            return backup_dir / filename
        return backup_dir
    
    def clean_temp_files(self, max_age_hours: int = 24):
        """Clean old temporary files"""
        try:
            temp_dir = self.get_temp_path()
            if not temp_dir.exists():
                return
            
            import time
            cutoff_time = time.time() - (max_age_hours * 3600)
            
            deleted_count = 0
            for file_path in temp_dir.rglob('*'):
                if file_path.is_file():
                    try:
                        if file_path.stat().st_mtime < cutoff_time:
                            file_path.unlink()
                            deleted_count += 1
                    except Exception as e:
                        logging.debug(f"Could not delete temp file {file_path}: {e}")
            
            if deleted_count > 0:
                logging.info(f"Cleaned {deleted_count} old temporary files")
                
        except Exception as e:
            logging.error(f"Error cleaning temp files: {e}")
    
    def create_directory_structure(self):
        """Create the standard directory structure"""
        directories = [
            self._base_path,
            self.get_temp_path(),
            self.get_cache_path(),
            self.get_backup_path(),
            self._base_path / "exports",
            self._base_path / "monitoring_data"
        ]
        
        for directory in directories:
            try:
                directory.mkdir(parents=True, exist_ok=True)
                logging.debug(f"Created directory: {directory}")
            except Exception as e:
                logging.error(f"Failed to create directory {directory}: {e}")


# Global instance
_path_manager = None

def get_path_manager() -> PathManager:
    """Get the global path manager instance"""
    global _path_manager
    if _path_manager is None:
        _path_manager = PathManager()
    return _path_manager


# Convenience functions for backward compatibility and easy access
def get_base_path() -> str:
    """Get the base path of the application as string"""
    return str(get_path_manager().base_path)

def get_resource_path(relative_path: str) -> str:
    """Get absolute path to resource as string"""
    return str(get_path_manager().get_resource_path(relative_path))

def get_app_directory() -> str:
    """Get the application directory as string"""
    return str(get_path_manager().app_directory)

def get_config_path(filename: str) -> str:
    """Get path for configuration file as string"""
    return str(get_path_manager().get_config_path(filename))

def get_logs_path(filename: str = "debug.log") -> str:
    """Get path for log file as string"""
    return str(get_path_manager().get_logs_path(filename))

def is_frozen() -> bool:
    """Check if running as compiled executable"""
    return get_path_manager().is_frozen


# Utility functions (keep these in paths.py as the single source)
def format_timestamp(seconds):
    """Format seconds into HH:MM:SS timestamp"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02}:{m:02}:{s:02}"

def open_folder(path, label="Folder", parent_window=None):
    """Open a folder in the file explorer"""
    if os.path.isdir(path):
        try:
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":  # macOS
                subprocess.run(["open", path])
            else:  # Linux
                subprocess.run(["xdg-open", path])
        except Exception as e:
            logging.error(f"Failed to open folder {path}: {e}")
            messagebox.showerror(f"{label} Error", 
                               f"Could not open {label.lower()}:\n{path}\n\nError: {e}", 
                               parent=parent_window)
    else:
        messagebox.showerror(f"{label} Error", 
                           f"The {label.lower()} does not exist:\n{path}", 
                           parent=parent_window)

def clean_folder_with_confirmation(folder_path, title="Confirm Cleanup", parent_window=None):
    """Clean a folder with confirmation dialog"""
    folder_path = Path(folder_path)
    if not folder_path.exists() or not folder_path.is_dir():
        messagebox.showerror("Invalid Folder", 
                           f"❌ Folder does not exist:\n{folder_path}", 
                           parent=parent_window)
        return

    items = list(folder_path.iterdir())
    if not items:
        messagebox.showinfo(title, "✅ Folder is already clean.", parent=parent_window)
        logging.info(f"{title}: Already empty — {folder_path}")
        return

    preview = "\n".join(f.name for f in items[:20])
    if len(items) > 20:
        preview += f"\n… and {len(items) - 20} more."

    confirm = messagebox.askyesno(
        title,
        f"⚠️ This will delete ALL contents of:\n{folder_path}\n\n"
        f"{len(items)} item(s):\n\n{preview}\n\nProceed?",
        parent=parent_window
    )

    if not confirm:
        return

    deleted = 0
    for item in items:
        try:
            if item.is_file() or item.is_symlink():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)
            deleted += 1
        except Exception as e:
            logging.error(f"Failed to delete {item.name}: {e}")

    messagebox.showinfo(title, f"✅ Deleted {deleted} item(s).", parent=parent_window)
    logging.info(f"🧹 Wiped {deleted} items from: {folder_path}")


def ensure_directory_structure():
    """Ensure the application directory structure exists"""
    get_path_manager().create_directory_structure()

def clean_temp_files(max_age_hours: int = 24):
    """Clean old temporary files"""
    get_path_manager().clean_temp_files(max_age_hours)