# api_monitor_module/ui/widgets.py
"""
Dashboard UI Widgets - Reusable components for the monitoring dashboard
"""

import tkinter as tk
import customtkinter as ctk
from datetime import datetime, timedelta

class StatsPanel(ctk.CTkFrame):
    """Top panel showing real-time statistics"""
    
    def __init__(self, parent, tracker):
        super().__init__(parent, fg_color="#2a2a2a", height=80)
        self.tracker = tracker
        self.grid_propagate(False)
        
        self.create_widgets()
    
    def create_widgets(self):
        """Create the stats widgets"""
        # Header
        header = ctk.CTkLabel(
            self,
            text="📊 Real-Time Statistics",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#00bfff"
        )
        header.pack(pady=(10, 5))
        
        # Stats container
        stats_container = ctk.CTkFrame(self, fg_color="transparent")
        stats_container.pack(fill="x", expand=True, padx=20, pady=(0, 10))
        
        # Configure grid for 4 columns
        for i in range(4):
            stats_container.grid_columnconfigure(i, weight=1)
        
        # Total calls
        self.total_calls_frame = self.create_stat_widget(
            stats_container, "Total API Calls", "0", "#00bfff"
        )
        self.total_calls_frame.grid(row=0, column=0, padx=10, sticky="ew")
        
        # Today's calls
        self.today_calls_frame = self.create_stat_widget(
            stats_container, "Today", "0", "#28a745"
        )
        self.today_calls_frame.grid(row=0, column=1, padx=10, sticky="ew")
        
        # Success rate
        self.success_rate_frame = self.create_stat_widget(
            stats_container, "Success Rate", "0%", "#ffc107"
        )
        self.success_rate_frame.grid(row=0, column=2, padx=10, sticky="ew")
        
        # Active users
        self.active_users_frame = self.create_stat_widget(
            stats_container, "Active Users", "0", "#17a2b8"
        )
        self.active_users_frame.grid(row=0, column=3, padx=10, sticky="ew")
    
    def create_stat_widget(self, parent, title, value, color):
        """Create a single stat widget"""
        frame = ctk.CTkFrame(parent, fg_color="#1a1a1a", corner_radius=8)
        
        # Title
        title_label = ctk.CTkLabel(
            frame,
            text=title,
            font=ctk.CTkFont(size=10),
            text_color="#aaa"
        )
        title_label.pack(pady=(8, 2))
        
        # Value
        value_label = ctk.CTkLabel(
            frame,
            text=value,
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=color
        )
        value_label.pack(pady=(0, 8))
        
        # Store reference to value label for updates
        frame.value_label = value_label
        
        return frame
    
    def update_data(self, stats_summary):
        """Update the panel with new data"""
        try:
            overview = stats_summary.get('overview', {})
            session = stats_summary.get('session', {})
            
            # Update values
            self.total_calls_frame.value_label.configure(
                text=f"{overview.get('total_calls_ever', 0):,}"
            )
            
            self.today_calls_frame.value_label.configure(
                text=f"{overview.get('today_calls', 0):,}"
            )
            
            success_rate = overview.get('success_rate', 0)
            self.success_rate_frame.value_label.configure(
                text=f"{success_rate:.1f}%"
            )
            
            # Update success rate color based on value
            if success_rate >= 95:
                color = "#28a745"  # Green
            elif success_rate >= 90:
                color = "#ffc107"  # Yellow
            else:
                color = "#dc3545"  # Red
            self.success_rate_frame.value_label.configure(text_color=color)
            
            self.active_users_frame.value_label.configure(
                text=f"{session.get('active_users', 0)}"
            )
            
        except Exception as e:
            print(f"Error updating stats panel: {e}")


class APIBreakdownPanel(ctk.CTkFrame):
    """Panel showing API call breakdown by type"""
    
    def __init__(self, parent, tracker):
        super().__init__(parent, fg_color="#2a2a2a")
        self.tracker = tracker
        
        self.create_widgets()
    
    def create_widgets(self):
        """Create the API breakdown widgets"""
        # Header
        header = ctk.CTkLabel(
            self,
            text="🔧 API Breakdown",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#00bfff"
        )
        header.pack(pady=(10, 5))
        
        # Scrollable frame for API list
        self.api_list_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="#1a1a1a",
            corner_radius=8
        )
        self.api_list_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
    
    def update_data(self, stats_summary):
        """Update the panel with new API breakdown data"""
        try:
            # Clear existing widgets
            for widget in self.api_list_frame.winfo_children():
                widget.destroy()
            
            api_breakdown = stats_summary.get('api_breakdown', {})
            top_apis = stats_summary.get('top_apis', [])
            
            if not api_breakdown and not top_apis:
                # No data available
                no_data_label = ctk.CTkLabel(
                    self.api_list_frame,
                    text="No API calls recorded yet.\nData will appear after API usage.",
                    font=ctk.CTkFont(size=12),
                    text_color="#aaa",
                    justify="center"
                )
                no_data_label.pack(pady=20)
                return
            
            # Use top_apis if available, otherwise use api_breakdown
            if top_apis:
                for api_type, api_data in top_apis:
                    total_calls = api_data.get('total_calls', 0)
                    success_rate = api_data.get('success_rate', 0)
                    avg_response_time = api_data.get('avg_response_time', 0)
                    
                    self.create_api_item(
                        api_type, total_calls, success_rate, avg_response_time
                    )
            else:
                # Fallback to api_breakdown
                for api_type, counts in api_breakdown.items():
                    success = counts.get('success', 0)
                    error = counts.get('error', 0)
                    total = success + error
                    success_rate = (success / total * 100) if total > 0 else 0
                    
                    self.create_api_item(api_type, total, success_rate, 0)
                    
        except Exception as e:
            print(f"Error updating API breakdown panel: {e}")
    
    def create_api_item(self, api_type, total_calls, success_rate, avg_response_time):
        """Create a single API item widget"""
        item_frame = ctk.CTkFrame(self.api_list_frame, fg_color="#2a2a2a", corner_radius=6)
        item_frame.pack(fill="x", padx=5, pady=3)
        
        # Top row - API type and total calls
        top_row = ctk.CTkFrame(item_frame, fg_color="transparent")
        top_row.pack(fill="x", padx=10, pady=(8, 4))
        
        api_label = ctk.CTkLabel(
            top_row,
            text=api_type.replace('_', ' ').title(),
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#fff"
        )
        api_label.pack(side="left")
        
        calls_label = ctk.CTkLabel(
            top_row,
            text=f"{total_calls:,} calls",
            font=ctk.CTkFont(size=11),
            text_color="#aaa"
        )
        calls_label.pack(side="right")
        
        # Bottom row - Success rate and response time
        bottom_row = ctk.CTkFrame(item_frame, fg_color="transparent")
        bottom_row.pack(fill="x", padx=10, pady=(0, 8))
        
        # Success rate with color coding
        if success_rate >= 95:
            rate_color = "#28a745"
            rate_icon = "🟢"
        elif success_rate >= 90:
            rate_color = "#ffc107"
            rate_icon = "🟡"
        else:
            rate_color = "#dc3545"
            rate_icon = "🔴"
        
        success_label = ctk.CTkLabel(
            bottom_row,
            text=f"{rate_icon} {success_rate:.1f}%",
            font=ctk.CTkFont(size=10),
            text_color=rate_color
        )
        success_label.pack(side="left")
        
        # Response time (if available)
        if avg_response_time > 0:
            if avg_response_time < 1000:  # Less than 1 second
                time_color = "#28a745"
                time_icon = "⚡"
            elif avg_response_time < 5000:  # Less than 5 seconds
                time_color = "#ffc107"
                time_icon = "⏱️"
            else:
                time_color = "#dc3545"
                time_icon = "🐌"
            
            time_label = ctk.CTkLabel(
                bottom_row,
                text=f"{time_icon} {avg_response_time:.0f}ms",
                font=ctk.CTkFont(size=10),
                text_color=time_color
            )
            time_label.pack(side="right")


class UserActivityPanel(ctk.CTkFrame):
    """Panel showing user activity information"""
    
    def __init__(self, parent, tracker):
        super().__init__(parent, fg_color="#2a2a2a")
        self.tracker = tracker
        
        self.create_widgets()
    
    def create_widgets(self):
        """Create the user activity widgets"""
        # Header
        header = ctk.CTkLabel(
            self,
            text="👥 User Activity",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#00bfff"
        )
        header.pack(pady=(10, 5))
        
        # Scrollable frame for user list
        self.user_list_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="#1a1a1a",
            corner_radius=8
        )
        self.user_list_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
    
    def update_data(self, user_activity):
        """Update the panel with new user activity data"""
        try:
            # Clear existing widgets
            for widget in self.user_list_frame.winfo_children():
                widget.destroy()
            
            if not user_activity:
                # No user data available
                no_data_label = ctk.CTkLabel(
                    self.user_list_frame,
                    text="No user activity recorded yet.\nActivity will appear after user logins.",
                    font=ctk.CTkFont(size=12),
                    text_color="#aaa",
                    justify="center"
                )
                no_data_label.pack(pady=20)
                return
            
            # Show recent users (last 10)
            recent_users = user_activity[:10] if len(user_activity) > 10 else user_activity
            
            for user_data in recent_users:
                self.create_user_item(user_data)
                
        except Exception as e:
            print(f"Error updating user activity panel: {e}")
    
    def create_user_item(self, user_data):
        """Create a single user activity item"""
        item_frame = ctk.CTkFrame(self.user_list_frame, fg_color="#2a2a2a", corner_radius=6)
        item_frame.pack(fill="x", padx=5, pady=3)
        
        # Email and status
        top_row = ctk.CTkFrame(item_frame, fg_color="transparent")
        top_row.pack(fill="x", padx=10, pady=(8, 4))
        
        # Email (truncated if too long)
        email = user_data.get('email', 'Unknown')
        if len(email) > 25:
            display_email = email[:22] + "..."
        else:
            display_email = email
        
        email_label = ctk.CTkLabel(
            top_row,
            text=display_email,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#fff"
        )
        email_label.pack(side="left")
        
        # Activity status
        days_since = user_data.get('days_since_last_seen', 0)
        if days_since == 0:
            status_text = "🟢 Active"
            status_color = "#28a745"
        elif days_since <= 1:
            status_text = "🟡 Recent"
            status_color = "#ffc107"
        else:
            status_text = f"⚪ {days_since}d ago"
            status_color = "#6c757d"
        
        status_label = ctk.CTkLabel(
            top_row,
            text=status_text,
            font=ctk.CTkFont(size=10),
            text_color=status_color
        )
        status_label.pack(side="right")
        
        # Call count and last seen
        bottom_row = ctk.CTkFrame(item_frame, fg_color="transparent")
        bottom_row.pack(fill="x", padx=10, pady=(0, 8))
        
        total_calls = user_data.get('total_calls', 0)
        calls_label = ctk.CTkLabel(
            bottom_row,
            text=f"{total_calls:,} calls",
            font=ctk.CTkFont(size=10),
            text_color="#aaa"
        )
        calls_label.pack(side="left")
        
        # Last seen time
        try:
            last_seen = user_data.get('last_seen', '')
            if last_seen:
                dt = datetime.fromisoformat(last_seen.replace('Z', '+00:00'))
                formatted_time = dt.strftime("%m/%d %H:%M")
            else:
                formatted_time = "Unknown"
        except:
            formatted_time = "Unknown"
        
        time_label = ctk.CTkLabel(
            bottom_row,
            text=formatted_time,
            font=ctk.CTkFont(size=10),
            text_color="#aaa"
        )
        time_label.pack(side="right")


class SystemHealthPanel(ctk.CTkFrame):
    """Panel showing system health information"""
    
    def __init__(self, parent, tracker, config_manager):
        super().__init__(parent, fg_color="#2a2a2a", height=100)
        self.tracker = tracker
        self.config_manager = config_manager
        self.grid_propagate(False)
        
        self.create_widgets()
    
    def create_widgets(self):
        """Create the system health widgets"""
        # Header
        header = ctk.CTkLabel(
            self,
            text="🏥 System Health",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#00bfff"
        )
        header.pack(pady=(10, 5))
        
        # Health indicators container
        health_container = ctk.CTkFrame(self, fg_color="transparent")
        health_container.pack(fill="x", expand=True, padx=20, pady=(0, 10))
        
        # Configure grid for 4 columns
        for i in range(4):
            health_container.grid_columnconfigure(i, weight=1)
        
        # Error rate
        self.error_rate_frame = self.create_health_widget(
            health_container, "Error Rate", "0%", "#28a745"
        )
        self.error_rate_frame.grid(row=0, column=0, padx=5, sticky="ew")
        
        # Response time
        self.response_time_frame = self.create_health_widget(
            health_container, "Avg Response", "0ms", "#28a745"
        )
        self.response_time_frame.grid(row=0, column=1, padx=5, sticky="ew")
        
        # Storage usage
        self.storage_frame = self.create_health_widget(
            health_container, "Storage", "0 MB", "#17a2b8"
        )
        self.storage_frame.grid(row=0, column=2, padx=5, sticky="ew")
        
        # Data retention
        self.retention_frame = self.create_health_widget(
            health_container, "Retention", "30d", "#6c757d"
        )
        self.retention_frame.grid(row=0, column=3, padx=5, sticky="ew")
    
    def create_health_widget(self, parent, title, value, color):
        """Create a single health indicator widget"""
        frame = ctk.CTkFrame(parent, fg_color="#1a1a1a", corner_radius=6)
        
        # Title
        title_label = ctk.CTkLabel(
            frame,
            text=title,
            font=ctk.CTkFont(size=9),
            text_color="#aaa"
        )
        title_label.pack(pady=(6, 2))
        
        # Value
        value_label = ctk.CTkLabel(
            frame,
            text=value,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=color
        )
        value_label.pack(pady=(0, 6))
        
        # Store reference to value label for updates
        frame.value_label = value_label
        
        return frame
    
    def update_data(self, system_health):
        """Update the panel with new system health data"""
        try:
            # Error rate
            error_rate = system_health.get('error_rate', 0)
            self.error_rate_frame.value_label.configure(text=f"{error_rate:.1f}%")
            
            # Color code error rate
            if error_rate <= 1:
                error_color = "#28a745"  # Green
            elif error_rate <= 5:
                error_color = "#ffc107"  # Yellow
            else:
                error_color = "#dc3545"  # Red
            self.error_rate_frame.value_label.configure(text_color=error_color)
            
            # Response time
            avg_response = system_health.get('avg_response_time', 0)
            if avg_response > 0:
                self.response_time_frame.value_label.configure(text=f"{avg_response:.0f}ms")
                
                # Color code response time
                if avg_response < 1000:  # Less than 1 second
                    response_color = "#28a745"  # Green
                elif avg_response < 5000:  # Less than 5 seconds
                    response_color = "#ffc107"  # Yellow
                else:
                    response_color = "#dc3545"  # Red
                self.response_time_frame.value_label.configure(text_color=response_color)
            else:
                self.response_time_frame.value_label.configure(text="N/A")
            
            # Storage usage
            storage_info = system_health.get('storage_info', {})
            if 'total_size_mb' in storage_info:
                size_mb = storage_info['total_size_mb']
                if size_mb < 1:
                    storage_text = f"{size_mb*1000:.0f} KB"
                elif size_mb < 1000:
                    storage_text = f"{size_mb:.1f} MB"
                else:
                    storage_text = f"{size_mb/1000:.1f} GB"
                
                self.storage_frame.value_label.configure(text=storage_text)
                
                # Color code storage (green if under 100MB, yellow if under 500MB, red if over)
                if size_mb < 100:
                    storage_color = "#28a745"
                elif size_mb < 500:
                    storage_color = "#ffc107"
                else:
                    storage_color = "#dc3545"
                self.storage_frame.value_label.configure(text_color=storage_color)
            
            # Data retention
            retention_config = self.config_manager.get_retention_config()
            retention_days = retention_config.get('detailed_days', 30)
            self.retention_frame.value_label.configure(text=f"{retention_days}d")
            
        except Exception as e:
            print(f"Error updating system health panel: {e}")