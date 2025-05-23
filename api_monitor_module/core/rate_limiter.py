# api_monitor_module/core/rate_limiter.py
"""
Rate Limiter - Handles rate limiting for API calls to prevent abuse
"""

import json
import time
import logging
import threading
from datetime import datetime, timedelta
from collections import defaultdict

class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded"""
    
    def __init__(self, message, retry_after=0):
        super().__init__(message)
        self.retry_after = retry_after
        self.message = message
    
    def __str__(self):
        if self.retry_after > 0:
            if self.retry_after > 60:
                minutes = int(self.retry_after / 60)
                return f"{self.message} (Retry in {minutes} minutes)"
            else:
                seconds = int(self.retry_after)
                return f"{self.message} (Retry in {seconds} seconds)"
        return self.message

class RateLimiter:
    """Manages rate limiting for API calls"""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.rate_limits_file = config_manager.rate_limits_file
        
        # Thread safety
        self._lock = threading.Lock()
        
        # In-memory rate limit tracking
        self.rate_data = self._load_rate_data()
        
        # Cleanup thread
        self._start_cleanup_thread()
    
    def _load_rate_data(self):
        """Load rate limiting data from file"""
        default_data = {
            'user_limits': {},      # user_email -> {api_type -> [timestamps]}
            'ip_limits': {},        # ip_address -> {api_type -> [timestamps]}
            'global_limits': {},    # api_type -> [timestamps]
            'blocked_users': {},    # user_email -> {reason, until_timestamp}
            'metadata': {
                'created': datetime.now().isoformat(),
                'last_cleanup': datetime.now().isoformat()
            }
        }
        
        if self.rate_limits_file.exists():
            try:
                with open(self.rate_limits_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                
                # Merge with defaults
                for key in default_data:
                    if key not in existing_data:
                        existing_data[key] = default_data[key]
                
                return existing_data
            except Exception as e:
                logging.error(f"Error loading rate limit data: {e}")
                return default_data
        else:
            self._save_rate_data(default_data)
            return default_data
    
    def _save_rate_data(self, data=None):
        """Save rate limiting data to file"""
        if data is None:
            data = self.rate_data
        
        try:
            with self._lock:
                data['metadata']['last_updated'] = datetime.now().isoformat()
                
                with open(self.rate_limits_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logging.error(f"Error saving rate limit data: {e}")
    
    def is_rate_limited(self, api_type, user_email=None, ip_address=None, 
                       max_calls=None, window_minutes=None):
        """
        Check if a request should be rate limited
        
        Args:
            api_type (str): Type of API call
            user_email (str): User making the request
            ip_address (str): IP address of request
            max_calls (int): Override default max calls
            window_minutes (int): Override default window
        
        Returns:
            tuple: (is_limited, reason, retry_after_seconds)
        """
        now = time.time()
        
        # Get rate limit configuration
        if max_calls is None or window_minutes is None:
            config = self.config_manager.get_rate_limit_config(api_type)
            max_calls = max_calls or config.get('max_calls', 100)
            window_minutes = window_minutes or config.get('window_minutes', 60)
        
        window_seconds = window_minutes * 60
        window_start = now - window_seconds
        
        with self._lock:
            # Check if user is blocked
            if user_email and user_email in self.rate_data['blocked_users']:
                block_info = self.rate_data['blocked_users'][user_email]
                if now < block_info.get('until_timestamp', 0):
                    retry_after = block_info['until_timestamp'] - now
                    return True, f"User blocked: {block_info.get('reason', 'Abuse detected')}", retry_after
                else:
                    # Block expired, remove it
                    del self.rate_data['blocked_users'][user_email]
            
            # Check user rate limit
            if user_email:
                if user_email not in self.rate_data['user_limits']:
                    self.rate_data['user_limits'][user_email] = {}
                
                user_data = self.rate_data['user_limits'][user_email]
                
                if api_type not in user_data:
                    user_data[api_type] = []
                
                # Clean old timestamps
                user_data[api_type] = [ts for ts in user_data[api_type] if ts > window_start]
                
                # Check if over limit
                if len(user_data[api_type]) >= max_calls:
                    oldest_call = min(user_data[api_type])
                    retry_after = oldest_call + window_seconds - now
                    return True, f"Rate limit exceeded for {api_type}", retry_after
                
                # Add current timestamp
                user_data[api_type].append(now)
            
            # Check IP rate limit (if provided)
            if ip_address:
                if ip_address not in self.rate_data['ip_limits']:
                    self.rate_data['ip_limits'][ip_address] = {}
                
                ip_data = self.rate_data['ip_limits'][ip_address]
                
                if api_type not in ip_data:
                    ip_data[api_type] = []
                
                # Clean old timestamps
                ip_data[api_type] = [ts for ts in ip_data[api_type] if ts > window_start]
                
                # Check if over limit (IP limits are typically higher)
                ip_max_calls = max_calls * 2  # Allow 2x for IP-based limiting
                if len(ip_data[api_type]) >= ip_max_calls:
                    oldest_call = min(ip_data[api_type])
                    retry_after = oldest_call + window_seconds - now
                    return True, f"IP rate limit exceeded for {api_type}", retry_after
                
                # Add current timestamp
                ip_data[api_type].append(now)
            
            # Check global rate limit
            if api_type not in self.rate_data['global_limits']:
                self.rate_data['global_limits'][api_type] = []
            
            global_data = self.rate_data['global_limits'][api_type]
            
            # Clean old timestamps
            global_data[:] = [ts for ts in global_data if ts > window_start]
            
            # Global limits are much higher (for system protection)
            global_max_calls = max_calls * 100
            if len(global_data) >= global_max_calls:
                oldest_call = min(global_data)
                retry_after = oldest_call + window_seconds - now
                return True, f"Global rate limit exceeded for {api_type}", retry_after
            
            # Add current timestamp
            global_data.append(now)
            
            # Save periodically (every 10 checks) to avoid too much I/O
            if len(global_data) % 10 == 0:
                self._save_rate_data()
        
        return False, "OK", 0
    
    def block_user(self, user_email, reason, duration_minutes=60):
        """
        Block a user for a specified duration
        
        Args:
            user_email (str): User to block
            reason (str): Reason for blocking
            duration_minutes (int): How long to block for
        """
        until_timestamp = time.time() + (duration_minutes * 60)
        
        with self._lock:
            self.rate_data['blocked_users'][user_email] = {
                'reason': reason,
                'until_timestamp': until_timestamp,
                'blocked_at': datetime.now().isoformat()
            }
            
            self._save_rate_data()
        
        logging.warning(f"User {user_email} blocked for {duration_minutes} minutes: {reason}")
    
    def unblock_user(self, user_email):
        """Remove block for a user"""
        with self._lock:
            if user_email in self.rate_data['blocked_users']:
                del self.rate_data['blocked_users'][user_email]
                self._save_rate_data()
                logging.info(f"User {user_email} unblocked")
                return True
        return False
    
    def get_user_rate_info(self, user_email, api_type):
        """Get current rate limit info for a user"""
        with self._lock:
            config = self.config_manager.get_rate_limit_config(api_type)
            max_calls = config.get('max_calls', 100)
            window_minutes = config.get('window_minutes', 60)
            
            if (user_email in self.rate_data['user_limits'] and 
                api_type in self.rate_data['user_limits'][user_email]):
                
                now = time.time()
                window_start = now - (window_minutes * 60)
                
                # Get recent calls
                recent_calls = [ts for ts in self.rate_data['user_limits'][user_email][api_type] 
                              if ts > window_start]
                
                calls_made = len(recent_calls)
                calls_remaining = max(0, max_calls - calls_made)
                
                # Calculate reset time
                reset_time = 0
                if recent_calls:
                    oldest_call = min(recent_calls)
                    reset_time = oldest_call + (window_minutes * 60)
                
                return {
                    'api_type': api_type,
                    'max_calls': max_calls,
                    'window_minutes': window_minutes,
                    'calls_made': calls_made,
                    'calls_remaining': calls_remaining,
                    'reset_timestamp': reset_time,
                    'reset_in_seconds': max(0, reset_time - now)
                }
            else:
                return {
                    'api_type': api_type,
                    'max_calls': max_calls,
                    'window_minutes': window_minutes,
                    'calls_made': 0,
                    'calls_remaining': max_calls,
                    'reset_timestamp': 0,
                    'reset_in_seconds': 0
                }
    
    def get_rate_limit_stats(self):
        """Get statistics about rate limiting"""
        with self._lock:
            now = time.time()
            
            # Count active rate limits
            active_users = 0
            active_ips = 0
            blocked_users = len(self.rate_data['blocked_users'])
            
            # Remove expired blocks while counting
            expired_blocks = []
            for user_email, block_info in self.rate_data['blocked_users'].items():
                if now >= block_info.get('until_timestamp', 0):
                    expired_blocks.append(user_email)
            
            for user_email in expired_blocks:
                del self.rate_data['blocked_users'][user_email]
            
            blocked_users = len(self.rate_data['blocked_users'])
            
            # Count users with recent activity
            window_start = now - 3600  # Last hour
            
            for user_email, user_data in self.rate_data['user_limits'].items():
                for api_type, timestamps in user_data.items():
                    if any(ts > window_start for ts in timestamps):
                        active_users += 1
                        break
            
            for ip_address, ip_data in self.rate_data['ip_limits'].items():
                for api_type, timestamps in ip_data.items():
                    if any(ts > window_start for ts in timestamps):
                        active_ips += 1
                        break
            
            # API type breakdown
            api_usage = {}
            for user_data in self.rate_data['user_limits'].values():
                for api_type, timestamps in user_data.items():
                    recent_calls = [ts for ts in timestamps if ts > window_start]
                    if api_type not in api_usage:
                        api_usage[api_type] = 0
                    api_usage[api_type] += len(recent_calls)
            
            return {
                'active_users_last_hour': active_users,
                'active_ips_last_hour': active_ips,
                'blocked_users': blocked_users,
                'blocked_user_list': list(self.rate_data['blocked_users'].keys()),
                'api_usage_last_hour': api_usage,
                'total_users_tracked': len(self.rate_data['user_limits']),
                'total_ips_tracked': len(self.rate_data['ip_limits'])
            }
    
    def reset_user_limits(self, user_email, api_type=None):
        """Reset rate limits for a user"""
        with self._lock:
            if user_email in self.rate_data['user_limits']:
                if api_type:
                    # Reset specific API type
                    if api_type in self.rate_data['user_limits'][user_email]:
                        del self.rate_data['user_limits'][user_email][api_type]
                        logging.info(f"Reset rate limits for {user_email} - {api_type}")
                else:
                    # Reset all API types for user
                    del self.rate_data['user_limits'][user_email]
                    logging.info(f"Reset all rate limits for {user_email}")
                
                self._save_rate_data()
                return True
        return False
    
    def _start_cleanup_thread(self):
        """Start background thread for periodic cleanup"""
        def cleanup_worker():
            while True:
                try:
                    time.sleep(3600)  # Run every hour
                    self._cleanup_old_data()
                except Exception as e:
                    logging.error(f"Rate limiter cleanup error: {e}")
        
        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()
    
    def _cleanup_old_data(self):
        """Clean up old rate limiting data"""
        now = time.time()
        cutoff_time = now - (24 * 60 * 60)  # Keep last 24 hours
        
        with self._lock:
            # Clean user limits
            for user_email in list(self.rate_data['user_limits'].keys()):
                user_data = self.rate_data['user_limits'][user_email]
                
                for api_type in list(user_data.keys()):
                    # Remove old timestamps
                    user_data[api_type] = [ts for ts in user_data[api_type] if ts > cutoff_time]
                    
                    # Remove empty API types
                    if not user_data[api_type]:
                        del user_data[api_type]
                
                # Remove empty users
                if not user_data:
                    del self.rate_data['user_limits'][user_email]
            
            # Clean IP limits
            for ip_address in list(self.rate_data['ip_limits'].keys()):
                ip_data = self.rate_data['ip_limits'][ip_address]
                
                for api_type in list(ip_data.keys()):
                    # Remove old timestamps
                    ip_data[api_type] = [ts for ts in ip_data[api_type] if ts > cutoff_time]
                    
                    # Remove empty API types
                    if not ip_data[api_type]:
                        del ip_data[api_type]
                
                # Remove empty IPs
                if not ip_data:
                    del self.rate_data['ip_limits'][ip_address]
            
            # Clean global limits
            for api_type in list(self.rate_data['global_limits'].keys()):
                self.rate_data['global_limits'][api_type] = [
                    ts for ts in self.rate_data['global_limits'][api_type] 
                    if ts > cutoff_time
                ]
                
                # Remove empty API types
                if not self.rate_data['global_limits'][api_type]:
                    del self.rate_data['global_limits'][api_type]
            
            # Remove expired blocks
            expired_blocks = []
            for user_email, block_info in self.rate_data['blocked_users'].items():
                if now >= block_info.get('until_timestamp', 0):
                    expired_blocks.append(user_email)
            
            for user_email in expired_blocks:
                del self.rate_data['blocked_users'][user_email]
            
            # Update metadata
            self.rate_data['metadata']['last_cleanup'] = datetime.now().isoformat()
            
            # Save cleaned data
            self._save_rate_data()
            
            logging.debug("Rate limiter cleanup completed")
            
            # Log cleanup statistics
            users_remaining = len(self.rate_data['user_limits'])
            ips_remaining = len(self.rate_data['ip_limits'])
            api_types_remaining = len(self.rate_data['global_limits'])
            blocks_removed = len(expired_blocks)
            
            logging.info(f"Rate limiter cleanup: {users_remaining} users, {ips_remaining} IPs, "
                        f"{api_types_remaining} API types tracked, {blocks_removed} expired blocks removed")