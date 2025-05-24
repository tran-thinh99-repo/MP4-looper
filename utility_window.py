# utility_window.py - UPDATED VERSION
"""
Detached Utility Window - Follows main UI, no title bar buttons
"""

import logging
import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox

class UtilityWindow(ctk.CTkToplevel):
    """Detached utility window that follows the main UI"""
    
    def __init__(self, parent, controller):
        super().__init__(parent)
        
        self.controller = controller
        self.parent = parent
        
        # Window state
        self.is_collapsed = False
        self.expanded_width = 220
        self.expanded_height = 600
        self.collapsed_width = 250
        self.collapsed_height = 80
        
        # Check admin status FIRST
        self.is_admin = self._check_admin_status()
        logging.info(f"Admin status check: {self.is_admin}")  # Debug log
        
        # Setup window - REMOVE TITLE BAR BUTTONS
        self.setup_window()
        
        # Create widgets
        self.create_widgets()
        
        # Position window to follow main UI
        self.position_window()
        
        
        # Add admin section if needed
        self._add_admin_section_if_needed()
        
        # Make window follow the main window
        self.setup_window_following()
        
    def setup_window(self):
        """Configure the utility window - NO TITLE BAR BUTTONS + STAY WITH MAIN"""
        self.title("MP4 Looper Utilities")
        self.geometry(f"{self.expanded_width}x{self.expanded_height}")
        self.resizable(False, False)
        
        # Make this window stay with the parent (important for Alt+Tab)
        self.transient(self.parent)  # This makes it stay with the main window
        
        # Set window style
        self.configure(fg_color="#1a1a1a")
        
        # Add a custom border to make it look nice
        self.configure(border_width=2, border_color="#404040")
        
        # Bind focus events to handle Alt+Tab properly
        self.bind("<FocusIn>", self.on_focus_in)
        self.bind("<FocusOut>", self.on_focus_out)
        self.parent.bind("<FocusIn>", self.on_parent_focus_in)
        self.parent.bind("<FocusOut>", self.on_parent_focus_out)
        
    def setup_window_following(self):
        """Make the utility window follow the main window - SAFE VERSION"""
        self.following_active = True
        
        def follow_main_window():
            try:
                # Check if both windows still exist before doing anything
                if (self.following_active and 
                    self.winfo_exists() and 
                    self.parent.winfo_exists()):
                    
                    # Get main window position and size
                    main_x = self.parent.winfo_rootx()
                    main_y = self.parent.winfo_rooty()
                    main_width = self.parent.winfo_width()
                    
                    # Calculate utility window position
                    utility_x = main_x + main_width + 10
                    utility_y = main_y
                    
                    # Get screen dimensions
                    screen_width = self.winfo_screenwidth()
                    screen_height = self.winfo_screenheight()
                    
                    # Make sure it stays on screen
                    if utility_x + self.winfo_width() > screen_width:
                        utility_x = main_x - self.winfo_width() - 10
                    
                    if utility_y + self.winfo_height() > screen_height:
                        utility_y = max(0, screen_height - self.winfo_height())
                    
                    # Update position
                    self.geometry(f"+{utility_x}+{utility_y}")
                    
                    # Schedule next update
                    self.after(100, follow_main_window)
                        
            except tk.TclError:
                # Window was destroyed, stop following
                self.following_active = False
            except Exception as e:
                if self.following_active:
                    self.after(500, follow_main_window)
        
        # Start following
        self.after(200, follow_main_window)
    
    def on_focus_in(self, event):
        """Handle utility window getting focus"""
        try:
            if self.winfo_exists():
                pass  # Focus gained, no logging needed
        except tk.TclError:
            pass  # Window was destroyed

    def on_focus_out(self, event):
        """Handle utility window losing focus"""
        try:
            if self.winfo_exists():
                pass  # Focus lost, no logging needed
        except tk.TclError:
            pass  # Window was destroyed

    def on_parent_focus_in(self, event):
        """Handle main window getting focus - show utility if it was visible"""
        try:
            if (hasattr(self, '_was_visible_before_hide') and 
                self._was_visible_before_hide and
                hasattr(self, 'utility_window') and 
                self.utility_window):
                # Check if utility window still exists before showing
                try:
                    if self.utility_window.winfo_exists():
                        self.after(100, self.utility_window.show_window)
                except (tk.TclError, AttributeError):
                    pass  # Window was destroyed or doesn't exist
        except Exception as e:
            pass  # Silent error handling

    def on_parent_focus_out(self, event):
        """Handle main window losing focus"""
        try:
            # Remember if utility was visible, but check if window exists first
            if hasattr(self, 'utility_window') and self.utility_window:
                try:
                    self._was_visible_before_hide = self.utility_window.winfo_viewable()
                except (tk.TclError, AttributeError):
                    # Window was destroyed or doesn't exist
                    self._was_visible_before_hide = False
            else:
                self._was_visible_before_hide = False
        except Exception as e:
            pass  # Silent error handling
    
    def create_widgets(self):
        """Create all utility widgets"""
        # Main container
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Header with collapse/expand button (NO PIN BUTTON)
        self.create_header()
        
        # Content frame (will be hidden when collapsed)
        self.content_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, pady=(10, 0))
        
        # Create all sections
        self.create_debug_section()
        self.create_support_section()
        self.create_about_section()
    
    def create_header(self):
        """Create the header with title and collapse button - NO PIN BUTTON"""
        header_frame = ctk.CTkFrame(self.main_frame, fg_color="#2a2a2a", height=50)
        header_frame.pack(fill="x", pady=(0, 5))
        header_frame.pack_propagate(False)
        
        # Title
        self.title_label = ctk.CTkLabel(
            header_frame,
            text="🔧 Utilities",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#00bfff"
        )
        self.title_label.pack(side="left", padx=10, pady=15)
        
        # Collapse/Expand button
        self.collapse_button = ctk.CTkButton(
            header_frame,
            text="🔽",  # Down arrow when expanded
            command=self.toggle_collapse,
            width=30,
            height=30,
            fg_color="transparent",
            hover_color="#404040",
            font=ctk.CTkFont(size=12)
        )
        self.collapse_button.pack(side="right", padx=10, pady=10)
        
        # REMOVED THE PIN BUTTON - NO MORE PINNING FEATURE
    
    def create_debug_section(self):
        """Create debug-related utilities"""
        debug_frame = ctk.CTkFrame(self.content_frame, fg_color="#232323")
        debug_frame.pack(fill="x", pady=(0, 8))
        
        debug_label = ctk.CTkLabel(
            debug_frame,
            text="🐛 Debug",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#ffc107"
        )
        debug_label.pack(pady=(8, 5))
        
        # Debug buttons
        buttons_data = [
            ("📄 View Log", self._show_debug_log, "#6c757d"),
            ("🧹 Clean Uploads", self._clean_canceled_uploads, "#6c757d")
        ]
        
        for text, command, color in buttons_data:
            btn = ctk.CTkButton(
                debug_frame,
                text=text,
                command=command,
                width=180,
                height=28,
                fg_color=color,
                hover_color=self._darken_color(color),
                font=ctk.CTkFont(size=10)
            )
            btn.pack(pady=2, padx=10)
        
        # Add padding at bottom
        ctk.CTkLabel(debug_frame, text="", height=5).pack()
    
    def create_support_section(self):
        """Create support-related utilities"""
        support_frame = ctk.CTkFrame(self.content_frame, fg_color="#232323")
        support_frame.pack(fill="x", pady=(0, 8))
        
        support_label = ctk.CTkLabel(
            support_frame,
            text="🛠️ Support",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#17a2b8"
        )
        support_label.pack(pady=(8, 5))
        
        # Support buttons
        buttons_data = [
            ("📤 Send Debug Info", self._send_debug_info, "#17a2b8"),
            ("❓ Help", self._show_help, "#6c757d")
        ]
        
        for text, command, color in buttons_data:
            btn = ctk.CTkButton(
                support_frame,
                text=text,
                command=command,
                width=180,
                height=28,
                fg_color=color,
                hover_color=self._darken_color(color),
                font=ctk.CTkFont(size=10)
            )
            btn.pack(pady=2, padx=10)
        
        # Add padding at bottom
        ctk.CTkLabel(support_frame, text="", height=5).pack()
    
    def create_about_section(self):
        """Create about/info section"""
        about_frame = ctk.CTkFrame(self.content_frame, fg_color="#232323")
        about_frame.pack(fill="x")
        
        about_label = ctk.CTkLabel(
            about_frame,
            text="ℹ️ About",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#6c757d"
        )
        about_label.pack(pady=(8, 5))
        
        # Version info
        try:
            version = self.controller.version if hasattr(self.controller, 'version') else "1.2.0"
            version_label = ctk.CTkLabel(
                about_frame,
                text=f"MP4 Looper v{version}\nby EAGLE NET",
                font=ctk.CTkFont(size=9),
                text_color="#888",
                justify="center"
            )
            version_label.pack(pady=(0, 8))
        except Exception:
            pass
    
    def _add_admin_section_if_needed(self):
        """Add admin section if user is admin - FIXED VERSION"""
        logging.info(f"Adding admin section - is_admin: {self.is_admin}")
        
        # ALWAYS add a debug section first to show what's happening
        try:
            from auth_module.email_auth import get_current_user
            current_user = get_current_user()
            
            debug_frame = ctk.CTkFrame(self.content_frame, fg_color="#1a1a2e")
            debug_frame.pack(fill="x", pady=(0, 8))
            
            debug_label = ctk.CTkLabel(
                debug_frame,
                text=f"🔍 Debug Info\nUser: {current_user}\nAdmin: {self.is_admin}",
                font=ctk.CTkFont(size=9),
                text_color="#ffc107",
                justify="center"
            )
            debug_label.pack(pady=8)
            logging.info("✅ Debug section added")
            
        except Exception as e:
            logging.error(f"Error creating debug section: {e}")
        
        # Now add admin section if user is admin
        if self.is_admin:
            try:
                # Create admin section AFTER debug section
                admin_frame = ctk.CTkFrame(self.content_frame, fg_color="#232323")
                admin_frame.pack(fill="x", pady=(0, 8))
                
                admin_label = ctk.CTkLabel(
                    admin_frame,
                    text="👑 Admin",
                    font=ctk.CTkFont(size=12, weight="bold"),
                    text_color="#e67e22"
                )
                admin_label.pack(pady=(8, 5))
                
                # MONITOR BUTTON - This is what you were looking for!
                monitor_btn = ctk.CTkButton(
                    admin_frame,
                    text="📊 Monitor",
                    command=self._show_admin_monitoring,
                    width=180,
                    height=28,
                    fg_color="#e67e22",
                    hover_color="#d35400",
                    font=ctk.CTkFont(size=10)
                )
                monitor_btn.pack(pady=2, padx=10)
                
                # Add padding
                ctk.CTkLabel(admin_frame, text="", height=5).pack()
                
                logging.info("✅ Admin section with Monitor button added successfully!")
                
            except Exception as e:
                logging.error(f"Error creating admin section: {e}")
        else:
            logging.info("❌ User is not admin - no Admin section will be shown")
    
    def toggle_collapse(self):
        """Toggle between collapsed and expanded state"""
        self.is_collapsed = not self.is_collapsed
        
        if self.is_collapsed:
            # Collapse - hide content and shrink window
            self.content_frame.pack_forget()
            self.geometry(f"{self.collapsed_width}x{self.collapsed_height}")
            self.collapse_button.configure(text="🔼")  # Up arrow when collapsed
            self.title_label.configure(text="🔧")  # Just icon when collapsed
        else:
            # Expand - show content and restore window size  
            self.content_frame.pack(fill="both", expand=True, pady=(10, 0))
            self.geometry(f"{self.expanded_width}x{self.expanded_height}")
            self.collapse_button.configure(text="🔽")  # Down arrow when expanded
            self.title_label.configure(text="🔧 Utilities")
    
    def position_window(self):
        """Position the utility window next to the main window"""
        # Wait for window to be ready
        self.update_idletasks()
        
        # Get main window position if possible
        try:
            main_x = self.parent.winfo_rootx()
            main_y = self.parent.winfo_rooty()
            main_width = self.parent.winfo_width()
            
            # Position to the right of main window with some gap
            x = main_x + main_width + 10
            y = main_y
            
            # Make sure it fits on screen
            screen_width = self.winfo_screenwidth()
            if x + self.expanded_width > screen_width:
                # If no room on right, put on left
                x = max(10, main_x - self.expanded_width - 10)
            
            # Make sure y is on screen
            screen_height = self.winfo_screenheight()
            if y + self.expanded_height > screen_height:
                y = screen_height - self.expanded_height - 50
            
            y = max(50, y)  # Don't go too high
            
        except Exception:
            # Fallback - position in top right corner
            screen_width = self.winfo_screenwidth()
            x = screen_width - self.expanded_width - 50
            y = 100
        
        self.geometry(f"{self.expanded_width}x{self.expanded_height}+{x}+{y}")
    
    def _check_admin_status(self):
        """Check if current user has admin privileges - IMPROVED VERSION"""
        try:
            # Method 1: Try controller's method
            if hasattr(self.controller, 'is_admin_user'):
                result = self.controller.is_admin_user()
                logging.info(f"Controller admin check: {result}")
                if result:
                    return True
            
            # Method 2: Try API monitor method
            if hasattr(self.controller, 'api_monitor') and self.controller.api_monitor:
                result = self.controller.api_monitor.is_admin_user()
                logging.info(f"API monitor admin check: {result}")
                if result:
                    return True
            
            # Method 3: Direct check with current user
            try:
                from auth_module.email_auth import get_current_user
                current_user = get_current_user()
                logging.info(f"Current user: {current_user}")
                
                # Check against known admin emails - ADD YOUR ACTUAL ADMIN EMAIL HERE
                admin_emails = [
                    "admin@vicgmail.com",
                    "admin@gmail.com", 
                    "your_admin_email@domain.com"  # Replace with your actual admin email
                ]
                
                is_admin = current_user in admin_emails
                logging.info(f"Direct admin check for {current_user}: {is_admin}")
                logging.info(f"Checking against admin emails: {admin_emails}")
                
                # TEMPORARY: Always return True for debugging
                logging.info("🔧 TEMPORARY: Forcing admin status to True for debugging")
                return True  # TEMPORARY - remove this line later
                
                return is_admin
                
            except Exception as e:
                logging.error(f"Error getting current user: {e}")
            
            return False
            
        except Exception as e:
            logging.error(f"Error checking admin status: {e}")
            return False
    
    def _darken_color(self, hex_color, factor=0.15):
        """Darken a hex color by a factor"""
        try:
            # Remove # and convert to RGB
            hex_color = hex_color.lstrip('#')
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            
            # Darken
            r = max(0, int(r * (1 - factor)))
            g = max(0, int(g * (1 - factor)))
            b = max(0, int(b * (1 - factor)))
            
            return f"#{r:02x}{g:02x}{b:02x}"
        except:
            return "#404040"  # Fallback
    
    def on_close(self):
        """Handle window close - hide instead of destroy"""
        self.withdraw()  # Hide window instead of destroying it
    
    def show_window(self):
        """Show the utility window"""
        try:
            if self.winfo_exists():
                self.deiconify()  # Show window
                self.lift()       # Bring to front
                self.following_active = True  # Resume following
        except tk.TclError:
            pass  # Cannot show utility window - it was destroyed
        except Exception as e:
            logging.error(f"Error showing utility window: {e}")

    def hide_window(self):
        """Hide the utility window"""
        try:
            if self.winfo_exists():
                self.following_active = False  # Stop following
                self.withdraw()
        except tk.TclError:
            pass  # Cannot hide utility window - it was destroyed
        except Exception as e:
            logging.error(f"Error hiding utility window: {e}")
    
    # Event handlers - delegate to controller/parent to avoid code duplication
    def _show_debug_log(self):
        """Show debug log - delegate to controller"""
        try:
            self.controller.show_debug_log(self.parent)
        except Exception as e:
            logging.error(f"Error showing debug log: {e}")
            messagebox.showerror("Error", f"Failed to open debug log: {e}", parent=self)
    
    def _clean_canceled_uploads(self):
        """Clean canceled uploads - delegate to controller"""
        try:
            self.controller.clean_canceled_uploads(self.parent)
        except Exception as e:
            logging.error(f"Error cleaning uploads: {e}")
            messagebox.showerror("Error", f"Failed to clean uploads: {e}", parent=self)
    
    def _send_debug_info(self):
        """Send debug info - reuse existing logic"""
        try:
            # Ask user for confirmation
            confirm = messagebox.askyesno(
                "Send Debug Information", 
                "This will send your debug log and device information to support.\n\n"
                "The debug log may contain file paths and application activity.\n"
                "No passwords or sensitive data will be included.\n\n"
                "Do you want to continue?",
                parent=self
            )
            
            if not confirm:
                return
            
            # Import the function
            from auth_module.email_auth import send_debug_info_to_support_enhanced
            
            # Send the debug info
            success = send_debug_info_to_support_enhanced()
            
            if success:
                messagebox.showinfo(
                    "Debug Info Sent", 
                    "Your debug information has been sent successfully!\n\n"
                    "Support can now review your logs to help with any issues.",
                    parent=self
                )
            else:
                messagebox.showerror(
                    "Failed to Send", 
                    "Failed to send debug information.\n"
                    "Please check your internet connection and try again.",
                    parent=self
                )
                
        except Exception as e:
            logging.error(f"Error sending debug info: {e}")
            messagebox.showerror("Error", f"An error occurred: {str(e)}", parent=self)
    
    def _show_help(self):
        """Show help window"""
        try:
            from help_window import HelpWindow
            help_window = HelpWindow(self.parent)
            help_window.focus_set()
        except Exception as e:
            logging.error(f"Error showing help: {e}")
            messagebox.showerror("Error", f"Failed to show help: {e}", parent=self)
    
    def _show_admin_monitoring(self):
        """Show admin monitoring dashboard - THIS IS YOUR MONITOR BUTTON!"""
        try:
            logging.info("🔥 Monitor button clicked!")
            
            # Try multiple ways to access the dashboard
            if hasattr(self.controller, 'api_monitor') and self.controller.api_monitor:
                self.controller.api_monitor.show_dashboard(parent_window=self.parent)
                logging.info("✅ Dashboard opened via api_monitor")
            else:
                # Fallback method
                logging.warning("⚠️ No api_monitor found, trying alternative...")
                messagebox.showinfo(
                    "Monitor Dashboard", 
                    "Monitor dashboard is not available.\n\n"
                    "This could be because:\n"
                    "• API monitoring is disabled\n"
                    "• You're not logged in as admin\n"
                    "• The monitoring module failed to load",
                    parent=self
                )
                
        except Exception as e:
            logging.error(f"❌ Error opening admin dashboard: {e}")
            messagebox.showerror(
                "Dashboard Error", 
                f"Failed to open monitoring dashboard:\n{str(e)}", 
                parent=self
            )
    
    def force_show_admin_section(self):
        """TEMPORARY: Force show admin section for debugging"""
        logging.info("🔧 FORCE SHOWING ADMIN SECTION FOR DEBUGGING")
        
        try:
            # Create admin section directly
            admin_frame = ctk.CTkFrame(self.content_frame, fg_color="#232323")
            admin_frame.pack(fill="x", pady=(0, 8))
            
            admin_label = ctk.CTkLabel(
                admin_frame,
                text="👑 Admin (FORCED)",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color="#e67e22"
            )
            admin_label.pack(pady=(8, 5))
            
            # MONITOR BUTTON
            monitor_btn = ctk.CTkButton(
                admin_frame,
                text="📊 Monitor",
                command=self._show_admin_monitoring,
                width=180,
                height=28,
                fg_color="#e67e22",
                hover_color="#d35400",
                font=ctk.CTkFont(size=10)
            )
            monitor_btn.pack(pady=2, padx=10)
            
            # Add padding
            ctk.CTkLabel(admin_frame, text="", height=5).pack()
            
            logging.info("✅ FORCED admin section created successfully!")
            
        except Exception as e:
            logging.error(f"❌ Error forcing admin section: {e}")
            
        # Also force admin status
        self.is_admin = True

# Factory function for easy creation
def create_utility_window(parent, controller):
    """Create and return a utility window instance"""
    return UtilityWindow(parent, controller)