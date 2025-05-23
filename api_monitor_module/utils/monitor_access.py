# api_monitor_module/utils/monitor_access.py
import gc
import logging

# Cache for the API monitor to avoid repeated lookups
_api_monitor_cache = None
_cache_checked = False

def get_api_monitor():
    """Global helper function to get the API monitor"""
    global _api_monitor_cache, _cache_checked
    
    # Return cached monitor if we have it
    if _api_monitor_cache is not None:
        return _api_monitor_cache
    
    # If we've already checked and didn't find it, return None
    if _cache_checked:
        return None
    
    try:
        # Mark that we've checked
        _cache_checked = True
        
        # Try to import and get the monitor directly from the app
        # This avoids the gc.get_objects() call that might trigger _gdbm imports
        import sys
        
        # Check if mp4_looper module is loaded
        if 'mp4_looper' in sys.modules:
            mp4_looper = sys.modules['mp4_looper']
            if hasattr(mp4_looper, 'MP4LooperApp'):
                # Try to find the running instance
                for obj in gc.get_objects():
                    if obj.__class__.__name__ == 'MP4LooperApp' and hasattr(obj, 'api_monitor'):
                        _api_monitor_cache = obj.api_monitor
                        return _api_monitor_cache
        
        # Alternative: Check for __main__ module
        if hasattr(sys.modules.get('__main__', None), 'app'):
            app = sys.modules['__main__'].app
            if hasattr(app, 'api_monitor'):
                _api_monitor_cache = app.api_monitor
                return _api_monitor_cache
                
    except Exception as e:
        # Only log this once, not every time
        if not hasattr(get_api_monitor, '_error_logged'):
            logging.debug(f"API monitor not available: {str(e)}")
            get_api_monitor._error_logged = True
    
    return None

def get_current_user():
    """Helper to get current authenticated user"""
    try:
        from auth_module.email_auth import get_current_user
        return get_current_user()
    except ImportError:
        return None

def track_api_call_simple(api_type, success=True, error_message=None, **kwargs):
    """Simple function to manually track an API call without decorators"""
    try:
        monitor = get_api_monitor()
        if monitor and hasattr(monitor, 'tracker'):
            user_email = get_current_user()
            
            monitor.tracker.record_api_call(
                api_type=api_type,
                user_email=user_email,
                success=success,
                response_time=kwargs.get('upload_time', 0) * 1000 if 'upload_time' in kwargs else None,
                error_message=error_message,
                custom_data=kwargs
            )
            
            for metric_name, value in kwargs.items():
                if isinstance(value, (int, float)) and metric_name != 'upload_time':
                    monitor.record_custom_metric(metric_name, value)
                    
            # Only log successful tracking in debug mode
            if logging.getLogger().isEnabledFor(logging.DEBUG):
                logging.debug(f"API call tracked: {api_type} - {'SUCCESS' if success else 'ERROR'}")
                
        else:
            # Only show this warning once per session
            if not hasattr(track_api_call_simple, '_warning_shown'):
                logging.info("API monitoring not available - calls will not be tracked")
                track_api_call_simple._warning_shown = True
            
    except Exception as e:
        # Only log this error once per session
        if not hasattr(track_api_call_simple, '_error_logged'):
            logging.warning(f"API tracking unavailable: {str(e)}")
            track_api_call_simple._error_logged = True

# Set a flag to indicate the module is loaded
_module_loaded = True