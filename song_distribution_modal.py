import tkinter as tk
import logging
from utils import center_window
from icon_helper import set_window_icon

class SongPoolDistributionModal(tk.Toplevel):
    """Compact Song Pool Distribution Modal - Better width utilization"""
    
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.parent = parent
        self.controller = controller
        
        # Set icon
        set_window_icon(self)
        
        # Modern dark theme colors
        self.colors = {
            'bg_primary': '#0f0f23',      # Deep dark blue
            'bg_secondary': '#1a1a2e',    # Darker blue
            'bg_card': '#16213e',         # Card background
            'accent': '#e94560',          # Pink/red accent
            'accent_hover': '#ff6b85',    # Lighter pink
            'text_primary': '#ffffff',    # White text
            'text_secondary': '#a0a0a0',  # Gray text
            'success': '#00d4aa',         # Teal green
            'warning': '#ffa726',         # Orange
            'gradient_start': '#667eea',  # Blue gradient start
            'gradient_end': '#764ba2'     # Purple gradient end
        }
        
        # Configure window - MUCH SMALLER AND WIDER
        self.configure(bg=self.colors['bg_primary'])
        self.title("🎵 Song Distribution Studio")
        self.geometry("900x600")  # Changed from 700x800 to 900x600 (wider, shorter)
        self.resizable(True, True)
        self.minsize(800, 500)  # Set minimum size
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        # State variables
        self.num_videos_var = tk.StringVar(value="7")
        self.distribution_method_var = tk.StringVar(value="sequential")
        self.total_songs = 0
        self.song_distribution = []
        
        # Create compact UI
        self.create_compact_ui()
        
        # Load data
        self.update_song_count()
        
        # Center window
        center_window(self)

        # Set up close protocol to clear distribution mode
        self.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def create_compact_ui(self):
        """Create compact UI using horizontal layout"""
        # Main container
        self.main_frame = tk.Frame(self, bg=self.colors['bg_primary'])
        self.main_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # TOP: Header (smaller)
        self.create_compact_header()
        
        # MIDDLE: Two-column layout for settings and preview
        self.create_main_content()
        
        # BOTTOM: Action buttons
        self.create_action_buttons()
    
    def create_compact_header(self):
        """Create a more compact header"""
        header_frame = tk.Frame(self.main_frame, bg=self.colors['bg_primary'], height=60)
        header_frame.pack(fill="x", pady=(0, 15))
        header_frame.pack_propagate(False)
        
        # Title and subtitle in one line
        title_frame = tk.Frame(header_frame, bg=self.colors['bg_primary'])
        title_frame.pack(expand=True)
        
        title_label = tk.Label(
            title_frame,
            text="🎵 Song Distribution Studio",
            font=("Segoe UI", 20, "bold"),
            fg=self.colors['text_primary'],
            bg=self.colors['bg_primary']
        )
        title_label.pack()
        
        subtitle_label = tk.Label(
            title_frame,
            text="Create unique song combinations for each video",
            font=("Segoe UI", 11),
            fg=self.colors['text_secondary'],
            bg=self.colors['bg_primary']
        )
        subtitle_label.pack()
    
    def create_main_content(self):
        """Create main content in two-column layout"""
        content_frame = tk.Frame(self.main_frame, bg=self.colors['bg_primary'])
        content_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        # Configure columns: Left 40%, Right 60%
        content_frame.grid_columnconfigure(0, weight=2)  # Settings column
        content_frame.grid_columnconfigure(1, weight=3)  # Preview column
        content_frame.grid_rowconfigure(0, weight=1)
        
        # LEFT COLUMN: Settings
        self.create_settings_column(content_frame)
        
        # RIGHT COLUMN: Preview
        self.create_preview_column(content_frame)
    
    def create_settings_column(self, parent):
        """Create the left settings column"""
        settings_frame = tk.Frame(parent, bg=self.colors['bg_card'])
        settings_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        # Settings header
        settings_header = tk.Label(
            settings_frame,
            text="⚙️ Settings",
            font=("Segoe UI", 16, "bold"),
            fg=self.colors['text_primary'],
            bg=self.colors['bg_card']
        )
        settings_header.pack(pady=(15, 10))
        
        # Stats card (compact)
        self.create_compact_stats(settings_frame)
        
        # Number of videos section
        self.create_video_count_section(settings_frame)
        
        # Distribution method section
        self.create_distribution_method_section(settings_frame)
        
        # Calculation display (compact)
        self.create_compact_calculation_display(settings_frame)
    
    def create_compact_stats(self, parent):
        """Create compact stats display"""
        stats_frame = tk.Frame(parent, bg=self.colors['bg_secondary'])
        stats_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        stats_content = tk.Frame(stats_frame, bg=self.colors['bg_secondary'])
        stats_content.pack(padx=10, pady=10)
        
        # Icon and text in one line
        icon_label = tk.Label(
            stats_content,
            text="📊",
            font=("Segoe UI", 16),
            fg=self.colors['success'],
            bg=self.colors['bg_secondary']
        )
        icon_label.pack(side="left", padx=(0, 8))
        
        text_frame = tk.Frame(stats_content, bg=self.colors['bg_secondary'])
        text_frame.pack(side="left")
        
        title_label = tk.Label(
            text_frame,
            text="Total Songs Available",
            font=("Segoe UI", 11, "bold"),
            fg=self.colors['text_primary'],
            bg=self.colors['bg_secondary']
        )
        title_label.pack(anchor="w")
        
        self.songs_value_label = tk.Label(
            text_frame,
            text="Loading...",
            font=("Segoe UI", 14, "bold"),
            fg=self.colors['success'],
            bg=self.colors['bg_secondary']
        )
        self.songs_value_label.pack(anchor="w")
    
    def create_video_count_section(self, parent):
        """Create compact video count section"""
        section_frame = tk.Frame(parent, bg=self.colors['bg_card'])
        section_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        # Title
        title_label = tk.Label(
            section_frame,
            text="Number of Videos",
            font=("Segoe UI", 12, "bold"),
            fg=self.colors['text_primary'],
            bg=self.colors['bg_card']
        )
        title_label.pack(anchor="w", pady=(0, 8))
        
        # Horizontal layout for count and slider
        count_frame = tk.Frame(section_frame, bg=self.colors['bg_card'])
        count_frame.pack(fill="x")
        
        # Large number display
        self.video_count_display = tk.Label(
            count_frame,
            text="7",
            font=("Segoe UI", 24, "bold"),
            fg=self.colors['accent'],
            bg=self.colors['bg_card']
        )
        self.video_count_display.pack(side="left", padx=(0, 15))
        
        # Slider
        self.video_slider = tk.Scale(
            count_frame,
            from_=2, to=30,
            orient="horizontal",
            variable=self.num_videos_var,
            command=self.on_video_count_changed,
            bg=self.colors['bg_secondary'],
            fg=self.colors['text_primary'],
            activebackground=self.colors['accent'],
            highlightthickness=0,
            troughcolor=self.colors['bg_secondary'],
            sliderrelief="flat",
            length=180,
            font=("Segoe UI", 9)
        )
        self.video_slider.pack(side="left", fill="x", expand=True)
    
    def create_distribution_method_section(self, parent):
        """Create compact distribution method section"""
        section_frame = tk.Frame(parent, bg=self.colors['bg_card'])
        section_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        # Title
        title_label = tk.Label(
            section_frame,
            text="Distribution Method",
            font=("Segoe UI", 12, "bold"),
            fg=self.colors['text_primary'],
            bg=self.colors['bg_card']
        )
        title_label.pack(anchor="w", pady=(0, 8))
        
        # Horizontal button layout
        button_frame = tk.Frame(section_frame, bg=self.colors['bg_card'])
        button_frame.pack(fill="x")
        
        # Sequential button
        self.sequential_btn = self.create_toggle_button(
            button_frame, "📊 Sequential", "sequential", True
        )
        self.sequential_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        # Random button
        self.random_btn = self.create_toggle_button(
            button_frame, "🎲 Random", "random", False
        )
        self.random_btn.pack(side="left", fill="x", expand=True, padx=(5, 0))
    
    def create_compact_calculation_display(self, parent):
        """Create compact calculation display"""
        calc_frame = tk.Frame(parent, bg=self.colors['bg_secondary'])
        calc_frame.pack(fill="x", padx=15, pady=(0, 15))
        
        calc_content = tk.Frame(calc_frame, bg=self.colors['bg_secondary'])
        calc_content.pack(padx=10, pady=8)
        
        # Songs per video
        self.songs_per_video_label = tk.Label(
            calc_content,
            text="Songs per video: ~0 (auto-calculated)",
            font=("Segoe UI", 10),
            fg=self.colors['text_secondary'],
            bg=self.colors['bg_secondary']
        )
        self.songs_per_video_label.pack(anchor="w", pady=(0, 3))
        
        # Loops needed
        self.loops_info_label = tk.Label(
            calc_content,
            text="Loops needed: ~0x to fill duration",
            font=("Segoe UI", 10),
            fg=self.colors['text_secondary'],
            bg=self.colors['bg_secondary']
        )
        self.loops_info_label.pack(anchor="w")
    
    def create_preview_column(self, parent):
        """Create the right preview column"""
        preview_frame = tk.Frame(parent, bg=self.colors['bg_card'])
        preview_frame.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        
        # Preview header
        preview_header = tk.Label(
            preview_frame,
            text="📋 Distribution Preview",
            font=("Segoe UI", 16, "bold"),
            fg=self.colors['text_primary'],
            bg=self.colors['bg_card']
        )
        preview_header.pack(pady=(15, 10))
        
        # Scrollable preview area
        preview_scroll_frame = tk.Frame(preview_frame, bg=self.colors['bg_card'])
        preview_scroll_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # Canvas and scrollbar
        canvas = tk.Canvas(
            preview_scroll_frame,
            bg=self.colors['bg_secondary'],
            highlightthickness=0
        )
        scrollbar = tk.Scrollbar(preview_scroll_frame, orient="vertical", command=canvas.yview)
        self.preview_frame = tk.Frame(canvas, bg=self.colors['bg_secondary'])
        
        self.preview_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.preview_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def create_action_buttons(self):
        """Create compact action buttons"""
        button_frame = tk.Frame(self.main_frame, bg=self.colors['bg_primary'])
        button_frame.pack(fill="x")
        
        # Horizontal layout for buttons
        buttons_container = tk.Frame(button_frame, bg=self.colors['bg_primary'])
        buttons_container.pack()
        
        # Start button
        self.start_button = self.create_action_button(
            buttons_container,
            "▶ Start Processing",
            self.start_processing,
            self.colors['success'],
            "#00b894"
        )
        self.start_button.pack(side="left", padx=(0, 10))
        
        # Cancel button
        cancel_button = self.create_action_button(
            buttons_container,
            "✕ Cancel",
            self.cancel,
            self.colors['bg_secondary'],
            "#636e72"
        )
        cancel_button.pack(side="left", padx=(10, 0))
    
    # Keep all the existing helper methods (create_toggle_button, create_action_button, etc.)
    def create_toggle_button(self, parent, text, value, is_selected):
        """Create a modern toggle button"""
        def on_click():
            self.distribution_method_var.set(value)
            self.update_toggle_buttons()
            self.update_preview()
        
        if is_selected:
            bg_color = self.colors['accent']
            fg_color = self.colors['text_primary']
        else:
            bg_color = self.colors['bg_secondary']
            fg_color = self.colors['text_secondary']
        
        button = tk.Button(
            parent,
            text=text,
            command=on_click,
            bg=bg_color,
            fg=fg_color,
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            bd=0,
            padx=15,
            pady=8,
            cursor="hand2"
        )
        
        # Hover effects
        def on_enter(e):
            if not is_selected:
                button.configure(bg=self.colors['accent_hover'])
        
        def on_leave(e):
            if not is_selected:
                button.configure(bg=self.colors['bg_secondary'])
        
        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)
        
        return button
    
    def create_action_button(self, parent, text, command, bg_color, hover_color):
        """Create a modern action button"""
        button = tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg_color,
            fg=self.colors['text_primary'],
            font=("Segoe UI", 12, "bold"),
            relief="flat",
            bd=0,
            padx=25,
            pady=12,
            cursor="hand2"
        )
        
        # Hover effects
        def on_enter(e):
            button.configure(bg=hover_color)
        
        def on_leave(e):
            button.configure(bg=bg_color)
        
        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)
        
        return button
    
    # Keep all existing event handlers and methods
    def on_video_count_changed(self, value):
        """Handle video count change"""
        self.video_count_display.configure(text=value)
        self.update_calculations()
        self.update_preview()
    
    def update_toggle_buttons(self):
        """Update toggle button states"""
        selected_method = self.distribution_method_var.get()
        
        # Update sequential button
        if selected_method == "sequential":
            self.sequential_btn.configure(
                bg=self.colors['accent'],
                fg=self.colors['text_primary']
            )
        else:
            self.sequential_btn.configure(
                bg=self.colors['bg_secondary'],
                fg=self.colors['text_secondary']
            )
        
        # Update random button
        if selected_method == "random":
            self.random_btn.configure(
                bg=self.colors['accent'],
                fg=self.colors['text_primary']
            )
        else:
            self.random_btn.configure(
                bg=self.colors['bg_secondary'],
                fg=self.colors['text_secondary']
            )
    
    def update_song_count(self):
        """Update the total song count"""
        # Example value - replace with actual logic
        self.total_songs = 302
        self.songs_value_label.configure(
            text=f"{self.total_songs} songs from current sheet"
        )
        self.update_calculations()
        self.update_preview()
    
    def update_calculations(self):
        """Update calculations display"""
        if self.total_songs == 0:
            return
        
        num_videos = int(self.num_videos_var.get())
        songs_per_video = self.total_songs // num_videos
        
        self.songs_per_video_label.configure(
            text=f"Songs per video: ~{songs_per_video} (auto-calculated)"
        )
        
        # Calculate loops
        duration_seconds = 3600  # 1 hour example
        avg_song_duration = 240  # 4 minutes
        duration_per_chunk = songs_per_video * avg_song_duration
        loops_needed = max(1, duration_seconds // duration_per_chunk)
        
        self.loops_info_label.configure(
            text=f"Loops needed: ~{loops_needed}x to fill {duration_seconds//3600}h"
        )
    
    def update_preview(self):
        """Update the preview display"""
        # Clear existing preview
        for widget in self.preview_frame.winfo_children():
            widget.destroy()
        
        if self.total_songs == 0:
            return
        
        num_videos = int(self.num_videos_var.get())
        
        # Create compact preview items
        for i in range(min(num_videos, 10)):  # Show max 10 for performance
            self.create_compact_preview_item(i + 1)
    
    def create_compact_preview_item(self, video_num):
        """Create a compact preview item"""
        # Calculate distribution for this video
        songs_per_video = self.total_songs // int(self.num_videos_var.get())
        start_song = (video_num - 1) * songs_per_video + 1
        end_song = start_song + songs_per_video - 1
        
        # Compact item container
        item_frame = tk.Frame(
            self.preview_frame,
            bg=self.colors['bg_card'],
            relief="solid",
            bd=1
        )
        item_frame.pack(fill="x", padx=8, pady=3)
        
        # Single row layout
        content_frame = tk.Frame(item_frame, bg=self.colors['bg_card'])
        content_frame.pack(fill="x", padx=10, pady=8)
        
        # Video icon and number (left)
        video_info = tk.Frame(content_frame, bg=self.colors['bg_card'])
        video_info.pack(side="left")
        
        video_icon = tk.Label(
            video_info,
            text="🎬",
            font=("Segoe UI", 14),
            fg=self.colors['accent'],
            bg=self.colors['bg_card']
        )
        video_icon.pack(side="left", padx=(0, 8))
        
        video_label = tk.Label(
            video_info,
            text=f"Video {video_num}",
            font=("Segoe UI", 12, "bold"),
            fg=self.colors['text_primary'],
            bg=self.colors['bg_card']
        )
        video_label.pack(side="left")
        
        # Song range (right)
        range_label = tk.Label(
            content_frame,
            text=f"Songs {start_song}-{end_song} ({songs_per_video} songs)",
            font=("Segoe UI", 10),
            fg=self.colors['text_secondary'],
            bg=self.colors['bg_card']
        )
        range_label.pack(side="right")
    
    def start_processing(self):
        """Start processing with distribution mode"""
        try:
            # Validate inputs first
            if self.total_songs == 0:
                tk.messagebox.showerror("No Songs", "No songs available for distribution. Please check your Google Sheet URL.", parent=self)
                return
                
            num_videos = int(self.num_videos_var.get())
            if num_videos < 2:
                tk.messagebox.showerror("Invalid Count", "Number of videos must be at least 2.", parent=self)
                return
            
            # Create distribution settings
            distribution_settings = {
                'enabled': True,
                'num_videos': num_videos,
                'distribution_method': self.distribution_method_var.get(),
                'song_distribution': self.calculate_song_ranges()
            }
            
            # Store distribution settings in the controller
            self.controller.distribution_settings = distribution_settings
            
            # Close the modal
            self.destroy()
            
            # Start processing on the main UI
            # This will trigger the distributed processing mode
            self.parent.start_processing()
            
        except Exception as e:
            tk.messagebox.showerror("Error", f"Failed to start processing:\n{str(e)}", parent=self)
    
    def calculate_song_ranges(self):
        """Calculate song ranges for each video"""
        num_videos = int(self.num_videos_var.get())
        songs_per_video = self.total_songs // num_videos
        
        song_ranges = []
        for i in range(num_videos):
            start_idx = i * songs_per_video + 1
            end_idx = start_idx + songs_per_video - 1
            
            # For the last video, include any remaining songs
            if i == num_videos - 1:
                end_idx = self.total_songs
                
            song_ranges.append((start_idx, end_idx, songs_per_video))
        
        return song_ranges
    
    def cancel(self):
        """Cancel and close - clear distribution mode"""
        if hasattr(self.controller, 'distribution_settings'):
            self.controller.distribution_settings = None
            logging.info("🎵 Distribution mode cancelled")
        self.destroy()

    def on_close(self):
        """Handle modal close - clear distribution mode"""
        if hasattr(self.controller, 'distribution_settings'):
            self.controller.distribution_settings = None
            logging.info("🎵 Distribution mode disabled - modal closed")
        self.destroy()