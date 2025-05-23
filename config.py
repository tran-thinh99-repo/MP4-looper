import os
import sys
from pathlib import Path
from paths import get_resource_path, get_base_path
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

BASE_DIR = Path.cwd()
FFMPEG_DIR = BASE_DIR / "ffmpeg"  # <-- Keep as Path object
SETTINGS_FILE = "looper_settings.json"
SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets.readonly']
SERVICE_ACCOUNT_PATH = get_resource_path("credentials.json")
FOLDER_ID_MAP_PATH = os.path.join(get_base_path(), "folder_id_map.json")
UPLOADER_WORKER_PATH = os.path.join(get_base_path(), "uploader_worker.py")
SETTINGS_FILE = os.path.join(os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__), "settings.json")

# Get environment variables with defaults
GOOGLE_DRIVE_ROOT_FOLDER_ID = os.getenv('GOOGLE_DRIVE_ROOT_FOLDER_ID', '')
GOOGLE_SPREADSHEET_ID = os.getenv('GOOGLE_SPREADSHEET_ID', '')
GOOGLE_SPREADSHEET_NAME = os.getenv('GOOGLE_SPREADSHEET_NAME', 'REGGAE')
GITHUB_REPO_OWNER = os.getenv('GITHUB_REPO_OWNER', 'tran-thinh99-repo')
GITHUB_REPO_NAME = os.getenv('GITHUB_REPO_NAME', 'MP4-looper')

# Additional sheet presets available for import
REGGAE_SHEET_URL = os.getenv('REGGAE_SHEET_URL', '')
GOSPEL_SHEET_URL = os.getenv('GOSPEL_SHEET_URL', '')

# Constants
AUTH_SHEET_NAME = "Auth"  # The name of your sheet tab
MAX_AUTH_AGE = 7 * 24 * 60 * 60  # 7 days in seconds
AUTH_SHEET_ID = os.getenv("AUTH_SHEET_ID", "13on93GUGOMSHzMw3JemVnQQj0KRfFh-qf5xHd4pbVO0")

DEFAULT_DURATION_SECONDS = 3600