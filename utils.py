import sys
import os
import subprocess
import tkinter as tk
import logging
import time
import re
import json
import threading
import ctypes

from pathlib import Path
from tkinter import messagebox

from requests import HTTPError
from paths import get_base_path

from config import SERVICE_ACCOUNT_PATH
 
class ToolTip(object):
    def __init__(self, widget, text='widget info'):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        self.id = None
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(500, self.showtip)

    def unschedule(self):
        _id = self.id
        self.id = None
        if _id:
            self.widget.after_cancel(_id)

    def showtip(self, event=None):
        if self.tipwindow or not self.text:
            return
        x, y, cx, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 25
        y = y + self.widget.winfo_rooty() + 20
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify='left',
                         background="#ffffe0", relief='solid', borderwidth=1,
                         font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()

def safe_operation(operation_name):
    """Decorator for common error handling pattern"""
    from functools import wraps
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                logging.debug(f"{operation_name} completed successfully")
                return result
            except Exception as e:
                logging.error(f"{operation_name} failed: {e}")
                return None
        return wrapper
    return decorator

def update_total_duration(tree, label):
        """Calculates and updates total duration displayed in a Treeview widget."""
        total_seconds = 0
        for item in tree.get_children():
            dur_str = tree.item(item)["values"][2]
            try:
                mins, secs = dur_str.replace("s", "").split("m")
                total_seconds += int(mins) * 60 + int(secs)
            except:
                continue
        hrs, mins = divmod(total_seconds, 3600)
        mins, secs = divmod(mins, 60)
        label.config(text=f"Total Duration: {hrs}h {mins}m {secs}s")

def log_utils_loaded():
    logging.debug(f"✅ {os.path.basename(__file__)} loaded successfully")

def get_gpu_usage(label=""):
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=utilization.gpu,memory.used,memory.total", "--format=csv,noheader,nounits"],
            capture_output=True, text=True
        )
        output = result.stdout.strip()
        if output:
            gpu_usage, mem_used, mem_total = map(int, output.split(","))
            return f"🖥 GPU ({label}): {gpu_usage}% | Memory: {mem_used} / {mem_total} MiB"
        else:
            return f"🖥 GPU ({label}): no output"
    except Exception as e:
        return f"🖥 GPU ({label}): error - {e}"

def toggle_new_song_input(entry_widget, checkbox_var):
    if checkbox_var.get():
        entry_widget.configure(state="disabled")
        entry_widget.delete(0, "end")
        entry_widget.insert(0, "5")
        logging.debug("Use default song count checkbox checked. Reset to 5.")
    else:
        entry_widget.configure(state="normal")
        logging.debug("Use default song count checkbox unchecked. Allowing user input.")

    logging.debug(f"Current song count input value: {entry_widget.get()}")

def setup_logging():
    # Use the same directory logic as auth storage
    if getattr(sys, 'frozen', False):
        # Running as a bundled executable
        log_dir = os.path.dirname(sys.executable)
    else:
        # Running as a script
        log_dir = os.path.dirname(os.path.abspath(__file__))
    
    log_path = os.path.join(log_dir, "debug.log")

    # Get the root logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # Remove existing FileHandlers to avoid duplicates
    for handler in logger.handlers[:]:
        if isinstance(handler, logging.FileHandler):
            logger.removeHandler(handler)

    # Add new file handler if none exists yet
    if not any(isinstance(h, logging.FileHandler) for h in logger.handlers):
        file_handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Add console output handler if none exists yet
    if not any(isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler) for h in logger.handlers):
        stream_handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    logging.debug("✅ Logging initialized")
    logging.debug(f"Debug log location: {log_path}")

def restart_app():
    try:
        logging.info("🔁 Restarting app now...")
        if getattr(sys, 'frozen', False):
            # We're running as a compiled .exe (PyInstaller)
            exe_path = sys.executable
            logging.debug(f"Restarting frozen executable: {exe_path}")
            os.execv(exe_path, [exe_path])
        else:
            # We're running as a normal .py script
            python = sys.executable
            script = os.path.abspath(sys.argv[0])
            logging.debug(f"Restarting script: {python} {script}")
            os.execl(python, python, script)
    except Exception as e:
        logging.error(f"❌ Failed to restart app: {e}")

def open_folder(path, label="Folder", parent_window=None):
    if os.path.isdir(path):
        os.startfile(path)
    else:
        messagebox.showerror(f"{label} Error", f"The {label.lower()} does not exist:\n{path}", parent=parent_window)

FOLDER_ID_MAP_PATH = Path(get_base_path()) / "folder_id_map.json"

def load_folder_id_map():
    if FOLDER_ID_MAP_PATH.exists():
        with open(FOLDER_ID_MAP_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_folder_id_map(map_data):
    with open(FOLDER_ID_MAP_PATH, "w", encoding="utf-8") as f:
        json.dump(map_data, f, indent=2)

def get_or_create_folder_cached(folder_name, parent_folder_id, drive_service):
    folder_map = load_folder_id_map()
    if folder_name in folder_map:
        return folder_map[folder_name]

    logging.debug(f"📁 Folder '{folder_name}' not cached — pulling all subfolders...")

    try:
        query = (
            f"'{parent_folder_id}' in parents and "
            f"mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        )

        all_folders = drive_service.files().list(
            q=query,
            spaces="drive",
            fields="files(id, name, createdTime)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
            pageSize=1000
        ).execute().get("files", [])

        for folder in all_folders:
            if folder["name"] == folder_name:
                folder_id = folder["id"]
                folder_map[folder_name] = folder_id
                save_folder_id_map(folder_map)
                logging.info(f"📁 Reused existing folder '{folder_name}' → {folder_id}")
                return folder_id

        # Not found, create
        file_metadata = {
            "name": folder_name,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [parent_folder_id],
        }

        folder = drive_service.files().create(
            body=file_metadata,
            fields="id",
            supportsAllDrives=True
        ).execute()

        folder_id = folder["id"]
        folder_map[folder_name] = folder_id
        save_folder_id_map(folder_map)
        logging.info(f"📁 Created new folder '{folder_name}' → {folder_id}")
        return folder_id

    except HTTPError as e:
        logging.error(f"❌ Drive error on folder lookup/create: {e}")
        return None

def extract_drive_folder_id(url_or_id):
    """Extracts folder ID from a full Drive URL or returns the ID if already clean."""
    match = re.search(r"/folders/([a-zA-Z0-9_-]+)", url_or_id)
    return match.group(1) if match else url_or_id

UPLOADER_WORKER_PATH = os.path.join(get_base_path(), "uploader_worker.py")

bat_path = os.path.join(get_base_path(), "launch_upload.bat")

def upload_large_file_subprocess(file_path, folder_id, file_name, progress_callback=None, done_callback=None):
    def run_upload():
        try:
            full_cmd = [
                sys.executable,  # full Python path (even in frozen .exe)
                UPLOADER_WORKER_PATH,
                file_path,
                folder_id,
                file_name,
                SERVICE_ACCOUNT_PATH,
            ]

            process = subprocess.Popen(
                full_cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW,
                cwd=get_base_path()
            )

            if progress_callback:
                progress_callback(0.0)

            if done_callback:
                done_callback()

        except Exception as e:
            logging.error(f"❌ Upload subprocess failed: {e}")
            if done_callback:
                done_callback()

    threading.Thread(target=run_upload, daemon=True).start()

def get_canceled_upload_folder_path():
    return os.path.join(
        os.environ["LOCALAPPDATA"],
        "Google", "DriveFS", "canceled_uploads"
    )

def folder_exceeds_threshold(folder_path, threshold_bytes=1 * 1024 ** 3):
    total = 0
    try:
        for root, _, files in os.walk(folder_path):
            for f in files:
                fp = os.path.join(root, f)
                try:
                    total += os.path.getsize(fp)
                    if total > threshold_bytes:
                        return True, total
                except OSError:
                    continue
    except Exception as e:
        logging.error(f"Error checking folder size: {e}")
        return False, 0
    return False, total

def check_canceled_upload_folder_status():
    cancel_folder = get_canceled_upload_folder_path()
    if os.path.isdir(cancel_folder):
        logging.info(f"📁 Canceled upload folder found at: {cancel_folder}")
        exceeds, size = folder_exceeds_threshold(cancel_folder)
        if exceeds:
            logging.warning(f"⚠️ Folder exceeds 1 GB: {size / (1024**3):.2f} GB")
        else:
            logging.info(f"✅ Folder is within limit: {size / (1024**2):.2f} MB")
    else:
        logging.info("❌ Canceled upload folder not found.")

def disable_cmd_edit_mode():
    kernel32 = ctypes.windll.kernel32
    h_stdin = kernel32.GetStdHandle(-10)  # STD_INPUT_HANDLE = -10

    # Get current console mode
    mode = ctypes.c_ulong()
    if not kernel32.GetConsoleMode(h_stdin, ctypes.byref(mode)):
        return

    # Disable ENABLE_QUICK_EDIT_MODE (0x0040)
    new_mode = mode.value & ~0x0040
    kernel32.SetConsoleMode(h_stdin, new_mode)

def extract_base_names(folder):
    base_names = set()

    for fname in os.listdir(folder):
        name_without_ext = os.path.splitext(fname)[0]
        match = re.match(r"^(\d+_[^_]+)", name_without_ext)
        if match:
            base_names.add(match.group(1))

    print("🔍 Detected base names in folder:")
    for name in sorted(base_names):
        print(f" - {name}")

def center_window(window, parent=None, offset_y=0):
    """
    Center a window on screen or relative to parent window.
    FIXED VERSION - handles windows that haven't calculated their size yet
    
    Args:
        window: The window to center (Tk or Toplevel)
        parent: Optional parent window to center on (if None, centers on screen)
        offset_y: Optional vertical offset from center (positive = down)
    """
    # CRITICAL: Force the window to calculate its size first
    window.update_idletasks()  # This is already here but not enough
    
    # ADDITIONAL FIX: Wait a moment for window to fully render
    window.after(1, lambda: _do_center_window(window, parent, offset_y))

def _do_center_window(window, parent=None, offset_y=0):
    """Helper function that does the actual centering after window is ready"""
    try:
        # Force another update to ensure size is calculated
        window.update_idletasks()
        
        # Get window dimensions - with fallback if still not ready
        window_width = window.winfo_width()
        window_height = window.winfo_height()
        
        # If window size is still 1x1 (not ready), use reasonable defaults
        if window_width <= 1:
            # Try to get requested width from geometry
            geometry = window.geometry()
            if 'x' in geometry:
                try:
                    window_width = int(geometry.split('x')[0])
                    window_height = int(geometry.split('x')[1].split('+')[0])
                except:
                    # Final fallback - use reasonable defaults based on window type
                    if hasattr(window, 'title') and 'Auth' in window.title():
                        window_width, window_height = 400, 280  # Auth dialog
                    elif hasattr(window, 'title') and 'Help' in window.title():
                        window_width, window_height = 500, 800  # Help window
                    elif hasattr(window, 'title') and 'Dashboard' in window.title():
                        window_width, window_height = 1000, 700  # Dashboard
                    else:
                        window_width, window_height = 600, 400  # Generic default
        
        if parent:
            # Center relative to parent
            parent_x = parent.winfo_rootx()
            parent_y = parent.winfo_rooty()
            parent_width = parent.winfo_width()
            parent_height = parent.winfo_height()
            
            # Calculate position
            x = parent_x + (parent_width - window_width) // 2
            y = parent_y + (parent_height - window_height) // 2 + offset_y
            
            # Make sure window stays on screen
            x = max(0, min(x, parent.winfo_screenwidth() - window_width))
            y = max(0, min(y, parent.winfo_screenheight() - window_height))
        else:
            # Center on screen
            screen_width = window.winfo_screenwidth()
            screen_height = window.winfo_screenheight()
            
            # Calculate position
            x = (screen_width - window_width) // 2
            y = (screen_height - window_height) // 2 + offset_y
            
            # Make sure window stays on screen
            x = max(0, min(x, screen_width - window_width))
            y = max(0, min(y, screen_height - window_height))
        
        # Set window position
        window.geometry(f"+{x}+{y}")
        
        logging.debug(f"Centered window: {window_width}x{window_height} at +{x}+{y}")
        
    except Exception as e:
        logging.error(f"Error centering window: {e}")
        # Fallback: just center on screen with default size
        try:
            screen_width = window.winfo_screenwidth()
            screen_height = window.winfo_screenheight()
            x = (screen_width - 600) // 2  # Assume 600px width
            y = (screen_height - 400) // 2  # Assume 400px height
            window.geometry(f"+{x}+{y}")
        except:
            pass  # Give up gracefully

def diagnose_file_locks(file_path):
    """Check if a file is locked and try to identify processes holding locks"""
    import os
    import subprocess
    import tempfile
    
    # Create a diagnostic log file
    log_path = os.path.join(tempfile.gettempdir(), "file_lock_diagnosis.txt")
    
    try:
        with open(log_path, "w") as f:
            f.write(f"File lock diagnosis for: {file_path}\n")
            f.write(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Check if file exists
            f.write(f"File exists: {os.path.exists(file_path)}\n")
            
            # Try to open the file for writing
            try:
                with open(file_path, "a+b") as test_f:
                    f.write("File can be opened for writing\n")
            except Exception as e:
                f.write(f"File cannot be opened for writing: {e}\n")
            
            # On Windows, use handle.exe or OpenedFilesView if available
            if os.name == 'nt':
                f.write("\nAttempting to identify processes with open handles...\n")
                
                # Try Process Explorer output (if available)
                try:
                    result = subprocess.run(
                        ['handle', file_path], 
                        capture_output=True, 
                        text=True,
                        timeout=5
                    )
                    f.write("Handle.exe output:\n")
                    f.write(result.stdout)
                    f.write(result.stderr)
                except:
                    f.write("Handle.exe not available or failed\n")
                
                # List running processes that might be relevant
                f.write("\nRunning processes that might be relevant:\n")
                try:
                    result = subprocess.run(
                        ['tasklist', '/FI', f'IMAGENAME eq {os.path.basename(file_path)}'], 
                        capture_output=True, 
                        text=True,
                        timeout=5
                    )
                    f.write(result.stdout)
                except:
                    f.write("Failed to list processes\n")
        
        return log_path
    except Exception as e:
        logging.error(f"Error in file lock diagnosis: {e}")
        return None

def create_update_diagnostic_report(update_file, target_file):
    """Create a comprehensive diagnostic report for update issues"""
    import os
    import sys
    import platform
    import time
    import tempfile
    
    report_path = os.path.join(tempfile.gettempdir(), "update_diagnostic.txt")
    
    try:
        with open(report_path, "w") as f:
            f.write("=== MP4 Looper Update Diagnostic Report ===\n")
            f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # System information
            f.write("=== System Information ===\n")
            f.write(f"OS: {platform.system()} {platform.version()} {platform.architecture()[0]}\n")
            f.write(f"Python: {sys.version}\n")
            f.write(f"Executable: {sys.executable}\n")
            f.write(f"Working directory: {os.getcwd()}\n\n")
            
            # Update file information
            f.write("=== Update File Information ===\n")
            f.write(f"Update file: {update_file}\n")
            if os.path.exists(update_file):
                f.write(f"  Size: {os.path.getsize(update_file)} bytes\n")
                f.write(f"  Last modified: {time.ctime(os.path.getmtime(update_file))}\n")
                f.write(f"  Readable: {os.access(update_file, os.R_OK)}\n")
                f.write(f"  Writable: {os.access(update_file, os.W_OK)}\n")
            else:
                f.write("  File does not exist!\n")
            f.write("\n")
            
            # Target file information
            f.write("=== Target File Information ===\n")
            f.write(f"Target file: {target_file}\n")
            if os.path.exists(target_file):
                f.write(f"  Size: {os.path.getsize(target_file)} bytes\n")
                f.write(f"  Last modified: {time.ctime(os.path.getmtime(target_file))}\n")
                f.write(f"  Readable: {os.access(target_file, os.R_OK)}\n")
                f.write(f"  Writable: {os.access(target_file, os.W_OK)}\n")
                
                # Try to determine if file is locked
                f.write("  Checking if file is locked...\n")
                try:
                    with open(target_file, "a+b") as test_f:
                        f.write("  File is not locked for writing\n")
                except Exception as e:
                    f.write(f"  File appears to be locked: {e}\n")
            else:
                f.write("  File does not exist!\n")
        
        return report_path
    except Exception as e:
        logging.error(f"Error creating diagnostic report: {e}")
        return None
    
def is_running_in_debug_mode():
    """Check if we're running in debug/development mode"""
    return 'debugpy' in sys.modules or any('debug' in arg.lower() for arg in sys.argv)

def check_environment_vars():
    """Check and log important environment variables"""
    env_vars = {
        "REGGAE_SHEET_URL": os.getenv("REGGAE_SHEET_URL"),
        "GOSPEL_SHEET_URL": os.getenv("GOSPEL_SHEET_URL"),
        "GOOGLE_DRIVE_ROOT_FOLDER_ID": os.getenv("GOOGLE_DRIVE_ROOT_FOLDER_ID"),
        "GOOGLE_SPREADSHEET_ID": os.getenv("GOOGLE_SPREADSHEET_ID"),
        "GITHUB_REPO_OWNER": os.getenv("GITHUB_REPO_OWNER"),
        "GITHUB_REPO_NAME": os.getenv("GITHUB_REPO_NAME")
    }
    
    missing = [key for key, value in env_vars.items() if not value]
    if missing:
        logging.warning(f"⚠️ Missing environment variables: {', '.join(missing)}")
    
    for key, value in env_vars.items():
        if value:
            # Mask long values for cleaner logs
            masked_value = value[:10] + "..." + value[-5:] if len(value) > 20 else value
            logging.debug(f"✅ Environment variable {key}={masked_value}")
    
    return env_vars

def format_duration(seconds):
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return h, m, s