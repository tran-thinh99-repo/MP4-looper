import os
import sys
import logging
import shutil
from tkinter import messagebox
from pathlib import Path

def get_base_path():
    """
    Returns the base path of the application. If bundled (e.g., with PyInstaller),
    it returns the AppData directory. Otherwise, it returns the current script directory.
    """
    if getattr(sys, 'frozen', False):
        # If bundled by PyInstaller, use a permanent install location
        APPDATA_DIR = Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "MP4Looper"
        base_path = APPDATA_DIR
    else:
        try:
            base_path = Path(__file__).resolve().parent
        except NameError:
            base_path = Path.cwd()

    # Ensure the path exists
    base_path.mkdir(parents=True, exist_ok=True)

    return str(base_path)

def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # If not running as a PyInstaller bundle, use the current directory
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
    
    return os.path.join(base_path, relative_path)

def format_timestamp(seconds):
    """Format seconds into HH:MM:SS timestamp"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02}:{m:02}:{s:02}"

def open_folder(path, label="Folder", parent_window=None):
    """Open a folder in the file explorer"""
    if os.path.isdir(path):
        os.startfile(path)
    else:
        from tkinter import messagebox
        messagebox.showerror(f"{label} Error", f"The {label.lower()} does not exist:\n{path}", parent=parent_window)

def clean_folder_with_confirmation(folder_path, title="Confirm Cleanup", parent_window=None):
    """Clean a folder with confirmation dialog"""
    
    folder_path = Path(folder_path)
    if not folder_path.exists() or not folder_path.is_dir():
        messagebox.showerror("Invalid Folder", f"❌ Folder does not exist:\n{folder_path}", parent=parent_window)
        return

    items = list(folder_path.iterdir())
    if not items:
        messagebox.showinfo(title, "✅ Folder is already clean.", parent=parent_window)
        logging.info(f"{title}: Already empty — {folder_path}")
        return

    preview = "\n".join(f.name for f in items[:20])
    if len(items) > 20:
        preview += f"\n… and {len(items) - 20} more."

    confirm = messagebox.askyesno(
        title,
        f"⚠️ This will delete ALL contents of:\n{folder_path}\n\n{len(items)} item(s):\n\n{preview}\n\nProceed?",
        parent=parent_window
    )

    if not confirm:
        return

    deleted = 0
    for item in items:
        try:
            if item.is_file() or item.is_symlink():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)
            deleted += 1
        except Exception as e:
            logging.error(f"Failed to delete {item.name}: {e}")

    messagebox.showinfo(title, f"✅ Deleted {deleted} item(s).", parent=parent_window)
    logging.info(f"🧹 Wiped {deleted} items from: {folder_path}")