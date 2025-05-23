# api_monitor_module/core/api_tracker_windows.py
"""Windows-Compatible API Tracker - Pure Python + JSON"""

import json
import time
import logging
import threading
import os
from datetime import datetime, timedelta
from collections import defaultdict
from pathlib import Path

class APITracker:
    """Windows-compatible API tracker using pure Python and JSON"""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.stats_file = config_manager.stats_file
        self._lock = threading.Lock()
        self.stats = self._load_stats()
        
        self.session_data = {
            'start_time': time.time(),
            'api_calls': [],
            'response_times': defaultdict(list),
            'active_users': set(),
            'errors': []
        }
        
        # Auto-save thread
        self._start_auto_save_thread()
        
        logging.info("✅ Windows-compatible API tracker initialized")
    
    def _load_stats(self):
        """Load statistics from JSON file"""
        default_stats = {
            'metadata': {
                'created': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat(),
                'version': '1.0.0-windows',
                'total_calls_ever': 0,
                'platform': 'windows'
            },
            'daily_stats': {},
            'api_types': {},
            'user_activity': {},
            'custom_metrics': {},
            'performance': {}
        }
        
        if self.stats_file.exists():
            try:
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    existing_stats = json.load(f)
                
                # Convert lists back to sets for unique_users
                self._convert_lists_to_sets(existing_stats)
                
                merged_stats = self._merge_stats(default_stats, existing_stats)
                total_calls = merged_stats.get('metadata', {}).get('total_calls_ever', 0)
                logging.info(f"📊 Loaded stats: {total_calls} total calls (Windows)")
                return merged_stats
                
            except Exception as e:
                logging.error(f"Error loading stats: {e}")
                return default_stats
        else:
            self._save_stats(default_stats)
            return default_stats
    
    def _convert_lists_to_sets(self, stats):
        """Convert unique_users lists back to sets after loading from JSON"""
        try:
            for date, daily_data in stats.get('daily_stats', {}).items():
                if 'unique_users' in daily_data:
                    if isinstance(daily_data['unique_users'], list):
                        daily_data['unique_users'] = set(daily_data['unique_users'])
                    elif not isinstance(daily_data['unique_users'], set):
                        daily_data['unique_users'] = set()
        except Exception as e:
            logging.debug(f"Error converting lists to sets: {e}")
    
    def _merge_stats(self, default, existing):
        """Merge existing stats with defaults"""
        result = existing.copy()
        for key, value in default.items():
            if key not in result:
                result[key] = value
            elif isinstance(value, dict) and isinstance(result[key], dict):
                result[key] = self._merge_stats(value, result[key])
        return result
    
    def _save_stats(self, stats=None):
        """Save statistics to JSON file"""
        if stats is None:
            stats = self.stats
        
        try:
            with self._lock:
                stats['metadata']['last_updated'] = datetime.now().isoformat()
                json_stats = self._serialize_for_json(stats)
                
                # Atomic write
                temp_file = str(self.stats_file) + ".tmp"
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(json_stats, f, indent=2, ensure_ascii=False)
                
                # Replace old file
                if os.path.exists(str(self.stats_file)):
                    try:
                        os.remove(str(self.stats_file))
                    except:
                        pass
                
                os.rename(temp_file, str(self.stats_file))
                
        except Exception as e:
            logging.error(f"Error saving stats: {e}")
    
    def _serialize_for_json(self, obj):
        """Convert objects to JSON-serializable format"""
        if isinstance(obj, dict):
            return {key: self._serialize_for_json(value) for key, value in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._serialize_for_json(item) for item in obj]
        elif isinstance(obj, set):
            return list(obj)
        elif hasattr(obj, 'isoformat'):
            return obj.isoformat()
        else:
            return obj
    
    def record_api_call(self, api_type, user_email=None, success=True, 
                       response_time=None, error_message=None, custom_data=None):
        """Record an API call"""
        now = time.time()
        today = datetime.now().strftime('%Y-%m-%d')
        
        with self._lock:
            # Update total calls
            self.stats['metadata']['total_calls_ever'] += 1
            
            # Initialize daily stats if needed
            if today not in self.stats['daily_stats']:
                self.stats['daily_stats'][today] = {
                    'total_calls': 0,
                    'successful_calls': 0,
                    'failed_calls': 0,
                    'unique_users': set(),
                    'api_breakdown': {}
                }
            
            daily = self.stats['daily_stats'][today]
            daily['total_calls'] += 1
            
            if success:
                daily['successful_calls'] += 1
            else:
                daily['failed_calls'] += 1
            
            if user_email:
                if not isinstance(daily['unique_users'], set):
                    daily['unique_users'] = set(daily['unique_users']) if daily['unique_users'] else set()
                daily['unique_users'].add(user_email)
            
            # API breakdown
            if api_type not in daily['api_breakdown']:
                daily['api_breakdown'][api_type] = {'success': 0, 'error': 0}
            daily['api_breakdown'][api_type]['success' if success else 'error'] += 1
            
            # Update API type statistics
            if api_type not in self.stats['api_types']:
                self.stats['api_types'][api_type] = {
                    'total_calls': 0,
                    'successful_calls': 0,
                    'failed_calls': 0,
                    'first_seen': datetime.now().isoformat(),
                    'last_seen': datetime.now().isoformat(),
                    'avg_response_time': 0,
                    'max_response_time': 0,
                    'response_times': [],
                    'recent_errors': []
                }
            
            api_stats = self.stats['api_types'][api_type]
            api_stats['total_calls'] += 1
            api_stats['last_seen'] = datetime.now().isoformat()
            
            if success:
                api_stats['successful_calls'] += 1
            else:
                api_stats['failed_calls'] += 1
                if error_message:
                    error_record = {
                        'timestamp': datetime.now().isoformat(),
                        'message': error_message,
                        'user': user_email
                    }
                    api_stats['recent_errors'].append(error_record)
                    # Keep only last 20 errors
                    if len(api_stats['recent_errors']) > 20:
                        api_stats['recent_errors'] = api_stats['recent_errors'][-20:]
            
            # Response time tracking
            if response_time is not None:
                api_stats['response_times'].append(response_time)
                # Keep only last 100
                if len(api_stats['response_times']) > 100:
                    api_stats['response_times'] = api_stats['response_times'][-100:]
                
                # Update averages
                if api_stats['response_times']:
                    api_stats['avg_response_time'] = sum(api_stats['response_times']) / len(api_stats['response_times'])
                    api_stats['max_response_time'] = max(api_stats['response_times'])
            
            # Update user activity
            if user_email:
                if user_email not in self.stats['user_activity']:
                    self.stats['user_activity'][user_email] = {
                        'first_seen': datetime.now().isoformat(),
                        'last_seen': datetime.now().isoformat(),
                        'total_calls': 0,
                        'api_usage': {}
                    }
                
                user_stats = self.stats['user_activity'][user_email]
                user_stats['last_seen'] = datetime.now().isoformat()
                user_stats['total_calls'] += 1
                
                if api_type not in user_stats['api_usage']:
                    user_stats['api_usage'][api_type] = 0
                user_stats['api_usage'][api_type] += 1
            
            # Update session data
            call_record = {
                'timestamp': now,
                'api_type': api_type,
                'user_email': user_email,
                'success': success,
                'response_time': response_time
            }
            self.session_data['api_calls'].append(call_record)
            
            if user_email:
                self.session_data['active_users'].add(user_email)
            
            if not success and error_message:
                self.session_data['errors'].append({
                    'timestamp': now,
                    'api_type': api_type,
                    'user_email': user_email,
                    'error': error_message
                })
            
            if response_time is not None:
                self.session_data['response_times'][api_type].append(response_time)
        
        # Log the call
        status = "SUCCESS" if success else "ERROR"
        log_msg = f"API [{api_type}] - {status}"
        if response_time:
            log_msg += f" ({response_time:.0f}ms)"
        if user_email:
            log_msg += f" - {user_email}"
        logging.debug(log_msg)
    
    def record_custom_metric(self, metric_name, value, unit="count", user_email=None):
        """Record a custom application metric"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        with self._lock:
            if metric_name not in self.stats['custom_metrics']:
                self.stats['custom_metrics'][metric_name] = {
                    'unit': unit,
                    'total_value': 0,
                    'count': 0,
                    'average': 0,
                    'max_value': value,
                    'min_value': value,
                    'daily_values': {},
                    'recent_values': []
                }
            
            metric = self.stats['custom_metrics'][metric_name]
            metric['total_value'] += value
            metric['count'] += 1
            metric['average'] = metric['total_value'] / metric['count']
            metric['max_value'] = max(metric['max_value'], value)
            metric['min_value'] = min(metric['min_value'], value)
            
            # Daily tracking
            if today not in metric['daily_values']:
                metric['daily_values'][today] = []
            metric['daily_values'][today].append(value)
            
            # Recent values
            metric['recent_values'].append({
                'timestamp': datetime.now().isoformat(),
                'value': value,
                'user': user_email
            })
            if len(metric['recent_values']) > 100:
                metric['recent_values'] = metric['recent_values'][-100:]
    
    def get_stats_summary(self, days_back=7):
        """Get a summary of statistics"""
        with self._lock:
            today = datetime.now().strftime('%Y-%m-%d')
            
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            date_range = []
            current_date = start_date
            while current_date <= end_date:
                date_range.append(current_date.strftime('%Y-%m-%d'))
                current_date += timedelta(days=1)
            
            # Aggregate data
            period_stats = {
                'total_calls': 0,
                'successful_calls': 0,
                'failed_calls': 0,
                'unique_users': set(),
                'api_breakdown': {},
                'daily_trend': []
            }
            
            for date_str in date_range:
                if date_str in self.stats['daily_stats']:
                    daily = self.stats['daily_stats'][date_str]
                    period_stats['total_calls'] += daily['total_calls']
                    period_stats['successful_calls'] += daily['successful_calls']
                    period_stats['failed_calls'] += daily['failed_calls']
                    
                    # Merge unique users
                    if isinstance(daily['unique_users'], (list, set)):
                        period_stats['unique_users'].update(daily['unique_users'])
                    
                    # Merge API breakdown
                    for api_type, counts in daily.get('api_breakdown', {}).items():
                        if api_type not in period_stats['api_breakdown']:
                            period_stats['api_breakdown'][api_type] = {'success': 0, 'error': 0}
                        period_stats['api_breakdown'][api_type]['success'] += counts.get('success', 0)
                        period_stats['api_breakdown'][api_type]['error'] += counts.get('error', 0)
                    
                    # Daily trend
                    success_rate = (daily['successful_calls'] / daily['total_calls'] * 100) if daily['total_calls'] > 0 else 0
                    period_stats['daily_trend'].append({
                        'date': date_str,
                        'calls': daily['total_calls'],
                        'success_rate': success_rate
                    })
                else:
                    period_stats['daily_trend'].append({
                        'date': date_str,
                        'calls': 0,
                        'success_rate': 0
                    })
            
            # Success rate
            success_rate = 0
            if period_stats['total_calls'] > 0:
                success_rate = (period_stats['successful_calls'] / period_stats['total_calls']) * 100
            
            # Session stats
            session_duration = time.time() - self.session_data['start_time']
            hour_ago = time.time() - 3600
            recent_calls = [c for c in self.session_data['api_calls'] if c['timestamp'] > hour_ago]
            
            # Top APIs
            api_totals = {}
            for api_type, stats in self.stats['api_types'].items():
                total = stats['total_calls']
                success = stats['successful_calls']
                api_totals[api_type] = {
                    'total_calls': total,
                    'success_rate': (success / total * 100) if total > 0 else 0,
                    'avg_response_time': stats.get('avg_response_time', 0)
                }
            
            top_apis = sorted(api_totals.items(), key=lambda x: x[1]['total_calls'], reverse=True)[:5]
            
            # Recent errors
            recent_errors = []
            for api_type, stats in self.stats['api_types'].items():
                for error in stats.get('recent_errors', [])[-5:]:
                    recent_errors.append({
                        'api_type': api_type,
                        'timestamp': error['timestamp'],
                        'message': error['message'],
                        'user': error.get('user', 'Unknown')
                    })
            recent_errors.sort(key=lambda x: x['timestamp'], reverse=True)
            recent_errors = recent_errors[:10]
            
            # Performance summary
            performance_summary = {}
            for api_type, times in self.session_data['response_times'].items():
                if times:
                    performance_summary[api_type] = {
                        'avg_response_time': sum(times) / len(times),
                        'max_response_time': max(times),
                        'min_response_time': min(times),
                        'call_count': len(times)
                    }
            
            return {
                'overview': {
                    'total_calls_ever': self.stats['metadata']['total_calls_ever'],
                    'period_calls': period_stats['total_calls'],
                    'today_calls': self.stats['daily_stats'].get(today, {}).get('total_calls', 0),
                    'success_rate': round(success_rate, 1),
                    'unique_users_period': len(period_stats['unique_users']),
                    'api_types_count': len(self.stats['api_types'])
                },
                'session': {
                    'duration_minutes': round(session_duration / 60, 1),
                    'calls_this_session': len(self.session_data['api_calls']),
                    'errors_this_session': len(self.session_data['errors']),
                    'active_users': len(self.session_data['active_users']),
                    'calls_last_hour': len(recent_calls)
                },
                'api_breakdown': period_stats['api_breakdown'],
                'top_apis': top_apis,
                'daily_trend': period_stats['daily_trend'],
                'recent_errors': recent_errors,
                'performance': performance_summary,
                'custom_metrics': self._get_custom_metrics_summary()
            }
    
    def _get_custom_metrics_summary(self):
        """Get summary of custom metrics"""
        summary = {}
        for metric_name, metric_data in self.stats['custom_metrics'].items():
            summary[metric_name] = {
                'current_average': round(metric_data['average'], 2),
                'total_value': metric_data['total_value'],
                'count': metric_data['count'],
                'max_value': metric_data['max_value'],
                'min_value': metric_data['min_value'],
                'unit': metric_data['unit']
            }
        return summary
    
    def get_user_activity(self, limit=50):
        """Get user activity data for dashboard display"""
        try:
            user_list = []
            
            with self._lock:
                now = datetime.now()
                
                for email, user_data in self.stats.get('user_activity', {}).items():
                    # Calculate days since last seen
                    last_seen_str = user_data.get('last_seen', '')
                    if last_seen_str:
                        try:
                            last_seen_dt = datetime.fromisoformat(last_seen_str.replace('Z', '+00:00'))
                            days_since = (now - last_seen_dt).days
                        except:
                            days_since = -1
                    else:
                        days_since = -1
                    
                    activity_record = {
                        'email': email,
                        'first_seen': user_data.get('first_seen', ''),
                        'last_seen': user_data.get('last_seen', ''),
                        'total_calls': user_data.get('total_calls', 0),
                        'days_since_last_seen': days_since,
                        'api_usage': user_data.get('api_usage', {})
                    }
                    
                    user_list.append(activity_record)
                
                # Sort by last seen (most recent first)
                user_list.sort(key=lambda x: x.get('last_seen', ''), reverse=True)
                
                # Limit results
                if limit and len(user_list) > limit:
                    user_list = user_list[:limit]
            
            return user_list
            
        except Exception as e:
            logging.error(f"Error getting user activity: {e}")
            return []
    
    def export_data(self, format="json", days_back=30):
        """Export monitoring data"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"api_monitoring_export_{timestamp}.{format}"
            file_path = self.config_manager.get_export_file_path(filename)
            
            export_data = {
                'metadata': {
                    'export_timestamp': datetime.now().isoformat(),
                    'app_name': self.config_manager.app_name,
                    'days_included': days_back,
                    'total_calls': self.stats['metadata']['total_calls_ever']
                },
                'summary': self.get_stats_summary(days_back),
                'api_types': self.stats['api_types'],
                'custom_metrics': self.stats['custom_metrics']
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
            
            logging.info(f"Data exported to: {file_path}")
            return str(file_path)
            
        except Exception as e:
            logging.error(f"Error exporting data: {e}")
            return None
    
    def cleanup_old_data(self):
        """Clean up old data"""
        retention_config = self.config_manager.get_retention_config()
        
        if not retention_config['auto_cleanup']:
            return
        
        try:
            with self._lock:
                cutoff_date = datetime.now() - timedelta(days=retention_config['detailed_days'])
                cutoff_str = cutoff_date.strftime('%Y-%m-%d')
                
                # Remove old daily stats
                dates_to_remove = [date_str for date_str in self.stats['daily_stats'] 
                                 if date_str < cutoff_str]
                
                for date_str in dates_to_remove:
                    del self.stats['daily_stats'][date_str]
                
                self._save_stats()
                logging.info(f"Cleanup completed. Removed {len(dates_to_remove)} days of old data.")
                
        except Exception as e:
            logging.error(f"Error during cleanup: {e}")
    
    def get_system_health(self):
        """Get system health indicators"""
        summary = self.get_stats_summary(1)
        
        error_rate = 0
        if summary['overview']['period_calls'] > 0:
            failed_calls = summary['overview']['period_calls'] - (summary['overview']['period_calls'] * summary['overview']['success_rate'] / 100)
            error_rate = (failed_calls / summary['overview']['period_calls']) * 100
        
        avg_response_time = 0
        if summary['performance']:
            times = [perf['avg_response_time'] for perf in summary['performance'].values()]
            avg_response_time = sum(times) / len(times) if times else 0
        
        health_status = "healthy"
        if error_rate > 10:
            health_status = "critical"
        elif error_rate > 5 or avg_response_time > 5000:
            health_status = "warning"
        
        return {
            'status': health_status,
            'error_rate': round(error_rate, 2),
            'avg_response_time': round(avg_response_time, 0),
            'calls_last_24h': summary['overview']['period_calls'],
            'active_users': summary['session']['active_users'],
            'storage_info': self.config_manager.get_storage_info()
        }
    
    def _start_auto_save_thread(self):
        """Start a thread that saves stats periodically"""
        def auto_save_worker():
            while True:
                try:
                    time.sleep(30)  # Save every 30 seconds
                    self._save_stats()
                except Exception as e:
                    logging.error(f"Auto-save error: {e}")
        
        save_thread = threading.Thread(target=auto_save_worker, daemon=True)
        save_thread.start()