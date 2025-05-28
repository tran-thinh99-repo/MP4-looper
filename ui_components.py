# ui_components.py
import os
import threading
import logging
import re
import tkinter as tk
import customtkinter as ctk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from tkinterdnd2 import TkinterDnD, DND_FILES

from help_window import HelpWindow
from utils import center_window, format_duration
from utility_window import create_utility_window  # NEW IMPORT
from settings_manager import get_settings
from song_distribution_modal import SongPoolDistributionModal

# Configure UI Theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

class BatchProcessorUI(TkinterDnD.Tk):
    def __init__(self, app_controller):
        super().__init__()
        self.title("MP4 Batch Processor")
        self.geometry("1000x1000")  # Back to original width since no sidebar
        self.minsize(1000, 1000)
        self.configure(bg="#1a1a1a")
        
        # Reference to the main application controller
        self.controller = app_controller
        
        # Get settings manager reference
        self.settings_manager = get_settings()
        
        # UI state variables
        self.file_paths = []
        self.rendering = False
        self.was_stopped = False
        self.current_file_index = -1
        self.folder_labels = []
        self.output_preview_labels = []
        self.selected_file = None
        
        # Initialize duration display variable
        default_duration = self.settings_manager.get("ui.loop_duration", "3600")
        try:
            duration_int = int(default_duration)
        except:
            duration_int = 3600
            
        h, m, s = format_duration(duration_int)
        display_text = ""
        if h > 0: display_text += f"{h}h "
        if m > 0 or (h > 0 and s > 0): display_text += f"{m}m "
        if s > 0 or (h == 0 and m == 0): display_text += f"{s}s"
        self.duration_display_var = tk.StringVar(value=f"({display_text.strip()})")
        
        # Create detached utility window (initially hidden)
        self.utility_window = None
        
        # Create and lay out the UI components
        self.create_ui()
        
        # Create utility window after main UI is ready
        self.after(500, self.create_utility_window)
        
        # Center window on screen
        self.after(100, lambda: center_window(self))
        
        # Set up close protocol
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_utility_window(self):
        """Create the detached utility window"""
        try:
            self.utility_window = create_utility_window(self, self.controller)
            # Start hidden - user can show it with the button
            self.utility_window.withdraw()
            logging.info("Utility window created (hidden)")
        except Exception as e:
            logging.error(f"Error creating utility window: {e}")

    def create_ui(self):
        import os
import threading
import logging
import re
import tkinter as tk
import customtkinter as ctk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from tkinterdnd2 import TkinterDnD, DND_FILES

from help_window import HelpWindow
from utils import center_window, format_duration
from utility_window import create_utility_window  # NEW IMPORT

from settings_manager import get_settings

# Configure UI Theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

class BatchProcessorUI(TkinterDnD.Tk):
    def __init__(self, app_controller):
        super().__init__()
        self.title("MP4 Batch Processor")
        self.geometry("1000x1000")  # Back to original width since no sidebar
        self.minsize(1000, 1000)
        self.configure(bg="#1a1a1a")
        
        # Reference to the main application controller
        self.controller = app_controller
        
        # Get settings manager reference
        self.settings_manager = get_settings()
        
        # UI state variables
        self.file_paths = []
        self.rendering = False
        self.was_stopped = False
        self.current_file_index = -1
        self.folder_labels = []
        self.output_preview_labels = []
        self.selected_file = None
        
        # Initialize duration display variable
        default_duration = self.settings_manager.get("ui.loop_duration", "3600")
        self.duration_display_var = tk.StringVar(value=format_duration(int(default_duration)))
        
        # Create detached utility window (initially hidden)
        self.utility_window = None
        
        # Create and lay out the UI components
        self.create_ui()

        # Set up focus handling for Alt+Tab
        self.bind("<FocusIn>", self.on_main_focus_in)
        self.bind("<FocusOut>", self.on_main_focus_out)
        
        # Track if utility was visible before losing focus
        self._utility_was_visible = False

        # Create utility window after main UI is ready
        self.after(500, self.create_utility_window)
        
        # Center window on screen
        self.after(100, lambda: center_window(self))
        
        # Set up close protocol
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_utility_window(self):
        """Create the detached utility window"""
        try:
            self.utility_window = create_utility_window(self, self.controller)
            # Start hidden - user can show it with the button
            self.utility_window.withdraw()
            logging.info("Utility window created (hidden)")
        except Exception as e:
            logging.error(f"Error creating utility window: {e}")

    def create_ui(self):
        # UPDATED: Back to single column layout (no sidebar)
        
        # Main container with padding
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Configure main container grid
        main_container.grid_columnconfigure(0, weight=1)
        main_container.grid_rowconfigure(0, weight=0)  # Top bar - fixed
        main_container.grid_rowconfigure(1, weight=0)  # Stats - fixed
        main_container.grid_rowconfigure(2, weight=1)  # Drop area - EXPANDABLE
        main_container.grid_rowconfigure(3, weight=0)  # File buttons - fixed
        main_container.grid_rowconfigure(4, weight=0)  # Duration - fixed
        main_container.grid_rowconfigure(5, weight=0)  # Folders - fixed
        main_container.grid_rowconfigure(6, weight=0)  # Sheet - fixed
        main_container.grid_rowconfigure(7, weight=0)  # Options - fixed
        main_container.grid_rowconfigure(8, weight=0)  # Controls - fixed
        main_container.grid_rowconfigure(9, weight=0)  # Progress - fixed
        
        r = 0  # Start row counter
        
        # === Top Bar with User Info, Logout, and Utility Button ===
        top_bar = ctk.CTkFrame(main_container, fg_color="#1a1a1a", height=50)
        top_bar.grid(row=r, column=0, sticky="ew", pady=(0, 10), padx=5)
        top_bar.grid_propagate(False)
        r += 1
        
        # Left side - App title
        left_section = ctk.CTkFrame(top_bar, fg_color="transparent")
        left_section.pack(side="left", fill="y", padx=10)
        
        app_title = ctk.CTkLabel(
            left_section,
            text="🎬 MP4 Looper",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#00bfff"
        )
        app_title.pack(side="left", pady=15)
        
        # NEW: Utility window toggle button (left side, after title)
        self.utility_toggle_button = ctk.CTkButton(
            left_section,
            text="🔧",
            command=self.toggle_utility_window,
            width=30,
            height=30,
            fg_color="transparent",
            hover_color="#404040",
            font=ctk.CTkFont(size=12)
        )
        self.utility_toggle_button.pack(side="left", padx=(20, 0), pady=15)
        
        # Right side - User info and logout
        right_section = ctk.CTkFrame(top_bar, fg_color="transparent")
        right_section.pack(side="right", fill="y", padx=10)
        
        # Get current user email
        try:
            from auth_module.email_auth import get_current_user
            current_user = get_current_user()
            user_display = current_user if current_user else "Unknown User"
            
            # Truncate long emails
            if len(user_display) > 25:
                user_display = user_display[:22] + "..."
                
        except Exception:
            user_display = "User"
        
        # User info label
        user_label = ctk.CTkLabel(
            right_section,
            text=f"👤 {user_display}",
            font=ctk.CTkFont(size=12),
            text_color="#aaa"
        )
        user_label.pack(side="left", pady=15, padx=(0, 10))
        
        # Logout button
        self.logout_button = ctk.CTkButton(
            right_section,
            text="🚪 Logout",
            command=self.logout_user,
            width=80,
            height=30,
            fg_color="#dc3545",
            hover_color="#c82333",
            font=ctk.CTkFont(size=11)
        )
        self.logout_button.pack(side="right", pady=10)
        
        # === Stats Frame ===
        stats_frame = ctk.CTkFrame(main_container, fg_color="transparent", height=30)
        stats_frame.grid(row=r, column=0, sticky="ew", pady=(0, 5), padx=5)
        r += 1
        
        # Status and count labels
        self.status_label = ctk.CTkLabel(stats_frame, text="Drag video files here", 
                                text_color="#00bfff", font=("Segoe UI", 12))
        self.status_label.pack(side="left")
        
        self.count_label = ctk.CTkLabel(stats_frame, text="", 
                                    text_color="#aaa", font=("Segoe UI", 12))
        self.count_label.pack(side="right")
        
        # === Drop Area - SAME AS BEFORE ===
        self.drop_area = ctk.CTkFrame(main_container, fg_color="#1e1e1e", corner_radius=10)
        self.drop_area.grid(row=r, column=0, sticky="nsew", pady=(0, 10), padx=5)
        r += 1
        
        # Configure drop area grid
        self.drop_area.grid_columnconfigure(0, weight=1)
        self.drop_area.grid_rowconfigure(0, weight=1)
        
        # Drop area content - using grid instead of pack
        drop_area_content = ctk.CTkFrame(self.drop_area, fg_color="transparent")
        drop_area_content.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        drop_area_content.grid_columnconfigure(0, weight=1)
        drop_area_content.grid_columnconfigure(1, weight=1)
        drop_area_content.grid_rowconfigure(0, weight=1)
        
        # Left side - Raw Preview
        drop_zone_left = ctk.CTkFrame(drop_area_content, fg_color="#232323", corner_radius=8)
        drop_zone_left.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        drop_zone_left.grid_columnconfigure(0, weight=1)
        drop_zone_left.grid_rowconfigure(0, weight=0)  # Header - fixed
        drop_zone_left.grid_rowconfigure(1, weight=0)  # Drop indicator - fixed
        drop_zone_left.grid_rowconfigure(2, weight=1)  # File list - expandable
        
        # Header for raw preview
        raw_header = ctk.CTkLabel(
            drop_zone_left, 
            text="Raw Preview", 
            text_color="#00bfff",
            font=("Segoe UI", 14, "bold")
        )
        raw_header.grid(row=0, column=0, pady=(10, 5), sticky="ew")

        # Drop indicator
        self.drop_indicator = ctk.CTkLabel(
            drop_zone_left, 
            text="🡇 Drag video files or folders here 🡇",
            fg_color="transparent", 
            text_color="#00bfff",
            font=("Segoe UI", 16, "bold"), 
            height=60
        )
        self.drop_indicator.grid(row=1, column=0, pady=10, sticky="ew")
        
        # Scrollable frame for files
        self.folder_frame = ctk.CTkScrollableFrame(drop_zone_left, fg_color="transparent")
        self.folder_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))

        # Right side - Output Preview
        drop_zone_right = ctk.CTkFrame(drop_area_content, fg_color="#232323", corner_radius=8)
        drop_zone_right.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        drop_zone_right.grid_columnconfigure(0, weight=1)
        drop_zone_right.grid_rowconfigure(0, weight=0)  # Header - fixed
        drop_zone_right.grid_rowconfigure(1, weight=1)  # Output list - expandable

        # Header for output preview
        output_header = ctk.CTkLabel(
            drop_zone_right, 
            text="Output Preview", 
            text_color="#00bfff",
            font=("Segoe UI", 14, "bold")
        )
        output_header.grid(row=0, column=0, pady=(10, 5), sticky="ew")
        
        # Scrollable frame for output files
        self.output_preview_frame = ctk.CTkScrollableFrame(drop_zone_right, fg_color="transparent")
        self.output_preview_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        
        # Register drop events
        drop_zone_left.drop_target_register(DND_FILES)
        drop_zone_left.dnd_bind("<<Drop>>", self.on_drop)
        self.drop_indicator.drop_target_register(DND_FILES)
        self.drop_indicator.dnd_bind("<<Drop>>", self.on_drop)
        
        # Hover effects
        drop_zone_left.bind("<Enter>", lambda e: drop_zone_left.configure(fg_color="#2a2a2a"))
        drop_zone_left.bind("<Leave>", lambda e: drop_zone_left.configure(fg_color="#232323"))
        
        # Synchronized scrolling
        def _on_mousewheel(event):
            self.folder_frame._parent_canvas.yview_scroll(int(-1*(event.delta/20)), "units")
            self.output_preview_frame._parent_canvas.yview_scroll(int(-1*(event.delta/20)), "units")
            return "break"

        self.folder_frame.bind_all("<MouseWheel>", _on_mousewheel)

        # === File Management Buttons ===
        file_buttons_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        file_buttons_frame.grid(row=r, column=0, sticky="ew", pady=5)
        r += 1
        
        file_buttons_frame.grid_columnconfigure(0, weight=1)
        file_buttons_frame.grid_columnconfigure(1, weight=1)
        file_buttons_frame.grid_columnconfigure(2, weight=1)
        
        browse_button = ctk.CTkButton(
            file_buttons_frame,
            text="Browse Files",
            command=self.browse_files
        )
        browse_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        self.clear_button = ctk.CTkButton(
            file_buttons_frame,
            text="🗑 Clear Queue",
            command=self.clear_queue,
            fg_color="#6c757d",
            hover_color="#5a6268"
        )
        self.clear_button.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        self.remove_selected_button = ctk.CTkButton(
            file_buttons_frame,
            text="Remove Selected",
            command=self.remove_selected_file,
            fg_color="#dc3545",
            hover_color="#c82333",
            state="disabled"
        )
        self.remove_selected_button.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        
        # === Duration Input ===
        self.create_duration_section(main_container, r)
        r += 1
        
        # === Output and Music Folders ===
        folder_frame = ctk.CTkFrame(main_container)
        folder_frame.grid(row=r, column=0, sticky="ew", pady=10)
        r += 1
        
        # Output folder row
        output_row = ctk.CTkFrame(folder_frame, fg_color="transparent")
        output_row.pack(pady=5, fill="x")
        
        ctk.CTkLabel(output_row, text="Output Folder:", width=120, anchor="w").pack(side="left", padx=(0, 10))
        
        self.output_entry = ctk.CTkEntry(output_row)
        self.output_entry.pack(side="left", padx=5, fill="x", expand=True)
        self.output_entry.insert(0, os.getcwd())
        
        output_browse = ctk.CTkButton(output_row, text="Browse", width=80, command=self.browse_output)
        output_browse.pack(side="left", padx=5)
        
        output_open = ctk.CTkButton(output_row, text="Open", width=80, command=self.open_output)
        output_open.pack(side="left", padx=5)
        
        output_clean = ctk.CTkButton(output_row, text="Clean", width=80, command=self.clean_output)
        output_clean.pack(side="left", padx=5)
        
        # Music folder row
        music_row = ctk.CTkFrame(folder_frame, fg_color="transparent")
        music_row.pack(pady=5, fill="x")
        
        ctk.CTkLabel(music_row, text="Music Folder:", width=120, anchor="w").pack(side="left", padx=(0, 10))
        
        self.music_entry = ctk.CTkEntry(music_row)
        self.music_entry.pack(side="left", padx=5, fill="x", expand=True)
        
        music_browse = ctk.CTkButton(music_row, text="Browse", width=80, command=self.browse_music)
        music_browse.pack(side="left", padx=5)
        
        music_open = ctk.CTkButton(music_row, text="Open", width=80, command=self.open_music)
        music_open.pack(side="left", padx=5)
        
        # === Google Sheet Section ===
        sheet_frame = ctk.CTkFrame(main_container)
        sheet_frame.grid(row=r, column=0, sticky="ew", pady=10)
        r += 1
        
        sheet_row = ctk.CTkFrame(sheet_frame, fg_color="transparent")
        sheet_row.pack(pady=5, fill="x")
        
        ctk.CTkLabel(sheet_row, text="Google Sheet URL:", width=120, anchor="w").pack(side="left", padx=(0, 10))
        
        self.sheet_dropdown = ctk.CTkOptionMenu(
            sheet_row,
            values=self.controller.get_sheet_presets(),
            command=self.apply_preset_sheet_url,
            width=100
        )
        self.sheet_dropdown.pack(side="left", padx=5)
        
        self.sheet_entry = ctk.CTkEntry(sheet_row)
        self.sheet_entry.pack(side="left", padx=5, fill="x", expand=True)
        
        # === Options Section ===
        options_frame = ctk.CTkFrame(main_container)
        options_frame.grid(row=r, column=0, sticky="ew", pady=10)
        r += 1
        
        # New song count
        song_count_row = ctk.CTkFrame(options_frame, fg_color="transparent")
        song_count_row.pack(pady=5, fill="x")
        
        self.use_default_song_count = tk.BooleanVar(value=True)
        self.new_song_count_var = tk.StringVar(value="5")
        
        self.new_song_count_entry = ctk.CTkEntry(
            song_count_row, 
            textvariable=self.new_song_count_var,
            width=50,
            state="disabled"
        )
        self.new_song_count_entry.pack(side="left", padx=(10, 10))
        
        self.use_default_checkbox = ctk.CTkCheckBox(
            song_count_row,
            text="Use default (5) newest songs",
            variable=self.use_default_song_count,
            command=self.toggle_song_count
        )
        self.use_default_checkbox.pack(side="left")
        
        # Other options row
        other_options_row = ctk.CTkFrame(options_frame, fg_color="transparent")
        other_options_row.pack(pady=5, fill="x")
        
        self.fade_audio_var = tk.BooleanVar(value=True)
        self.fade_audio_checkbox = ctk.CTkCheckBox(
            other_options_row,
            text="Fade audio out at end (5s)",
            variable=self.fade_audio_var
        )
        self.fade_audio_checkbox.pack(side="left", padx=(10, 20))
        
        self.export_timestamp_var = tk.BooleanVar(value=True)
        self.export_timestamp_checkbox = ctk.CTkCheckBox(
            other_options_row,
            text="Export timestamp",
            variable=self.export_timestamp_var
        )
        self.export_timestamp_checkbox.pack(side="left", padx=(0, 20))
        
        self.auto_upload_var = tk.BooleanVar(value=False)
        self.auto_upload_checkbox = ctk.CTkCheckBox(
            other_options_row,
            text="Auto-upload after render",
            variable=self.auto_upload_var
        )
        self.auto_upload_checkbox.pack(side="left")
        
        # Add transition dropdown
        transition_label = ctk.CTkLabel(
            other_options_row,
            text="Transition:",
            font=("Segoe UI", 12)
        )
        transition_label.pack(side="left", padx=(20, 5))

        self.transition_var = tk.StringVar(value="None")
        self.transition_dropdown = ctk.CTkOptionMenu(
            other_options_row,
            values=["None", "fade", "slide_left", "slide_right", "zoom", 
                    "wipe_down", "wipe_up", "blinds", "pixelate", 
                    "dissolve", "expand_line"],
            variable=self.transition_var,
            width=120
        )
        self.transition_dropdown.pack(side="left", padx=(0, 20))

        # === Control Buttons ===
        control_frame = ctk.CTkFrame(main_container)
        control_frame.grid(row=r, column=0, sticky="ew", pady=10)
        r += 1

        self.distribution_button = ctk.CTkButton(
            control_frame,
            text="🎵 Song Distribution",
            command=self.show_distribution_modal,
            fg_color="#e67e22",
            hover_color="#d35400"
        )
        self.distribution_button.pack(side="left", padx=5, fill="x", expand=True)
        
        self.start_button = ctk.CTkButton(
            control_frame,
            text="▶ Start Processing",
            command=self.start_processing,
            fg_color="#28a745",
            hover_color="#218838"
        )
        self.start_button.pack(side="left", padx=5, fill="x", expand=True)
        
        self.stop_button = ctk.CTkButton(
            control_frame,
            text="⏹ Stop",
            command=self.stop_processing,
            state="disabled",
            fg_color="#dc3545",
            hover_color="#c82333"
        )
        self.stop_button.pack(side="left", padx=5, fill="x", expand=True)
        
        self.upload_button = ctk.CTkButton(
            control_frame,
            text="📤 Upload to Drive",
            command=self.upload_to_drive,
            fg_color="#17a2b8",
            hover_color="#138496"
        )
        self.upload_button.pack(side="left", padx=5, fill="x", expand=True)
        
        # === Progress Tracking ===
        progress_frame = ctk.CTkFrame(main_container)
        progress_frame.grid(row=r, column=0, sticky="ew", pady=10)
        r += 1
        
        style = ttk.Style()
        style.configure("TProgressbar", 
                        thickness=10, 
                        background='#007bff', 
                        troughcolor='#e9ecef', 
                        borderwidth=0)
        
        self.progress_bar = ttk.Progressbar(progress_frame, length=300, mode="determinate", style="TProgressbar")
        self.progress_bar.pack(pady=10, fill="x")
        
        self.progress_var = tk.StringVar(value="Ready")
        self.progress_label = ctk.CTkLabel(
            progress_frame,
            textvariable=self.progress_var,
            font=("Arial", 12)
        )
        self.progress_label.pack(pady=5)
        
        # Initialize missing attributes
        self.current_file_var = tk.StringVar(value="")
        
        # Create context menu
        self.create_context_menu()

        # ADDED: Configure upload access based on admin status
        self._configure_upload_access()

    def on_main_focus_in(self, event):
        """Handle main window getting focus"""
        logging.debug("🔥 Main window gained focus")
        
        # If utility window was visible before, show it again
        if (hasattr(self, 'utility_window') and 
            self.utility_window and 
            hasattr(self, '_utility_was_visible') and 
            self._utility_was_visible):
            
            try:
                self.after(200, lambda: self.utility_window.show_window())
                logging.debug("Restoring utility window visibility")
            except Exception as e:
                logging.error(f"Error restoring utility window: {e}")

    def on_main_focus_out(self, event):
        """Handle main window losing focus"""
        logging.debug("🔥 Main window lost focus")
        
        # Remember if utility window was visible
        if hasattr(self, 'utility_window') and self.utility_window:
            try:
                self._utility_was_visible = self.utility_window.winfo_viewable()
                logging.debug(f"Utility was visible: {self._utility_was_visible}")
            except Exception as e:
                logging.error(f"Error checking utility visibility: {e}")
                self._utility_was_visible = False

    def toggle_utility_window(self):
        """Toggle the utility window visibility - UPDATED VERSION"""
        try:
            if self.utility_window:
                # Check if window exists and is visible
                try:
                    if self.utility_window.winfo_viewable():
                        self.utility_window.hide_window()
                        self.utility_toggle_button.configure(fg_color="transparent")
                        self._utility_was_visible = False
                    else:
                        self.utility_window.show_window()
                        self.utility_toggle_button.configure(fg_color="#28a745")
                        self._utility_was_visible = True
                except tk.TclError:
                    # Window was destroyed, recreate it
                    self.create_utility_window()
                    if self.utility_window:
                        self.utility_window.show_window()
                        self.utility_toggle_button.configure(fg_color="#28a745")
                        self._utility_was_visible = True
            else:
                # Create window if it doesn't exist
                self.create_utility_window()
                if self.utility_window:
                    self.utility_window.show_window()
                    self.utility_toggle_button.configure(fg_color="#28a745")
                    self._utility_was_visible = True
        except Exception as e:
            logging.error(f"Error toggling utility window: {e}")

    # The create_duration_section method is now called in the create_ui method
    def create_duration_section(self, main_container, r):
        """Create an enhanced duration input section"""
        duration_frame = ctk.CTkFrame(main_container)
        duration_frame.grid(row=r, column=0, sticky="ew", pady=10)
        
        # Top row with label and converted display
        top_row = ctk.CTkFrame(duration_frame, fg_color="transparent")
        top_row.pack(pady=(5, 2), fill="x")
        
        # Duration label
        duration_label = ctk.CTkLabel(
            top_row, 
            text="Loop Duration (seconds):", 
            font=("Arial", 12)
        )
        duration_label.pack(side="left", padx=(10, 5))
        
        # Add the converted time display
        self.duration_display = ctk.CTkLabel(
            top_row,
            textvariable=self.duration_display_var,
            font=("Arial", 12),
            text_color="#00bfff"  # Light blue for visibility
        )
        self.duration_display.pack(side="left", padx=5)
        
        # Duration input field
        duration_input_frame = ctk.CTkFrame(duration_frame, fg_color="transparent")
        duration_input_frame.pack(pady=5)
        
        self.duration_input = ctk.CTkEntry(duration_input_frame, width=100)
        self.duration_input.pack(side="top", pady=5)
        self.duration_input.insert(0, "3600")  # Default to 1 hour
        
        # FIXED: Add proper event bindings for real-time updates
        self.duration_input.bind("<KeyRelease>", self.validate_and_display_duration)
        self.duration_input.bind("<FocusOut>", self.validate_and_display_duration) 
        self.duration_input.bind("<Return>", self.validate_and_display_duration)
        # Add immediate update when user finishes typing
        self.duration_input.bind("<KeyPress>", lambda e: self.after(100, self.validate_and_display_duration))
        
        # Time buttons frame
        time_buttons_frame = ctk.CTkFrame(duration_frame, fg_color="transparent")
        time_buttons_frame.pack(pady=5)
        
        # Add decrement buttons (-11h, -3h, -1h)
        self.create_duration_button(time_buttons_frame, "-11h", -39600, "#dc3545")
        self.create_duration_button(time_buttons_frame, "-3h", -10800, "#dc3545")
        self.create_duration_button(time_buttons_frame, "-1h", -3600, "#dc3545")
        
        # Add increment buttons (+1h, +3h, +11h)
        self.create_duration_button(time_buttons_frame, "+1h", 3600, "#28a745")
        self.create_duration_button(time_buttons_frame, "+3h", 10800, "#28a745")
        self.create_duration_button(time_buttons_frame, "+11h", 39600, "#28a745")
        
        # Initialize the display
        self.update_duration_display(3600)
        
        return duration_frame
        
    def create_duration_button(self, parent, text, seconds, color=None):
        """Create a button for quick duration setting"""
        button = ctk.CTkButton(
            parent,
            text=text,
            width=60,
            command=lambda: self.adjust_duration(seconds),
            fg_color=color if color else None
        )
        button.pack(side="left", padx=5)
        return button

    def adjust_duration(self, seconds):
        """Adjust the duration by the specified number of seconds - FIXED VERSION"""
        try:
            # Get the current duration
            current_duration = int(self.duration_input.get())
            
            # Calculate the new duration
            new_duration = current_duration + seconds
            
            # Ensure it's at least 1 second
            new_duration = max(1, new_duration)
            
            # Update the entry field
            self.duration_input.delete(0, tk.END)
            self.duration_input.insert(0, str(new_duration))
            
            # CRITICAL FIX: Force update the display immediately
            self.update_duration_display(new_duration)
            
            # CRITICAL FIX: Update the output preview as well
            self.update_file_display()
            
            # Save the setting immediately
            try:
                self.settings_manager.set("ui.loop_duration", str(new_duration))
            except Exception as e:
                logging.debug(f"Could not save duration setting: {e}")
            
        except ValueError:
            # If the current value isn't a valid integer, reset to default
            default_duration = self.settings_manager.get("ui.loop_duration", "3600")
            self.duration_input.delete(0, tk.END)
            self.duration_input.insert(0, default_duration)
            self.update_duration_display(int(default_duration))
            self.update_file_display()  # Update output preview too

    def validate_and_display_duration(self, event=None):
        """Validate the duration input and update the display - COMPLETE FIX"""
        current_text = self.duration_input.get().strip()
        
        # If empty, use default
        if not current_text:
            default_duration = self.settings_manager.get("ui.loop_duration", "3600")
            self.duration_input.delete(0, tk.END)
            self.duration_input.insert(0, default_duration)
            self.update_duration_display(int(default_duration))
            self.update_file_display()  # Update output preview
            return
        
        try:
            # Try to convert to an integer
            duration = int(current_text)
            
            # Enforce minimum value of 1 second
            if duration < 1:
                duration = 1
                self.duration_input.delete(0, tk.END)
                self.duration_input.insert(0, "1")
            
            # CRITICAL: Always update both displays
            self.update_duration_display(duration)
            self.update_file_display()  # Update output preview
            
            # Save the duration in settings
            try:
                self.settings_manager.set("ui.loop_duration", str(duration))
            except Exception as e:
                logging.debug(f"Could not save duration setting: {e}")
            
        except ValueError:
            # If not a valid integer, reset to current setting or default
            try:
                current_setting = self.settings_manager.get("ui.loop_duration", "3600")
                self.duration_input.delete(0, tk.END)
                self.duration_input.insert(0, current_setting)
                self.update_duration_display(int(current_setting))
                self.update_file_display()  # Update output preview
            except:
                # Final fallback
                self.duration_input.delete(0, tk.END)
                self.duration_input.insert(0, "3600")
                self.update_duration_display(3600)
                self.update_file_display()  # Update output preview

    def update_duration_display(self, seconds):
        """Update the display showing the duration in h:m:s format"""
        h, m, s = format_duration(seconds)  # Use utils version
        
        # Create display text
        display_text = ""
        if h > 0:
            display_text += f"{h}h "
        if m > 0 or (h > 0 and s > 0):
            display_text += f"{m}m "
        if s > 0 or (h == 0 and m == 0):
            display_text += f"{s}s"
        
        # Update the display
        self.duration_display_var.set(f"({display_text.strip()})")

    def show_help(self):
        """Show the help window"""
        help_window = HelpWindow(self)
        help_window.focus_set()  # Set focus to the help window

    def set_duration(self, seconds):
        """Set the duration value"""
        self.duration_input.delete(0, tk.END)
        self.duration_input.insert(0, str(seconds))
        # Update the display too
        self.update_duration_display(seconds)

    def validate_duration(self, event=None):
        """Validate that duration is a number"""
        current_text = self.duration_input.get()
        if not current_text.isdigit():
            self.duration_input.delete(0, tk.END)
            self.duration_input.insert(0, "3600")  # Reset to default
            self.update_duration_display(3600)  # Update display

    def on_drop(self, event):
        """Handle drag and drop of files with improved feedback"""
        # Check if we're currently processing - this replaces the disabled state check
        if self.rendering:
            messagebox.showwarning("Processing in Progress", "Cannot add files while processing.")
            return
            
        file_paths = self.tk.splitlist(event.data)
        
        # Let controller handle the file processing
        new_items, duplicates = self.controller.process_dropped_files(file_paths)
        
        if duplicates and not new_items:
            messagebox.showinfo("Skipped Duplicates", "These items were already added:\n" + "\n".join(os.path.basename(p) for p in duplicates))
            return  # Stop here if everything was duplicate

        if duplicates:
            messagebox.showinfo("Some Items Skipped", "Some items were already in the queue.")

        # FIXED: Hide the drop indicator when files are added
        if new_items:
            self.drop_indicator.grid_forget()

        self.file_paths.extend(new_items)
        
        # Update status label and file count
        self.update_file_count()
        
        # Add new items to the UI with side-by-side display
        self.update_file_display()
        
        # Give visual feedback on successful add
        if new_items:
            logging.info(f"Added {len(new_items)} items to queue")
            
            # Flash the drop area briefly green for success feedback
            original_color = self.drop_area.cget("fg_color")
            self.drop_area.configure(fg_color="#2a5d2a")  # Green for success
            self.after(500, lambda: self.drop_area.configure(fg_color=original_color))

    def browse_files(self):
        """Browse for MP4 files with improved feedback"""
        if self.rendering:
            messagebox.showwarning("Processing in Progress", "Cannot add files while processing.")
            return
            
        files = filedialog.askopenfilenames(filetypes=[("MP4 files", "*.mp4")])
        if not files:
            return
        
        new_items, duplicates = self.controller.process_selected_files(files)
        
        # Add new files to the queue
        self.file_paths.extend(new_items)
        
        # Show warnings for duplicates if needed
        if duplicates and not new_items:
            messagebox.showinfo("Skipped Duplicates", "All selected files were already in the queue.")
            return
        elif duplicates:
            messagebox.showinfo("Some Files Skipped", "Some files were already in the queue.")
        
        # Update the file count
        self.update_file_count()
        
        # FIXED: Hide the drop indicator when files are added
        if new_items:
            self.drop_indicator.grid_forget()
        
        # Update both file displays
        self.update_file_display()
        
        # Log the changes
        if new_items:
            logging.info(f"Added {len(new_items)} files via browse dialog")
            
            # Visual feedback - flash green
            original_color = self.drop_area.cget("fg_color")
            self.drop_area.configure(fg_color="#2a5d2a")  # Green for success
            self.after(500, lambda: self.drop_area.configure(fg_color=original_color))

    def update_file_count(self):
        """Update the file count display"""
        count = len(self.file_paths)
        
        # Update the count label
        if count == 0:
            self.count_label.configure(text="No files queued")
        elif count == 1:
            self.count_label.configure(text="1 file queued")
        else:
            self.count_label.configure(text=f"{count} files queued")
        
        # Update status label
        if count > 0:
            folder_count = sum(1 for path in self.file_paths if os.path.isdir(path))
            file_count = count - folder_count
            
            if folder_count and file_count:
                self.status_label.configure(text=f"🗂 {folder_count} folders, 📄 {file_count} files queued")
            elif folder_count:
                self.status_label.configure(text=f"🗂 {folder_count} folders queued")
            else:
                self.status_label.configure(text=f"📄 {file_count} files queued")

    def browse_output(self):
        """Browse for output folder - UPDATED METHOD"""
        folder = filedialog.askdirectory()
        if folder:
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, folder)
            # Save setting immediately
            self.on_setting_changed('output_folder', folder)

    def browse_music(self):
        """Browse for music folder - UPDATED METHOD"""
        folder = filedialog.askdirectory()
        if folder:
            self.music_entry.delete(0, tk.END)
            self.music_entry.insert(0, folder)
            # Save setting immediately
            self.on_setting_changed('music_folder', folder)

    def open_output(self):
        """Open the output folder"""
        path = self.output_entry.get().strip()
        self.controller.open_folder(path, "Output Folder", self)

    def open_music(self):
        """Open the music folder"""
        path = self.music_entry.get().strip()
        self.controller.open_folder(path, "Music Folder", self)

    def clean_output(self):
        """Clean the output folder"""
        path = Path(self.output_entry.get().strip())
        self.controller.clean_folder(path, "Clean Output Folder", self)

    def toggle_song_count(self):
        """Toggle the new song count entry field"""
        if self.use_default_song_count.get():
            self.new_song_count_entry.configure(state="disabled")
        else:
            self.new_song_count_entry.configure(state="normal")

    def apply_preset_sheet_url(self, selected):
        """Apply a preset sheet URL - UPDATED METHOD"""
        url = self.controller.get_sheet_preset_url(selected)
        if url:
            self.sheet_entry.delete(0, tk.END)
            self.sheet_entry.insert(0, url)
            
            # Save both preset and URL
            self.on_setting_changed('sheet_preset', selected)
            self.on_setting_changed('sheet_url', url)
            
            logging.info(f"Applied preset '{selected}' with URL: {url}")
        else:
            logging.warning(f"No URL found for preset '{selected}'")

    def show_debug_log(self):
        """Show the debug log file"""
        self.controller.show_debug_log(self)

    def clean_canceled_uploads(self):
        """Clean canceled uploads from Google Drive"""
        self.controller.clean_canceled_uploads(self)

    def start_processing(self):
        """Start processing the queued files - FIXED with proper distribution mode support"""
        if not self.file_paths:
            messagebox.showwarning("No Files", "No files are queued for processing")
            return
            
        if not self.validate_inputs():
            return
            
        # Validate song list CSV
        if not self.controller.handle_song_csv_validation(self.sheet_entry.get().strip()):
            return
        
        # FIXED: Check if we're in distribution mode - improved check
        distribution_mode = (hasattr(self.controller, 'distribution_settings') and 
                            self.controller.distribution_settings is not None)
        
        if distribution_mode:
            # Show distribution mode confirmation
            distribution_settings = self.controller.distribution_settings
            num_videos = distribution_settings['num_videos']
            method = distribution_settings['distribution_method']
            
            confirm_msg = (
                f"🎵 Start Distribution Mode Processing?\n\n"
                f"• Number of videos: {num_videos}\n"
                f"• Distribution method: {method.title()}\n"
                f"• Source files: {len(self.file_paths)}\n\n"
                f"This will create {num_videos} videos with unique song combinations.\n\n"
                f"💡 Tip: Close the Distribution Modal to return to normal mode."
            )
            
            if not messagebox.askyesno("Confirm Distribution Processing", confirm_msg, parent=self):
                return
                
            logging.info(f"🎵 Starting distribution mode: {num_videos} videos, {method} method")
        else:
            # FIXED: Normal mode - show standard confirmation
            confirm_msg = (
                f"▶ Start Normal Processing?\n\n"
                f"• Number of files: {len(self.file_paths)}\n"
                f"• Processing mode: One video per file\n"
                f"• Output: Individual videos\n\n"
                f"Each file will be processed separately with the same settings.\n\n"
                f"💡 Tip: Use 'Song Distribution' button for multiple videos from one file."
            )
            
            if not messagebox.askyesno("Confirm Normal Processing", confirm_msg, parent=self):
                return
                
            logging.info(f"▶ Starting normal mode: {len(self.file_paths)} files")
        
        # Lock the UI during processing
        self.lock_ui_during_processing()
        
        self.rendering = True
        self.was_stopped = False
        self.current_file_index = 0
        
        # Get processing parameters
        params = {
            "file_paths": self.file_paths,
            "duration": int(self.duration_input.get()),
            "output_folder": self.output_entry.get().strip(),
            "music_folder": self.music_entry.get().strip(),
            "sheet_url": self.sheet_entry.get().strip(),
            "new_song_count": 5 if self.use_default_song_count.get() else int(self.new_song_count_var.get()),
            "export_timestamp": self.export_timestamp_var.get(),
            "fade_audio": self.fade_audio_var.get(),
            "auto_upload": self.auto_upload_var.get(),
            "transition": self.transition_var.get()
        }
        
        # Update UI status based on mode
        if distribution_mode:
            self.progress_var.set("Starting distribution mode processing...")
            self.status_label.configure(text=f"🎵 Distribution Mode: {num_videos} videos")
        else:
            self.progress_var.set("Starting normal processing...")
            self.status_label.configure(text=f"▶ Normal Mode: {len(self.file_paths)} files")
        
        # Start processing thread
        threading.Thread(target=self.controller.process_files, args=(params, self), daemon=True).start()

    def lock_ui_during_processing(self):
        """Lock UI elements during processing to prevent interference - COMPLETE FIX"""
        # Set rendering flag
        self.rendering = True
        
        # Disable ALL buttons except stop - COMPLETE LIST
        buttons_to_disable = [
            "Browse Files", 
            "🗑 Clear Queue", 
            "Remove Selected", 
            "🎵 Song Distribution", 
            "📤 Upload to Drive",
            # Duration adjustment buttons
            "+1h", "+3h", "+11h", "-1h", "-3h", "-11h",
            # Folder management buttons
            "Browse",  # Output and Music folder browse buttons
            "Open",    # Output and Music folder open buttons  
            "Clean"    # Output folder clean button
        ]
        
        self._disable_buttons_by_text(buttons_to_disable)
        
        # Disable input fields
        input_fields = [
            self.output_entry,
            self.music_entry, 
            self.sheet_entry,
            self.duration_input,
            self.new_song_count_entry
        ]
        
        for field in input_fields:
            if hasattr(field, 'configure'):
                try:
                    field.configure(state="disabled")
                except Exception as e:
                    logging.debug(f"Could not disable field: {e}")
        
        # Disable checkboxes
        checkboxes = [
            self.use_default_checkbox,
            self.fade_audio_checkbox,
            self.export_timestamp_checkbox,
            self.auto_upload_checkbox
        ]
        
        for checkbox in checkboxes:
            if hasattr(checkbox, 'configure'):
                try:
                    checkbox.configure(state="disabled")
                except Exception as e:
                    logging.debug(f"Could not disable checkbox: {e}")
        
        # Disable dropdowns
        dropdowns = [
            self.sheet_dropdown,
            self.transition_dropdown
        ]
        
        for dropdown in dropdowns:
            if hasattr(dropdown, 'configure'):
                try:
                    dropdown.configure(state="disabled")
                except Exception as e:
                    logging.debug(f"Could not disable dropdown: {e}")
        
        # Update start/stop buttons
        self.start_button.configure(state="disabled", text="🔄 Processing...")
        self.stop_button.configure(state="normal")
        
        # Change window title to show processing status
        original_title = self.title()
        self.title(f"{original_title} - PROCESSING")
        self._original_title = original_title
        
        # Show processing indicator in status
        self.status_label.configure(text="🔄 Processing in progress - UI locked", text_color="#ffc107")
        
        logging.info("🔒 UI fully locked during processing")

    def _disable_buttons_by_text(self, button_texts):
        """Helper method to find and disable buttons by their text"""
        def search_and_disable(widget):
            try:
                # Check if this widget is a button with matching text
                if hasattr(widget, 'cget') and hasattr(widget, 'configure'):
                    try:
                        button_text = widget.cget("text")
                        if button_text in button_texts:
                            widget.configure(state="disabled")
                            logging.debug(f"Disabled button: {button_text}")
                    except:
                        pass  # Not a button or can't get text
                
                # Recursively search child widgets
                if hasattr(widget, 'winfo_children'):
                    for child in widget.winfo_children():
                        search_and_disable(child)
            except Exception as e:
                logging.debug(f"Error searching widget: {e}")
        
        # Start search from the main window
        search_and_disable(self)

    def unlock_ui_after_processing(self):
        """Unlock UI elements after processing is complete - COMPLETE UNLOCK"""
        # Reset rendering flag
        self.rendering = False
        
        # Re-enable ALL buttons
        buttons_to_enable = [
            "Browse Files", 
            "🗑 Clear Queue", 
            "Remove Selected", 
            "🎵 Song Distribution", 
            "📤 Upload to Drive",
            # Duration adjustment buttons
            "+1h", "+3h", "+11h", "-1h", "-3h", "-11h",
            # Folder management buttons
            "Browse",  # Output and Music folder browse buttons
            "Open",    # Output and Music folder open buttons
            "Clean"    # Output folder clean button
        ]
        
        self._enable_buttons_by_text(buttons_to_enable)
        
        # Re-enable input fields
        input_fields = [
            self.output_entry,
            self.music_entry,
            self.sheet_entry, 
            self.duration_input
        ]
        
        for field in input_fields:
            if hasattr(field, 'configure'):
                try:
                    field.configure(state="normal")
                except Exception as e:
                    logging.debug(f"Could not enable field: {e}")
        
        # Re-enable checkboxes
        checkboxes = [
            self.use_default_checkbox,
            self.fade_audio_checkbox,
            self.export_timestamp_checkbox,
            self.auto_upload_checkbox
        ]
        
        for checkbox in checkboxes:
            if hasattr(checkbox, 'configure'):
                try:
                    checkbox.configure(state="normal")
                except Exception as e:
                    logging.debug(f"Could not enable checkbox: {e}")
        
        # Re-enable dropdowns
        dropdowns = [
            self.sheet_dropdown,
            self.transition_dropdown
        ]
        
        for dropdown in dropdowns:
            if hasattr(dropdown, 'configure'):
                try:
                    dropdown.configure(state="normal")
                except Exception as e:
                    logging.debug(f"Could not enable dropdown: {e}")
        
        # Handle song count entry based on checkbox state
        self.toggle_song_count()
        
        # Reset start/stop buttons
        self.start_button.configure(state="normal", text="▶ Start Processing")
        self.stop_button.configure(state="disabled")
        
        # Restore window title
        if hasattr(self, '_original_title'):
            self.title(self._original_title)
            delattr(self, '_original_title')
        
        # Reset status
        count = len(self.file_paths)
        if count > 0:
            self.status_label.configure(text=f"📄 {count} file{'s' if count > 1 else ''} queued", text_color="#00bfff")
        else:
            self.status_label.configure(text="Drag video files here", text_color="#00bfff")
        
        logging.info("🔓 UI fully unlocked after processing")

    def _enable_buttons_by_text(self, button_texts):
        """Helper method to find and enable buttons by their text"""
        def search_and_enable(widget):
            try:
                # Check if this widget is a button with matching text
                if hasattr(widget, 'cget') and hasattr(widget, 'configure'):
                    try:
                        button_text = widget.cget("text")
                        if button_text in button_texts:
                            widget.configure(state="normal")
                    except:
                        pass  # Not a button or can't get text
                
                # Recursively search child widgets
                if hasattr(widget, 'winfo_children'):
                    for child in widget.winfo_children():
                        search_and_enable(child)
            except Exception as e:
                logging.debug(f"Error searching widget: {e}")
        
        # Start search from the main window
        search_and_enable(self)

    def validate_inputs(self):
        """Validate all required inputs"""
        # Check duration
        if not self.duration_input.get().isdigit():
            messagebox.showerror("Invalid Input", "Duration must be a number")
            return False
            
        # Check output folder
        output_folder = self.output_entry.get().strip()
        if not output_folder:
            messagebox.showerror("Invalid Input", "Output folder is required")
            return False
            
        if not os.path.isdir(output_folder):
            try:
                os.makedirs(output_folder)
            except Exception as e:
                messagebox.showerror("Invalid Output", f"Cannot create output folder: {e}")
                return False
                
        # Check music folder
        music_folder = self.music_entry.get().strip()
        if not music_folder:
            messagebox.showerror("Invalid Input", "Music folder is required")
            return False
            
        if not os.path.isdir(music_folder):
            messagebox.showerror("Invalid Input", "Music folder does not exist")
            return False
            
        # Check Google Sheet URL
        sheet_url = self.sheet_entry.get().strip()
        if not sheet_url:
            messagebox.showerror("Invalid Input", "Google Sheet URL is required")
            return False
            
        return True

    def update_progress(self, value, message=None):
        """Update progress bar and message"""
        self.progress_bar["value"] = value
        if message:
            self.progress_var.set(message)

    def set_current_file(self, index, filename):
        """Update current file information"""
        self.current_file_index = index
        self.current_file_var.set(f"Current file: {filename}")

    def processing_complete(self):
        """Reset UI after processing is complete - UPDATED"""
        self.rendering = False
        self.progress_var.set("Processing complete")
        self.current_file_var.set("")
        
        # Unlock the UI
        self.unlock_ui_after_processing()
        
        # Clear distribution settings if they exist
        if hasattr(self.controller, 'distribution_settings'):
            self.controller.distribution_settings = None
        
        # Store a flag indicating processing is complete
        self.processing_finished = True
        
        # Only show message if not uploading
        if not hasattr(self.controller, '_drive_uploader') or not self.controller._drive_uploader.is_uploading:
            self._show_completion_message()

    def _show_completion_message(self):
        """Show the appropriate completion message"""
        # Check for both processing and upload completion
        processing_done = hasattr(self, 'processing_finished') and self.processing_finished
        upload_done = hasattr(self, 'upload_finished') and self.upload_finished
        
        if processing_done or upload_done:
            if processing_done and upload_done:
                messagebox.showinfo("Complete", "Batch processing and upload completed")
            elif processing_done:
                messagebox.showinfo("Complete", "Batch processing completed")
            elif upload_done:
                messagebox.showinfo("Complete", "Upload to Google Drive completed")
            
            # Reset the flags
            if hasattr(self, 'processing_finished'):
                self.processing_finished = False
            if hasattr(self, 'upload_finished'):
                self.upload_finished = False

    def stop_processing(self):
        """Stop all processing - UPDATED"""
        if not self.rendering:
            return
            
        confirm = messagebox.askyesno("Confirm Stop", 
                                    "Are you sure you want to stop processing?\n\n"
                                    "This will interrupt the current render and may leave incomplete files.",
                                    parent=self)
        if not confirm:
            return
            
        self.rendering = False
        self.was_stopped = True
        self.controller.stop_processing()
                
        self.progress_var.set("Processing stopped by user")
        self.current_file_var.set("")
        
        # Unlock the UI
        self.unlock_ui_after_processing()
        
        # Clear distribution settings if they exist
        if hasattr(self.controller, 'distribution_settings'):
            self.controller.distribution_settings = None
        
    def clear_queue(self):
        """Clear the file queue with confirmation"""
        if self.rendering:
            messagebox.showwarning("Cannot Clear", "Processing is in progress. Stop processing first.")
            return
            
        if not self.file_paths:
            return
            
        if messagebox.askyesno("Confirm Clear", f"Are you sure you want to clear all {len(self.file_paths)} files from the queue?"):
            self.file_paths = []
            
            # Clear UI elements - both sides
            for label in self.folder_labels:
                label.destroy()
            self.folder_labels = []
            
            for label in self.output_preview_labels:
                label.destroy()
            self.output_preview_labels = []
            
            self.update_file_count()
            self.current_file_var.set("")
            
            # FIXED: Show the drop indicator again when queue is empty
            self.drop_indicator.grid(row=1, column=0, pady=20, sticky="ew")
            
            # Deselect any selected file
            self.deselect_file()
            
            logging.info("Queue cleared")
        
    def upload_to_drive(self, only_file=None):
        """Handle the upload button click - Admin only"""
        # Check admin status first
        if not self._is_current_user_admin():
            messagebox.showwarning(
                "Access Denied", 
                "Upload to Drive feature is only available to administrators.",
                parent=self
            )
            return
        
        # Get the output folder
        output_folder = self.output_entry.get().strip()
        
        # Validate the output folder
        if not output_folder or not os.path.isdir(output_folder):
            messagebox.showerror("Invalid Folder", "Please specify a valid output folder")
            return
        
        # Call the controller's upload method
        self.controller.upload_to_drive(output_folder, only_file)

    def apply_settings(self, settings_dict):
        """Apply settings to UI components - SIMPLIFIED VERSION"""
        try:
            # Use settings manager directly instead of duplicating logic
            if "output_folder" in settings_dict:
                self.output_entry.delete(0, tk.END)
                self.output_entry.insert(0, settings_dict["output_folder"])
                
            if "music_folder" in settings_dict:
                self.music_entry.delete(0, tk.END)
                self.music_entry.insert(0, settings_dict["music_folder"])
                
            if "loop_duration" in settings_dict:
                self.duration_input.delete(0, tk.END)
                self.duration_input.insert(0, str(settings_dict["loop_duration"]))
                self.update_duration_display(int(settings_dict.get("loop_duration", 3600)))
                
            if "sheet_url" in settings_dict:
                self.sheet_entry.delete(0, tk.END)
                self.sheet_entry.insert(0, settings_dict["sheet_url"])
                
            if "sheet_preset" in settings_dict and settings_dict["sheet_preset"] in self.controller.get_sheet_presets():
                self.sheet_dropdown.set(settings_dict["sheet_preset"])
                
            if "use_default_song_count" in settings_dict:
                self.use_default_song_count.set(settings_dict["use_default_song_count"])
                
            if "default_song_count" in settings_dict:
                self.new_song_count_var.set(str(settings_dict["default_song_count"]))
                
            if "fade_audio" in settings_dict:
                self.fade_audio_var.set(settings_dict["fade_audio"])
                
            if "export_timestamp" in settings_dict:
                self.export_timestamp_var.set(settings_dict["export_timestamp"])
                
            if "auto_upload" in settings_dict:
                self.auto_upload_var.set(settings_dict["auto_upload"])
                
            if "transition" in settings_dict:
                self.transition_var.set(settings_dict["transition"])

            self.toggle_song_count()
            logging.debug("Settings applied to UI successfully")
            
        except Exception as e:
            logging.error(f"Error applying settings to UI: {e}")

    def on_setting_changed(self, setting_name, value):
        """Handle when a setting is changed through the UI"""
        try:
            # Map UI setting names to settings manager paths
            setting_map = {
                'output_folder': 'ui.output_folder',
                'music_folder': 'ui.music_folder',
                'loop_duration': 'ui.loop_duration',
                'sheet_url': 'sheets.sheet_url',
                'sheet_preset': 'sheets.sheet_preset',
                'use_default_song_count': 'processing.use_default_song_count',
                'default_song_count': 'processing.default_song_count',
                'fade_audio': 'processing.fade_audio',
                'export_timestamp': 'processing.export_timestamp',
                'auto_upload': 'processing.auto_upload',
                'transition': 'processing.transition'
            }
            
            # Get the settings path
            settings_path = setting_map.get(setting_name)
            if settings_path:
                # Save the setting
                self.settings_manager.set(settings_path, value)
                logging.debug(f"Saved setting {settings_path} = {value}")
            else:
                logging.warning(f"Unknown setting name: {setting_name}")
                
        except Exception as e:
            logging.error(f"Error saving setting {setting_name}: {e}")

    # 2. Modify the get_current_settings method to include auto_upload (if not already present)
    def get_current_settings(self):
        """Get current settings from UI elements - SIMPLIFIED VERSION"""
        try:
            return {
                "output_folder": self.output_entry.get().strip(),
                "music_folder": self.music_entry.get().strip(),
                "loop_duration": self.duration_input.get().strip(),
                "sheet_url": self.sheet_entry.get().strip(),
                "sheet_preset": self.sheet_dropdown.get(),
                "use_default_song_count": self.use_default_song_count.get(),
                "default_song_count": self.new_song_count_var.get(),
                "fade_audio": self.fade_audio_var.get(),
                "export_timestamp": self.export_timestamp_var.get(),
                "auto_upload": self.auto_upload_var.get(),
                "transition": self.transition_var.get()  # ADD THIS
            }
        except Exception as e:
            logging.error(f"Error getting current settings: {e}")
            return {}

    def on_close(self):
        """Handle window close event - SIMPLIFIED VERSION"""
        if self.rendering:
            if not messagebox.askyesno("Confirm Exit", "Processing is in progress. Are you sure you want to exit?"):
                return
            self.stop_processing()
        
        try:
            # Save current settings using settings manager directly
            current_settings = self.get_current_settings()
            for key, value in current_settings.items():
                if key in ["output_folder", "music_folder", "loop_duration"]:
                    self.settings_manager.set(f"ui.{key}", value)
                elif key in ["sheet_url", "sheet_preset"]:
                    self.settings_manager.set(f"sheets.{key}", value)
                elif key in ["use_default_song_count", "default_song_count", "fade_audio", "export_timestamp", "auto_upload"]:
                    self.settings_manager.set(f"processing.{key}", value)
            
            # Close utility window
            if self.utility_window:
                try:
                    self.utility_window.following_active = False
                    self.utility_window.destroy()
                except Exception:
                    pass
                    
        except Exception as e:
            logging.error(f"Error during window close: {e}")
        
        try:
            self.destroy()
        except Exception:
            import sys
            sys.exit(0)

    def on_close_handler(self):
        """Handle application close - save settings"""
        try:
            # Save current UI state before closing
            self.save_ui_settings()
            
            # Save window geometry if tracking enabled
            if self.settings_manager.get("advanced.track_window_position", True):
                try:
                    geometry = self.ui.geometry()
                    self.settings_manager.set("ui.window_geometry", geometry, save=False)
                    
                    x = self.ui.winfo_rootx()
                    y = self.ui.winfo_rooty()
                    self.settings_manager.set("ui.window_position", f"{x},{y}")
                    
                except Exception as e:
                    logging.debug(f"Could not save window position: {e}")
                    
        except Exception as e:
            logging.error(f"Error during application close: {e}")

    def create_context_menu(self):
        """Create the context menu for folders/files"""
        self.context_menu = tk.Menu(self, tearoff=0, bg="#333333", fg="#ffffff", activebackground="#1f538d")
        self.context_menu.add_command(label="Remove Selected", command=self.remove_selected_file)
        self.context_menu.add_command(label="Clear All", command=self.clear_queue)
        
        # Add context menu to the folder frame
        self.folder_frame.bind("<Button-3>", self.show_context_menu)

    def show_context_menu(self, event):
        """Show context menu for the folder frame"""
        if not self.file_paths or self.rendering:
            return
        
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def update_file_display(self):
        """Update both file lists with easier selection capabilities"""
        # Clear existing displays
        for label in self.folder_labels:
            label.destroy()
        self.folder_labels = []
        
        for label in self.output_preview_labels:
            label.destroy()
        self.output_preview_labels = []
        
        # Deselect any selected file first
        self.deselect_file()
        
        # FIXED: Always check if we should show/hide the drop indicator
        if not self.file_paths:
            # Show the drop indicator when no files
            self.drop_indicator.grid(row=1, column=0, pady=20, sticky="ew")
            self.remove_selected_button.configure(state="disabled")
            return
        else:
            # Hide the drop indicator when files exist
            self.drop_indicator.grid_forget()
        
        duration = 3600  # Default to 3600s (1h) - matches the default input
        try:
            if hasattr(self, 'duration_input') and self.duration_input.get().strip():
                duration_text = self.duration_input.get().strip()
                if duration_text.isdigit():
                    duration = int(duration_text)
                else:
                    # Fallback to settings if input is invalid
                    duration = int(self.settings_manager.get("ui.loop_duration", "3600"))
            else:
                # If duration_input doesn't exist yet, use settings
                duration = int(self.settings_manager.get("ui.loop_duration", "3600"))
        except:
            duration = 3600  # Final fallback
        
        h, m, s = format_duration(duration)
        time_suffix = f"{h}h" if h > 0 else ""
        time_suffix += f"{m}m" if m > 0 else ""
        time_suffix += f"{s}s" if s > 0 else ""
        
        # Group files by their parent folder
        folders_dict = {}
        for path in self.file_paths:
            folder_path = os.path.dirname(path)
            folder_name = os.path.basename(folder_path)
            
            if folder_path not in folders_dict:
                folders_dict[folder_path] = {
                    "name": folder_name,
                    "files": []
                }
            folders_dict[folder_path]["files"].append(path)
        
        # Add all folders and files to both displays
        for folder_path, folder_data in folders_dict.items():
            folder_name = folder_data["name"]
            
            # Left side - Folder header
            folder_container = ctk.CTkFrame(self.folder_frame, fg_color="#1e2124", corner_radius=6)
            folder_container.pack(anchor="w", fill="x", padx=5, pady=3)
            
            # Create a selectable folder header with clear visual feedback
            folder_header = ctk.CTkButton(
                folder_container, 
                text=f"📁 {folder_name}",
                anchor="w",
                fg_color="transparent",
                text_color="#00bfff",
                hover_color="#2a4264",
                font=("Segoe UI", 12, "bold"),
                height=30,
                command=lambda fp=folder_path, btn=None: self.select_item(fp, is_folder=True, button=btn)
            )
            folder_header.pack(anchor="w", fill="x", padx=5, pady=(5, 0))
            folder_header._command = lambda fp=folder_path, btn=folder_header: self.select_item(fp, is_folder=True, button=btn)
            
            self.folder_labels.append(folder_container)
            
            # Right side - Output folder header (non-selectable)
            output_folder_container = ctk.CTkFrame(self.output_preview_frame, fg_color="#1e2124", corner_radius=6)
            output_folder_container.pack(anchor="w", fill="x", padx=5, pady=3)
            
            output_folder_header = ctk.CTkLabel(
                output_folder_container, 
                text=f"📁 {folder_name}", 
                anchor="w", 
                text_color="#00bfff",
                font=("Segoe UI", 12, "bold")
            )
            output_folder_header.pack(anchor="w", fill="x", padx=5, pady=(5, 0))
            
            self.output_preview_labels.append(output_folder_container)
            
            # Add files with indentation
            files_container_left = ctk.CTkFrame(folder_container, fg_color="transparent")
            files_container_left.pack(anchor="w", fill="x", padx=15, pady=(0, 5))
            
            files_container_right = ctk.CTkFrame(output_folder_container, fg_color="transparent")
            files_container_right.pack(anchor="w", fill="x", padx=15, pady=(0, 5))
            
            for file_path in folder_data["files"]:
                # Left side - Original file with button for easier selection
                file_button = ctk.CTkButton(
                    files_container_left,
                    text=f"🎬 {os.path.basename(file_path)}",
                    anchor="w",
                    fg_color="transparent",
                    hover_color="#2a4264",
                    text_color="#bbb",
                    height=25,
                    command=lambda fp=file_path, btn=None: self.select_item(fp, is_folder=False, button=btn)
                )
                file_button.pack(anchor="w", fill="x", pady=(0, 2))
                file_button._command = lambda fp=file_path, btn=file_button: self.select_item(fp, is_folder=False, button=btn)
                
                self.folder_labels.append(file_button)
                
                # Right side - Output preview (non-selectable)
                base_name = os.path.splitext(os.path.basename(file_path))[0]
                output_name = f"{base_name}_{time_suffix}.mp4"
                
                output_label = ctk.CTkLabel(
                    files_container_right, 
                    text=f"⟹ {output_name}", 
                    anchor="w", 
                    text_color="#8cffb0"  # Light green color for output
                )
                output_label.pack(anchor="w", fill="x", pady=(0, 2))
                
                self.output_preview_labels.append(output_label)

    def select_item(self, path, is_folder=False, button=None):
        """Select an item (file or folder) with clear visual feedback"""
        if self.rendering:
            return
        
        # Deselect previous selection
        self.deselect_file()
        
        # Store selection information
        self.selected_file = {
            "path": path,
            "button": button,
            "is_folder": is_folder
        }
        
        # Highlight the selected button
        if button:
            button.configure(fg_color="#1f538d")
        
        # Enable remove button
        self.remove_selected_button.configure(state="normal")
        
        # Update status text
        if is_folder:
            folder_name = os.path.basename(path)
            self.status_label.configure(text=f"Selected folder: {folder_name}")
        else:
            file_name = os.path.basename(path)
            self.status_label.configure(text=f"Selected file: {file_name}")

    def deselect_file(self):
        """Remove selection highlight"""
        if hasattr(self, 'selected_file') and self.selected_file:
            # Reset highlight on button
            if self.selected_file.get("button"):
                self.selected_file["button"].configure(fg_color="transparent")
            
            # Clear selection data
            self.selected_file = None
            
            # Disable remove button
            self.remove_selected_button.configure(state="disabled")
            
            # Reset status text
            count = len(self.file_paths)
            if count > 0:
                self.status_label.configure(text=f"🎬 {count} file{'s' if count > 1 else ''} queued")
            else:
                self.status_label.configure(text="Drag video files here")

    def remove_selected_file(self):
        """Remove the selected file or folder from the queue"""
        if self.rendering or not hasattr(self, 'selected_file') or not self.selected_file:
            return
        
        if self.selected_file["is_folder"]:
            # If folder selected, remove all files in that folder
            folder_path = self.selected_file["path"]
            folder_name = os.path.basename(folder_path)
            original_count = len(self.file_paths)
            
            self.file_paths = [path for path in self.file_paths if os.path.dirname(path) != folder_path]
            removed_count = original_count - len(self.file_paths)
            
            logging.info(f"Removed folder '{folder_name}' containing {removed_count} files")
            messagebox.showinfo("Files Removed", f"Removed {removed_count} files from folder '{folder_name}'")
        else:
            # If file selected, remove just that file
            file_path = self.selected_file["path"]
            file_name = os.path.basename(file_path)
            
            if file_path in self.file_paths:
                self.file_paths.remove(file_path)
                logging.info(f"Removed file: {file_name}")
                messagebox.showinfo("File Removed", f"Removed '{file_name}'")
        
        # Clear selection
        self.deselect_file()
        
        # Update UI
        self.update_file_count()
        self.update_file_display()
        
        # FIXED: Show drop indicator if queue becomes empty
        if not self.file_paths:
            self.drop_indicator.grid(row=1, column=0, pady=20, sticky="ew")

    # Event handlers
    def on_output_folder_change(self, event=None):
        """Handle output folder change"""
        path = self.output_entry.get().strip()
        if path:
            self.settings_manager.set("ui.output_folder", path)

    def on_music_folder_change(self, event=None):
        """Handle music folder change"""
        path = self.music_entry.get().strip()
        if path:
            self.settings_manager.set("ui.music_folder", path)

    def on_duration_change(self, event=None):
        """Handle duration change"""
        duration = self.duration_input.get().strip()
        if duration.isdigit():
            self.settings_manager.set("ui.loop_duration", duration)
    
    def on_sheet_url_change(self, event=None):
        """Handle Google Sheet URL change"""
        url = self.sheet_entry.get().strip()
        result = self.validate_path(
            url, 
            self.validate_sheet_url,
            "sheet_url", 
            self.sheet_entry,
            error_message="The URL doesn't appear to be a valid Google Sheets URL.\nPlease check the URL and try again."
        )
        
        if result and isinstance(result, tuple) and len(result) >= 3:
            _, converted_url, was_converted = result
            
            # Update entry with converted URL if needed
            if was_converted:
                self.sheet_entry.delete(0, tk.END)
                self.sheet_entry.insert(0, converted_url)
                self.controller.save_setting("sheet_url", converted_url)
                
                # Show conversion notification
                messagebox.showinfo(
                    "URL Converted", 
                    "The Google Sheet URL has been converted to a direct access format for better compatibility.", 
                    parent=self
                )
    
    def _darken_color(self, hex_color, factor=0.15):
        """Darken a hex color by a factor (0-1)"""
        # Skip the '#' and convert to RGB
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        
        # Darken each component
        r = max(0, int(r * (1 - factor)))
        g = max(0, int(g * (1 - factor)))
        b = max(0, int(b * (1 - factor)))
        
        # Convert back to hex
        return f"#{r:02x}{g:02x}{b:02x}"

    def send_debug_info(self):
        """Handle the Send Debug Info button click"""
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
            
            # Show processing message
            self.progress_var.set("Sending debug information...")
            self.update_idletasks()
            
            # Send the debug info
            success = send_debug_info_to_support_enhanced()
            
            if success:
                messagebox.showinfo(
                    "Debug Info Sent", 
                    "Your debug information has been sent successfully!\n\n"
                    "Support can now review your logs to help with any issues.",
                    parent=self
                )
                self.progress_var.set("Debug information sent successfully")
            else:
                messagebox.showerror(
                    "Failed to Send", 
                    "Failed to send debug information.\n"
                    "Please check your internet connection and try again.",
                    parent=self
                )
                self.progress_var.set("Failed to send debug information")
                
        except Exception as e:
            logging.error(f"Error sending debug info: {e}")
            messagebox.showerror(
                "Error", 
                f"An error occurred while sending debug information:\n{str(e)}",
                parent=self
            )

    def show_admin_monitoring(self):
        """Show the admin monitoring dashboard"""
        try:
            self.controller.api_monitor.show_dashboard(parent_window=self)
        except Exception as e:
            logging.error(f"Error opening admin dashboard: {e}")
            messagebox.showerror(
                "Dashboard Error", 
                f"Failed to open monitoring dashboard:\n{str(e)}", 
                parent=self
            )

    def show_distribution_modal(self):
        """Show the song pool distribution modal - UPDATED"""
        if self.rendering:
            messagebox.showwarning("Processing in Progress", "Cannot configure distribution while processing.", parent=self)
            return
        
        if not self.sheet_entry.get().strip():
            messagebox.showwarning("No Sheet URL", "Please configure a Google Sheet URL first.", parent=self)
            return
        
        if not self.file_paths:
            messagebox.showwarning("No Files", "Please add some video files to the queue first.", parent=self)
            return
        
        # Import here to avoid circular imports
        from song_distribution_modal import SongPoolDistributionModal
        
        modal = SongPoolDistributionModal(self, self.controller)
        modal.wait_window()  # This blocks until modal is closed

    def logout_user(self):
        """Handle user logout"""
        # Ask for confirmation
        result = messagebox.askyesno(
            "Confirm Logout", 
            "Are you sure you want to logout?\n\nYou'll need to sign in again to continue using the application.",
            parent=self
        )
        
        if result:
            try:
                # Import the logout function
                from auth_module.email_auth import logout
                
                # Clear authentication data
                if logout():
                    logging.info("User logged out successfully")
                    
                    # Show success message
                    messagebox.showinfo(
                        "Logged Out", 
                        "You have been logged out successfully.\nThe application will now close.",
                        parent=self
                    )
                    
                    # Close the application
                    self.destroy()
                    
                    # Exit the application completely
                    import sys
                    sys.exit(0)
                    
                else:
                    messagebox.showerror(
                        "Logout Failed", 
                        "Failed to logout. Please try again.",
                        parent=self
                    )
                    
            except Exception as e:
                logging.error(f"Error during logout: {e}")
                messagebox.showerror(
                    "Logout Error", 
                    f"An error occurred during logout:\n{str(e)}",
                    parent=self
                )

    def _is_current_user_admin(self):
        """Check if current user is admin - REUSE existing check"""
        try:
            # Use controller's existing admin check
            return self.controller.is_admin_user()
        except Exception as e:
            logging.debug(f"Error checking admin status: {e}")
            return False

    def _configure_upload_access(self):
        """Configure upload elements based on admin status"""
        is_admin = self._is_current_user_admin()
        
        # Configure auto-upload checkbox
        if is_admin:
            self.auto_upload_checkbox.configure(
                state="normal",
                text_color="#fff",
                text="Auto-upload after render"
            )
        else:
            self.auto_upload_checkbox.configure(
                state="disabled",
                text_color="#666",
                text="Auto-upload after render (Admin only)"
            )
            self.auto_upload_var.set(False)  # Ensure it's unchecked for non-admins
        
        # Configure upload button
        if is_admin:
            self.upload_button.configure(
                state="normal",
                fg_color="#17a2b8",
                hover_color="#138496",
                text="📤 Upload to Drive"
            )
        else:
            self.upload_button.configure(
                state="disabled",
                fg_color="#666666",
                hover_color="#666666",
                text="📤 Upload to Drive (Admin only)"
            )