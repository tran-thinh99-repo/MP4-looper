# api_monitor_module/utils/decorators.py
"""
Decorators for API tracking and rate limiting
"""

import time
import logging
from functools import wraps

def track_api_call(tracker, rate_limiter, api_type, rate_limit_user=None, 
                  max_calls=None, window_minutes=None, auto_block_abuse=True):
    """
    Decorator to track API calls and apply rate limiting
    
    Args:
        tracker: APITracker instance
        rate_limiter: RateLimiter instance
        api_type (str): Type of API call
        rate_limit_user (str): User email for rate limiting (can be callable)
        max_calls (int): Maximum calls allowed in window
        window_minutes (int): Time window in minutes
        auto_block_abuse (bool): Whether to auto-block abusive users
    
    Returns:
        Decorator function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            user_email = None
            success = True
            error_message = None
            result = None
            
            try:
                # Get user email for rate limiting
                if rate_limit_user:
                    if callable(rate_limit_user):
                        user_email = rate_limit_user()
                    elif isinstance(rate_limit_user, str):
                        if rate_limit_user == "current_user":
                            # Try to get current authenticated user
                            try:
                                from auth_module.email_auth import get_current_user
                                user_email = get_current_user()
                            except ImportError:
                                logging.debug("Could not import get_current_user for rate limiting")
                        else:
                            user_email = rate_limit_user
                
                # Check rate limiting
                if user_email and rate_limiter:
                    is_limited, reason, retry_after = rate_limiter.is_rate_limited(
                        api_type, user_email, None, max_calls, window_minutes
                    )
                    
                    if is_limited:
                        error_message = f"Rate limited: {reason}"
                        success = False
                        
                        # Record the rate limit hit
                        response_time = (time.time() - start_time) * 1000
                        tracker.record_api_call(
                            api_type, user_email, False, response_time, error_message
                        )
                        
                        # Auto-block if abuse patterns detected
                        if auto_block_abuse:
                            blocked, block_reason, duration = rate_limiter.auto_block_if_abuse(
                                user_email, api_type
                            )
                            if blocked:
                                error_message += f" | Auto-blocked: {block_reason}"
                        
                        # Import and raise the exception
                        from ..core.rate_limiter import RateLimitExceeded
                        
                        # Return appropriate error response
                        if hasattr(func, '__annotations__') and 'return' in func.__annotations__:
                            # If function is annotated to return a tuple, return (False, error_message)
                            return False, error_message
                        else:
                            # Otherwise, raise an exception or return None based on function type
                            raise RateLimitExceeded(error_message, retry_after)
                
                # Execute the original function
                result = func(*args, **kwargs)
                
                # Determine success based on result
                if isinstance(result, tuple) and len(result) >= 2:
                    # Function returns (success, message) or similar tuple
                    success = bool(result[0])
                    if not success and len(result) > 1:
                        error_message = str(result[1])
                elif result is False:
                    success = False
                    error_message = "Function returned False"
                elif result is None:
                    # Some functions return None on success, others on failure
                    # We'll assume success unless an exception was raised
                    success = True
                else:
                    success = True
                
            except Exception as e:
                # Import here to avoid circular imports
                from ..core.rate_limiter import RateLimitExceeded
                
                if isinstance(e, RateLimitExceeded):
                    # Re-raise rate limit exceptions
                    raise
                else:
                    success = False
                    error_message = str(e)
                    logging.error(f"API call {api_type} failed: {error_message}")
                    
                    # Re-raise the original exception after recording
                    result = e
            
            finally:
                # Record the API call
                response_time = (time.time() - start_time) * 1000
                
                if tracker:
                    tracker.record_api_call(
                        api_type=api_type,
                        user_email=user_email,
                        success=success,
                        response_time=response_time,
                        error_message=error_message,
                        custom_data={
                            'function_name': func.__name__,
                            'args_count': len(args),
                            'kwargs_count': len(kwargs)
                        }
                    )
                
                # Log the call with appropriate level
                log_level = logging.DEBUG if success else logging.WARNING
                log_msg = f"API [{api_type}] {func.__name__} - {'SUCCESS' if success else 'ERROR'}"
                if response_time:
                    log_msg += f" ({response_time:.0f}ms)"
                if user_email:
                    log_msg += f" - {user_email}"
                if error_message and not success:
                    log_msg += f" - {error_message}"
                
                logging.log(log_level, log_msg)
            
            # Handle exceptions
            if isinstance(result, Exception):
                raise result
            
            return result
        
        # Add metadata to the wrapped function
        wrapper._api_type = api_type
        wrapper._is_tracked = True
        wrapper._original_func = func
        
        return wrapper
    return decorator

def track_custom_metric(tracker, metric_name, value_extractor=None, unit="count"):
    """
    Decorator to track custom metrics
    
    Args:
        tracker: APITracker instance
        metric_name (str): Name of the metric to track
        value_extractor (callable): Function to extract value from result
        unit (str): Unit of measurement
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            # Extract value for the metric
            if value_extractor and callable(value_extractor):
                try:
                    value = value_extractor(result, *args, **kwargs)
                except Exception as e:
                    logging.error(f"Error extracting metric value for {metric_name}: {e}")
                    value = 1  # Default to counting occurrences
            else:
                # Default to counting function calls
                value = 1
            
            # Get user email if available
            user_email = None
            try:
                from auth_module.email_auth import get_current_user
                user_email = get_current_user()
            except ImportError:
                pass
            
            # Record the metric
            if tracker:
                tracker.record_custom_metric(metric_name, value, unit, user_email)
            
            return result
        
        wrapper._metric_name = metric_name
        wrapper._is_metric_tracked = True
        
        return wrapper
    return decorator

def track_response_time(tracker, operation_name):
    """
    Decorator to specifically track response times for operations
    
    Args:
        tracker: APITracker instance
        operation_name (str): Name of the operation
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
                
                # Record as custom metric
                if tracker:
                    tracker.record_custom_metric(
                        f"{operation_name}_response_time", 
                        response_time, 
                        "milliseconds"
                    )
                
                return result
                
            except Exception as e:
                response_time = (time.time() - start_time) * 1000
                
                # Still record the response time even on error
                if tracker:
                    tracker.record_custom_metric(
                        f"{operation_name}_response_time", 
                        response_time, 
                        "milliseconds"
                    )
                
                raise
        
        return wrapper
    return decorator

def require_admin(config_manager, error_message="Administrator privileges required"):
    """
    Decorator to require admin privileges for a function
    
    Args:
        config_manager: ConfigManager instance
        error_message (str): Error message for access denied
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get current user
            current_user = None
            try:
                from auth_module.email_auth import get_current_user
                current_user = get_current_user()
            except ImportError:
                pass
            
            if not current_user or not config_manager.is_admin(current_user):
                raise PermissionError(error_message)
            
            return func(*args, **kwargs)
        
        wrapper._requires_admin = True
        return wrapper
    return decorator

def rate_limit_only(rate_limiter, api_type, max_calls=None, window_minutes=None):
    """
    Decorator for rate limiting without API tracking
    
    Args:
        rate_limiter: RateLimiter instance
        api_type (str): Type of operation for rate limiting
        max_calls (int): Maximum calls allowed
        window_minutes (int): Time window in minutes
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get current user
            user_email = None
            try:
                from auth_module.email_auth import get_current_user
                user_email = get_current_user()
            except ImportError:
                pass
            
            # Check rate limit
            if user_email and rate_limiter:
                is_limited, reason, retry_after = rate_limiter.is_rate_limited(
                    api_type, user_email, None, max_calls, window_minutes
                )
                
                if is_limited:
                    from ..core.rate_limiter import RateLimitExceeded
                    raise RateLimitExceeded(f"Rate limited: {reason}", retry_after)
            
            return func(*args, **kwargs)
        
        wrapper._rate_limited = True
        wrapper._api_type = api_type
        
        return wrapper
    return decorator

# Remove the duplicate RateLimitExceeded class definition since it's now in rate_limiter.py

# Convenience functions for common patterns
def track_auth_call(tracker, rate_limiter):
    """Convenience decorator for authentication-related API calls"""
    return track_api_call(
        tracker, rate_limiter, "auth_operation", 
        rate_limit_user="current_user", max_calls=10, window_minutes=60
    )

def track_upload_call(tracker, rate_limiter):
    """Convenience decorator for upload-related API calls"""
    return track_api_call(
        tracker, rate_limiter, "file_upload", 
        rate_limit_user="current_user", max_calls=50, window_minutes=60
    )

def track_debug_call(tracker, rate_limiter):
    """Convenience decorator for debug-related API calls"""
    return track_api_call(
        tracker, rate_limiter, "debug_upload", 
        rate_limit_user="current_user", max_calls=3, window_minutes=60
    )

def track_sheets_call(tracker, rate_limiter):
    """Convenience decorator for Google Sheets API calls"""
    return track_api_call(
        tracker, rate_limiter, "sheets_operation", 
        rate_limit_user="current_user", max_calls=100, window_minutes=60
    )