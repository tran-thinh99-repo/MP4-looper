import os
import subprocess
import logging
import psutil
import re
from pathlib import Path
from tkinter import messagebox

# Import modules from existing application
from utils import (setup_logging, disable_cmd_edit_mode,
                  open_folder, check_canceled_upload_folder_status)
from song_utils import generate_song_list_from_google_sheet
from post_render_check import validate_render
from config import SETTINGS_FILE, SHEET_PRESETS
from ui_components import BatchProcessorUI
from dependency_checker import main as check_dependencies
from paths import get_resource_path, get_base_path, clean_folder_with_confirmation

class MP4LooperApp:
    def __init__(self):
        self.ui = BatchProcessorUI(self)
        self.ui.title("MP4 Looper")  # Call on ui, not self
        icon_path = get_resource_path("mp4_looper_icon.ico")
        self.ui.iconbitmap(default=icon_path)  # Call on ui, not self
        setup_logging()
        disable_cmd_edit_mode()
        check_dependencies()

        # State variables
        self.settings = {}
        self.current_process = None
        self.process_pid = None
        self.rendering = False
        self.was_stopped = False
        
        # Load saved settings
        self.load_settings()
        
        # Initialize UI
        self.ui.apply_settings(self.settings)
        
        # Check for canceled uploads
        check_canceled_upload_folder_status()

    def load_settings(self):
        """Load saved settings"""
        settings_path = SETTINGS_FILE
        
        if os.path.exists(settings_path):
            try:
                with open(settings_path, "r", encoding="utf-8") as f:
                    self.settings = json.load(f)
                logging.info(f"Settings loaded from {settings_path}")
            except Exception as e:
                logging.error(f"Failed to load settings: {e}")
                self.settings = {}
        else:
            self.settings = {}

    def save_settings(self, settings=None):
        """Save current settings"""
        if settings is None:
            settings = self.ui.get_current_settings()
            
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2)
            logging.debug(f"Settings saved to {SETTINGS_FILE}")
        except Exception as e:
            logging.error(f"Failed to save settings: {e}")
    
    def save_setting(self, key, value):
        """Save a single setting value"""
        self.settings[key] = value
        self.save_settings()

    def get_sheet_presets(self):
        """Get available sheet presets"""
        return list(SHEET_PRESETS.keys())
    
    def get_sheet_preset_url(self, preset_name):
        """Get URL for a sheet preset"""
        return SHEET_PRESETS.get(preset_name, "")

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
        import getpass
        username = getpass.getuser()
        path = Path(f"C:/Users/{username}/AppData/Local/Google/DriveFS/canceled_uploads")
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
        """Process all files in the queue"""
        self.rendering = True
        ui.rendering = True
        
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
        
        for index, file_path in enumerate(file_paths[:]):
            if not self.rendering or not ui.rendering:
                break
                
            file_name = os.path.basename(file_path)
            
            # Update UI
            ui.update_progress(0, f"Processing file {index+1} of {total_files}: {file_name}")
            ui.set_current_file(index, file_name)
            
            # Generate output filename
            base_name = os.path.splitext(file_name)[0]
            h, m, s = self.format_duration(duration)
            time_suffix = f"{h}h" if h > 0 else ""
            time_suffix += f"{m}m" if m > 0 else ""
            time_suffix += f"{s}s" if s > 0 else ""
            output_name = f"{base_name}_{time_suffix}.mp4"
            
            logging.info(f"Processing file {index+1}/{total_files}: {file_name}")
            logging.info(f"Output: {output_name}, Duration: {duration}s")
            
            # Generate song list
            if not self.generate_song_list(base_name, duration, output_folder, music_folder, sheet_url, new_song_count, export_timestamp):
                logging.error("Failed to generate song list, skipping file")
                continue
                
            # Render video
            success = self.render_video(file_path, output_folder, output_name, duration, fade_audio, ui)
            
            if success and auto_upload:
                self.upload_to_drive(output_folder, output_name)
        
        # Update UI when done
        self.rendering = False
        ui.processing_complete()

    def format_duration(self, seconds):
        """Format seconds into hours, minutes, seconds"""
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        return h, m, s

    def generate_song_list(self, base_name, duration, output_folder, music_folder, sheet_url, new_song_count, export_timestamp):
        """Generate song list for the current file using direct sheet access"""
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
            
            result = generate_song_list_from_google_sheet(
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
            logging.error(f"Error generating song list: {e}")
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
            
            # Start FFmpeg process
            self.current_process = subprocess.Popen(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
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
                
if __name__ == "__main__":
    # Create a missing import
    import json
    
    try:
        app = MP4LooperApp()
        app.run()
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        print(f"Fatal error: {e}")
        messagebox.showerror("Error", f"An unexpected error occurred: {e}")