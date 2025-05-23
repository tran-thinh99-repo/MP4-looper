@echo off
cd /d "%~dp0"  :: change working dir to this script's folder

echo Building MP4 Looper...

:: Clean old builds
rmdir /s /q build
del /q MP4_Looper.spec
rmdir /s /q "MP4 Looper build"

:: Create build directory if it doesn't exist
if not exist "MP4 Looper build" mkdir "MP4 Looper build"

:: Build with PyInstaller
pyinstaller ^
  --noconfirm ^
  --windowed ^
  --onefile ^
  --noconsole ^
  --name "MP4 Looper" ^
  --icon="mp4_looper_icon.ico" ^
  --distpath "MP4 Looper build" ^
  --hidden-import=tkinterdnd2 ^
  --hidden-import=customtkinter ^
  --hidden-import=google.oauth2 ^
  --hidden-import=googleapiclient ^
  --hidden-import=gspread ^
  --add-data "help_content_en.md;." ^
  --add-data "help_content_vi.md;." ^
  --add-data "credentials.json;." ^
  --add-data "mp4_looper_icon.ico;." ^
  --add-data ".env;." ^
  --add-binary "..\\ffmpeg\\ffmpeg.exe;." ^
  --add-binary "..\\ffmpeg\\ffprobe.exe;." ^
  mp4_looper.py

echo.
echo ✅ Build complete! Check the "MP4 Looper build" folder.