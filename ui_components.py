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
from utils import center_window

# Configure UI Theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

class BatchProcessorUI(TkinterDnD.Tk):
    def __init__(self, app_controller):
        super().__init__()
        self.title("MP4 Batch Processor")
        self.geometry("900x900")
        self.configure(bg="#1a1a1a")
        
        # Reference to the main application controller
        self.controller = app_controller
        
        # UI state variables
        self.file_paths = []
        self.rendering = False
        self.was_stopped = False
        self.current_file_index = -1
        self.folder_labels = []
        self.output_preview_labels = []
        self.selected_file = None
        
        # Initialize duration display variable that was missing
        self.duration_display_var = tk.StringVar(value="(1h)")
        
        # Create and lay out the UI components
        self.create_ui()
        
        # Center window on screen
        self.after(100, lambda: center_window(self))
        
        # Set up close protocol
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_ui(self):
        # Main container with padding
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Use grid system with incremental rows
        main_container.grid_columnconfigure(0, weight=1)
        r = 0  # Start row counter
        
        # === Drag and Drop Zone ===
        # Create a frame for stats above the drop zone
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
        
        # Create the drop area with darker background 
        self.drop_area = ctk.CTkFrame(main_container, fg_color="#1e1e1e", corner_radius=10)
        self.drop_area.grid(row=r, column=0, sticky="nsew", pady=(0, 10), padx=5)
        main_container.grid_rowconfigure(r, weight=1)  # Make this row expandable
        r += 1
        
        # Split the drop area into two columns
        drop_area_content = ctk.CTkFrame(self.drop_area, fg_color="transparent")
        drop_area_content.pack(fill="both", expand=True, padx=10, pady=10)
        drop_area_content.grid_columnconfigure(0, weight=1)
        drop_area_content.grid_columnconfigure(1, weight=1)
        drop_area_content.grid_rowconfigure(0, weight=1)
        
        # Left side - File queue
        drop_zone_left = ctk.CTkFrame(drop_area_content, fg_color="#232323", corner_radius=8)
        drop_zone_left.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        
        # Header for raw preview
        raw_header = ctk.CTkLabel(
            drop_zone_left, 
            text="Raw Preview", 
            text_color="#00bfff",
            font=("Segoe UI", 14, "bold")
        )
        raw_header.pack(pady=(10, 5))

        drop_zone_left.pack_propagate(False)

        # Add drop indicator (will be hidden when files are added)
        self.drop_indicator = ctk.CTkLabel(drop_zone_left, text="🡇 Drag video files or folders here 🡇",
                                    fg_color="transparent", text_color="#00bfff",
                                    font=("Segoe UI", 16, "bold"), height=100)
        self.drop_indicator.place(relx=0.5, rely=0.5, anchor="center")
        
        # Create a scrollable frame for showing added files
        self.folder_frame = ctk.CTkScrollableFrame(drop_zone_left, fg_color="transparent")
        self.folder_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Register the drop zone and indicator for drag and drop
        drop_zone_left.drop_target_register(DND_FILES)
        drop_zone_left.dnd_bind("<<Drop>>", self.on_drop)
        self.drop_indicator.drop_target_register(DND_FILES)
        self.drop_indicator.dnd_bind("<<Drop>>", self.on_drop)
        
        # Change style when hovering over drop zone
        drop_zone_left.bind("<Enter>", lambda e: drop_zone_left.configure(fg_color="#2a2a2a"))
        drop_zone_left.bind("<Leave>", lambda e: drop_zone_left.configure(fg_color="#232323"))
        
        # Right side - Output preview
        drop_zone_right = ctk.CTkFrame(drop_area_content, fg_color="#232323", corner_radius=8)
        drop_zone_right.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

        # Header for output preview
        output_header = ctk.CTkLabel(
            drop_zone_right, 
            text="Output Preview", 
            text_color="#00bfff",
            font=("Segoe UI", 14, "bold")
        )
        output_header.pack(pady=(10, 5))
        
        drop_zone_right.pack_propagate(False)

        # Create a scrollable frame for showing output file names
        self.output_preview_frame = ctk.CTkScrollableFrame(drop_zone_right, fg_color="transparent")
        self.output_preview_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Synchronize scrolling
        def _on_mousewheel(event):
            # Scroll both frames together
            self.folder_frame._parent_canvas.yview_scroll(int(-1*(event.delta/20)), "units")
            self.output_preview_frame._parent_canvas.yview_scroll(int(-1*(event.delta/20)), "units")
            return "break"  # Prevent default scrolling

        # Bind the mousewheel event to both frames
        self.folder_frame.bind_all("<MouseWheel>", _on_mousewheel)

        # File management buttons frame
        file_buttons_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        file_buttons_frame.grid(row=r, column=0, sticky="ew", pady=5)
        r += 1
        
        # Evenly distribute file management buttons
        file_buttons_frame.grid_columnconfigure(0, weight=1)
        file_buttons_frame.grid_columnconfigure(1, weight=1)
        file_buttons_frame.grid_columnconfigure(2, weight=1)
        
        # Add Browse Files button
        browse_button = ctk.CTkButton(
            file_buttons_frame,
            text="Browse Files",
            command=self.browse_files
        )
        browse_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        # Add Clear Queue button
        self.clear_button = ctk.CTkButton(
            file_buttons_frame,
            text="🗑 Clear Queue",
            command=self.clear_queue,
            fg_color="#6c757d",  # Gray
            hover_color="#5a6268"
        )
        self.clear_button.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # Add Remove Selected button
        self.remove_selected_button = ctk.CTkButton(
            file_buttons_frame,
            text="Remove Selected",
            command=self.remove_selected_file,
            fg_color="#dc3545",  # Red
            hover_color="#c82333",
            state="disabled"  # Initially disabled
        )
        self.remove_selected_button.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        
        # === Duration Input ===
        # Use the improved duration section that contains duration_display_var
        self.create_duration_section(main_container, r)
        r += 1
        
        # Output folder section
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
        
        # Google Sheet section
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
        
        # Options section
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
        
        # Control buttons
        control_frame = ctk.CTkFrame(main_container)
        control_frame.grid(row=r, column=0, sticky="ew", pady=10)
        r += 1
        
        # Use horizontal layout for controls with modern styling
        self.start_button = ctk.CTkButton(
            control_frame,
            text="▶ Start Processing",
            command=self.start_processing,
            fg_color="#28a745",  # Green
            hover_color="#218838"
        )
        self.start_button.pack(side="left", padx=5, fill="x", expand=True)
        
        self.stop_button = ctk.CTkButton(
            control_frame,
            text="⏹ Stop",
            command=self.stop_processing,
            state="disabled",
            fg_color="#dc3545",  # Red
            hover_color="#c82333"
        )
        self.stop_button.pack(side="left", padx=5, fill="x", expand=True)
        
        self.upload_button = ctk.CTkButton(
            control_frame,
            text="📤 Upload to Drive",
            command=self.upload_to_drive,  # This should call the method above
            fg_color="#17a2b8",  # Teal
            hover_color="#138496"
        )
        self.upload_button.pack(side="left", padx=5, fill="x", expand=True)
        
        # Progress tracking
        progress_frame = ctk.CTkFrame(main_container)
        progress_frame.grid(row=r, column=0, sticky="ew", pady=10)
        r += 1
        
        # Modernized progress bar style
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
        
        # Debug section with better layout
        debug_frame = ctk.CTkFrame(main_container)
        debug_frame.grid(row=r, column=0, sticky="ew", pady=10)
        r += 1

        # Create a sub-frame to hold the buttons in a row with equal width
        buttons_frame = ctk.CTkFrame(debug_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", expand=True)
        buttons_frame.columnconfigure(0, weight=1)
        buttons_frame.columnconfigure(1, weight=1)
        buttons_frame.columnconfigure(2, weight=1)

        self.debug_button = ctk.CTkButton(
            buttons_frame,
            text="Show Debug Log",
            command=self.show_debug_log,
            fg_color="#6c757d",  # Gray
            hover_color="#5a6268"
        )
        self.debug_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

        self.clean_uploads_button = ctk.CTkButton(
            buttons_frame,
            text="Clean Canceled Uploads",
            command=self.clean_canceled_uploads,
            fg_color="#6c757d",  # Gray
            hover_color="#5a6268"
        )
        self.clean_uploads_button.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        # Add help button
        self.help_button = ctk.CTkButton(
            buttons_frame,
            text="❓ Help",
            command=self.show_help,
            fg_color="#6c757d",  # Gray
            hover_color="#5a6268"
        )
        self.help_button.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        
        # Initialize the missing attribute for showing current file
        self.current_file_var = tk.StringVar(value="")
        
        # Create a context menu for file management
        self.create_context_menu()

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
        # The duration_display_var was moved to __init__
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
        
        # Add input validation and display update
        self.duration_input.bind("<KeyRelease>", self.validate_and_display_duration)
        self.duration_input.bind("<FocusOut>", self.validate_and_display_duration)
        
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
        """Adjust the duration by the specified number of seconds"""
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
            
            # Update the display
            self.update_duration_display(new_duration)
            
            # Save the new duration in settings
            self.controller.save_setting("loop_duration", str(new_duration))
            
        except ValueError:
            # If the current value isn't a valid integer, reset to 600 (10 minutes)
            self.duration_input.delete(0, tk.END)
            self.duration_input.insert(0, "3600")
            self.update_duration_display(3600)

    def validate_and_display_duration(self, event=None):
        """Validate the duration input and update the display"""
        current_text = self.duration_input.get().strip()
        
        # If empty, set to 3600 (1 hour)
        if not current_text:
            self.duration_input.delete(0, tk.END)
            self.duration_input.insert(0, "3600")
            self.update_duration_display(3600)
            return
        
        try:
            # Try to convert to an integer
            duration = int(current_text)
            
            # Enforce minimum value of 1 second
            if duration < 1:
                duration = 1
                self.duration_input.delete(0, tk.END)
                self.duration_input.insert(0, "1")
            
            # Update the display
            self.update_duration_display(duration)
            
            # Save the duration in settings
            self.controller.save_setting("loop_duration", str(duration))
            
        except ValueError:
            # If not a valid integer, reset to previous value or 3600
            self.duration_input.delete(0, tk.END)
            self.duration_input.insert(0, "3600")
            self.update_duration_display(3600)

    def update_duration_display(self, seconds):
        """Update the display showing the duration in h:m:s format"""
        h, m, s = self.format_duration_display(seconds)
        
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

    def format_duration_display(self, seconds):
        """Format seconds into hours, minutes, seconds for display"""
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        return h, m, s

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

        # Hide the drop indicator only when first items are being added
        if not self.file_paths and new_items:
            self.drop_indicator.place_forget()

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
        
        # Hide the drop indicator if first files are being added
        if len(self.file_paths) == len(new_items):
            self.drop_indicator.place_forget()
        
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
        """Browse for output folder"""
        folder = filedialog.askdirectory()
        if folder:
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, folder)
            self.controller.save_setting("output_folder", folder)

    def browse_music(self):
        """Browse for music folder"""
        folder = filedialog.askdirectory()
        if folder:
            self.music_entry.delete(0, tk.END)
            self.music_entry.insert(0, folder)
            self.controller.save_setting("music_folder", folder)

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
        """Apply a preset sheet URL"""
        url = self.controller.get_sheet_preset_url(selected)
        if url:
            self.sheet_entry.delete(0, tk.END)
            self.sheet_entry.insert(0, url)
            self.controller.save_setting("sheet_preset", selected)
            self.controller.save_setting("sheet_url", url)
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
        """Start processing the queued files"""
        if not self.file_paths:
            messagebox.showwarning("No Files", "No files are queued for processing")
            return
            
        if not self.validate_inputs():
            return
            
        # Validate song list CSV
        if not self.controller.handle_song_csv_validation(self.sheet_entry.get().strip()):
            return
            
        self.rendering = True
        self.was_stopped = False
        self.current_file_index = 0
        
        # Update UI state
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        
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
            "auto_upload": self.auto_upload_var.get()
        }
        
        # Start processing thread
        threading.Thread(target=self.controller.process_files, args=(params, self), daemon=True).start()

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
        """Reset UI after processing is complete"""
        self.rendering = False
        self.progress_var.set("Processing complete")
        self.current_file_var.set("")
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        
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
        """Stop all processing"""
        if not self.rendering:
            return
            
        confirm = messagebox.askyesno("Confirm Stop", "Are you sure you want to stop processing?")
        if not confirm:
            return
            
        self.rendering = False
        self.was_stopped = True
        self.controller.stop_processing()
                
        self.progress_var.set("Processing stopped")
        self.current_file_var.set("")
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        
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
            
            # Show the drop indicator again
            self.drop_indicator.place(relx=0.5, rely=0.5, anchor="center")
            
            logging.info("Queue cleared")
        
    def upload_to_drive(self, only_file=None):
        """Handle the upload button click"""
        # Get the output folder
        output_folder = self.output_entry.get().strip()
        
        # Validate the output folder
        if not output_folder or not os.path.isdir(output_folder):
            messagebox.showerror("Invalid Folder", "Please specify a valid output folder")
            return
        
        # Call the controller's upload method
        self.controller.upload_to_drive(output_folder, only_file)

    def apply_settings(self, settings):
        """Apply loaded settings to UI elements"""
        if "output_folder" in settings:
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, settings["output_folder"])
            
        if "music_folder" in settings:
            self.music_entry.delete(0, tk.END)
            self.music_entry.insert(0, settings["music_folder"])
            
        if "sheet_url" in settings:
            self.sheet_entry.delete(0, tk.END)
            self.sheet_entry.insert(0, settings["sheet_url"])
            
        if "sheet_preset" in settings and settings["sheet_preset"] in self.controller.get_sheet_presets():
            self.sheet_dropdown.set(settings["sheet_preset"])
            
        if "loop_duration" in settings:
            self.duration_input.delete(0, tk.END)
            self.duration_input.insert(0, settings["loop_duration"])
            try:
                duration = int(settings["loop_duration"])
                self.update_duration_display(duration)
            except ValueError:
                # If not a valid integer, set a default
                self.duration_input.delete(0, tk.END)
                self.duration_input.insert(0, "600")
                self.update_duration_display(600)
            
        if "use_default_song_count" in settings:
            self.use_default_song_count.set(settings["use_default_song_count"])
            
        if "default_song_count" in settings:
            self.new_song_count_var.set(str(settings["default_song_count"]))
            
        # Add auto-upload setting
        if "auto_upload" in settings:
            self.auto_upload_var.set(settings["auto_upload"])
            
        if "fade_audio" in settings:
            self.fade_audio_var.set(settings["fade_audio"])
            
        if "export_timestamp" in settings:
            self.export_timestamp_var.set(settings["export_timestamp"])
            
        # Update UI state based on settings
        self.toggle_song_count()

    # 2. Modify the get_current_settings method to include auto_upload (if not already present)
    def get_current_settings(self):
        """Get current settings from UI elements"""
        return {
            "output_folder": self.output_entry.get().strip(),
            "music_folder": self.music_entry.get().strip(),
            "sheet_url": self.sheet_entry.get().strip(),
            "sheet_preset": self.sheet_dropdown.get(),
            "loop_duration": self.duration_input.get(),
            "use_default_song_count": self.use_default_song_count.get(),
            "default_song_count": self.new_song_count_var.get(),
            "auto_upload": self.auto_upload_var.get(),  # Add auto-upload preference
            "fade_audio": self.fade_audio_var.get(),
            "export_timestamp": self.export_timestamp_var.get(),
        }

    def on_close(self):
        """Handle window close event"""
        if self.rendering:
            if not messagebox.askyesno("Confirm Exit", "Processing is in progress. Are you sure you want to exit?"):
                return
            
            # Stop processing
            self.stop_processing()
        
        # Save settings before exit
        self.controller.save_settings(self.get_current_settings())
        
        # Destroy window, but wrap in a try/except to suppress any Tkinter errors during shutdown
        try:
            self.destroy()
        except Exception:
            # Just ignore any errors during window destruction
            import sys
            sys.exit(0)  # Force exit cleanly

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
        
        # If no files, show the drop indicator
        if not self.file_paths:
            self.drop_indicator.place(relx=0.5, rely=0.5, anchor="center")
            self.remove_selected_button.configure(state="disabled")
            return
        else:
            self.drop_indicator.place_forget()
        
        # Get the current duration for output file naming
        duration = 600  # Default to 600s (10m)
        if self.duration_input.get().isdigit():
            duration = int(self.duration_input.get())
        
        h, m, s = self.format_duration(duration)
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

    def format_duration(self, seconds):
        """Format seconds into hours, minutes, seconds"""
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        return h, m, s

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

    def setup_validated_entry(self, parent, label_text, entry_var=None, callback=None):
        """Create a standardized entry with validation"""
        # Create containing frame
        entry_row = ctk.CTkFrame(parent, fg_color="transparent")
        entry_row.pack(pady=5, fill="x")
        
        # Add label
        ctk.CTkLabel(entry_row, text=label_text, width=120, anchor="w").pack(side="left", padx=(0, 10))
        
        # Create entry with variable if provided
        entry = ctk.CTkEntry(entry_row, textvariable=entry_var) if entry_var else ctk.CTkEntry(entry_row)
        entry.pack(side="left", padx=5, fill="x", expand=True)
        
        # Set up validation if callback provided
        if callback:
            # Focus and key bindings
            entry.bind("<FocusOut>", callback)
            entry.bind("<Return>", callback)
            # Paste binding
            entry.bind("<Control-v>", lambda e: self.after(50, callback))
            # Context menu
            self.setup_paste_menu(entry, callback)
            
        return entry_row, entry
    
    def setup_paste_menu(self, entry_widget, validation_callback):
        """Set up a right-click paste menu for entry widgets with validation"""
        paste_menu = tk.Menu(self, tearoff=0, bg="#333333", fg="#ffffff", activebackground="#1f538d")
        paste_menu.add_command(label="Paste", command=lambda: self.paste_and_validate(entry_widget, validation_callback))
        entry_widget.bind("<Button-3>", lambda e: self.show_paste_menu(e, paste_menu))
        entry_widget._paste_menu = paste_menu  # Prevent garbage collection
    
    def show_paste_menu(self, event, menu):
        """Show the paste context menu"""
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
    
    def paste_and_validate(self, entry_widget, validation_callback):
        """Paste from clipboard and then validate the entry"""
        try:
            clipboard_content = self.clipboard_get()
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, clipboard_content)
            self.after(50, validation_callback)
        except Exception as e:
            logging.error(f"Paste error: {e}")
    
    def set_entry_feedback(self, entry_widget, is_valid, message=None, show_dialog=True):
        """Provide visual feedback for entry validation"""
        # Visual feedback with color
        original_color = entry_widget.cget("fg_color")
        feedback_color = "#2a5d2a" if is_valid else "#5d2a2a"  # Green for valid, red for invalid
        
        entry_widget.configure(fg_color=feedback_color)
        self.after(500, lambda: entry_widget.configure(fg_color=original_color))
        
        # Show dialog message if provided and requested
        if message and show_dialog:
            dialog_type = messagebox.showinfo if is_valid else messagebox.showwarning
            dialog_type(
                "Validation " + ("Success" if is_valid else "Warning"),
                message,
                parent=self
            )
    
    def validate_path(self, path, validate_func, setting_name, entry_widget, success_message=None, error_message=None):
        """Common validation logic for path entries"""
        if not path:
            return
        
        # Clean the path
        path = path.strip().strip('"\'')
        entry_widget.delete(0, tk.END)
        entry_widget.insert(0, path)
        
        # Validate and give feedback
        result = validate_func(path)
        is_valid = result if not isinstance(result, (tuple, list)) else result[0]
        
        if is_valid:
            # Save validated path to settings
            self.controller.save_setting(setting_name, path)
            # Visual feedback
            message = success_message if success_message else f"'{path}' is valid."
            self.set_entry_feedback(entry_widget, True, message, show_dialog=bool(success_message))
            logging.info(f"{setting_name} validated and saved: {path}")
            return result
        else:
            # Invalid feedback
            message = error_message if error_message else f"'{path}' is invalid."
            self.set_entry_feedback(entry_widget, False, message, show_dialog=True)
            return False
    
    # Validation methods
    def validate_output_folder(self, path):
        """Validate output folder path and create if doesn't exist"""
        try:
            folder_path = Path(path)
            
            # Create if doesn't exist
            if not folder_path.exists():
                folder_path.mkdir(parents=True, exist_ok=True)
                logging.info(f"Created output folder: {folder_path}")
            
            # Verify directory and permissions
            if not folder_path.is_dir():
                return False
                
            # Test write permissions
            test_file = folder_path / ".write_test"
            try:
                test_file.touch()
                test_file.unlink()
            except PermissionError:
                return False
                
            return True
        except Exception as e:
            logging.error(f"Output folder validation error: {e}")
            return False
    
    def validate_music_folder(self, path):
        """Validate music folder path and check for WAV files"""
        try:
            folder_path = Path(path)
            
            # Basic validation
            if not folder_path.exists() or not folder_path.is_dir():
                return False
            
            # Check for WAV files
            wav_files = list(folder_path.glob("*.wav"))
            has_wav_files = bool(wav_files)
            
            # Find subdirectories with WAV files if none at root
            subdirs_with_wav = []
            if not has_wav_files:
                for subdir in folder_path.glob("**/"):
                    if list(subdir.glob("*.wav")) and subdir != folder_path:
                        subdirs_with_wav.append(subdir.relative_to(folder_path))
            
            # Return validation result with extra info
            return (True, has_wav_files, subdirs_with_wav)
        except Exception as e:
            logging.error(f"Music folder validation error: {e}")
            return False
    
    def validate_sheet_url(self, url):
        """Validate Google Sheet URL with enhanced checks"""
        if not url:
            return False
        
        # Clean the URL
        url = url.strip().strip('"\'')
        
        # Check URL pattern
        sheets_patterns = [
            r'https://docs\.google\.com/spreadsheets/d/([a-zA-Z0-9_-]+)',
            r'https://docs\.google\.com/spreadsheets/d/e/([a-zA-Z0-9_-]+)'
        ]
        
        is_valid_url = any(re.match(pattern, url) for pattern in sheets_patterns)
        if not is_valid_url:
            return False
        
        # Convert edit URLs to direct access format
        if "edit" in url or "#gid=" in url:
            try:
                sheet_id_match = re.search(r'/d/([a-zA-Z0-9_-]+)', url)
                gid_match = re.search(r'gid=(\d+)', url)
                
                if sheet_id_match:
                    sheet_id = sheet_id_match.group(1)
                    gid = gid_match.group(1) if gid_match else "0"
                    direct_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&gid={gid}"
                    
                    return (True, direct_url, True)  # (valid, converted_url, was_converted)
            except Exception as e:
                logging.error(f"Failed to convert sheet URL: {e}")
        
        return (True, url, False)  # (valid, same_url, no_conversion)
    
    # Event handlers
    def on_output_folder_change(self, event=None):
        """Handle output folder path change"""
        path = self.output_entry.get().strip()
        result = self.validate_path(
            path, 
            self.validate_output_folder,
            "output_folder", 
            self.output_entry,
            success_message=None,  # No message for success
            error_message=f"The folder '{path}' is invalid or not writable.\nPlease check the path and try again."
        )
    
    def on_music_folder_change(self, event=None):
        """Handle music folder path change"""
        path = self.music_entry.get().strip()
        result = self.validate_path(
            path, 
            self.validate_music_folder,
            "music_folder", 
            self.music_entry,
            error_message=f"The folder '{path}' is invalid or doesn't exist.\nPlease check the path and try again."
        )
        
        if result and isinstance(result, tuple) and len(result) >= 3:
            _, has_wav_files, subdirs_with_wav = result
            
            # Show warning if no WAV files at root level
            if not has_wav_files:
                if subdirs_with_wav:
                    top_subdirs = subdirs_with_wav[:5]
                    more_count = len(subdirs_with_wav) - 5 if len(subdirs_with_wav) > 5 else 0
                    
                    subdirs_text = "\n".join(str(d) for d in top_subdirs)
                    if more_count:
                        subdirs_text += f"\n... and {more_count} more"
                    
                    messagebox.showinfo(
                        "WAV Files in Subdirectories", 
                        f"No WAV files found at the root level of the selected folder.\n\n"
                        f"However, WAV files were found in these subdirectories:\n\n"
                        f"{subdirs_text}", 
                        parent=self
                    )
                else:
                    messagebox.showwarning(
                        "No WAV Files", 
                        f"The folder '{path}' doesn't contain any WAV files.\n"
                        "Please select a folder containing WAV files.", 
                        parent=self
                    )
    
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
        self.duration_display_var = tk.StringVar(value="(10m)")
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
        self.duration_input.insert(0, "600")  # Default to 10 minutes
        
        # Add input validation and display update
        self.duration_input.bind("<KeyRelease>", self.validate_and_display_duration)
        self.duration_input.bind("<FocusOut>", self.validate_and_display_duration)
        
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
        self.update_duration_display(600)
        
        return duration_frame

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

    def adjust_duration(self, seconds):
        """Adjust the duration by the specified number of seconds"""
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
            
            # Update the display
            self.update_duration_display(new_duration)
            
            # Save the new duration in settings
            self.controller.save_setting("loop_duration", str(new_duration))
            
        except ValueError:
            # If the current value isn't a valid integer, reset to 600 (10 minutes)
            self.duration_input.delete(0, tk.END)
            self.duration_input.insert(0, "600")
            self.update_duration_display(600)

    def validate_and_display_duration(self, event=None):
        """Validate the duration input and update the display"""
        current_text = self.duration_input.get().strip()
        
        # If empty, set to 600 (10 minutes)
        if not current_text:
            self.duration_input.delete(0, tk.END)
            self.duration_input.insert(0, "600")
            self.update_duration_display(600)
            return
        
        try:
            # Try to convert to an integer
            duration = int(current_text)
            
            # Enforce minimum value of 1 second
            if duration < 1:
                duration = 1
                self.duration_input.delete(0, tk.END)
                self.duration_input.insert(0, "1")
            
            # Update the display
            self.update_duration_display(duration)
            
            # Save the duration in settings
            self.controller.save_setting("loop_duration", str(duration))
            
        except ValueError:
            # If not a valid integer, reset to previous value or 600
            self.duration_input.delete(0, tk.END)
            self.duration_input.insert(0, "600")
            self.update_duration_display(600)

    def update_duration_display(self, seconds):
        """Update the display showing the duration in h:m:s format"""
        h, m, s = self.format_duration_display(seconds)
        
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

    def format_duration_display(self, seconds):
        """Format seconds into hours, minutes, seconds for display"""
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        return h, m, s