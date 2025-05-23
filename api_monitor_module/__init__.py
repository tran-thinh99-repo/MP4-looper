# api_monitor_module/__init__.py - PRODUCTION VERSION
"""API Monitoring Module"""

import logging

from .core.api_tracker import APITracker
from .core.config_manager import ConfigManager
from .core.rate_limiter import RateLimiter

# Import dashboard with error handling
AdminDashboard = None
try:
    from .ui.dashboard import AdminDashboard
except ImportError as e:
    logging.warning(f"AdminDashboard not available: {e}")
except Exception as e:
    logging.error(f"Error loading AdminDashboard: {e}")

try:
    from .utils.decorators import track_api_call
except ImportError:
    def track_api_call(*args, **kwargs):
        def decorator(func): return func
        return decorator

from .utils.monitor_access import get_api_monitor, get_current_user, track_api_call_simple

class APIMonitor:
    """API Monitor class"""
    
    def __init__(self, app_name, admin_emails, storage_path=None):
        self.app_name = app_name
        self.admin_emails = admin_emails if isinstance(admin_emails, list) else [admin_emails]
        
        try:
            self.config_manager = ConfigManager(app_name, storage_path)
            self.tracker = APITracker(self.config_manager)
            self.rate_limiter = RateLimiter(self.config_manager)
            self.config_manager.set_admin_emails(self.admin_emails)
            self._dashboard = None
            
            logging.info(f"✅ API Monitor initialized for '{app_name}'")
            
        except Exception as e:
            logging.error(f"Critical error initializing API Monitor: {e}")
            raise
    
    def is_admin_user(self, user_email=None):
        """Check if current user is an admin"""
        if user_email is None:
            try:
                from auth_module.email_auth import get_current_user
                user_email = get_current_user()
            except ImportError:
                return False
        return user_email in self.admin_emails
    
    def show_dashboard(self, parent_window=None):
        """Show the admin dashboard"""
        if not self.is_admin_user():
            try:
                from tkinter import messagebox
                messagebox.showerror("Access Denied", "Administrator privileges required")
            except ImportError:
                print("Access Denied: Administrator privileges required")
            return
        
        try:
            if AdminDashboard and (self._dashboard is None or not self._dashboard.winfo_exists()):
                self._dashboard = AdminDashboard(self.tracker, self.config_manager, parent_window)
            elif AdminDashboard:
                self._dashboard.lift()
                self._dashboard.focus_force()
            else:
                try:
                    from tkinter import messagebox
                    messagebox.showinfo(
                        "Dashboard Unavailable", 
                        "The monitoring dashboard is temporarily unavailable.\n"
                        "Please try again later.",
                        parent=parent_window
                    )
                except ImportError:
                    print("Dashboard unavailable")
        except Exception as e:
            logging.error(f"Error showing dashboard: {e}")
            try:
                from tkinter import messagebox
                messagebox.showerror(
                    "Dashboard Error", 
                    f"An error occurred while opening the dashboard.\n"
                    f"Please check the debug log for details.",
                    parent=parent_window
                )
            except:
                print(f"Dashboard error: {e}")
    
    def record_custom_metric(self, metric_name, value, unit="count"):
        """Record a custom metric"""
        try:
            self.tracker.record_custom_metric(metric_name, value, unit)
        except Exception as e:
            logging.debug(f"Error recording custom metric: {e}")
    
    def get_stats_summary(self):
        """Get current statistics summary"""
        try:
            return self.tracker.get_stats_summary()
        except Exception as e:
            logging.debug(f"Error getting stats summary: {e}")
            return {'overview': {'total_calls_ever': 0}, 'session': {'active_users': 0}}
    
    def export_data(self, format="json", days_back=30):
        """Export monitoring data"""
        try:
            return self.tracker.export_data(format, days_back)
        except Exception as e:
            logging.debug(f"Error exporting data: {e}")
            return None
    
    def cleanup_old_data(self):
        """Clean up old data"""
        try:
            self.tracker.cleanup_old_data()
        except Exception as e:
            logging.debug(f"Error cleaning up data: {e}")

def setup_monitoring(app_name, admin_emails, storage_path=None, auto_cleanup=True):
    """Setup function"""
    try:
        return APIMonitor(app_name, admin_emails, storage_path)
    except Exception as e:
        logging.error(f"Failed to setup monitoring: {e}")
        
        class DummyAPIMonitor:
            def __init__(self):
                self.app_name = app_name
                self.admin_emails = admin_emails if isinstance(admin_emails, list) else [admin_emails]
            
            def is_admin_user(self, email=None):
                if email is None:
                    try:
                        from auth_module.email_auth import get_current_user
                        email = get_current_user()
                    except ImportError:
                        return False
                return email in self.admin_emails
            
            def get_stats_summary(self):
                return {'overview': {'total_calls_ever': 0}, 'session': {'active_users': 0}}
            
            def record_custom_metric(self, *args, **kwargs): pass
            def export_data(self, *args, **kwargs): return None
            def cleanup_old_data(self): pass
            def show_dashboard(self, parent_window=None):
                try:
                    from tkinter import messagebox
                    messagebox.showinfo("Dashboard Unavailable", 
                                      "The monitoring dashboard is not available.", parent=parent_window)
                except ImportError:
                    print("Dashboard unavailable")
        
        logging.warning("Created dummy API monitor")
        return DummyAPIMonitor()

__all__ = ['APIMonitor', 'APITracker', 'ConfigManager', 'RateLimiter', 'AdminDashboard', 
           'setup_monitoring', 'track_api_call', 'get_api_monitor', 'get_current_user', 
           'track_api_call_simple']