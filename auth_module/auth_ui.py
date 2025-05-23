import os
import tkinter as tk
import customtkinter as ctk
import logging
import sys
from .email_auth import authenticate_user, is_authenticated
from config import SERVICE_ACCOUNT_PATH
from paths import get_resource_path

# Global tk state tracking
_root_window = None

class AuthDialog(ctk.CTkToplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.title("MP4 Looper - Authentication")
        self.geometry("400x280")
        self.resizable(False, False)
        
        # Try to set icon using the same method as the main app
        try:
            icon_path = get_resource_path("mp4_looper_icon.ico")
            self.iconbitmap(default=icon_path)
            logging.debug(f"Set auth dialog icon: {icon_path}")
        except Exception as e:
            logging.debug(f"Could not set auth dialog icon: {e}")
        
        # Set up the UI
        self.create_ui()
        
        # Make modal
        self.transient(master)
        self.grab_set()
        
        # Center on screen
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        window_width = 400
        window_height = 280
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.geometry(f"+{x}+{y}")
        
        # Result
        self.auth_result = False
        
    def create_ui(self):
        # Main frame with padding
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(padx=20, pady=10, fill="both", expand=True)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame, 
            text="Please Sign In",
            font=("Segoe UI", 18, "bold")
        )
        title_label.pack(pady=(0, 15))
        
        # Email field
        email_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        email_frame.pack(fill="x", pady=3)
        
        email_label = ctk.CTkLabel(email_frame, text="Email:", width=80, anchor="w")
        email_label.pack(side="left", padx=(0, 10))
        
        self.email_entry = ctk.CTkEntry(email_frame, width=250, height=35)
        self.email_entry.pack(side="left", fill="x", expand=True)
        
        # Password field
        password_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        password_frame.pack(fill="x", pady=3)
        
        password_label = ctk.CTkLabel(password_frame, text="Password:", width=80, anchor="w")
        password_label.pack(side="left", padx=(0, 10))
        
        self.password_entry = ctk.CTkEntry(password_frame, width=250, height=35, show="•")
        self.password_entry.pack(side="left", fill="x", expand=True)
        
        # Remember me checkbox
        self.remember_var = tk.BooleanVar(value=False)
        self.remember_checkbox = ctk.CTkCheckBox(
            main_frame,
            text="Remember me on this device",
            variable=self.remember_var
        )
        self.remember_checkbox.pack(pady=(8, 0), anchor="w")
        
        # Error message
        self.error_var = tk.StringVar(value="")
        self.error_label = ctk.CTkLabel(
            main_frame, 
            textvariable=self.error_var,
            text_color="#ff3333",
            font=("Segoe UI", 12),
            height=20
        )
        self.error_label.pack(pady=(5, 5), fill="x")
        
        # Buttons
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(5, 10))
        
        self.login_button = ctk.CTkButton(
            button_frame,
            text="Sign In",
            command=self.authenticate,
            fg_color="#28a745",
            hover_color="#218838",
            height=45,
            font=("Segoe UI", 14, "bold")
        )
        self.login_button.pack(side="left", padx=5, fill="x", expand=True)
        
        self.cancel_button = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self.cancel,
            fg_color="#6c757d",
            hover_color="#5a6268",
            height=45,
            font=("Segoe UI", 14)
        )
        self.cancel_button.pack(side="left", padx=5, fill="x", expand=True)
        
        # Bind Enter key to authenticate
        self.bind("<Return>", lambda event: self.authenticate())
        
        # Focus email entry
        self.email_entry.focus_set()
        
    def authenticate(self):
        """Authenticate the user with entered credentials"""
        email = self.email_entry.get().strip()
        password = self.password_entry.get()
        remember = self.remember_var.get()
        
        # Basic validation
        if not email or not password:
            self.error_var.set("Please enter both email and password")
            return
        
        # Show authenticating status
        self.error_var.set("Authenticating...")
        self.update_idletasks()
        
        # Try to authenticate
        success, message = authenticate_user(email, password, remember)
        
        if success:
            self.auth_result = True
            self.after(100, self._close_safely)
        else:
            # Set a shorter error message in the dialog
            if "database" in message.lower():
                self.error_var.set("Cannot access authentication database")
                
                # Show a more detailed error dialog
                from tkinter import messagebox
                
                # Extract service account email if available
                service_email = "Unknown"
                try:
                    import json
                    with open(SERVICE_ACCOUNT_PATH, "r") as f:
                        creds = json.load(f)
                        service_email = creds.get("client_email", "Unknown")
                except Exception:
                    pass
                    
                error_details = (
                    "Could not access the authentication database.\n\n"
                    "Possible solutions:\n"
                    "1. Check your internet connection\n"
                    "2. Verify the spreadsheet ID is correct\n"
                    f"3. Share the spreadsheet with this service account:\n"
                    f"   {service_email}\n\n"
                    "Do you want to continue without authentication?"
                )
                
                allow_continue = messagebox.askyesno("Authentication Error", error_details)
                if allow_continue:
                    # Allow the user to continue anyway
                    self.auth_result = True
                    self.after(100, self._close_safely)
            else:
                # Regular authentication errors (wrong password, etc.)
                self.error_var.set(message)
            
            # Shake effect for failed login
            self._shake_window()
            
    def _close_safely(self):
        """Close dialog safely by scheduling self-destruction"""
        self.grab_release()  # Release grab to allow parent window to continue
        self.destroy()
    
    def cancel(self):
        """Cancel authentication and close dialog"""
        self.auth_result = False
        self.after(100, self._close_safely)
    
    def _shake_window(self):
        """Create a shake effect for failed login"""
        def _shake(count, distance):
            if count > 0:
                x, y = self.winfo_x(), self.winfo_y()
                self.geometry(f"+{x + distance}+{y}")
                self.after(50, lambda: _shake(count - 1, -distance))
        
        _shake(6, 10)

def show_auth_dialog(master=None):
    """Show authentication dialog and return result"""
    global _root_window
    
    # First check if already authenticated
    if is_authenticated():
        return True
    
    # If we don't have a master window and we need to create one
    created_root = False
    if master is None:
        # Create a new CTk root window and hide it
        _root_window = ctk.CTk()
        
        # Try to set the icon for the temporary root window
        try:
            if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
                icon_path = os.path.join(sys._MEIPASS, "mp4_looper_icon.ico")
                if os.path.exists(icon_path):
                    _root_window.iconbitmap(default=icon_path)
        except:
            pass
            
        _root_window.withdraw()  # Hide the window
        master = _root_window
        created_root = True
    
    try:
        # Show dialog and get result
        dialog = AuthDialog(master)
        dialog.wait_window()
        auth_result = dialog.auth_result
    except Exception as e:
        import logging
        logging.error(f"Error in authentication dialog: {e}")
        auth_result = False
    finally:
        # Clean up if we created a temp root
        if created_root:
            try:
                # Cancel any pending after() calls
                for after_id in master.tk.call('after', 'info'):
                    try:
                        master.after_cancel(after_id)
                    except Exception:
                        pass
                
                # Destroy root window
                master.destroy()
                _root_window = None
            except Exception:
                pass
    
    return auth_result