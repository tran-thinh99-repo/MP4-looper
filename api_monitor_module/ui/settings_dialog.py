# api_monitor_module/ui/settings_dialog.py
"""
Settings Dialog - Configuration interface for the monitoring system
"""

import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox, filedialog
from utils import center_window

class SettingsDialog(ctk.CTkToplevel):
    """Settings dialog for monitoring configuration"""
    
    def __init__(self, parent, config_manager):
        super().__init__(parent)
        
        self.config_manager = config_manager
        self.parent = parent
        
        # Setup window
        self.title("Monitoring Settings")
        self.geometry("500x600")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        # Center on parent
        center_window(self)
        
        # Create UI
        self.create_ui()
        
        # Load current settings
        self.load_current_settings()
    
    def create_ui(self):
        """Create the settings UI"""
        # Main container
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="⚙️ Monitoring Settings",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#00bfff"
        )
        title_label.pack(pady=(0, 20))
        
        # Create tabview for different setting categories
        self.tabview = ctk.CTkTabview(main_frame)
        self.tabview.pack(fill="both", expand=True, pady=(0, 20))
        
        # Data Retention tab
        self.create_retention_tab()
        
        # Rate Limiting tab
        self.create_rate_limiting_tab()
        
        # UI Settings tab
        self.create_ui_settings_tab()
        
        # Advanced tab
        self.create_advanced_tab()
        
        # Buttons frame
        buttons_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", pady=(10, 0))
        
        # Save button
        save_button = ctk.CTkButton(
            buttons_frame,
            text="💾 Save Settings",
            command=self.save_settings,
            fg_color="#28a745",
            hover_color="#218838",
            width=120
        )
        save_button.pack(side="left", padx=(0, 10))
        
        # Reset to defaults button
        reset_button = ctk.CTkButton(
            buttons_frame,
            text="🔄 Reset to Defaults",
            command=self.reset_to_defaults,
            fg_color="#dc3545",
            hover_color="#c82333",
            width=140
        )
        reset_button.pack(side="left", padx=10)
        
        # Cancel button
        cancel_button = ctk.CTkButton(
            buttons_frame,
            text="❌ Cancel",
            command=self.destroy,
            fg_color="#6c757d",
            hover_color="#5a6268",
            width=100
        )
        cancel_button.pack(side="right")
    
    def create_retention_tab(self):
        """Create the data retention settings tab"""
        retention_tab = self.tabview.add("Data Retention")
        
        # Detailed data retention
        detailed_frame = ctk.CTkFrame(retention_tab)
        detailed_frame.pack(fill="x", pady=10, padx=10)
        
        ctk.CTkLabel(
            detailed_frame,
            text="📊 Detailed Data Retention",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(10, 5))
        
        ctk.CTkLabel(
            detailed_frame,
            text="How many days of detailed API call data to keep:",
            font=ctk.CTkFont(size=11),
            text_color="#aaa"
        ).pack(pady=(0, 5))
        
        self.detailed_days_var = tk.StringVar(value="30")
        detailed_entry_frame = ctk.CTkFrame(detailed_frame, fg_color="transparent")
        detailed_entry_frame.pack(pady=(0, 10))
        
        self.detailed_days_entry = ctk.CTkEntry(
            detailed_entry_frame,
            textvariable=self.detailed_days_var,
            width=100
        )
        self.detailed_days_entry.pack(side="left", padx=(0, 10))
        
        ctk.CTkLabel(
            detailed_entry_frame,
            text="days (recommended: 30)",
            text_color="#aaa"
        ).pack(side="left")
        
        # Summary data retention
        summary_frame = ctk.CTkFrame(retention_tab)
        summary_frame.pack(fill="x", pady=10, padx=10)
        
        ctk.CTkLabel(
            summary_frame,
            text="📈 Summary Data Retention",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(10, 5))
        
        ctk.CTkLabel(
            summary_frame,
            text="How many months of summary data to keep:",
            font=ctk.CTkFont(size=11),
            text_color="#aaa"
        ).pack(pady=(0, 5))
        
        self.summary_months_var = tk.StringVar(value="12")
        summary_entry_frame = ctk.CTkFrame(summary_frame, fg_color="transparent")
        summary_entry_frame.pack(pady=(0, 10))
        
        self.summary_months_entry = ctk.CTkEntry(
            summary_entry_frame,
            textvariable=self.summary_months_var,
            width=100
        )
        self.summary_months_entry.pack(side="left", padx=(0, 10))
        
        ctk.CTkLabel(
            summary_entry_frame,
            text="months (recommended: 12)",
            text_color="#aaa"
        ).pack(side="left")
        
        # Auto cleanup
        cleanup_frame = ctk.CTkFrame(retention_tab)
        cleanup_frame.pack(fill="x", pady=10, padx=10)
        
        ctk.CTkLabel(
            cleanup_frame,
            text="🧹 Automatic Cleanup",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(10, 5))
        
        self.auto_cleanup_var = tk.BooleanVar(value=True)
        self.auto_cleanup_checkbox = ctk.CTkCheckBox(
            cleanup_frame,
            text="Automatically clean up old data",
            variable=self.auto_cleanup_var
        )
        self.auto_cleanup_checkbox.pack(pady=(0, 10))
        
        cleanup_note = ctk.CTkLabel(
            cleanup_frame,
            text="When enabled, old detailed data is automatically archived\nand removed based on retention settings.",
            font=ctk.CTkFont(size=10),
            text_color="#aaa",
            justify="center"
        )
        cleanup_note.pack(pady=(0, 10))
    
    def create_rate_limiting_tab(self):
        """Create the rate limiting settings tab"""
        rate_tab = self.tabview.add("Rate Limiting")
        
        # Global rate limiting
        global_frame = ctk.CTkFrame(rate_tab)
        global_frame.pack(fill="x", pady=10, padx=10)
        
        ctk.CTkLabel(
            global_frame,
            text="🛡️ Global Rate Limiting",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(10, 5))
        
        self.rate_limiting_enabled_var = tk.BooleanVar(value=True)
        self.rate_limiting_checkbox = ctk.CTkCheckBox(
            global_frame,
            text="Enable rate limiting",
            variable=self.rate_limiting_enabled_var
        )
        self.rate_limiting_checkbox.pack(pady=(0, 10))
        
        # Debug upload limits
        debug_frame = ctk.CTkFrame(rate_tab)
        debug_frame.pack(fill="x", pady=10, padx=10)
        
        ctk.CTkLabel(
            debug_frame,
            text="🛠️ Debug Upload Limits",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(10, 5))
        
        debug_settings_frame = ctk.CTkFrame(debug_frame, fg_color="transparent")
        debug_settings_frame.pack(pady=(0, 10))
        
        ctk.CTkLabel(debug_settings_frame, text="Max calls:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.debug_max_calls_var = tk.StringVar(value="3")
        debug_calls_entry = ctk.CTkEntry(debug_settings_frame, textvariable=self.debug_max_calls_var, width=80)
        debug_calls_entry.grid(row=0, column=1, padx=5, pady=2)
        
        ctk.CTkLabel(debug_settings_frame, text="Window (minutes):").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.debug_window_var = tk.StringVar(value="60")
        debug_window_entry = ctk.CTkEntry(debug_settings_frame, textvariable=self.debug_window_var, width=80)
        debug_window_entry.grid(row=1, column=1, padx=5, pady=2)
        
        # Auth operation limits
        auth_frame = ctk.CTkFrame(rate_tab)
        auth_frame.pack(fill="x", pady=10, padx=10)
        
        ctk.CTkLabel(
            auth_frame,
            text="🔐 Authentication Limits",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(10, 5))
        
        auth_settings_frame = ctk.CTkFrame(auth_frame, fg_color="transparent")
        auth_settings_frame.pack(pady=(0, 10))
        
        ctk.CTkLabel(auth_settings_frame, text="Max calls:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.auth_max_calls_var = tk.StringVar(value="10")
        auth_calls_entry = ctk.CTkEntry(auth_settings_frame, textvariable=self.auth_max_calls_var, width=80)
        auth_calls_entry.grid(row=0, column=1, padx=5, pady=2)
        
        ctk.CTkLabel(auth_settings_frame, text="Window (minutes):").grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.auth_window_var = tk.StringVar(value="60")
        auth_window_entry = ctk.CTkEntry(auth_settings_frame, textvariable=self.auth_window_var, width=80)
        auth_window_entry.grid(row=1, column=1, padx=5, pady=2)
    
    def create_ui_settings_tab(self):
        """Create the UI settings tab"""
        ui_tab = self.tabview.add("UI Settings")
        
        # Theme settings
        theme_frame = ctk.CTkFrame(ui_tab)
        theme_frame.pack(fill="x", pady=10, padx=10)
        
        ctk.CTkLabel(
            theme_frame,
            text="🎨 Theme Settings",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(10, 5))
        
        self.theme_var = tk.StringVar(value="dark")
        theme_menu = ctk.CTkOptionMenu(
            theme_frame,
            variable=self.theme_var,
            values=["dark", "light"]
        )
        theme_menu.pack(pady=(0, 10))
        
        # Auto-refresh settings
        refresh_frame = ctk.CTkFrame(ui_tab)
        refresh_frame.pack(fill="x", pady=10, padx=10)
        
        ctk.CTkLabel(
            refresh_frame,
            text="🔄 Auto-Refresh Settings",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(10, 5))
        
        self.auto_refresh_var = tk.BooleanVar(value=False)
        auto_refresh_checkbox = ctk.CTkCheckBox(
            refresh_frame,
            text="Enable auto-refresh by default",
            variable=self.auto_refresh_var
        )
        auto_refresh_checkbox.pack(pady=(0, 5))
        
        refresh_interval_frame = ctk.CTkFrame(refresh_frame, fg_color="transparent")
        refresh_interval_frame.pack(pady=(0, 10))
        
        ctk.CTkLabel(refresh_interval_frame, text="Refresh interval:").pack(side="left", padx=(0, 5))
        self.refresh_interval_var = tk.StringVar(value="30")
        refresh_interval_entry = ctk.CTkEntry(
            refresh_interval_frame,
            textvariable=self.refresh_interval_var,
            width=80
        )
        refresh_interval_entry.pack(side="left", padx=5)
        ctk.CTkLabel(refresh_interval_frame, text="seconds").pack(side="left", padx=(5, 0))
        
        # Window settings
        window_frame = ctk.CTkFrame(ui_tab)
        window_frame.pack(fill="x", pady=10, padx=10)
        
        ctk.CTkLabel(
            window_frame,
            text="🪟 Window Settings",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(10, 5))
        
        self.remember_position_var = tk.BooleanVar(value=True)
        remember_checkbox = ctk.CTkCheckBox(
            window_frame,
            text="Remember window position",
            variable=self.remember_position_var
        )
        remember_checkbox.pack(pady=(0, 10))
    
    def create_advanced_tab(self):
        """Create the advanced settings tab"""
        advanced_tab = self.tabview.add("Advanced")
        
        # Storage settings
        storage_frame = ctk.CTkFrame(advanced_tab)
        storage_frame.pack(fill="x", pady=10, padx=10)
        
        ctk.CTkLabel(
            storage_frame,
            text="💾 Storage Settings",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(10, 5))
        
        # Max file size
        max_size_frame = ctk.CTkFrame(storage_frame, fg_color="transparent")
        max_size_frame.pack(pady=(0, 5))
        
        ctk.CTkLabel(max_size_frame, text="Max file size:").pack(side="left", padx=(0, 5))
        self.max_file_size_var = tk.StringVar(value="50")
        max_size_entry = ctk.CTkEntry(max_size_frame, textvariable=self.max_file_size_var, width=80)
        max_size_entry.pack(side="left", padx=5)
        ctk.CTkLabel(max_size_frame, text="MB").pack(side="left", padx=(5, 0))
        
        # Storage location
        location_frame = ctk.CTkFrame(storage_frame, fg_color="transparent")
        location_frame.pack(fill="x", pady=(5, 10))
        
        ctk.CTkLabel(location_frame, text="Storage location:").pack(anchor="w", pady=(0, 5))
        
        location_path_frame = ctk.CTkFrame(location_frame, fg_color="transparent")
        location_path_frame.pack(fill="x")
        
        self.storage_path_var = tk.StringVar()
        storage_path_entry = ctk.CTkEntry(
            location_path_frame,
            textvariable=self.storage_path_var,
            state="readonly"
        )
        storage_path_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        browse_button = ctk.CTkButton(
            location_path_frame,
            text="Browse",
            command=self.browse_storage_location,
            width=80
        )
        browse_button.pack(side="right")
        
        # Admin settings
        admin_frame = ctk.CTkFrame(advanced_tab)
        admin_frame.pack(fill="x", pady=10, padx=10)
        
        ctk.CTkLabel(
            admin_frame,
            text="👑 Admin Settings",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(10, 5))
        
        # Admin emails
        admin_emails_frame = ctk.CTkFrame(admin_frame, fg_color="transparent")
        admin_emails_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(admin_emails_frame, text="Admin emails (one per line):").pack(anchor="w", pady=(0, 5))
        
        self.admin_emails_text = ctk.CTkTextbox(admin_emails_frame, height=80)
        self.admin_emails_text.pack(fill="x", pady=(0, 5))
        
        admin_note = ctk.CTkLabel(
            admin_emails_frame,
            text="Users with these email addresses can access the monitoring dashboard.",
            font=ctk.CTkFont(size=10),
            text_color="#aaa"
        )
        admin_note.pack(anchor="w")
        
        # Export/Import settings
        export_frame = ctk.CTkFrame(advanced_tab)
        export_frame.pack(fill="x", pady=10, padx=10)
        
        ctk.CTkLabel(
            export_frame,
            text="📤 Export/Import",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=(10, 5))
        
        export_buttons_frame = ctk.CTkFrame(export_frame, fg_color="transparent")
        export_buttons_frame.pack(pady=(0, 10))
        
        export_config_button = ctk.CTkButton(
            export_buttons_frame,
            text="Export Config",
            command=self.export_config,
            width=120
        )
        export_config_button.pack(side="left", padx=(0, 10))
        
        import_config_button = ctk.CTkButton(
            export_buttons_frame,
            text="Import Config",
            command=self.import_config,
            width=120
        )
        import_config_button.pack(side="left")
    
    def load_current_settings(self):
        """Load current settings into the UI"""
        try:
            # Data retention settings
            retention_config = self.config_manager.get_retention_config()
            self.detailed_days_var.set(str(retention_config.get('detailed_days', 30)))
            self.summary_months_var.set(str(retention_config.get('summary_months', 12)))
            self.auto_cleanup_var.set(retention_config.get('auto_cleanup', True))
            
            # Rate limiting settings
            self.rate_limiting_enabled_var.set(self.config_manager.get('rate_limits.global_enabled', True))
            
            debug_limits = self.config_manager.get_rate_limit_config('debug_upload')
            self.debug_max_calls_var.set(str(debug_limits.get('max_calls', 3)))
            self.debug_window_var.set(str(debug_limits.get('window_minutes', 60)))
            
            auth_limits = self.config_manager.get_rate_limit_config('auth_operation')
            self.auth_max_calls_var.set(str(auth_limits.get('max_calls', 10)))
            self.auth_window_var.set(str(auth_limits.get('window_minutes', 60)))
            
            # UI settings
            ui_config = self.config_manager.get_ui_config()
            self.theme_var.set(ui_config.get('theme', 'dark'))
            self.auto_refresh_var.set(ui_config.get('auto_refresh', False))
            self.refresh_interval_var.set(str(ui_config.get('refresh_interval', 30)))
            self.remember_position_var.set(ui_config.get('remember_position', True))
            
            # Advanced settings
            self.max_file_size_var.set(str(self.config_manager.get('retention.max_file_size_mb', 50)))
            
            # Storage path
            file_paths = self.config_manager.get_file_paths()
            self.storage_path_var.set(file_paths.get('storage_path', ''))
            
            # Admin emails
            admin_emails = self.config_manager.get_admin_emails()
            self.admin_emails_text.delete("1.0", "end")
            self.admin_emails_text.insert("1.0", "\n".join(admin_emails))
            
        except Exception as e:
            print(f"Error loading settings: {e}")
    
    def save_settings(self):
        """Save all settings"""
        try:
            # Validate inputs
            if not self.validate_inputs():
                return
            
            # Data retention settings
            self.config_manager.set('retention.detailed_days', int(self.detailed_days_var.get()))
            self.config_manager.set('retention.summary_months', int(self.summary_months_var.get()))
            self.config_manager.set('retention.auto_cleanup', self.auto_cleanup_var.get())
            self.config_manager.set('retention.max_file_size_mb', int(self.max_file_size_var.get()))
            
            # Rate limiting settings
            self.config_manager.set('rate_limits.global_enabled', self.rate_limiting_enabled_var.get())
            
            # Debug upload limits
            debug_limits = {
                'max_calls': int(self.debug_max_calls_var.get()),
                'window_minutes': int(self.debug_window_var.get())
            }
            self.config_manager.set('rate_limits.default_limits.debug_upload', debug_limits)
            
            # Auth operation limits
            auth_limits = {
                'max_calls': int(self.auth_max_calls_var.get()),
                'window_minutes': int(self.auth_window_var.get())
            }
            self.config_manager.set('rate_limits.default_limits.auth_operation', auth_limits)
            
            # UI settings
            self.config_manager.update_ui_config(
                theme=self.theme_var.get(),
                auto_refresh=self.auto_refresh_var.get(),
                refresh_interval_seconds=int(self.refresh_interval_var.get()),
                remember_window_position=self.remember_position_var.get()
            )
            
            # Admin emails
            admin_emails_text = self.admin_emails_text.get("1.0", "end").strip()
            if admin_emails_text:
                admin_emails = [email.strip() for email in admin_emails_text.split('\n') if email.strip()]
                self.config_manager.set_admin_emails(admin_emails)
            
            # Show success message
            messagebox.showinfo(
                "Settings Saved",
                "Settings have been saved successfully!\n\nSome changes may require restarting the dashboard to take effect.",
                parent=self
            )
            
            self.destroy()
            
        except ValueError as e:
            messagebox.showerror("Invalid Input", f"Please check your input values:\n{e}", parent=self)
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save settings:\n{e}", parent=self)
    
    def validate_inputs(self):
        """Validate all user inputs"""
        try:
            # Validate numeric inputs
            detailed_days = int(self.detailed_days_var.get())
            if detailed_days < 1 or detailed_days > 365:
                raise ValueError("Detailed days must be between 1 and 365")
            
            summary_months = int(self.summary_months_var.get())
            if summary_months < 1 or summary_months > 120:
                raise ValueError("Summary months must be between 1 and 120")
            
            max_file_size = int(self.max_file_size_var.get())
            if max_file_size < 1 or max_file_size > 1000:
                raise ValueError("Max file size must be between 1 and 1000 MB")
            
            refresh_interval = int(self.refresh_interval_var.get())
            if refresh_interval < 10 or refresh_interval > 3600:
                raise ValueError("Refresh interval must be between 10 and 3600 seconds")
            
            # Validate rate limiting inputs
            debug_max_calls = int(self.debug_max_calls_var.get())
            if debug_max_calls < 1 or debug_max_calls > 1000:
                raise ValueError("Debug max calls must be between 1 and 1000")
            
            debug_window = int(self.debug_window_var.get())
            if debug_window < 1 or debug_window > 1440:
                raise ValueError("Debug window must be between 1 and 1440 minutes")
            
            auth_max_calls = int(self.auth_max_calls_var.get())
            if auth_max_calls < 1 or auth_max_calls > 1000:
                raise ValueError("Auth max calls must be between 1 and 1000")
            
            auth_window = int(self.auth_window_var.get())
            if auth_window < 1 or auth_window > 1440:
                raise ValueError("Auth window must be between 1 and 1440 minutes")
            
            # Validate admin emails
            admin_emails_text = self.admin_emails_text.get("1.0", "end").strip()
            if admin_emails_text:
                admin_emails = [email.strip() for email in admin_emails_text.split('\n') if email.strip()]
                for email in admin_emails:
                    if '@' not in email or '.' not in email:
                        raise ValueError(f"Invalid email address: {email}")
            
            return True
            
        except ValueError as e:
            messagebox.showerror("Validation Error", str(e), parent=self)
            return False
    
    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        result = messagebox.askyesno(
            "Reset Settings",
            "Are you sure you want to reset all settings to their default values?\n\nThis action cannot be undone.",
            parent=self
        )
        
        if result:
            try:
                # Reset configuration to defaults
                self.config_manager.reset_to_defaults()
                
                # Reload settings in UI
                self.load_current_settings()
                
                messagebox.showinfo(
                    "Settings Reset",
                    "All settings have been reset to their default values.",
                    parent=self
                )
                
            except Exception as e:
                messagebox.showerror("Reset Error", f"Failed to reset settings:\n{e}", parent=self)
    
    def browse_storage_location(self):
        """Browse for a new storage location"""
        current_path = self.storage_path_var.get()
        initial_dir = current_path if current_path else None
        
        new_path = filedialog.askdirectory(
            title="Select Storage Location",
            initialdir=initial_dir,
            parent=self
        )
        
        if new_path:
            self.storage_path_var.set(new_path)
            
            # Show warning about moving data
            messagebox.showwarning(
                "Storage Location Changed",
                "Changing the storage location will require moving existing data.\n\n"
                "This change will take effect after restarting the application.",
                parent=self
            )
    
    def export_config(self):
        """Export configuration to a file"""
        try:
            file_path = filedialog.asksaveasfilename(
                title="Export Configuration",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                parent=self
            )
            
            if file_path:
                success = self.config_manager.export_config(file_path)
                if success:
                    messagebox.showinfo(
                        "Export Successful",
                        f"Configuration exported to:\n{file_path}",
                        parent=self
                    )
                else:
                    messagebox.showerror("Export Failed", "Failed to export configuration.", parent=self)
                    
        except Exception as e:
            messagebox.showerror("Export Error", f"Error exporting configuration:\n{e}", parent=self)
    
    def import_config(self):
        """Import configuration from a file"""
        try:
            file_path = filedialog.askopenfilename(
                title="Import Configuration",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                parent=self
            )
            
            if file_path:
                result = messagebox.askyesno(
                    "Import Configuration",
                    "Importing a configuration will overwrite current settings.\n\n"
                    "Are you sure you want to continue?",
                    parent=self
                )
                
                if result:
                    success = self.config_manager.import_config(file_path)
                    if success:
                        # Reload settings in UI
                        self.load_current_settings()
                        
                        messagebox.showinfo(
                            "Import Successful",
                            "Configuration imported successfully!\n\n"
                            "Settings have been updated in the dialog.",
                            parent=self
                        )
                    else:
                        messagebox.showerror("Import Failed", "Failed to import configuration.", parent=self)
                        
        except Exception as e:
            messagebox.showerror("Import Error", f"Error importing configuration:\n{e}", parent=self)