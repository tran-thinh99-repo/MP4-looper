# api_monitor_module/ui/dashboard.py
"""
Admin Dashboard - Main monitoring interface
"""

import tkinter as tk
import customtkinter as ctk
import threading
import time
import logging
from datetime import datetime, timedelta
from tkinter import messagebox, filedialog
from .widgets import StatsPanel, APIBreakdownPanel, UserActivityPanel, SystemHealthPanel

class AdminDashboard(ctk.CTkToplevel):
    """Main admin dashboard window"""
    
    def __init__(self, tracker, config_manager, parent_window=None):
        super().__init__(parent_window)
        
        self.tracker = tracker
        self.config_manager = config_manager
        self.parent_window = parent_window
        
        # UI state
        self.is_refreshing = False
        self.auto_refresh_enabled = False
        self.refresh_interval = 30  # seconds
        self.refresh_thread = None
        
        # Setup window
        self.setup_window()
        
        # Create UI components
        self.create_ui()
        
        # Load initial data
        self.refresh_data()
        
        # Position window
        self.position_window()
    
    def setup_window(self):
        """Configure the main window"""
        self.title("API Monitoring Dashboard - MP4 Looper")
        self.geometry("1000x700")
        self.minsize(800, 600)
        
        # Set icon if available
        try:
            from paths import get_resource_path
            icon_path = get_resource_path("mp4_looper_icon.ico")
            self.iconbitmap(default=icon_path)
        except:
            pass
        
        # Configure grid weights
        self.grid_rowconfigure(1, weight=1)  # Main content area
        self.grid_columnconfigure(0, weight=1)
        
        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def create_ui(self):
        """Create the main UI layout"""
        # Top toolbar
        self.create_toolbar()
        
        # Main content area
        self.create_main_content()
        
        # Bottom status bar
        self.create_status_bar()
    
    def create_toolbar(self):
        """Create the top toolbar with controls"""
        toolbar_frame = ctk.CTkFrame(self, height=60, fg_color="#2a2a2a")
        toolbar_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        toolbar_frame.grid_propagate(False)
        
        # Left side - Title and status
        left_frame = ctk.CTkFrame(toolbar_frame, fg_color="transparent")
        left_frame.pack(side="left", fill="y", padx=10)
        
        title_label = ctk.CTkLabel(
            left_frame, 
            text="📊 API Monitoring Dashboard",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#00bfff"
        )
        title_label.pack(side="top", pady=(10, 0))
        
        self.status_indicator = ctk.CTkLabel(
            left_frame,
            text="🟢 System Healthy",
            font=ctk.CTkFont(size=12),
            text_color="#28a745"
        )
        self.status_indicator.pack(side="top", pady=(0, 10))
        
        # Right side - Controls
        controls_frame = ctk.CTkFrame(toolbar_frame, fg_color="transparent")
        controls_frame.pack(side="right", fill="y", padx=10, pady=10)
        
        # Refresh button
        self.refresh_button = ctk.CTkButton(
            controls_frame,
            text="🔄 Refresh",
            command=self.refresh_data,
            width=100,
            fg_color="#17a2b8",
            hover_color="#138496"
        )
        self.refresh_button.pack(side="left", padx=5)
        
        # Auto-refresh toggle
        self.auto_refresh_var = tk.BooleanVar()
        self.auto_refresh_checkbox = ctk.CTkCheckBox(
            controls_frame,
            text="Auto-refresh",
            variable=self.auto_refresh_var,
            command=self.toggle_auto_refresh
        )
        self.auto_refresh_checkbox.pack(side="left", padx=10)
        
        # Export button
        export_button = ctk.CTkButton(
            controls_frame,
            text="📤 Export",
            command=self.export_data,
            width=100,
            fg_color="#28a745",
            hover_color="#218838"
        )
        export_button.pack(side="left", padx=5)
        
        # Settings button
        settings_button = ctk.CTkButton(
            controls_frame,
            text="⚙️ Settings",
            command=self.show_settings,
            width=100,
            fg_color="#6c757d",
            hover_color="#5a6268"
        )
        settings_button.pack(side="left", padx=5)
    
    def create_main_content(self):
        """Create the main content panels"""
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        
        # Configure grid weights for responsive layout
        main_frame.grid_rowconfigure(0, weight=0)  # Real-time stats (fixed height)
        main_frame.grid_rowconfigure(1, weight=1)  # Main panels (expandable)
        main_frame.grid_rowconfigure(2, weight=0)  # System health (fixed height)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Top row - Real-time stats panel
        self.stats_panel = StatsPanel(main_frame, self.tracker)
        self.stats_panel.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        # Middle row - Three column layout
        middle_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        middle_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 10))
        
        # Configure middle frame columns
        middle_frame.grid_columnconfigure(0, weight=1)  # API Breakdown
        middle_frame.grid_columnconfigure(1, weight=1)  # User Activity
        middle_frame.grid_columnconfigure(2, weight=1)  # Performance/Errors
        middle_frame.grid_rowconfigure(0, weight=1)
        
        # API Breakdown Panel (Left)
        self.api_panel = APIBreakdownPanel(middle_frame, self.tracker)
        self.api_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        
        # User Activity Panel (Center)
        self.user_panel = UserActivityPanel(middle_frame, self.tracker)
        self.user_panel.grid(row=0, column=1, sticky="nsew", padx=5)
        
        # Performance & Errors Panel (Right)
        self.performance_panel = self.create_performance_panel(middle_frame)
        self.performance_panel.grid(row=0, column=2, sticky="nsew", padx=(5, 0))
        
        # Bottom row - System health panel
        self.health_panel = SystemHealthPanel(main_frame, self.tracker, self.config_manager)
        self.health_panel.grid(row=2, column=0, sticky="ew")
    
    def create_performance_panel(self, parent):
        """Create the performance and errors panel"""
        panel = ctk.CTkFrame(parent, fg_color="#2a2a2a")
        
        # Header
        header = ctk.CTkLabel(
            panel,
            text="📈 Performance & Errors",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#00bfff"
        )
        header.pack(pady=(10, 5))
        
        # Create notebook for tabs
        self.performance_notebook = ctk.CTkTabview(panel)
        self.performance_notebook.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Performance tab
        perf_tab = self.performance_notebook.add("Performance")
        self.performance_text = ctk.CTkTextbox(
            perf_tab,
            wrap="word",
            font=ctk.CTkFont(family="Courier", size=11)
        )
        self.performance_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Errors tab
        errors_tab = self.performance_notebook.add("Recent Errors")
        self.errors_text = ctk.CTkTextbox(
            errors_tab,
            wrap="word",
            font=ctk.CTkFont(family="Courier", size=11)
        )
        self.errors_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Rate Limits tab
        limits_tab = self.performance_notebook.add("Rate Limits")
        self.limits_text = ctk.CTkTextbox(
            limits_tab,
            wrap="word",
            font=ctk.CTkFont(family="Courier", size=11)
        )
        self.limits_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        return panel
    
    def create_status_bar(self):
        """Create the bottom status bar"""
        status_frame = ctk.CTkFrame(self, height=30, fg_color="#1a1a1a")
        status_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(5, 10))
        status_frame.grid_propagate(False)
        
        # Left side - Last update time
        self.last_update_label = ctk.CTkLabel(
            status_frame,
            text="Last updated: Never",
            font=ctk.CTkFont(size=10),
            text_color="#aaa"
        )
        self.last_update_label.pack(side="left", padx=10, pady=5)
        
        # Right side - Data retention info
        retention_config = self.config_manager.get_retention_config()
        retention_text = f"Retention: {retention_config['detailed_days']}d detailed, {retention_config['summary_months']}m summary"
        retention_label = ctk.CTkLabel(
            status_frame,
            text=retention_text,
            font=ctk.CTkFont(size=10),
            text_color="#aaa"
        )
        retention_label.pack(side="right", padx=10, pady=5)
    
    def refresh_data(self):
        """Refresh all dashboard data"""
        if self.is_refreshing:
            return
        
        self.is_refreshing = True
        self.refresh_button.configure(state="disabled", text="Refreshing...")
        
        def refresh_worker():
            try:
                # Force clear any cached data first
                if hasattr(self.tracker, '_stats_cache'):
                    self.tracker._stats_cache = None
                
                # Get fresh data with immediate stats refresh
                if hasattr(self.tracker, '_save_stats'):
                    self.tracker._save_stats()  # Force save any pending data
                
                stats_summary = self.tracker.get_stats_summary()
                user_activity = self.tracker.get_user_activity()
                system_health = self.tracker.get_system_health()
                
                # Debug log the stats we got
                logging.info(f"Dashboard refresh - Total calls: {stats_summary.get('overview', {}).get('total_calls_ever', 'N/A')}")
                logging.info(f"Dashboard refresh - Session calls: {stats_summary.get('session', {}).get('calls_this_session', 'N/A')}")
                
                # Update UI on main thread
                self.after(0, lambda: self._update_ui_data(stats_summary, user_activity, system_health))
                
            except Exception as e:
                logging.error(f"Error refreshing dashboard data: {e}")
                import traceback
                logging.error(f"Refresh error traceback: {traceback.format_exc()}")
                self.after(0, lambda: self._show_refresh_error(str(e)))
            finally:
                self.after(0, self._refresh_complete)
        
        # Run refresh in background thread
        refresh_thread = threading.Thread(target=refresh_worker, daemon=True)
        refresh_thread.start()
    
    def _update_ui_data(self, stats_summary, user_activity, system_health):
        """Update UI with new data (runs on main thread)"""
        try:
            # Update individual panels
            self.stats_panel.update_data(stats_summary)
            self.api_panel.update_data(stats_summary)
            self.user_panel.update_data(user_activity)
            self.health_panel.update_data(system_health)
            
            # Update performance panel
            self._update_performance_data(stats_summary)
            
            # Update status indicator
            self._update_status_indicator(system_health)
            
            # Update last refresh time
            current_time = datetime.now().strftime("%H:%M:%S")
            self.last_update_label.configure(text=f"Last updated: {current_time}")
            
        except Exception as e:
            logging.error(f"Error updating UI data: {e}")
    
    def _update_performance_data(self, stats_summary):
        """Update the performance panel with current data"""
        try:
            # Performance data
            perf_text = "Response Time Analysis:\n" + "="*30 + "\n\n"
            
            if stats_summary.get('performance'):
                for api_type, perf_data in stats_summary['performance'].items():
                    avg_time = perf_data.get('avg_response_time', 0)
                    max_time = perf_data.get('max_response_time', 0)
                    min_time = perf_data.get('min_response_time', 0)
                    call_count = perf_data.get('call_count', 0)
                    
                    perf_text += f"{api_type}:\n"
                    perf_text += f"  Average: {avg_time:.0f}ms\n"
                    perf_text += f"  Range: {min_time:.0f}ms - {max_time:.0f}ms\n"
                    perf_text += f"  Calls: {call_count}\n\n"
            else:
                perf_text += "No performance data available yet.\n"
                perf_text += "Performance metrics will appear after API calls are made."
            
            self.performance_text.delete("1.0", "end")
            self.performance_text.insert("1.0", perf_text)
            
            # Recent errors
            errors_text = "Recent API Errors:\n" + "="*25 + "\n\n"
            
            recent_errors = stats_summary.get('recent_errors', [])
            if recent_errors:
                for i, error in enumerate(recent_errors[:10], 1):  # Show last 10
                    timestamp = error.get('timestamp', 'Unknown')
                    api_type = error.get('api_type', 'Unknown')
                    message = error.get('message', 'No message')
                    user = error.get('user', 'Unknown')
                    
                    # Format timestamp
                    try:
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        formatted_time = dt.strftime("%H:%M:%S")
                    except:
                        formatted_time = timestamp
                    
                    errors_text += f"{i}. [{formatted_time}] {api_type}\n"
                    errors_text += f"   User: {user}\n"
                    errors_text += f"   Error: {message}\n\n"
            else:
                errors_text += "No recent errors! 🎉\n"
                errors_text += "Your API calls are running smoothly."
            
            self.errors_text.delete("1.0", "end")
            self.errors_text.insert("1.0", errors_text)
            
            # Rate limits (if rate limiter is available)
            limits_text = "Rate Limiting Status:\n" + "="*25 + "\n\n"
            
            try:
                # Try to get rate limit stats from the rate limiter
                rate_stats = self.tracker.config_manager.get('rate_limits', {})
                if rate_stats:
                    limits_text += f"Global Rate Limiting: {'Enabled' if rate_stats.get('global_enabled', False) else 'Disabled'}\n\n"
                    
                    default_limits = rate_stats.get('default_limits', {})
                    if default_limits:
                        limits_text += "Default Limits:\n"
                        for api_type, limits in default_limits.items():
                            max_calls = limits.get('max_calls', 'N/A')
                            window = limits.get('window_minutes', 'N/A')
                            limits_text += f"  {api_type}: {max_calls} calls per {window} minutes\n"
                    else:
                        limits_text += "No rate limits configured.\n"
                else:
                    limits_text += "Rate limiting configuration not available.\n"
                    
            except Exception as e:
                limits_text += f"Error loading rate limit data: {e}\n"
            
            self.limits_text.delete("1.0", "end")
            self.limits_text.insert("1.0", limits_text)
            
        except Exception as e:
            logging.error(f"Error updating performance data: {e}")
    
    def _update_status_indicator(self, system_health):
        """Update the system status indicator"""
        try:
            status = system_health.get('status', 'unknown')
            error_rate = system_health.get('error_rate', 0)
            
            if status == 'healthy':
                self.status_indicator.configure(
                    text="🟢 System Healthy",
                    text_color="#28a745"
                )
            elif status == 'warning':
                self.status_indicator.configure(
                    text="🟡 System Warning",
                    text_color="#ffc107"
                )
            elif status == 'critical':
                self.status_indicator.configure(
                    text="🔴 System Critical",
                    text_color="#dc3545"
                )
            else:
                self.status_indicator.configure(
                    text="⚪ Status Unknown",
                    text_color="#6c757d"
                )
        except Exception as e:
            logging.error(f"Error updating status indicator: {e}")
    
    def _show_refresh_error(self, error_message):
        """Show error message for refresh failure"""
        messagebox.showerror(
            "Refresh Error",
            f"Failed to refresh dashboard data:\n\n{error_message}",
            parent=self
        )
    
    def _refresh_complete(self):
        """Called when refresh is complete"""
        self.is_refreshing = False
        self.refresh_button.configure(state="normal", text="🔄 Refresh")
    
    def toggle_auto_refresh(self):
        """Toggle auto-refresh functionality"""
        self.auto_refresh_enabled = self.auto_refresh_var.get()
        
        if self.auto_refresh_enabled:
            self.start_auto_refresh()
        else:
            self.stop_auto_refresh()
    
    def start_auto_refresh(self):
        """Start auto-refresh in background thread"""
        if self.refresh_thread and self.refresh_thread.is_alive():
            return
        
        def auto_refresh_worker():
            while self.auto_refresh_enabled and self.winfo_exists():
                try:
                    time.sleep(self.refresh_interval)
                    if self.auto_refresh_enabled and not self.is_refreshing:
                        self.after(0, self.refresh_data)
                except Exception as e:
                    logging.error(f"Auto-refresh error: {e}")
                    break
        
        self.refresh_thread = threading.Thread(target=auto_refresh_worker, daemon=True)
        self.refresh_thread.start()
        
        logging.info(f"Auto-refresh started (every {self.refresh_interval} seconds)")
    
    def stop_auto_refresh(self):
        """Stop auto-refresh"""
        self.auto_refresh_enabled = False
        logging.info("Auto-refresh stopped")
    
    def export_data(self):
        """Export monitoring data"""
        try:
            # Ask user for export format
            export_format = messagebox.askyesno(
                "Export Format",
                "Choose export format:\n\nYes = JSON (detailed)\nNo = CSV (summary)",
                parent=self
            )
            
            format_str = "json" if export_format else "csv"
            
            # Export data
            self.refresh_button.configure(state="disabled", text="Exporting...")
            
            def export_worker():
                try:
                    file_path = self.tracker.export_data(format=format_str, days_back=30)
                    
                    if file_path:
                        self.after(0, lambda: self._export_success(file_path))
                    else:
                        self.after(0, lambda: self._export_error("Export failed"))
                        
                except Exception as e:
                    self.after(0, lambda: self._export_error(str(e)))
                finally:
                    self.after(0, lambda: self.refresh_button.configure(state="normal", text="🔄 Refresh"))
            
            export_thread = threading.Thread(target=export_worker, daemon=True)
            export_thread.start()
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export data:\n{e}", parent=self)
    
    def _export_success(self, file_path):
        """Show export success message"""
        result = messagebox.askyesno(
            "Export Complete",
            f"Data exported successfully to:\n{file_path}\n\nWould you like to open the export folder?",
            parent=self
        )
        
        if result:
            try:
                import os
                folder_path = os.path.dirname(file_path)
                os.startfile(folder_path)  # Windows
            except Exception as e:
                logging.error(f"Failed to open export folder: {e}")
    
    def _export_error(self, error_message):
        """Show export error message"""
        messagebox.showerror("Export Failed", f"Failed to export data:\n{error_message}", parent=self)
    
    def show_settings(self):
        """Show settings dialog"""
        from .settings_dialog import SettingsDialog
        
        try:
            settings_dialog = SettingsDialog(self, self.config_manager)
            settings_dialog.focus()
        except Exception as e:
            logging.error(f"Error opening settings dialog: {e}")
            messagebox.showerror("Settings Error", f"Failed to open settings:\n{e}", parent=self)
    
    def position_window(self):
        """Position the dashboard window"""
        self.update_idletasks()
        
        if self.parent_window:
            # Center on parent window
            parent_x = self.parent_window.winfo_rootx()
            parent_y = self.parent_window.winfo_rooty()
            parent_width = self.parent_window.winfo_width()
            parent_height = self.parent_window.winfo_height()
            
            x = parent_x + (parent_width - 1000) // 2
            y = parent_y + (parent_height - 700) // 2
        else:
            # Center on screen
            screen_width = self.winfo_screenwidth()
            screen_height = self.winfo_screenheight()
            
            x = (screen_width - 1000) // 2
            y = (screen_height - 700) // 2
        
        self.geometry(f"+{x}+{y}")
    
    def on_close(self):
        """Handle window close"""
        self.stop_auto_refresh()
        
        try:
            self.destroy()
        except Exception as e:
            logging.error(f"Error closing dashboard: {e}")