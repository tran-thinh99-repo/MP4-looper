import sys
import os
import subprocess
import tkinter as tk
import logging
import urllib.request
import zipfile
import shutil
import winreg
import re
import json
import threading
import ctypes
import concurrent.futures
from pathlib import Path
from tkinter import messagebox
from config import FFMPEG_URL, FFMPEG_ZIP, FFMPEG_DIR, FFMPEG_BIN, FFPROBE_BIN, SCOPES, SERVICE_ACCOUNT_PATH
from paths import get_base_path

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

# 🔑 Load from config.py
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_PATH, scopes=SCOPES)

drive_service = build('drive', 'v3', credentials=credentials)

def get_unique_filename(service, name, parent_id):
    base, ext = os.path.splitext(name)
    counter = 1
    new_name = name
    while file_exists(service, new_name, parent_id):
        new_name = f"{base}_{counter}{ext}"
        counter += 1
    return new_name

def file_exists(service, name, parent_id):
    query = f"'{parent_id}' in parents and name = '{name}' and trashed = false"
    results = service.files().list(q=query, fields="files(id)").execute()
    return bool(results.get("files"))

def upload_to_drive(local_path, folder_id, service, override_name=None, progress_callback=None):
    filename = override_name or os.path.basename(local_path)

    file_metadata = {
        "name": filename,
        "parents": [folder_id],
    }

    media = MediaFileUpload(local_path, resumable=True)

    request = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id',
        supportsAllDrives=True
    )

    def do_upload_chunks():
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status and progress_callback:
                progress_callback(status.progress())
        return response.get("id")

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(do_upload_chunks)
        return future.result()
    
def is_tool_available(tool_name, fallback_path=None):
    try:
        subprocess.run([tool_name, "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except FileNotFoundError:
        if fallback_path and Path(fallback_path).exists():
            try:
                subprocess.run([str(fallback_path), "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return True
            except Exception:
                return False
        return False

def show_progress(block_num, block_size, total_size):
    downloaded = block_num * block_size
    percent = min(100, downloaded * 100 / total_size) if total_size > 0 else 0
    print(f"\rDownloading... {percent:.2f}% complete", end="")

def download_and_extract_ffmpeg():
    need_download = True

    if FFMPEG_ZIP.exists():
        print("Found existing ffmpeg.zip — checking integrity...")
        try:
            with zipfile.ZipFile(FFMPEG_ZIP, 'r') as test_zip:
                bad_file = test_zip.testzip()
                if bad_file:
                    raise zipfile.BadZipFile(f"Corrupt file inside zip: {bad_file}")
            print("Zip file is valid. Skipping download.")
            need_download = False
        except zipfile.BadZipFile:
            print("Zip file is corrupted. Deleting and re-downloading...")
            FFMPEG_ZIP.unlink()
            need_download = True

    if need_download:
        print("Downloading FFmpeg...")
        urllib.request.urlretrieve(FFMPEG_URL, FFMPEG_ZIP, reporthook=show_progress)
        print("\nDownload complete.")

        print("Extracting FFmpeg...")
        if FFMPEG_DIR.exists():
            print("Removing old FFmpeg folder...")
            shutil.rmtree(FFMPEG_DIR)

        with zipfile.ZipFile(FFMPEG_ZIP, 'r') as zip_ref:
            zip_ref.extractall(FFMPEG_DIR)

        print("FFmpeg extraction complete.")

    # This block always runs, to ensure the binaries are in place (even if we skipped re-download)
    for root, dirs, files in os.walk(FFMPEG_DIR):
        root_path = Path(root)
        if "ffmpeg.exe" in files:
            ffmpeg_path = root_path / "ffmpeg.exe"
            if ffmpeg_path != FFMPEG_BIN:
                shutil.copy(ffmpeg_path, FFMPEG_BIN)
        if "ffprobe.exe" in files:
            ffprobe_path = root_path / "ffprobe.exe"
            if ffprobe_path != FFPROBE_BIN:
                shutil.copy(ffprobe_path, FFPROBE_BIN)

    print(f"FFmpeg and ffprobe installed in: {FFMPEG_DIR}")

def is_in_system_path(path_to_check):
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_READ) as key:
            current_path, _ = winreg.QueryValueEx(key, "Path")
            return path_to_check.lower() in current_path.lower()
    except Exception:
        return False

def add_to_system_path(path_to_add):
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_ALL_ACCESS) as key:
            current_path, _ = winreg.QueryValueEx(key, "Path")
            if path_to_add not in current_path:
                new_path = current_path + ";" + path_to_add
                winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, new_path)
                print(f"Added to system PATH: {path_to_add}")
                print("You may need to restart your terminal or log out/in to apply changes.")
            else:
                print("FFmpeg path is already in system PATH.")
    except Exception as e:
        print(f"Failed to update system PATH: {e}")

def format_timestamp(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02}:{m:02}:{s:02}"
        
def is_path_in_env(path_to_check):
    """Checks if a path or its parents are in the current session PATH (fuzzy match)."""
    check = str(Path(path_to_check).resolve()).lower()
    env_paths = [str(Path(p).resolve()).lower() for p in os.environ["PATH"].split(os.pathsep) if p.strip()]
    return any(check in p or p in check for p in env_paths)

def ensure_ffmpeg_installed():
    try:
        print("Checking for ffmpeg and ffprobe...")

        # 1. Check if ffmpeg is already available globally
        ffmpeg_ok = is_tool_available("ffmpeg")
        ffprobe_ok = is_tool_available("ffprobe")

        if ffmpeg_ok and ffprobe_ok:
            print("ffmpeg and ffprobe are already available globally.")
            return

        # 2. Check fallback path (our custom FFmpeg_DIR)
        fallback_found = is_tool_available(str(FFMPEG_BIN)) and is_tool_available(str(FFPROBE_BIN))
        if fallback_found:
            print("ffmpeg found via fallback location.")
        else:
            print("ffmpeg not found. Installing FFmpeg...")
            download_and_extract_ffmpeg()

        # 3. Add to current session PATH if not already present
        ffmpeg_dir_str = str(FFMPEG_DIR)
        print(f"Checking if FFMPEG_DIR is in current session PATH: {ffmpeg_dir_str}")
        if not is_path_in_env(ffmpeg_dir_str):
            os.environ["PATH"] += os.pathsep + ffmpeg_dir_str
            print("Temporarily added FFmpeg to current session PATH.")
        else:
            print("FFmpeg already in current session PATH.")

        # 4. Add to system/user PATH via registry if not already there
        if not is_in_system_path(ffmpeg_dir_str):
            print("FFmpeg not found in user system PATH, adding it...")
            add_to_system_path(ffmpeg_dir_str)
        else:
            print("FFmpeg already in user system PATH (registry).")

        # 5. Recheck after setup
        ffmpeg_ok = is_tool_available("ffmpeg", fallback_path=FFMPEG_BIN)
        ffprobe_ok = is_tool_available("ffprobe", fallback_path=FFPROBE_BIN)

        print(f"\nffmpeg: {'found' if ffmpeg_ok else 'not found'}")
        print(f"ffprobe: {'found' if ffprobe_ok else 'not found'}")

        if not ffmpeg_ok:
            print(f"You can use ffmpeg directly from: {FFMPEG_BIN}")
        if not ffprobe_ok:
            print(f"You can use ffprobe directly from: {FFPROBE_BIN}")

        if ffmpeg_ok and ffprobe_ok:
            print("\nFFmpeg and ffprobe are ready to use.")
        else:
            print("\nOne or both tools are still unavailable from the command line.")
            print("Try restarting your terminal or system for changes to take effect.")

    except Exception as e:
        print(f"\nError occurred: {e}")

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
    log_path = Path(get_base_path()) / "debug.log"

    # Get the root logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # Remove existing FileHandlers to avoid duplicates
    # (but preserve any StreamHandlers that might be needed)
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

    except HttpError as e:
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