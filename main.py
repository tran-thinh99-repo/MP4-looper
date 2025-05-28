# mp4_looper.py - FIXED API MONITOR SETUP
import os
import subprocess
import logging
import psutil
import re
import sys
import time
import customtkinter as ctk
from pathlib import Path
from tkinter import messagebox
from dotenv import load_dotenv

# Import modules from existing application
from icon_helper import set_window_icon
from utils import (setup_logging, disable_cmd_edit_mode, check_environment_vars, format_duration,
                  open_folder, check_canceled_upload_folder_status)
from song_utils import generate_distributed_song_lists, generate_song_list_for_batch
from post_render_check import validate_render
from config import GITHUB_REPO_NAME, GITHUB_REPO_OWNER, VERSION
from ui_components import BatchProcessorUI
from dependency_checker import main as check_dependencies
from paths import get_base_path, clean_folder_with_confirmation
from update_module.update_checker import UpdateChecker

from auth_module.email_auth import handle_authentication

from settings_manager import get_settings

class MP4LooperApp:
    def __init__(self):
        setup_logging()
        load_environment_variables()
        check_dependencies()
        
        # Initialize settings manager EARLY
        self.settings_manager = get_settings()
        check_environment_vars()
        self.initialized = False
        
        # Check authentication - ONLY use handle_authentication()
        if not handle_authentication():
            logging.warning("Authentication failed or cancelled. Exiting application.")
            sys.exit(0)

        # FIXED: Only initialize monitoring for admin users
        self.api_monitor = self._initialize_monitoring_if_admin()
        
        import gc
        gc.collect()
        
        # Application settings
        self.app_name = "MP4 Looper"

        # Load sheet presets from environment variables
        self.sheet_presets = {
            "Reggae": os.getenv("REGGAE_SHEET_URL", ""),
            "Gospel": os.getenv("GOSPEL_SHEET_URL", "")
        }
        
        # Initialize UI and other components
        self.ui = BatchProcessorUI(self)
        self.ui.title(f"{self.app_name} v{VERSION} by EAGLE NET")

        # One-line update check that will be shown after UI loads
        self.ui.after(1000, lambda: UpdateChecker(
            self.app_name, 
            VERSION, 
            GITHUB_REPO_OWNER, 
            GITHUB_REPO_NAME, 
        ).check_and_notify(self.ui))

        set_window_icon(self.ui)
        disable_cmd_edit_mode()

        # State variables
        self.current_process = None
        self.process_pid = None
        self.rendering = False
        self.was_stopped = False
        
        # Apply saved settings to UI
        self.apply_saved_settings()
        
        # Check for canceled uploads
        check_canceled_upload_folder_status()
        
        # Mark as successfully initialized
        self.initialized = True

    def _initialize_monitoring_if_admin(self):
        """Initialize monitoring only for admin users"""
        try:
            # Check if current user is admin BEFORE creating monitoring
            from auth_module.email_auth import get_current_user
            current_user = get_current_user()
            
            # List of admin emails
            admin_emails = ["admin@vicgmail.com"]
            
            if current_user and current_user in admin_emails:
                logging.info(f"🔧 Admin user detected: {current_user} - Initializing full monitoring")
                
                try:
                    from api_monitor_module import setup_monitoring
                    
                    api_monitor = setup_monitoring(
                        app_name="MP4 Looper",
                        admin_emails=admin_emails,
                        auto_cleanup=True
                    )
                    
                    # Set up global reference for monitor_access
                    import api_monitor_module.utils.monitor_access as monitor_access
                    monitor_access._api_monitor_cache = api_monitor
                    monitor_access._cache_checked = False
                    
                    # Test the monitoring system
                    stats = api_monitor.get_stats_summary()
                    logging.info(f"✅ Admin monitoring active - Total calls: {stats['overview']['total_calls_ever']}")
                    
                    return api_monitor
                    
                except ImportError as import_err:
                    logging.info(f"API monitoring module not available: {import_err}")
                    return self._create_dummy_monitor()
                    
                except Exception as setup_err:
                    logging.warning(f"API monitoring setup failed: {setup_err}")
                    return self._create_dummy_monitor()
            else:
                logging.info(f"👤 Regular user: {current_user} - Using lightweight monitoring")
                return self._create_dummy_monitor()
                
        except Exception as e:
            logging.error(f"❌ Error checking admin status: {e}")
            return self._create_dummy_monitor()

    def _create_dummy_monitor(self):
        """Create a lightweight dummy monitor that doesn't create files"""
        class DummyMonitor:
            def __init__(self):
                # No file creation, no storage, just basic functionality
                pass
                
            def is_admin_user(self, email=None): 
                if email is None:
                    try:
                        from auth_module.email_auth import get_current_user
                        email = get_current_user()
                    except ImportError:
                        return False
                admin_emails = ["admin@vicgmail.com"]
                return email in admin_emails
            
            def get_stats_summary(self):
                return {'overview': {'total_calls_ever': 0}}
            
            def record_custom_metric(self, *args, **kwargs):
                pass  # Do nothing - no tracking for non-admins
            
            def export_data(self, *args, **kwargs):
                return None
            
            def cleanup_old_data(self):
                pass  # No data to clean
                
            def show_dashboard(self, parent_window=None):
                from tkinter import messagebox
                messagebox.showinfo(
                    "Dashboard Unavailable", 
                    "The monitoring dashboard is only available to administrators.\n\n"
                    "Contact your system administrator for access.",
                    parent=parent_window
                )
        
        logging.info("✅ Lightweight monitoring created - no file storage for regular users")
        return DummyMonitor()
    
    def apply_saved_settings(self):
        """Apply saved settings to UI components - SIMPLIFIED VERSION"""
        try:
            # Get settings directly from settings manager
            settings = {
                "output_folder": self.settings_manager.get("ui.output_folder", os.getcwd()),
                "music_folder": self.settings_manager.get("ui.music_folder", ""),
                "loop_duration": self.settings_manager.get("ui.loop_duration", "3600"),
                "sheet_url": self.settings_manager.get("sheets.sheet_url", ""),
                "sheet_preset": self.settings_manager.get("sheets.sheet_preset", "Reggae"),
                "use_default_song_count": self.settings_manager.get("processing.use_default_song_count", True),
                "default_song_count": self.settings_manager.get("processing.default_song_count", "5"),
                "fade_audio": self.settings_manager.get("processing.fade_audio", True),
                "export_timestamp": self.settings_manager.get("processing.export_timestamp", True),
                "auto_upload": self.settings_manager.get("processing.auto_upload", False),
            }
            
            # Apply to UI
            self.ui.apply_settings(settings)
            logging.info("Settings applied to UI successfully")
            
        except Exception as e:
            logging.error(f"Error applying settings: {e}")

    def get_sheet_presets(self):
        """Return available sheet preset names for dropdown"""
        if self.sheet_presets:
            return list(self.sheet_presets.keys())
        return ["No Presets"]
    
    def get_sheet_preset_url(self, preset_name):
        """Get URL for a sheet preset"""
        return self.sheet_presets.get(preset_name, "")
    
    # When initializing the sheet dropdown in the UI
    def init_sheet_dropdown(self):
        # The controller is available as self.controller in your UI class
        presets = self.controller.get_sheet_presets()
        
        self.sheet_dropdown = ctk.CTkOptionMenu(
            self.sheet_row,
            values=presets,
            command=self.apply_preset_sheet_url,
            width=100
        )
        
        # Select first item by default if available
        if presets:
            self.sheet_dropdown.set(presets[0])

    def open_folder(self, path, label="Folder", parent=None):
        """Open a folder in file explorer"""
        open_folder(path, label, parent)
    
    def clean_folder(self, path, title="Confirm Cleanup", parent=None):
        """Clean a folder with confirmation"""
        clean_folder_with_confirmation(path, title, parent)
    
    def show_debug_log(self, parent=None):
        """Show the debug log file"""
        log_path = os.path.join(get_base_path(), "debug.log")
        if os.path.exists(log_path):
            try:
                os.startfile(log_path)  # Windows only
            except Exception as e:
                logging.error(f"Failed to open log file: {e}")
                messagebox.showerror("Error", f"Failed to open debug log: {e}", parent=parent)
        else:
            messagebox.showerror("Error", "Debug log not found", parent=parent)
    
    def clean_canceled_uploads(self, parent=None):
        """Clean canceled uploads from Google Drive"""
        path = Path(os.path.join(os.environ["LOCALAPPDATA"], "Google", "DriveFS", "canceled_uploads"))
        clean_folder_with_confirmation(path, "Clean Canceled Uploads", parent)

    def process_dropped_files(self, file_paths):
        """Process dropped files and return new items and duplicates"""
        new_items = []
        duplicates = []
        
        for path in file_paths:
            path = path.replace("{", "").replace("}", "")  # Clean up any braces from Windows paths
            
            if os.path.isdir(path):
                # Special folder handling: look for a file with the same name as the folder
                folder_name = os.path.basename(path)
                target_file = os.path.join(path, f"{folder_name}.mp4")
                
                if os.path.isfile(target_file) and "_edit" not in target_file.lower():
                    if target_file in self.ui.file_paths:
                        duplicates.append(target_file)
                        continue
                    # Add the file from within the folder
                    new_items.append(target_file)
                else:
                    # If no matching file found, scan for all valid MP4 files
                    mp4_files = []
                    try:
                        for file in os.listdir(path):
                            if file.lower().endswith('.mp4') and '_edit' not in file.lower():
                                full_path = os.path.join(path, file)
                                if full_path not in self.ui.file_paths:
                                    mp4_files.append(full_path)
                    except Exception as e:
                        logging.error(f"Error scanning folder {path}: {e}")
                    
                    if mp4_files:
                        # Add all valid MP4 files from the folder
                        new_items.extend(mp4_files)
                    else:
                        # Show a warning if no valid files found
                        messagebox.showwarning("No Valid Files", f"No valid MP4 files found in folder: {folder_name}")
                        
            elif os.path.isfile(path) and path.lower().endswith('.mp4'):
                # For individual files
                if path in self.ui.file_paths:
                    duplicates.append(path)
                    continue
                    
                new_items.append(path)
        
        return new_items, duplicates

    def process_selected_files(self, files):
        """Process manually selected files and return new items and duplicates"""
        new_items = []
        duplicates = []
        
        # Process each file
        for file in files:
            if file not in self.ui.file_paths:
                new_items.append(file)
            else:
                duplicates.append(file)
        
        return new_items, duplicates

    def handle_song_csv_validation(self, sheet_url):
        """Handle validation of song sheet data without downloading"""
        logging.info(f"Using Google Sheet directly from URL: {sheet_url}")
        return True

    def process_files(self, params, ui):
        """Process all files in the queue with enhanced progress tracking"""
        self.rendering = True
        ui.rendering = True
        
        # Check if we're in distribution mode
        distribution_settings = getattr(self, 'distribution_settings', None)
        
        if distribution_settings and distribution_settings.get('enabled'):
            # Process in distribution mode with progress
            self.process_files_distributed_with_progress(params, ui, distribution_settings)
            return
        
        file_paths = params["file_paths"]
        duration = params["duration"]
        output_folder = params["output_folder"]
        music_folder = params["music_folder"]
        sheet_url = params["sheet_url"]
        new_song_count = params["new_song_count"]
        export_timestamp = params["export_timestamp"]
        fade_audio = params["fade_audio"]
        auto_upload = params["auto_upload"]
        transition = params.get("transition", "None")
        
        total_files = len(file_paths)
        
        # STEP 1: Initial setup (5% progress)
        ui.update_progress(1, "🔧 Initializing batch processing...")
        time.sleep(0.5)  # Brief pause to show the message
        
        # Track batch processing start
        try:
            from api_monitor_module.utils.monitor_access import track_api_call_simple
            track_api_call_simple("batch_processing_start", success=True, total_files=total_files)
            ui.update_progress(3, "📊 Starting API monitoring...")
            time.sleep(0.3)
        except ImportError:
            logging.debug("API tracking not available - continuing without tracking")
        
        ui.update_progress(5, f"✅ Ready to process {total_files} files")
        time.sleep(0.5)
        
        # Process each file with detailed progress
        for index, file_path in enumerate(file_paths[:]):
            if not self.rendering or not ui.rendering:
                break
                
            file_name = os.path.basename(file_path)
            
            # Calculate base progress for this file (each file gets equal portion of 90%)
            file_base_progress = 5 + (index * 90 // total_files)
            file_progress_range = 90 // total_files
            
            # STEP 2: File preparation (10% of file progress)
            ui.update_progress(
                file_base_progress, 
                f"📁 Processing file {index+1}/{total_files}: {file_name}"
            )
            ui.set_current_file(index, file_name)
            time.sleep(0.3)
            
            # Generate output filename
            base_name = os.path.splitext(file_name)[0]
            
            # Create duration suffix
            h, m, s = format_duration(duration)
            time_suffix = f"{h}h" if h > 0 else ""
            time_suffix += f"{m}m" if m > 0 else ""
            time_suffix += f"{s}s" if s > 0 else ""
            
            output_name = f"{base_name}_{time_suffix}.mp4"
            
            ui.update_progress(
                file_base_progress + (file_progress_range * 0.1), 
                f"📝 Preparing: {output_name}"
            )
            
            logging.info(f"Processing file {index+1}/{total_files}: {file_name}")
            logging.info(f"Output: {output_name}, Duration: {duration}s, Transition: {transition}")
            
            # STEP 3: Song list generation (20% of file progress)
            song_list_filename = f"{base_name}_song_list.txt"
            
            ui.update_progress(
                file_base_progress + (file_progress_range * 0.2), 
                f"🎵 Generating song list for {file_name}..."
            )
            
            if not self.generate_song_list_with_progress(
                song_list_filename, duration, output_folder, music_folder, 
                sheet_url, new_song_count, export_timestamp, ui, 
                file_base_progress + (file_progress_range * 0.2),
                file_base_progress + (file_progress_range * 0.5)
            ):
                logging.error("Failed to generate song list, skipping file")
                ui.update_progress(
                    file_base_progress + (file_progress_range * 0.5), 
                    f"❌ Failed to generate song list for {file_name}"
                )
                continue
            
            # STEP 4: Video rendering (50% of file progress)
            ui.update_progress(
                file_base_progress + (file_progress_range * 0.5), 
                f"🎬 Starting video render for {file_name}..."
            )
            
            success = self.render_video(file_path, output_folder, output_name, duration, 
                                    fade_audio, ui, transition)
            
            if success:
                ui.update_progress(
                    file_base_progress + (file_progress_range * 0.9), 
                    f"✅ Completed {file_name}"
                )
                
                # STEP 5: Auto upload if enabled (10% of file progress)
                if auto_upload:
                    ui.update_progress(
                        file_base_progress + (file_progress_range * 0.95), 
                        f"📤 Uploading {output_name}..."
                    )
                    self.upload_to_drive(output_folder, output_name)
            else:
                ui.update_progress(
                    file_base_progress + (file_progress_range * 0.9), 
                    f"❌ Failed to render {file_name}"
                )
        
        # STEP 6: Cleanup and completion (final 5%)
        ui.update_progress(95, "🧹 Cleaning up temporary files...")
        time.sleep(0.5)
        
        # Track batch processing completion
        try:
            from api_monitor_module.utils.monitor_access import track_api_call_simple
            track_api_call_simple("batch_processing_complete", success=True, 
                                files_processed=index+1 if 'index' in locals() else 0)
            ui.update_progress(98, "📊 Finalizing processing...")
            time.sleep(0.3)
        except ImportError:
            logging.debug("API tracking not available for completion")
        
        # Final completion
        ui.update_progress(100, f"🎉 Batch processing completed! Processed {total_files} files")
        
        # Update UI when done
        self.rendering = False
        ui.processing_complete()

    def generate_song_list_with_progress(self, output_filename, duration, output_folder, 
                                   music_folder, sheet_url, new_song_count, 
                                   export_timestamp, ui, start_progress, end_progress):
        """Generate song list with progress updates"""
        try:
            progress_range = end_progress - start_progress
            
            # Step 1: URL conversion (10% of song list progress)
            ui.update_progress(
                start_progress + (progress_range * 0.1),
                "🔗 Processing Google Sheet URL..."
            )
            
            # Convert edit URL to the direct API access URL if needed
            if "edit" in sheet_url or "#gid=" in sheet_url:
                sheet_id = re.search(r'/d/([a-zA-Z0-9_-]+)', sheet_url).group(1)
                match = re.search(r'gid=(\d+)', sheet_url)
                gid = match.group(1) if match else "0"
                
                direct_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&gid={gid}"
                logging.info(f"Converted sheet URL to direct access: {direct_url}")
                sheet_url = direct_url
            
            # Step 2: Connecting to Google Sheets (30% of song list progress)
            ui.update_progress(
                start_progress + (progress_range * 0.3),
                "📊 Connecting to Google Sheets..."
            )
            
            # Step 3: Loading song data (50% of song list progress)
            ui.update_progress(
                start_progress + (progress_range * 0.5),
                "🎵 Loading song data from sheet..."
            )
            
            # Step 4: Processing songs (70% of song list progress)
            ui.update_progress(
                start_progress + (progress_range * 0.7),
                "🎯 Selecting and organizing songs..."
            )
            
            # Step 5: Creating files (90% of song list progress)
            ui.update_progress(
                start_progress + (progress_range * 0.9),
                "💾 Creating song list and timestamp files..."
            )
            
            # Actually generate the song list
            result = generate_song_list_for_batch(
                sheet_url=sheet_url,
                output_filename=output_filename,
                duration_in_seconds=duration,
                music_folder=music_folder,
                output_folder=output_folder,
                new_song_count=new_song_count,
                export_song_list=True,
                export_timestamp=export_timestamp
            )
            
            if isinstance(result, tuple) and result[0] == "missing":
                missing_files = result[1]
                ui.update_progress(
                    start_progress + (progress_range * 0.95),
                    f"❌ Missing {len(missing_files)} WAV files"
                )
                message = (
                    "Could not generate background music.\n\n"
                    f"Missing .wav files in:\n{music_folder}\n\n"
                    + "\n".join(missing_files[:10]) + 
                    ("\n..." if len(missing_files) > 10 else "")
                )
                messagebox.showerror("Missing WAV Files", message)
                return False
            
            # Step 6: Song list completed (100% of song list progress)
            ui.update_progress(
                end_progress,
                "✅ Song list generated successfully"
            )
            
            return bool(result)
            
        except Exception as e:
            ui.update_progress(
                end_progress,
                f"❌ Song list generation failed: {str(e)[:50]}..."
            )
            logging.error(f"Error generating song list (batch): {e}")
            return False

    def process_files_distributed_with_progress(self, params, ui, distribution_settings):
        """Process files in distribution mode with enhanced progress - COMPLETE FIXED VERSION"""
        try:
            file_paths = params["file_paths"]
            duration = params["duration"]
            output_folder = params["output_folder"]
            music_folder = params["music_folder"]
            sheet_url = params["sheet_url"]
            export_timestamp = params["export_timestamp"]
            fade_audio = params["fade_audio"]
            auto_upload = params["auto_upload"]
            transition = params.get("transition", "None")
            
            num_videos = distribution_settings['num_videos']
            
            # STEP 1: Initial setup (5% progress)
            ui.update_progress(1, "🎵 Initializing distribution mode...")
            time.sleep(0.5)
            
            # Track batch processing start
            try:
                from api_monitor_module.utils.monitor_access import track_api_call_simple
                track_api_call_simple("distributed_batch_start", success=True, 
                                    total_files=num_videos, distribution_mode=True)
                ui.update_progress(3, "📊 Starting distribution monitoring...")
                time.sleep(0.3)
            except ImportError:
                logging.debug("API tracking not available")
            
            # STEP 2: Generate distributed song lists (20% progress)
            ui.update_progress(5, f"🎯 Generating song distribution for {num_videos} videos...")
            
            video_song_lists = generate_distributed_song_lists(
                sheet_url, distribution_settings, duration,
                music_folder, output_folder, export_timestamp
            )
            
            if not video_song_lists:
                ui.update_progress(10, "❌ Failed to generate distributed song lists")
                return
            
            if isinstance(video_song_lists, tuple) and video_song_lists[0] == "missing":
                missing_files = video_song_lists[1]
                ui.update_progress(10, f"❌ Missing {len(missing_files)} WAV files")
                message = (
                    "Could not generate background music.\n\n"
                    f"Missing .wav files in:\n{music_folder}\n\n"
                    + "\n".join(missing_files[:10]) + 
                    ("\n..." if len(missing_files) > 10 else "")
                )
                messagebox.showerror("Missing WAV Files", message)
                return
            
            ui.update_progress(20, f"✅ Generated {num_videos} unique song combinations")
            time.sleep(0.5)
            
            # Track all concat files for final cleanup
            concat_files_to_cleanup = []
            
            # STEP 3: Process each video (70% progress total)
            for i, video_info in enumerate(video_song_lists):
                if not self.rendering or not ui.rendering:
                    break
                
                video_num = video_info['video_num']
                temp_music_path = video_info['temp_music_path']
                old_base_name = video_info['base_name']
                
                # Calculate progress for this video
                video_base_progress = 20 + (i * 70 // num_videos)
                video_progress_range = 70 // num_videos
                
                # Use the first file in queue for all videos, or cycle through if multiple files
                file_index = i % len(file_paths)
                file_path = file_paths[file_index]
                file_name = os.path.basename(file_path)
                
                # FIXED: Better progress messages showing video part
                ui.update_progress(
                    video_base_progress, 
                    f"🎬 Distribution Mode - Video {video_num}/{num_videos}: {file_name}"
                )
                ui.set_current_file(i, f"Distribution Video {video_num}/{num_videos} - {file_name}")
                
                # File renaming and preparation (20% of video progress)
                ui.update_progress(
                    video_base_progress + (video_progress_range * 0.2),
                    f"📝 Preparing files for video {video_num}..."
                )
                
                # Generate output filename and rename files
                base_name = os.path.splitext(file_name)[0]
                h, m, s = format_duration(duration)
                time_suffix = f"{h}h" if h > 0 else ""
                time_suffix += f"{m}m" if m > 0 else ""
                time_suffix += f"{s}s" if s > 0 else ""
                output_name = f"{base_name}_Part{video_num}_{time_suffix}.mp4"
                
                # Generate output filename and rename files
                base_name = os.path.splitext(file_name)[0]
                h, m, s = format_duration(duration)
                time_suffix = f"{h}h" if h > 0 else ""
                time_suffix += f"{m}m" if m > 0 else ""
                time_suffix += f"{s}s" if s > 0 else ""
                output_name = f"{base_name}_Part{video_num}_{time_suffix}.mp4"

                # ADDED: Rename timestamp files to match the output video name
                if 'timestamp_path' in video_info and video_info['timestamp_path']:
                    old_timestamp_path = video_info['timestamp_path']
                    if os.path.exists(old_timestamp_path):
                        # Create new timestamp filename matching the video
                        new_timestamp_name = f"{base_name}_Part{video_num}_song_list_timestamp.txt"
                        new_timestamp_path = os.path.join(output_folder, new_timestamp_name)
                        
                        try:
                            # Rename the timestamp file
                            os.rename(old_timestamp_path, new_timestamp_path)
                            video_info['timestamp_path'] = new_timestamp_path  # Update the reference
                            logging.info(f"📝 Renamed timestamp file to: {new_timestamp_name}")
                        except Exception as e:
                            logging.error(f"Failed to rename timestamp file: {e}")

                # Also rename the full timestamp file if it exists
                old_timestamp_full_path = old_timestamp_path.replace('_timestamp.txt', '_timestamp_full.txt') if 'timestamp_path' in video_info else None
                if old_timestamp_full_path and os.path.exists(old_timestamp_full_path):
                    new_timestamp_full_name = f"{base_name}_Part{video_num}_song_list_timestamp_full.txt"
                    new_timestamp_full_path = os.path.join(output_folder, new_timestamp_full_name)
                    
                    try:
                        os.rename(old_timestamp_full_path, new_timestamp_full_path)
                        logging.info(f"📝 Renamed full timestamp file to: {new_timestamp_full_name}")
                    except Exception as e:
                        logging.error(f"Failed to rename full timestamp file: {e}")

                # Video rendering (80% of video progress)
                ui.update_progress(
                    video_base_progress + (video_progress_range * 0.4),
                    f"🎬 Rendering Video {video_num}/{num_videos} with {video_info['songs_count']} unique songs..."
                )
                
                logging.info(f"Distribution Mode: Processing video {video_num}/{num_videos}: {output_name}")
                logging.info(f"Using {video_info['songs_count']} unique songs, {video_info['loops']} loops")
                logging.info(f"Transition: {transition}")
                
                # Render video using the distributed temp music WITH TRANSITION
                success = self.render_video_distributed(
                    file_path, output_folder, output_name, duration, 
                    fade_audio, ui, temp_music_path, transition,
                    video_num, num_videos  # Pass video info for better progress
                )
                
                if success:
                    ui.update_progress(
                        video_base_progress + (video_progress_range * 0.9),
                        f"✅ Completed Video {video_num}/{num_videos}"
                    )
                    
                    # Auto upload if enabled
                    if auto_upload:
                        ui.update_progress(
                            video_base_progress + (video_progress_range * 0.95),
                            f"📤 Uploading Video {video_num}/{num_videos}..."
                        )
                        self.upload_to_drive(output_folder, output_name)
                else:
                    ui.update_progress(
                        video_base_progress + (video_progress_range * 0.9),
                        f"❌ Failed Video {video_num}/{num_videos}"
                    )
                    logging.error(f"Failed to render video {video_num}/{num_videos}")
                
                # Cleanup temp files for this video (98% of video progress)
                ui.update_progress(
                    video_base_progress + (video_progress_range * 0.98),
                    f"🧹 Cleaning up temp files for Video {video_num}..."
                )
                
                # Clean up temp music file immediately after each video
                try:
                    if os.path.exists(temp_music_path):
                        os.remove(temp_music_path)
                        logging.info(f"🗑️ Cleaned up temp music for video {video_num}: {temp_music_path}")
                        
                except Exception as e:
                    logging.error(f"Error cleaning up temp music for video {video_num}: {e}")
                
                # Collect concat files for final cleanup (don't delete yet)
                if 'concat_file_path' in video_info:
                    concat_files_to_cleanup.append(video_info['concat_file_path'])
            
            # STEP 4: Final cleanup including concat files (10% progress)
            ui.update_progress(90, "🧹 Final cleanup of all temporary files...")
            time.sleep(0.3)
            
            # Clean up all concat files at the end
            concat_cleaned = 0
            for concat_file in concat_files_to_cleanup:
                try:
                    if os.path.exists(concat_file):
                        os.remove(concat_file)
                        concat_cleaned += 1
                        logging.info(f"🗑️ Cleaned up concat file: {concat_file}")
                except Exception as e:
                    logging.error(f"Error cleaning up concat file {concat_file}: {e}")
            
            if concat_cleaned > 0:
                logging.info(f"🧹 Successfully cleaned up {concat_cleaned} concat files after distribution processing")
            
            ui.update_progress(93, "🧹 Cleaning up song list files...")
            
            # Also clean up individual song list files if desired
            song_lists_cleaned = 0
            for video_info in video_song_lists:
                try:
                    # Clean up song list file
                    if 'song_list_path' in video_info and os.path.exists(video_info['song_list_path']):
                        # Only clean up if it's a Part file (not the main song list)
                        if "Part" in video_info['song_list_path']:
                            os.remove(video_info['song_list_path'])
                            song_lists_cleaned += 1
                            logging.info(f"🗑️ Cleaned up song list: {video_info['song_list_path']}")
                            
                    # Note: Keep timestamp files as they're useful for users
                            
                except Exception as e:
                    logging.error(f"Error cleaning up song list files: {e}")
            
            if song_lists_cleaned > 0:
                logging.info(f"🧹 Cleaned up {song_lists_cleaned} temporary song list files")
            
            ui.update_progress(95, "🧹 All temporary files cleaned up...")
            time.sleep(0.5)
            
            # Track completion
            try:
                from api_monitor_module.utils.monitor_access import track_api_call_simple
                track_api_call_simple("distributed_batch_complete", success=True,
                                    videos_processed=num_videos, concat_files_cleaned=concat_cleaned)
                ui.update_progress(98, "📊 Finalizing distribution processing...")
                time.sleep(0.3)
            except ImportError:
                logging.debug("API tracking not available")
            
            # Final success message
            ui.update_progress(100, f"🎉 Distribution processing completed! Created {num_videos} videos")
            
            # Summary logging
            logging.info(f"🎉 Distribution processing completed successfully!")
            logging.info(f"📊 Created {num_videos} videos with unique song combinations")
            logging.info(f"🧹 Cleaned up {concat_cleaned} concat files and {song_lists_cleaned} temp song lists")
            logging.info(f"🎬 Used transition: {transition}")
            
            # Update UI when done
            self.rendering = False
            ui.processing_complete()
            
            # Clear distribution settings
            if hasattr(self, 'distribution_settings'):
                self.distribution_settings = None
                logging.info("🎵 Distribution mode completed - settings cleared")
            
        except Exception as e:
            logging.error(f"💥 Error in distributed processing: {e}")
            import traceback
            logging.error(traceback.format_exc())
            
            ui.update_progress(0, f"❌ Distribution processing failed: {str(e)[:50]}...")
            
            # Ensure UI is unlocked even on error
            self.rendering = False
            ui.processing_complete()
            
            # Clear distribution settings on error too
            if hasattr(self, 'distribution_settings'):
                self.distribution_settings = None

    def render_video_distributed(self, input_file, output_folder, output_name, 
                       duration, fade_audio, ui, temp_music_path, transition="None",
                       video_num=None, total_videos=None):
        """Render video with pre-generated distributed music - ENHANCED VERSION"""
        
        # Create a wrapper UI update function that includes video info
        original_update_progress = ui.update_progress
        
        def distribution_progress_wrapper(progress, message):
            if video_num and total_videos:
                # Enhance message with video part info
                enhanced_message = f"Video {video_num}/{total_videos} - {message}"
                original_update_progress(progress, enhanced_message)
            else:
                original_update_progress(progress, message)
        
        # Temporarily replace the update function
        ui.update_progress = distribution_progress_wrapper
        
        # First, temporarily move the temp_music file to match expected naming
        base_name = os.path.splitext(output_name)[0]
        if "_" in base_name:
            base_name = base_name.rsplit("_", 1)[0]
        
        expected_temp_music = os.path.join(output_folder, f"{base_name}_temp_music.wav")
        
        # Copy or rename temp music to expected location
        import shutil
        if temp_music_path != expected_temp_music:
            try:
                shutil.copy2(temp_music_path, expected_temp_music)
                logging.info(f"📁 Copied temp music for video {video_num}: {expected_temp_music}")
            except Exception as e:
                logging.error(f"Failed to copy temp music: {e}")
                ui.update_progress = original_update_progress
                return False
        
        try:
            # Use the regular render_video with transition support and bitrate matching
            logging.info(f"🎬 Starting distributed render for video {video_num}/{total_videos}")
            success = self.render_video(input_file, output_folder, output_name, duration, 
                                fade_audio, ui, transition)
            
            if success:
                logging.info(f"✅ Distributed video {video_num}/{total_videos} completed successfully")
            else:
                logging.error(f"❌ Distributed video {video_num}/{total_videos} failed")
                
            return success
            
        finally:
            # Restore original progress function
            ui.update_progress = original_update_progress
            
            # Clean up the copied temp music if we created it
            if temp_music_path != expected_temp_music and os.path.exists(expected_temp_music):
                try:
                    os.remove(expected_temp_music)
                    logging.info(f"🗑️ Cleaned up copied temp music: {expected_temp_music}")
                except Exception as e:
                    logging.debug(f"Could not clean up temp music: {e}")

    def render_video(self, input_file, output_folder, output_name, duration, fade_audio, ui, transition="None"):
        """FIXED: GPU rendering with original bitrate matching and proper filter chain handling"""
        try:
            output_path = os.path.join(output_folder, output_name)
            
            # Look for the specific temp music file
            base_name = os.path.splitext(output_name)[0]
            if "_" in base_name:
                base_name = base_name.rsplit("_", 1)[0]
            
            temp_music_path = os.path.join(output_folder, f"{base_name}_temp_music.wav")
            
            if not os.path.exists(temp_music_path):
                temp_music_path = os.path.join(output_folder, "temp_music.wav")
                if not os.path.exists(temp_music_path):
                    logging.error(f"No temp music file found for {output_name}")
                    return False
            
            # Import the bitrate detection function
            from post_render_check import get_video_bitrate
            
            logging.info(f"Using temp music file: {temp_music_path}")
            logging.info(f"Input video file: {input_file}")
            logging.info(f"Output path: {output_path}")
            logging.info(f"Target duration: {duration} seconds")
            
            # Verify input files exist
            if not os.path.exists(input_file):
                logging.error(f"Input video file not found: {input_file}")
                return False
                
            if not os.path.exists(temp_music_path):
                logging.error(f"Temp music file not found: {temp_music_path}")
                return False
            
            # ADDED: Detect source video bitrate
            ui.update_progress(2, "🔍 Analyzing source video bitrate...")
            source_bitrate = get_video_bitrate(input_file)
            logging.info(f"📊 Source video bitrate detected: {source_bitrate}")
            
            # STRICT GPU CHECK - Cancel if GPU not available - FIXED VERSION
            try:
                logging.info("🔍 Verifying GPU encoding availability...")
                ui.update_progress(5, "Checking GPU encoding...")
                
                # Import and use proper FFmpeg detection for GPU test
                from ffmpeg_utils import find_executable
                
                ffmpeg_path = find_executable("ffmpeg")
                if not ffmpeg_path:
                    error_msg = (
                        "❌ FFmpeg not found!\n\n"
                        "FFmpeg is required for GPU encoding.\n"
                        "Please ensure the application was properly installed with all bundled components.\n"
                        "Rendering has been cancelled."
                    )
                    logging.error("❌ FFmpeg not found for GPU test - cancelling render")
                    messagebox.showerror("FFmpeg Not Found", error_msg, parent=ui)
                    return False
                
                logging.info(f"🔍 Testing GPU encoding with: {ffmpeg_path}")
                
                gpu_test_result = subprocess.run([
                    ffmpeg_path, "-f", "lavfi", "-i", "testsrc=duration=1:size=320x240:rate=1",
                    "-c:v", "h264_nvenc", "-preset", "fast", "-f", "null", "-"
                ], capture_output=True, timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
                
                if gpu_test_result.returncode != 0:
                    error_msg = (
                        "❌ GPU encoding (NVENC) is not available!\n\n"
                        "This could be due to:\n"
                        "• Outdated NVIDIA drivers\n"
                        "• Non-NVIDIA GPU\n" 
                        "• NVENC not supported on your GPU\n"
                        "• GPU busy with other tasks\n\n"
                        "Please update your NVIDIA drivers and try again.\n"
                        "Rendering has been cancelled."
                    )
                    logging.error("❌ GPU encoding test failed - cancelling render")
                    logging.error(f"GPU test stderr: {gpu_test_result.stderr}")
                    
                    messagebox.showerror("GPU Encoding Failed", error_msg, parent=ui)
                    return False
                
                logging.info("✅ GPU encoding verified - proceeding with render")
                
            except subprocess.TimeoutExpired:
                error_msg = (
                    "❌ GPU encoding test timed out!\n\n"
                    "Your GPU may be busy or unresponsive.\n"
                    "Rendering has been cancelled."
                )
                logging.error("❌ GPU test timed out - cancelling render")
                messagebox.showerror("GPU Test Timeout", error_msg, parent=ui)
                return False
                
            except Exception as e:
                error_msg = (
                    f"❌ Failed to test GPU encoding!\n\n"
                    f"Error: {str(e)}\n\n"
                    "Rendering has been cancelled."
                )
                logging.error(f"❌ GPU test exception: {e}")
                messagebox.showerror("GPU Test Failed", error_msg, parent=ui)
                return False
            
            # Check if transition is requested
            temp_transition_path = None
            if transition != "None":
                logging.info(f"Applying {transition} transition...")
                ui.update_progress(8, f"Applying {transition} transition...")
                
                temp_transition_path = os.path.join(output_folder, f"{base_name}_transition_temp.mp4")
                
                # Apply transition using transitions_lib
                from transitions_lib import process_video
                try:
                    process_video(input_file, temp_transition_path, transition, transition_duration=1.5)
                    input_file = temp_transition_path  # Use transition video as input
                    logging.info(f"✅ {transition} transition applied successfully")
                except Exception as e:
                    logging.error(f"❌ Failed to apply transition: {e}")
                    messagebox.showerror(
                        "Transition Failed", 
                        f"Failed to apply {transition} transition.\n\nError: {str(e)}\n\nRendering cancelled.",
                        parent=ui
                    )
                    return False
            
            # FIXED: GPU rendering with detected bitrate
            if fade_audio:
                fade_start = max(duration - 5, 0)
                # Use separate audio filter chain (no GPU conflict)
                ffmpeg_cmd = [
                    ffmpeg_path, "-y",
                    
                    # FIXED: Simplified GPU setup - no hwaccel_output_format to avoid filter conflicts
                    "-hwaccel", "cuda",
                    
                    # Video input with infinite loop
                    "-stream_loop", "-1", 
                    "-i", str(input_file),
                    
                    # Audio input with infinite loop  
                    "-stream_loop", "-1",
                    "-i", str(temp_music_path),
                    
                    # Map streams
                    "-map", "0:v:0",  # Video from first input
                    "-map", "1:a:0",  # Audio from second input
                    
                    # FIXED: GPU encoding settings with detected bitrate
                    "-c:v", "h264_nvenc",
                    "-preset", "fast", 
                    "-b:v", source_bitrate,  # FIXED: Use detected bitrate instead of hardcoded 8M
                    
                    # Audio encoding with fade filter
                    "-c:a", "aac",
                    "-b:a", "192k",
                    "-af", f"afade=t=out:st={fade_start}:d=5",
                    
                    # Set duration
                    "-t", str(duration),
                    
                    # Output file
                    str(output_path)
                ]
            else:
                # No audio filter - even simpler
                ffmpeg_cmd = [
                    ffmpeg_path, "-y",
                    
                    # FIXED: Simplified GPU setup
                    "-hwaccel", "cuda",
                    
                    # Video input with infinite loop
                    "-stream_loop", "-1", 
                    "-i", str(input_file),
                    
                    # Audio input with infinite loop  
                    "-stream_loop", "-1",
                    "-i", str(temp_music_path),
                    
                    # Map streams
                    "-map", "0:v:0",  # Video from first input
                    "-map", "1:a:0",  # Audio from second input
                    
                    # FIXED: GPU encoding settings with detected bitrate
                    "-c:v", "h264_nvenc",
                    "-preset", "fast", 
                    "-b:v", source_bitrate,  # FIXED: Use detected bitrate instead of hardcoded 8M
                    
                    # Audio encoding (no filters)
                    "-c:a", "aac",
                    "-b:a", "192k",
                    
                    # Set duration
                    "-t", str(duration),
                    
                    # Output file
                    str(output_path)
                ]
            
            logging.info(f"🚀 Executing GPU FFmpeg command with {source_bitrate} bitrate:")
            logging.info(f"Command: {' '.join(ffmpeg_cmd)}")
            
            # Update progress bar
            ui.update_progress(10, f"Starting GPU render ({duration}s, {source_bitrate})...")
            
            # Start FFmpeg process
            startupinfo = None
            if sys.platform == "win32":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE

            self.current_process = subprocess.Popen(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )
            
            # Track process
            self.process_pid = psutil.Process(self.current_process.pid)
            
            # PROGRESS MONITORING with thread-safe updates
            import threading
            import queue
            import time
            
            # Create a queue for thread-safe progress updates
            progress_queue = queue.Queue()
            stderr_lines = []  # Collect all stderr for debugging
            
            def monitor_ffmpeg_progress():
                """Monitor FFmpeg stderr for progress info"""
                try:
                    while True:
                        line = self.current_process.stderr.readline()
                        if not line:
                            break
                            
                        line = line.strip()
                        stderr_lines.append(line)  # Store for debugging
                        
                        # Look for time= in the line (FFmpeg progress indicator)
                        if "time=" in line and "fps=" in line:
                            try:
                                # Extract time from FFmpeg progress line
                                time_match = None
                                for part in line.split():
                                    if part.startswith("time="):
                                        time_str = part.split("=")[1]
                                        time_match = time_str
                                        break
                                
                                if time_match:
                                    # Parse time string (format: HH:MM:SS.ss)
                                    time_parts = time_match.split(":")
                                    if len(time_parts) == 3:
                                        hours = float(time_parts[0])
                                        minutes = float(time_parts[1])
                                        seconds = float(time_parts[2])
                                        
                                        current_seconds = hours * 3600 + minutes * 60 + seconds
                                        progress_percent = min(100, (current_seconds / duration) * 100)
                                        
                                        # Put progress update in queue
                                        progress_queue.put({
                                            'progress': progress_percent,
                                            'current_time': current_seconds,
                                            'message': f"GPU Rendering ({source_bitrate}): {int(progress_percent)}% ({int(current_seconds)}s / {duration}s)"
                                        })
                            
                            except Exception as e:
                                # Don't log every parsing error, just continue
                                pass
                        
                        # Check if we should stop
                        if not self.rendering:
                            break
                            
                except Exception as e:
                    logging.error(f"Progress monitoring error: {e}")
            
            # Start progress monitoring thread
            progress_thread = threading.Thread(target=monitor_ffmpeg_progress, daemon=True)
            progress_thread.start()
            
            # MAIN LOOP: Update UI with progress
            last_update_time = 0
            
            while self.current_process.poll() is None:  # While FFmpeg is still running
                # Check for stop request
                if not self.rendering:
                    try:
                        self.current_process.terminate()
                        logging.info("🛑 GPU rendering stopped by user")
                        return False
                    except:
                        pass
                    break
                
                # Process progress updates (limit to avoid UI flooding)
                current_time = time.time()
                if current_time - last_update_time > 0.5:  # Update every 0.5 seconds
                    try:
                        # Get the latest progress update
                        latest_progress = None
                        while not progress_queue.empty():
                            latest_progress = progress_queue.get_nowait()
                        
                        if latest_progress:
                            ui.update_progress(
                                latest_progress['progress'], 
                                latest_progress['message']
                            )
                            last_update_time = current_time
                            
                    except queue.Empty:
                        pass
                    except Exception as e:
                        logging.debug(f"Progress update error: {e}")
                
                # Small sleep to prevent excessive CPU usage
                time.sleep(0.1)
            
            # Wait for process to complete
            return_code = self.current_process.wait()
            
            # Wait for progress thread to finish
            progress_thread.join(timeout=2)
            
            # Check return code
            if return_code != 0:
                logging.error(f"❌ GPU FFmpeg FAILED with return code: {return_code}")
                
                # Look for specific filter-related errors
                filter_errors = []
                for line in stderr_lines[-20:]:
                    if any(keyword in line.lower() for keyword in [
                        'filter', 'convert', 'format', 'hwaccel', 'cuda'
                    ]):
                        filter_errors.append(line)
                
                error_msg = (
                    f"❌ GPU rendering failed!\n\n"
                    f"Return code: {return_code}\n\n"
                    f"This indicates a GPU filter chain issue.\n"
                    f"Rendering has been cancelled."
                )
                
                if filter_errors:
                    error_msg += f"\n\nFilter errors:\n" + "\n".join(filter_errors[-3:])
                
                logging.error("❌ GPU rendering failed - operation cancelled")
                for line in stderr_lines[-10:]:
                    logging.error(f"FFmpeg stderr: {line}")
                
                messagebox.showerror("GPU Rendering Failed", error_msg, parent=ui)
                return False
            
            # Clean up transition temp file if it exists
            if temp_transition_path and os.path.exists(temp_transition_path):
                try:
                    os.remove(temp_transition_path)
                    logging.info("🗑️ Cleaned up transition temp file")
                except Exception as e:
                    logging.error(f"Failed to clean up transition temp: {e}")
            
            # Validate the output
            if not os.path.exists(output_path):
                logging.error(f"❌ Output file not found: {output_path}")
                messagebox.showerror(
                    "Render Failed", 
                    f"Output file was not created:\n{output_path}\n\nRendering failed.",
                    parent=ui
                )
                return False
            
            # Check file size
            file_size = os.path.getsize(output_path)
            if file_size < 1024 * 1024:  # Less than 1MB is suspicious
                logging.error(f"❌ Output file too small: {file_size} bytes")
                messagebox.showerror(
                    "Render Failed", 
                    f"Output file is suspiciously small ({file_size} bytes).\nRendering may have failed.",
                    parent=ui
                )
                return False
            
            logging.info(f"✅ Output file created: {file_size // (1024*1024)}MB with {source_bitrate} bitrate")
            
            # Verify duration
            try:
                from post_render_check import get_mp4_duration
                actual_duration = get_mp4_duration(output_path)
                logging.info(f"📏 Final duration: {actual_duration}s (target: {duration}s)")
                
                if actual_duration < duration * 0.90:  # 90% tolerance
                    logging.warning(f"⚠️ Output significantly shorter than expected: {actual_duration}s < {duration}s")
                    
            except Exception as e:
                logging.warning(f"Could not verify duration: {e}")
            
            # Clean up temp files
            temp_files_to_clean = [
                f"{base_name}_temp_music.wav",
                f"{base_name}_music_concat.txt", 
                "temp_music.wav",
                "music_concat.txt"
            ]
            
            for temp_file in temp_files_to_clean:
                temp_path = os.path.join(output_folder, temp_file)
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                        logging.info(f"🗑️ Cleaned up: {temp_path}")
                    except Exception as e:
                        logging.debug(f"Could not delete {temp_path}: {e}")
            
            # Final success update
            ui.update_progress(100, f"✅ GPU render completed with {source_bitrate} bitrate!")
            logging.info(f"🎉 GPU video rendering completed successfully with {source_bitrate} bitrate!")
            
            return True
            
        except Exception as e:
            logging.error(f"💥 GPU render error: {e}")
            import traceback
            logging.error(traceback.format_exc())
            
            messagebox.showerror(
                "Rendering Error", 
                f"An unexpected error occurred during GPU rendering:\n\n{str(e)}\n\nRendering has been cancelled.",
                parent=ui
            )
            return False
            
    def stop_processing(self):
        """Stop all processing"""
        self.rendering = False
        self.was_stopped = True
        
        if self.current_process and self.current_process.poll() is None:
            try:
                self.current_process.terminate()
                logging.info("Process terminated")
            except Exception as e:
                logging.error(f"Error terminating process: {e}")
                
        # Clean up any output files
        try:
            current_file = self.ui.file_paths[self.ui.current_file_index]
            base_name = os.path.splitext(os.path.basename(current_file))[0]
            output_folder = self.ui.output_entry.get().strip()
            
            # Look for files that start with the base name
            for file in os.listdir(output_folder):
                if file.startswith(base_name) and file.endswith((".mp4", "_song_list.txt", "_song_list_timestamp.txt")):
                    file_path = os.path.join(output_folder, file)
                    try:
                        os.remove(file_path)
                        logging.info(f"Deleted incomplete file: {file_path}")
                    except Exception as e:
                        logging.error(f"Failed to delete file: {e}")
        except Exception as e:
            logging.error(f"Error cleaning up files: {e}")
        
    def run(self):
        """Run the application"""
        self.ui.mainloop()

    def upload_to_drive(self, output_folder, only_file=None):
        """Upload files to Google Drive using integrated uploader"""
        try:
            # Update UI to show we're starting the upload process
            self.ui.progress_var.set("Preparing upload...")
            self.ui.progress_bar["value"] = 0
            
            # Create callbacks for progress and status updates
            def update_progress(filename, progress):
                # Update progress bar in UI
                percent = int(progress * 100)
                self.ui.update_progress(percent, f"Uploading {filename}: {percent}%")
            
            def update_status(message):
                # Update status message in UI without logging again
                self.ui.progress_var.set(message)
            
            # Define a completion callback
            def upload_complete():
                self.ui.progress_var.set("Upload completed")
                
                # Set upload finished flag and show message
                self.ui.upload_finished = True
                self.ui.after(500, self.ui._show_completion_message)
            
            # Import uploader here to avoid circular imports
            from drive_uploader import DriveUploader
            
            # Create uploader instance
            uploader = DriveUploader()
            
            # Set callbacks for UI updates and completion
            uploader.set_callbacks(update_progress, update_status)
            uploader.completion_callback = upload_complete
            
            # Initialize upload_finished flag to False
            self.ui.upload_finished = False
            
            # Connect to Google Drive
            self.ui.progress_var.set("Connecting to Google Drive...")
            if not uploader.connect():
                messagebox.showerror("Upload Failed", "Failed to connect to Google Drive")
                return False
            
            # Add files to upload queue
            upload_path = output_folder
            if only_file:
                self.ui.progress_var.set(f"Preparing to upload {only_file}...")
            else:
                self.ui.progress_var.set(f"Scanning folder: {output_folder}")
            
            if not uploader.upload_folder(upload_path, only_file):
                messagebox.showerror("Upload Failed", "Failed to prepare files for upload")
                return False
            
            # Start upload process
            if not uploader.start_upload():
                messagebox.showerror("Upload Failed", "Failed to start upload process")
                return False
            
            # Store the uploader instance to prevent garbage collection
            self._drive_uploader = uploader
            
            # Inform user upload has started
            self.ui.progress_var.set("Upload started in background")
            
            return True
            
        except Exception as e:
            logging.error(f"Upload error: {e}")
            messagebox.showerror("Upload Failed", f"Error: {str(e)}")
            return False

    def is_admin_user(self, user_email=None):
        """Check if current user is admin (needed for showing admin button)"""
        try:
            return self.api_monitor.is_admin_user(user_email)
        except AttributeError:
            # If api_monitor is not initialized yet, check manually
            if user_email is None:
                try:
                    from auth_module.email_auth import get_current_user
                    user_email = get_current_user()
                except ImportError:
                    return False
            
            # Check against admin emails directly
            admin_emails = ["admin@vicgmail.com"]  # Your admin email
            return user_email in admin_emails
        
def load_environment_variables():
    """Load environment variables from .env file, handling PyInstaller paths"""
    try:
        # First, check if running as PyInstaller bundle
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            # When running as PyInstaller onefile, .env is in _MEIPASS
            env_path = os.path.join(sys._MEIPASS, '.env')
            logging.debug(f"Looking for .env file in PyInstaller temp dir: {env_path}")
            if os.path.exists(env_path):
                logging.info(f"Loading .env from PyInstaller temp dir: {env_path}")
                load_dotenv(env_path)
                return True
        
        # If not found in _MEIPASS or not running from PyInstaller,
        # try in the application directory
        app_dir = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else sys.argv[0]))
        env_path = os.path.join(app_dir, '.env')
        
        logging.debug(f"Looking for .env file in app dir: {env_path}")
        if os.path.exists(env_path):
            logging.info(f"Loading .env from app dir: {env_path}")
            load_dotenv(env_path)
            return True
            
        # Try one directory up (parent directory)
        parent_dir = os.path.abspath(os.path.join(app_dir, '..'))
        env_path = os.path.join(parent_dir, '.env')
        
        logging.debug(f"Looking for .env file in parent dir: {env_path}")
        if os.path.exists(env_path):
            logging.info(f"Loading .env from parent dir: {env_path}")
            load_dotenv(env_path)
            return True
            
        logging.warning("Could not find .env file in any location")
        return False
        
    except Exception as e:
        logging.error(f"Error loading environment variables: {e}")
        return False
        
if __name__ == "__main__":
    try:
        app = MP4LooperApp()
        
        # Only run the app if it was fully initialized (authentication succeeded)
        if hasattr(app, 'initialized') and app.initialized:
            app.run()
        else:
            # Authentication was cancelled, exit gracefully
            logging.info("Exiting application due to authentication cancellation")
            sys.exit(0)  # Exit with code 0 (success)
            
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        print(f"Fatal error: {e}")
        messagebox.showerror("Error", f"An unexpected error occurred: {e}")