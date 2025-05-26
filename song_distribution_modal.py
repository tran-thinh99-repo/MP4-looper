import tkinter as tk
from utils import center_window
from icon_helper import set_window_icon

class SongPoolDistributionModal(tk.Toplevel):
    """Modern Song Pool Distribution Modal with beautiful UI"""
    
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
        
        # Configure window
        self.configure(bg=self.colors['bg_primary'])
        self.title("🎵 Song Distribution Studio")
        self.geometry("700x800")
        self.resizable(True, True)
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        # State variables
        self.num_videos_var = tk.StringVar(value="7")
        self.distribution_method_var = tk.StringVar(value="sequential")
        self.total_songs = 0
        self.song_distribution = []
        
        # Create modern UI
        self.create_modern_ui()
        
        # Load data
        self.update_song_count()
        
        # Center window
        center_window()
    
    def create_modern_ui(self):
        """Create beautiful modern UI"""
        # Main container with gradient effect
        self.main_frame = tk.Frame(self, bg=self.colors['bg_primary'])
        self.main_frame.pack(fill="both", expand=True)
        
        # Create header section
        self.create_header()
        
        # Create stats section
        self.create_stats_section()
        
        # Create settings section
        self.create_settings_section()
        
        # Create preview section
        self.create_preview_section()
        
        # Create action buttons
        self.create_action_buttons()
    
    def create_header(self):
        """Create modern header with gradient effect"""
        header_frame = tk.Frame(self.main_frame, bg=self.colors['bg_primary'], height=120)
        header_frame.pack(fill="x", padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        # Create gradient canvas
        canvas = tk.Canvas(header_frame, height=120, highlightthickness=0)
        canvas.pack(fill="x")
        
        # Draw gradient background
        def draw_gradient():
            width = canvas.winfo_width()
            if width > 1:  # Only draw if canvas has been sized
                # Clear canvas
                canvas.delete("all")
                
                # Create gradient
                for i in range(width):
                    ratio = i / width
                    # Interpolate between gradient colors
                    color = self.interpolate_color(
                        self.colors['gradient_start'], 
                        self.colors['gradient_end'], 
                        ratio
                    )
                    canvas.create_line(i, 0, i, 120, fill=color, width=1)
                
                # Add title text with shadow effect
                # Shadow
                canvas.create_text(
                    width//2 + 2, 42, 
                    text="🎵 Song Distribution Studio", 
                    font=("Segoe UI", 24, "bold"),
                    fill="#000000",
                    anchor="center"
                )
                # Main text
                canvas.create_text(
                    width//2, 40, 
                    text="🎵 Song Distribution Studio", 
                    font=("Segoe UI", 24, "bold"),
                    fill=self.colors['text_primary'],
                    anchor="center"
                )
                
                # Subtitle
                canvas.create_text(
                    width//2, 70, 
                    text="Create unique song combinations for each video", 
                    font=("Segoe UI", 12),
                    fill=self.colors['text_secondary'],
                    anchor="center"
                )
        
        # Bind to configure event to redraw gradient when window resizes
        canvas.bind('<Configure>', lambda e: draw_gradient())
        
        # Initial draw after a short delay
        self.after(10, draw_gradient)
    
    def create_stats_section(self):
        """Create modern stats cards"""
        stats_frame = tk.Frame(self.main_frame, bg=self.colors['bg_primary'])
        stats_frame.pack(fill="x", padx=30, pady=20)
        
        # Songs info card
        self.songs_card = self.create_info_card(
            stats_frame, 
            "📊", 
            "Total Songs Available", 
            "Loading...",
            self.colors['success']
        )
        self.songs_card.pack(fill="x")
    
    def create_settings_section(self):
        """Create modern settings section"""
        settings_container = tk.Frame(self.main_frame, bg=self.colors['bg_primary'])
        settings_container.pack(fill="x", padx=30, pady=(0, 20))
        
        # Settings card
        settings_card = self.create_card(settings_container)
        settings_card.pack(fill="x")
        
        # Card header
        header_frame = tk.Frame(settings_card, bg=self.colors['bg_card'])
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        title_label = tk.Label(
            header_frame,
            text="⚙️ Distribution Settings",
            font=("Segoe UI", 16, "bold"),
            fg=self.colors['text_primary'],
            bg=self.colors['bg_card']
        )
        title_label.pack(anchor="w")
        
        # Settings content
        content_frame = tk.Frame(settings_card, bg=self.colors['bg_card'])
        content_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        # Number of videos
        self.create_video_count_section(content_frame)
        
        # Distribution method
        self.create_distribution_method_section(content_frame)
        
        # Stats display
        self.create_calculation_display(content_frame)
    
    def create_video_count_section(self, parent):
        """Create video count selection with modern slider"""
        section_frame = tk.Frame(parent, bg=self.colors['bg_card'])
        section_frame.pack(fill="x", pady=(0, 20))
        
        # Label
        label = tk.Label(
            section_frame,
            text="Number of Videos",
            font=("Segoe UI", 12, "bold"),
            fg=self.colors['text_primary'],
            bg=self.colors['bg_card']
        )
        label.pack(anchor="w", pady=(0, 10))
        
        # Slider container
        slider_frame = tk.Frame(section_frame, bg=self.colors['bg_card'])
        slider_frame.pack(fill="x")
        
        # Value display
        self.video_count_display = tk.Label(
            slider_frame,
            text="7",
            font=("Segoe UI", 20, "bold"),
            fg=self.colors['accent'],
            bg=self.colors['bg_card']
        )
        self.video_count_display.pack(side="left", padx=(0, 20))
        
        # Slider
        self.video_slider = tk.Scale(
            slider_frame,
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
            length=300,
            font=("Segoe UI", 10)
        )
        self.video_slider.pack(side="left", fill="x", expand=True)
    
    def create_distribution_method_section(self, parent):
        """Create distribution method selection with modern buttons"""
        section_frame = tk.Frame(parent, bg=self.colors['bg_card'])
        section_frame.pack(fill="x", pady=(0, 20))
        
        # Label
        label = tk.Label(
            section_frame,
            text="Distribution Method",
            font=("Segoe UI", 12, "bold"),
            fg=self.colors['text_primary'],
            bg=self.colors['bg_card']
        )
        label.pack(anchor="w", pady=(0, 10))
        
        # Button container
        button_frame = tk.Frame(section_frame, bg=self.colors['bg_card'])
        button_frame.pack(fill="x")
        
        # Sequential button
        self.sequential_btn = self.create_toggle_button(
            button_frame, "📊 Sequential", "sequential", True
        )
        self.sequential_btn.pack(side="left", padx=(0, 10))
        
        # Random button
        self.random_btn = self.create_toggle_button(
            button_frame, "🎲 Random", "random", False
        )
        self.random_btn.pack(side="left")
    
    def create_calculation_display(self, parent):
        """Create calculation display section"""
        calc_frame = tk.Frame(parent, bg=self.colors['bg_secondary'])
        calc_frame.pack(fill="x", pady=(10, 0))
        calc_frame.configure(relief="solid", bd=1)
        
        # Padding frame
        padded_frame = tk.Frame(calc_frame, bg=self.colors['bg_secondary'])
        padded_frame.pack(fill="x", padx=15, pady=15)
        
        # Songs per video
        self.songs_per_video_label = tk.Label(
            padded_frame,
            text="Songs per video: ~0 (auto-calculated)",
            font=("Segoe UI", 11),
            fg=self.colors['text_secondary'],
            bg=self.colors['bg_secondary']
        )
        self.songs_per_video_label.pack(anchor="w", pady=(0, 5))
        
        # Loops needed
        self.loops_info_label = tk.Label(
            padded_frame,
            text="Loops needed: ~0x to fill duration",
            font=("Segoe UI", 11),
            fg=self.colors['text_secondary'],
            bg=self.colors['bg_secondary']
        )
        self.loops_info_label.pack(anchor="w")
    
    def create_preview_section(self):
        """Create modern preview section"""
        preview_container = tk.Frame(self.main_frame, bg=self.colors['bg_primary'])
        preview_container.pack(fill="both", expand=True, padx=30, pady=(0, 20))
        
        # Preview card
        preview_card = self.create_card(preview_container)
        preview_card.pack(fill="both", expand=True)
        
        # Header
        header_frame = tk.Frame(preview_card, bg=self.colors['bg_card'])
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        title_label = tk.Label(
            header_frame,
            text="📋 Distribution Preview",
            font=("Segoe UI", 16, "bold"),
            fg=self.colors['text_primary'],
            bg=self.colors['bg_card']
        )
        title_label.pack(anchor="w")
        
        # Scrollable preview area
        preview_scroll_frame = tk.Frame(preview_card, bg=self.colors['bg_card'])
        preview_scroll_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Canvas and scrollbar for custom scrolling
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
        """Create modern action buttons"""
        button_container = tk.Frame(self.main_frame, bg=self.colors['bg_primary'])
        button_container.pack(fill="x", padx=30, pady=(0, 30))
        
        # Start button
        self.start_button = self.create_action_button(
            button_container,
            "▶ Start Processing",
            self.start_processing,
            self.colors['success'],
            "#00b894"
        )
        self.start_button.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        # Cancel button
        cancel_button = self.create_action_button(
            button_container,
            "✕ Cancel",
            self.cancel,
            self.colors['bg_secondary'],
            "#636e72"
        )
        cancel_button.pack(side="left", fill="x", expand=True, padx=(10, 0))
    
    # Helper methods for creating UI components
    def create_card(self, parent):
        """Create a modern card container"""
        card = tk.Frame(
            parent, 
            bg=self.colors['bg_card'],
            relief="solid",
            bd=1
        )
        return card
    
    def create_info_card(self, parent, icon, title, value, accent_color):
        """Create an info card with icon and stats"""
        card = self.create_card(parent)
        
        # Content frame
        content = tk.Frame(card, bg=self.colors['bg_card'])
        content.pack(fill="x", padx=20, pady=20)
        
        # Icon and title
        header_frame = tk.Frame(content, bg=self.colors['bg_card'])
        header_frame.pack(fill="x", pady=(0, 10))
        
        icon_label = tk.Label(
            header_frame,
            text=icon,
            font=("Segoe UI", 20),
            fg=accent_color,
            bg=self.colors['bg_card']
        )
        icon_label.pack(side="left", padx=(0, 10))
        
        title_label = tk.Label(
            header_frame,
            text=title,
            font=("Segoe UI", 12, "bold"),
            fg=self.colors['text_primary'],
            bg=self.colors['bg_card']
        )
        title_label.pack(side="left", anchor="w")
        
        # Value
        value_label = tk.Label(
            content,
            text=value,
            font=("Segoe UI", 16, "bold"),
            fg=accent_color,
            bg=self.colors['bg_card']
        )
        value_label.pack(anchor="w")
        
        # Store reference to value label
        card.value_label = value_label
        
        return card
    
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
            font=("Segoe UI", 11, "bold"),
            relief="flat",
            bd=0,
            padx=20,
            pady=10,
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
            padx=20,
            pady=15,
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
    
    def interpolate_color(self, color1, color2, ratio):
        """Interpolate between two hex colors"""
        # Remove # and convert to RGB
        r1, g1, b1 = int(color1[1:3], 16), int(color1[3:5], 16), int(color1[5:7], 16)
        r2, g2, b2 = int(color2[1:3], 16), int(color2[3:5], 16), int(color2[5:7], 16)
        
        # Interpolate
        r = int(r1 + (r2 - r1) * ratio)
        g = int(g1 + (g2 - g1) * ratio)
        b = int(b1 + (b2 - b1) * ratio)
        
        return f"#{r:02x}{g:02x}{b:02x}"
    
    # Event handlers (keeping the original functionality)
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
        """Update the total song count (simplified for demo)"""
        # This would normally connect to your actual song counting logic
        self.total_songs = 302  # Example value
        self.songs_card.value_label.configure(
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
        
        # Calculate loops (example)
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
        
        # Create preview items
        for i in range(num_videos):
            self.create_preview_item(i + 1)
    
    def create_preview_item(self, video_num):
        """Create a modern preview item"""
        # Calculate distribution for this video
        songs_per_video = self.total_songs // int(self.num_videos_var.get())
        start_song = (video_num - 1) * songs_per_video + 1
        end_song = start_song + songs_per_video - 1
        
        # Item container
        item_frame = tk.Frame(
            self.preview_frame, 
            bg=self.colors['bg_card'],
            relief="solid",
            bd=1
        )
        item_frame.pack(fill="x", padx=10, pady=5)
        
        # Content
        content_frame = tk.Frame(item_frame, bg=self.colors['bg_card'])
        content_frame.pack(fill="x", padx=15, pady=15)
        
        # Video header
        header_frame = tk.Frame(content_frame, bg=self.colors['bg_card'])
        header_frame.pack(fill="x", pady=(0, 10))
        
        video_icon = tk.Label(
            header_frame,
            text="🎬",
            font=("Segoe UI", 16),
            fg=self.colors['accent'],
            bg=self.colors['bg_card']
        )
        video_icon.pack(side="left", padx=(0, 10))
        
        video_label = tk.Label(
            header_frame,
            text=f"Video {video_num}",
            font=("Segoe UI", 14, "bold"),
            fg=self.colors['text_primary'],
            bg=self.colors['bg_card']
        )
        video_label.pack(side="left")
        
        # Song range
        range_label = tk.Label(
            content_frame,
            text=f"Songs {start_song}-{end_song} ({songs_per_video} songs)",
            font=("Segoe UI", 11),
            fg=self.colors['text_secondary'],
            bg=self.colors['bg_card']
        )
        range_label.pack(anchor="w")
        
        # Progress bar visualization
        progress_frame = tk.Frame(content_frame, bg=self.colors['bg_card'])
        progress_frame.pack(fill="x", pady=(10, 0))
        
        # Create visual progress bar
        progress_bg = tk.Frame(
            progress_frame, 
            bg=self.colors['bg_secondary'], 
            height=8
        )
        progress_bg.pack(fill="x")
        
        # Fill based on song count
        max_songs = self.total_songs // int(self.num_videos_var.get()) + 10
        fill_ratio = min(1.0, songs_per_video / max_songs)
        
        progress_fill = tk.Frame(
            progress_bg, 
            bg=self.colors['success'], 
            height=8
        )
        progress_fill.place(x=0, y=0, relwidth=fill_ratio, height=8)
    
    def start_processing(self):
        """Start processing - placeholder"""
        # This would connect to your actual processing logic
        print("Starting processing with distribution mode...")
        self.destroy()
    
    def cancel(self):
        """Cancel and close"""
        self.destroy()