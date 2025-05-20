import os
import sys
from pathlib import Path
from paths import get_resource_path, get_base_path

FFMPEG_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
BASE_DIR = Path.cwd()
FFMPEG_ZIP = BASE_DIR / "ffmpeg.zip"
FFMPEG_DIR = BASE_DIR / "ffmpeg"  # <-- Keep as Path object
FFMPEG_BIN = FFMPEG_DIR / "ffmpeg.exe"
FFPROBE_BIN = FFMPEG_DIR / "ffprobe.exe"
OFFLINE_CSV_BACKUP = "reggae_music_backup.csv"
SETTINGS_FILE = "looper_settings.json"
DEFAULT_MUSIC_FOLDER = "\\Ren1\0000_MUSIC"
DEBUG_LOG_FILE = "debug_log.txt"
GOOGLE_SERVICE_ACCOUNT_KEY = "credentials.json"
GOOGLE_DRIVE_ROOT_FOLDER_ID = "1XPtNN0hSo_fpH7FY7dTcDV0TqThTmJXY"
SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_PATH = get_resource_path("credentials.json")
FOLDER_ID_MAP_PATH = os.path.join(get_base_path(), "folder_id_map.json")
UPLOADER_WORKER_PATH = os.path.join(get_base_path(), "uploader_worker.py")

SETTINGS_FILE = os.path.join(os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else __file__), "settings.json")

RENDER_DIR = os.getcwd()  # temporary fallback — actual value is loaded later
FOLDER_ID = "17wOEXg-uAC04qEHog0KT2dhh3WkOEpXO"

SHEET_PRESETS = {
    "Reggae": "https://docs.google.com/spreadsheets/d/107JwSxtewrJX4T0o6sfelsV53nc3a5N3sh3wP3sK0E8/edit?gid=1002948794#gid=1002948794",
    "Gospel": "https://docs.google.com/spreadsheets/d/e/2PACX-1vTbd3nMP31hHfDTHR_70bv2vZvItOCrOU_LWK9xSn7BTrxw8dPMSAY0--uUk3_yehoOH-Iw_vloUuH4/pub?gid=501698625&single=true&output=csv"
}