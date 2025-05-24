# mp4_looper.py - FIXED API MONITOR SETUP
import os
import subprocess
import logging
import psutil
import re
import sys
import json
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
from config import GITHUB_REPO_NAME, GITHUB_REPO_OWNER
from ui_components import BatchProcessorUI
from dependency_checker import main as check_dependencies
from paths import get_resource_path, get_base_path, clean_folder_with_confirmation
from update_module.update_checker import UpdateChecker

from auth_module.email_auth import handle_authentication

from settings_manager import get_settings

class MP4LooperApp:
    def __init__(self):
        setup_logging()
        load_environment_variables()  # Remove load_dotenv() - load_environment_variables() handles it
        check_dependencies()
        # Initialize settings manager EARLY
        self.settings_manager = get_settings()

        # Check environment variables and log their status
        check_environment_vars()
        
        # Initialize this attribute to track initialization status
        self.initialized = False
        
        # Check authentication - ONLY use handle_authentication()
        if not handle_authentication():
            logging.warning("Authentication failed or cancelled. Exiting application.")
            sys.exit(0)

        # FIXED: Initialize API monitoring with proper error handling
        try:
            # Import with fallback handling
            try:
                from api_monitor_module import setup_monitoring
                
                self.api_monitor = setup_monitoring(
                    app_name="MP4 Looper",
                    admin_emails=["admin@vicgmail.com"],
                    auto_cleanup=True
                )
                logging.info("✅ API monitoring initialized")
                
                # Set up global reference for monitor_access
                import api_monitor_module.utils.monitor_access as monitor_access
                monitor_access._api_monitor_cache = self.api_monitor
                monitor_access._cache_checked = False  # Reset the cache check
                
                # Test the monitoring system
                stats = self.api_monitor.get_stats_summary()
                logging.info(f"✅ API monitoring active - Total calls: {stats['overview']['total_calls_ever']}")
                
            except ImportError as import_err:
                logging.warning(f"API monitoring module not available: {import_err}")
                self.api_monitor = self._create_dummy_monitor()
                
            except Exception as setup_err:
                logging.warning(f"API monitoring setup failed: {setup_err}")
                self.api_monitor = self._create_dummy_monitor()
                
        except Exception as e:
            logging.error(f"❌ Critical error in API monitoring setup: {e}")
            self.api_monitor = self._create_dummy_monitor()
            
        # Set the cache reference even for dummy monitor
        try:
            import api_monitor_module.utils.monitor_access as monitor_access
            monitor_access._api_monitor_cache = self.api_monitor
            monitor_access._cache_checked = False
        except:
            pass

        import gc
        gc.collect()
        
        # Application settings
        self.app_name = "MP4 Looper"
        self.version = "1.2.0"  # Production version

        # Load sheet presets from environment variables
        self.sheet_presets = {
            "Reggae": os.getenv("REGGAE_SHEET_URL", ""),
            "Gospel": os.getenv("GOSPEL_SHEET_URL", "")
        }
        
        # Initialize UI and other components
        self.ui = BatchProcessorUI(self)
        self.ui.title(f"{self.app_name} v{self.version} by EAGLE NET")

        # One-line update check that will be shown after UI loads
        self.ui.after(1000, lambda: UpdateChecker(
            self.app_name, 
            self.version, 
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

    def _create_dummy_monitor(self):
        """Create a dummy monitor object that won't cause crashes"""
        class DummyMonitor:
            def is_admin_user(self, email=None): 
                # Check against admin emails directly
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
                pass
            
            def export_data(self, *args, **kwargs):
                return None
            
            def cleanup_old_data(self):
                pass
                
            def show_dashboard(self, parent_window=None):
                from tkinter import messagebox
                messagebox.showinfo(
                    "Dashboard Unavailable", 
                    "The monitoring dashboard is not available.\n\n"
                    "This may be due to missing Python dependencies.\n"
                    "The application will continue to work normally.",
                    parent=parent_window
                )
        
        logging.info("✅ Dummy API monitor created - application will work without monitoring")
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
                        
            elif os.path.isfile(path) and path.lower().endswith('.mp4') and '_edit' not in path.lower():
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
        """Process all files in the queue with batch optimization"""
        self.rendering = True
        ui.rendering = True
        
        # Check if we're in distribution mode
        distribution_settings = getattr(self, 'distribution_settings', None)
        
        if distribution_settings and distribution_settings.get('enabled'):
            # Process in distribution mode
            self.process_files_distributed(params, ui, distribution_settings)
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
        
        total_files = len(file_paths)
        
        # Track batch processing start - FIXED with error handling
        try:
            from api_monitor_module.utils.monitor_access import track_api_call_simple
            track_api_call_simple("batch_processing_start", success=True, total_files=total_files)
        except ImportError:
            logging.debug("API tracking not available - continuing without tracking")
        
        # Initialize batch song generator (this will reuse connections/data)
        for index, file_path in enumerate(file_paths[:]):
            if not self.rendering or not ui.rendering:
                break
                
            file_name = os.path.basename(file_path)
            
            # Update UI
            ui.update_progress(0, f"Processing file {index+1} of {total_files}: {file_name}")
            ui.set_current_file(index, file_name)
            
            # Generate output filename
            base_name = os.path.splitext(file_name)[0]
            h, m, s = format_duration(duration)
            time_suffix = f"{h}h" if h > 0 else ""
            time_suffix += f"{m}m" if m > 0 else ""
            time_suffix += f"{s}s" if s > 0 else ""
            output_name = f"{base_name}_{time_suffix}.mp4"
            
            logging.info(f"Processing file {index+1}/{total_files}: {file_name}")
            logging.info(f"Output: {output_name}, Duration: {duration}s")
            
            # Generate song list using batch-optimized method
            if not self.generate_song_list(base_name, duration, output_folder, music_folder, 
                                            sheet_url, new_song_count, export_timestamp):
                logging.error("Failed to generate song list, skipping file")
                continue
                
            # Render video
            success = self.render_video(file_path, output_folder, output_name, duration, fade_audio, ui)
            
            if success and auto_upload:
                self.upload_to_drive(output_folder, output_name)
        
        # Track batch processing completion - FIXED with error handling
        try:
            from api_monitor_module.utils.monitor_access import track_api_call_simple
            track_api_call_simple("batch_processing_complete", success=True, 
                                files_processed=index+1 if 'index' in locals() else 0)
        except ImportError:
            logging.debug("API tracking not available for completion")
        
        # Update UI when done
        self.rendering = False
        ui.processing_complete()

    def process_files_distributed(self, params, ui, distribution_settings):
        """Process files in distribution mode"""
        try:
            file_paths = params["file_paths"]
            duration = params["duration"]
            output_folder = params["output_folder"]
            music_folder = params["music_folder"]
            sheet_url = params["sheet_url"]
            export_timestamp = params["export_timestamp"]
            fade_audio = params["fade_audio"]
            auto_upload = params["auto_upload"]
            
            num_videos = distribution_settings['num_videos']
            
            # Track batch processing start
            try:
                from api_monitor_module.utils.monitor_access import track_api_call_simple
                track_api_call_simple("distributed_batch_start", success=True, 
                                    total_files=num_videos,
                                    distribution_mode=True)
            except ImportError:
                logging.debug("API tracking not available")
            
            # Generate distributed song lists for all videos
            ui.update_progress(0, f"Generating distributed song lists for {num_videos} videos...")
            
            video_song_lists = generate_distributed_song_lists(
                sheet_url, distribution_settings, duration,
                music_folder, output_folder, export_timestamp
            )
            
            if not video_song_lists:
                ui.update_progress(0, "Failed to generate distributed song lists")
                return
            
            if isinstance(video_song_lists, tuple) and video_song_lists[0] == "missing":
                missing_files = video_song_lists[1]
                message = (
                    "Could not generate background music.\n\n"
                    f"Missing .wav files in:\n{music_folder}\n\n"
                    + "\n".join(missing_files[:10]) + 
                    ("\n..." if len(missing_files) > 10 else "")
                )
                messagebox.showerror("Missing WAV Files", message)
                return
            
            # Process each video
            for i, video_info in enumerate(video_song_lists):
                if not self.rendering or not ui.rendering:
                    break
                
                video_num = video_info['video_num']
                temp_music_path = video_info['temp_music_path']
                old_base_name = video_info['base_name']  # e.g., "Part1"
                
                # Use the first file in queue for all videos, or cycle through if multiple files
                file_index = i % len(file_paths)
                file_path = file_paths[file_index]
                file_name = os.path.basename(file_path)
                
                # Update UI
                ui.update_progress(0, f"Processing video {video_num} of {num_videos}: {file_name}")
                ui.set_current_file(i, f"Video {video_num} - {file_name}")
                
                # Generate output filename with actual base name
                base_name = os.path.splitext(file_name)[0]
                h, m, s = format_duration(duration)
                time_suffix = f"{h}h" if h > 0 else ""
                time_suffix += f"{m}m" if m > 0 else ""
                time_suffix += f"{s}s" if s > 0 else ""
                output_name = f"{base_name}_Part{video_num}_{time_suffix}.mp4"
                
                # FIXED: Rename song list files to match the actual video name
                # Rename song list file
                old_song_list_path = video_info['song_list_path']
                new_song_list_name = f"{base_name}_Part{video_num}_song_list.txt"
                new_song_list_path = os.path.join(output_folder, new_song_list_name)
                
                try:
                    if os.path.exists(old_song_list_path):
                        os.rename(old_song_list_path, new_song_list_path)
                        logging.info(f"Renamed song list: {old_song_list_path} -> {new_song_list_path}")
                except Exception as e:
                    logging.error(f"Failed to rename song list file: {e}")
                
                # FIXED: Rename timestamp file if it exists
                if video_info.get('timestamp_path') and os.path.exists(video_info['timestamp_path']):
                    old_timestamp_path = video_info['timestamp_path']
                    new_timestamp_name = f"{base_name}_Part{video_num}_song_list_timestamp.txt"
                    new_timestamp_path = os.path.join(output_folder, new_timestamp_name)
                    
                    try:
                        os.rename(old_timestamp_path, new_timestamp_path)
                        logging.info(f"Renamed timestamp file: {old_timestamp_path} -> {new_timestamp_path}")
                    except Exception as e:
                        logging.error(f"Failed to rename timestamp file: {e}")
                
                # FIXED: Rename temp music and concat files to match
                # Rename temp music file
                old_temp_music_path = temp_music_path
                new_temp_music_name = f"{base_name}_Part{video_num}_temp_music.wav"
                new_temp_music_path = os.path.join(output_folder, new_temp_music_name)
                
                try:
                    if os.path.exists(old_temp_music_path):
                        os.rename(old_temp_music_path, new_temp_music_path)
                        temp_music_path = new_temp_music_path  # Update the path for rendering
                        logging.info(f"Renamed temp music: {old_temp_music_path} -> {new_temp_music_path}")
                except Exception as e:
                    logging.error(f"Failed to rename temp music file: {e}")
                
                # Rename concat file
                if video_info.get('concat_file_path') and os.path.exists(video_info['concat_file_path']):
                    old_concat_path = video_info['concat_file_path']
                    new_concat_name = f"{base_name}_Part{video_num}_music_concat.txt"
                    new_concat_path = os.path.join(output_folder, new_concat_name)
                    
                    try:
                        os.rename(old_concat_path, new_concat_path)
                        logging.info(f"Renamed concat file: {old_concat_path} -> {new_concat_path}")
                    except Exception as e:
                        logging.error(f"Failed to rename concat file: {e}")
                
                logging.info(f"Processing video {video_num}/{num_videos}: {output_name}")
                logging.info(f"Using {video_info['songs_count']} unique songs, {video_info['loops']} loops")
                
                # Render video using the distributed temp music
                success = self.render_video_distributed(
                    file_path, output_folder, output_name, duration, 
                    fade_audio, ui, temp_music_path
                )
                
                if success and auto_upload:
                    self.upload_to_drive(output_folder, output_name)
                
                # Clean up temp files for this video
                try:
                    if os.path.exists(temp_music_path):
                        os.remove(temp_music_path)
                        logging.info(f"Cleaned up temp music: {temp_music_path}")
                    
                    # Clean up concat file if it exists
                    concat_file_path = os.path.join(output_folder, f"{base_name}_Part{video_num}_music_concat.txt")
                    if os.path.exists(concat_file_path):
                        os.remove(concat_file_path)
                        logging.info(f"Cleaned up concat file: {concat_file_path}")
                        
                except Exception as e:
                    logging.error(f"Error cleaning up temp files: {e}")
            
            # Track completion
            try:
                from api_monitor_module.utils.monitor_access import track_api_call_simple
                track_api_call_simple("distributed_batch_complete", success=True,
                                    videos_processed=num_videos)
            except ImportError:
                logging.debug("API tracking not available")
            
            # Update UI when done
            self.rendering = False
            ui.processing_complete()
            
            # Clear distribution settings
            self.distribution_settings = None
            
        except Exception as e:
            logging.error(f"Error in distributed processing: {e}")
            self.rendering = False
            ui.processing_complete()

    def render_video_distributed(self, input_file, output_folder, output_name, 
                           duration, fade_audio, ui, temp_music_path):
        """Render video with pre-generated distributed music"""
        try:
            output_path = os.path.join(output_folder, output_name)
            
            # Check if temp music exists
            if not os.path.exists(temp_music_path):
                logging.error(f"Temp music file not found: {temp_music_path}")
                return False
            
            # Setup ffmpeg command (same as original but with specific temp music)
            fade_filter = []
            if fade_audio:
                fade_start = max(duration - 5, 0)
                fade_filter = ["-af", f"afade=t=out:st={fade_start}:d=5"]
            
            ffmpeg_cmd = [
                "ffmpeg",
                "-y",
                "-hwaccel", "cuda",
                "-hwaccel_output_format", "cuda",  # Keep frames in GPU memory
                "-stream_loop", "-1", "-i", str(input_file),
                "-stream_loop", "-1", "-i", str(temp_music_path),
                "-map", "0:v:0",
                "-map", "1:a:0",
                "-c:v", "copy",  # Copy video stream (no re-encoding)
                "-c:a", "aac",
                "-b:a", "192k",
                "-t", str(duration),
                *fade_filter,
                "-shortest",
                str(output_path)
            ]
            
            logging.info(f"Executing FFmpeg with CUDA acceleration: {' '.join(ffmpeg_cmd)}")
            
            # Log GPU usage before starting
            try:
                gpu_result = subprocess.run(
                    ["nvidia-smi", "--query-gpu=utilization.gpu,memory.used,memory.total", "--format=csv,noheader,nounits"],
                    capture_output=True, text=True, timeout=2
                )
                if gpu_result.returncode == 0:
                    gpu_usage, mem_used, mem_total = map(int, gpu_result.stdout.strip().split(","))
                    logging.info(f"🖥 GPU Status before render: {gpu_usage}% utilization, {mem_used}/{mem_total} MB memory")
            except Exception as e:
                logging.debug(f"Could not check GPU status: {e}")
            
            # Update progress bar to 0
            ui.update_progress(0, "Starting render...")
            
            # Start FFmpeg process with CREATE_NO_WINDOW flag
            startupinfo = None
            if sys.platform == "win32":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE

            self.current_process = subprocess.Popen(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )
            
            # Track process for pause/stop functionality
            self.process_pid = psutil.Process(self.current_process.pid)
            
            # Monitor progress
            for line in iter(self.current_process.stdout.readline, ''):
                if not self.rendering:
                    self.process_pid.terminate()
                    logging.info("Rendering stopped by user")
                    return False
                    
                if "time=" in line:
                    for part in line.split():
                        if "time=" in part:
                            timestamp = part.split("=")[1]
                            try:
                                h, m, s = map(float, timestamp.split(":"))
                                current_time = h * 3600 + m * 60 + s
                                progress = min(100, (current_time / duration) * 100)
                                ui.update_progress(progress, f"Progress: {int(progress)}%")
                            except Exception as e:
                                logging.error(f"Progress update error: {e}")
                            break
            
            # Wait for process to complete
            self.current_process.wait()
            
            # Validate the output
            if not os.path.exists(output_path):
                logging.error(f"Output file not found: {output_path}")
                return False
                
            # Verify the output using post_render_check
            if not validate_render(output_path, duration):
                logging.error("Post-render validation failed")
                return False
            
            ui.update_progress(100, "Render complete")
            
            return True
            
        except Exception as e:
            logging.error(f"Error rendering distributed video: {e}")
            return False

    def generate_song_list(self, base_name, duration, output_folder, music_folder, 
                           sheet_url, new_song_count, export_timestamp):
        """Generate song list using batch optimization"""
        try:
            output_filename = f"{base_name}_song_list.txt"
            
            # Convert edit URL to the direct API access URL if needed
            if "edit" in sheet_url or "#gid=" in sheet_url:
                # Extract the sheet ID and gid
                sheet_id = re.search(r'/d/([a-zA-Z0-9_-]+)', sheet_url).group(1)
                match = re.search(r'gid=(\d+)', sheet_url)
                gid = match.group(1) if match else "0"
                
                # Construct direct access URL for easier parsing
                direct_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&gid={gid}"
                logging.info(f"Converted sheet URL to direct access: {direct_url}")
                sheet_url = direct_url
            
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
                message = (
                    "Could not generate background music.\n\n"
                    f"Missing .wav files in:\n{music_folder}\n\n"
                    + "\n".join(missing_files[:10]) + 
                    ("\n..." if len(missing_files) > 10 else "")
                )
                messagebox.showerror("Missing WAV Files", message)
                return False
                
            return bool(result)
            
        except Exception as e:
            logging.error(f"Error generating song list (batch): {e}")
            return False

    def render_video(self, input_file, output_folder, output_name, duration, fade_audio, ui):
        """Render a video with the given parameters"""
        try:
            output_path = os.path.join(output_folder, output_name)
            
            # Find the temp music file created by song list generator
            temp_music_path = os.path.join(output_folder, "temp_music.wav")
            if not os.path.exists(temp_music_path):
                logging.error(f"Temp music file not found: {temp_music_path}")
                return False
                
            # Setup ffmpeg command
            fade_filter = []
            if fade_audio:
                fade_start = max(duration - 5, 0)
                fade_filter = ["-af", f"afade=t=out:st={fade_start}:d=5"]
                
            ffmpeg_cmd = [
                "ffmpeg",
                "-y",
                "-hwaccel", "cuda",
                "-stream_loop", "-1", "-i", str(input_file),
                "-stream_loop", "-1", "-i", str(temp_music_path),
                "-map", "0:v:0",
                "-map", "1:a:0",
                "-c:v", "copy",
                "-c:a", "aac",
                "-b:a", "192k",
                "-t", str(duration),
                *fade_filter,
                "-shortest",
                str(output_path)
            ]
            
            logging.info(f"Executing FFmpeg: {' '.join(ffmpeg_cmd)}")
            
            # Update progress bar to 0
            ui.update_progress(0, "Starting render...")
            
            # Start FFmpeg process with CREATE_NO_WINDOW flag
            startupinfo = None
            if sys.platform == "win32":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE

            self.current_process = subprocess.Popen(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )
            
            # Track process for pause/stop functionality
            self.process_pid = psutil.Process(self.current_process.pid)
            
            # Monitor progress
            for line in iter(self.current_process.stdout.readline, ''):
                if not self.rendering:
                    self.process_pid.terminate()
                    logging.info("Rendering stopped by user")
                    return False
                    
                if "time=" in line:
                    for part in line.split():
                        if "time=" in part:
                            timestamp = part.split("=")[1]
                            try:
                                h, m, s = map(float, timestamp.split(":"))
                                current_time = h * 3600 + m * 60 + s
                                progress = min(100, (current_time / duration) * 100)
                                ui.update_progress(progress, f"Progress: {int(progress)}%")
                            except Exception as e:
                                logging.error(f"Progress update error: {e}")
                            break
            
            # Wait for process to complete
            self.current_process.wait()
            
            # Validate the output
            if not os.path.exists(output_path):
                logging.error(f"Output file not found: {output_path}")
                return False
                
            # Verify the output using post_render_check
            if not validate_render(output_path, duration):
                logging.error("Post-render validation failed")
                return False
                
            # Clean up temp files
            temp_files = ["temp_music.wav", "music_concat.txt"]
            for temp_file in temp_files:
                temp_path = os.path.join(output_folder, temp_file)
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                        logging.info(f"Deleted temp file: {temp_path}")
                    except Exception as e:
                        logging.error(f"Failed to delete temp file: {e}")
            
            ui.update_progress(100, "Render complete")
            
            return True
            
        except Exception as e:
            logging.error(f"Error rendering video: {e}")
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