@echo off
cd /d "%~dp0"

echo Building MP4 Looper...
echo.

:: Check if ffmpeg files exist
if not exist "..\ffmpeg\ffmpeg.exe" (
    echo ERROR: ffmpeg.exe not found at ..\ffmpeg\ffmpeg.exe
    pause
    exit /b 1
)

if not exist "..\ffmpeg\ffprobe.exe" (
    echo ERROR: ffprobe.exe not found at ..\ffmpeg\ffprobe.exe
    pause
    exit /b 1
)

echo ✅ Found ffmpeg.exe and ffprobe.exe

:: Clean old builds
rmdir /s /q build 2>nul
del /q MP4_Looper.spec 2>nul
rmdir /s /q "MP4 Looper build" 2>nul

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
  --add-binary "..\ffmpeg\ffmpeg.exe;." ^
  --add-binary "..\ffmpeg\ffprobe.exe;." ^
  main.py

echo.
if exist "MP4 Looper build\MP4 Looper.exe" (
    echo ✅ Build complete! Check the "MP4 Looper build" folder.
) else (
    echo ❌ Build failed! Check the error messages above.
)
pause