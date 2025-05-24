import os
import tkinter as tk
import customtkinter as ctk
import logging
import sys
from .email_auth import authenticate_user, is_authenticated

from icon_helper import set_window_icon

# Global tk state tracking
_root_window = None

class AuthDialog(ctk.CTkToplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.title("MP4 Looper - Authentication")
        self.geometry("400x280")
        self.resizable(False, False)
        
        # ADD THESE NEW ATTRIBUTES for spam protection
        self.is_authenticating = False  # Prevent multiple simultaneous attempts
        self.last_attempt_time = 0      # Track when last attempt was made
        self.attempt_count = 0          # Count attempts in current session
        self.min_delay_between_attempts = 2  # Minimum seconds between attempts

        # Try to set icon using the same method as the main app
        set_window_icon(self)
        
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
        """Authenticate the user with spam protection"""
        import time
        
        # SPAM PROTECTION 1: Prevent double-clicking
        if self.is_authenticating:
            return  # Already processing, ignore this click
        
        # SPAM PROTECTION 2: Minimum delay between attempts
        current_time = time.time()
        time_since_last = current_time - self.last_attempt_time
        
        if time_since_last < self.min_delay_between_attempts:
            remaining_time = self.min_delay_between_attempts - time_since_last
            self.error_var.set(f"Please wait {remaining_time:.1f} seconds...")
            return
        
        # SPAM PROTECTION 3: Escalating delays after multiple failures
        self.attempt_count += 1
        if self.attempt_count > 3:
            # After 3 attempts, require longer waits
            required_delay = min(self.attempt_count * 2, 30)  # Max 30 seconds
            if time_since_last < required_delay:
                remaining_time = required_delay - time_since_last
                self.error_var.set(f"Too many attempts. Wait {remaining_time:.0f} seconds...")
                return
        
        # SPAM PROTECTION 4: Basic input validation
        email = self.email_entry.get().strip()
        password = self.password_entry.get()
        remember = self.remember_var.get()
        
        if not email or not password:
            self.error_var.set("Please enter both email and password")
            return
        
        # Prevent further clicks and show loading state
        self.is_authenticating = True
        self.last_attempt_time = current_time
        self.login_button.configure(state="disabled", text="Signing in...")
        self.error_var.set("Authenticating...")
        self.update_idletasks()
        
        try:
            # Try to authenticate (this will hit the rate limiter if needed)
            success, message = authenticate_user(email, password, remember)
            
            if success:
                self.attempt_count = 0  # Reset on successful login
                self.auth_result = True
                self.after(100, self._close_safely)
            else:
                # Handle authentication failure
                if "rate limit" in message.lower() or "too many" in message.lower():
                    # If it's a rate limit error, show the message and increase delays
                    self.error_var.set("Too many attempts. Please wait before trying again.")
                    self.attempt_count += 3  # Penalize rate limit hits more
                else:
                    # Regular authentication errors
                    self.error_var.set(message)
                
                # Shake effect for failed login
                self._shake_window()
                
        except Exception as e:
            self.error_var.set("An error occurred. Please try again.")
            logging.error(f"Authentication error: {e}")
            
        finally:
            # Re-enable the button after a short delay
            self.after(1000, self._reset_button_state)  # 1 second delay
            
    def _reset_button_state(self):
        """Reset the button state after authentication attempt"""
        self.is_authenticating = False
        self.login_button.configure(state="normal", text="Sign In")

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