#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Centralized utilities for FFmpeg-related functionality,
including executable detection, availability checking, and installation.
"""

import os
import sys
import re
import logging
import subprocess
import shutil
from pathlib import Path

from config import FFMPEG_DIR
from utils import is_running_in_debug_mode

def find_executable(name):
    """Find an executable, prioritizing bundled versions with the application"""
    exe_name = f"{name}.exe" if sys.platform == "win32" else name
    
    # HIGHEST PRIORITY: Check if running from PyInstaller bundle
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # When running as PyInstaller onefile, binaries are in _MEIPASS
        meipass_path = os.path.join(sys._MEIPASS, exe_name)
        logging.debug(f"Checking for {name} in PyInstaller temp dir: {meipass_path}")
        if os.path.isfile(meipass_path) and os.access(meipass_path, os.X_OK):
            logging.info(f"Found {name} in PyInstaller temp dir: {meipass_path}")
            return meipass_path
    
    # SECOND PRIORITY: Check in development bundled locations
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        app_dir = os.path.dirname(sys.executable)
    else:
        # Running as script
        app_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    
    logging.debug(f"Application directory: {app_dir}")
    
    # Check in application directory and subdirectories
    bundled_locations = [
        os.path.join(app_dir, exe_name),
        os.path.join(app_dir, "ffmpeg", exe_name),
        os.path.join(app_dir, "bin", exe_name),
    ]
    
    # For development, also check relative paths
    debug_mode = is_running_in_debug_mode()
    if debug_mode:
        # Add paths relative to your development structure
        parent_dir = os.path.abspath(os.path.join(app_dir, ".."))
        bundled_locations.extend([
            os.path.join(parent_dir, "ffmpeg", exe_name),
            os.path.join(app_dir, "..", "ffmpeg", exe_name),
        ])
    
    # Check bundled locations BEFORE checking PATH
    for location in bundled_locations:
        logging.debug(f"Checking for {name} at: {location}")
        if os.path.isfile(location) and os.access(location, os.X_OK):
            logging.info(f"Found bundled {name} at: {location}")
            return location
    
    # LAST RESORT: Fall back to PATH (system installed versions)
    path_exe = shutil.which(name)
    if path_exe:
        logging.warning(f"Using system {name} from PATH (bundled version not found): {path_exe}")
        return path_exe
    
    # Not found anywhere
    logging.error(f"{name} not found in any location")
    return None

def check_ffmpeg_availability():
    """Check if FFmpeg and FFprobe are available"""
    results = {
        "ffmpeg": {"available": False, "path": None, "version": None, "is_bundled": False},
        "ffprobe": {"available": False, "path": None, "version": None, "is_bundled": False},
        "hardware_accel": {
            "nvenc": False,
            "hevc_nvenc": False,
            "qsv": False,
            "vaapi": False,
            "amf": False
        }
    }
    
    # Get application directory
    app_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    
    # Check for FFmpeg
    ffmpeg_path = find_executable("ffmpeg")
    if ffmpeg_path:
        results["ffmpeg"]["available"] = True
        results["ffmpeg"]["path"] = ffmpeg_path
        
        # Check if using bundled version
        results["ffmpeg"]["is_bundled"] = app_dir in ffmpeg_path
        bundled_str = " (bundled)" if results["ffmpeg"]["is_bundled"] else ""
        
        # Get version
        version_result = run_command([ffmpeg_path, "-version"])
        if version_result["success"]:
            first_line = version_result["stdout"].split("\n")[0]
            version_match = re.search(r'version\s+(\S+)', first_line)
            if version_match:
                results["ffmpeg"]["version"] = version_match.group(1)
                logging.info(f"FFmpeg found: {ffmpeg_path}{bundled_str} (version {version_match.group(1)})")
            else:
                logging.info(f"FFmpeg found: {ffmpeg_path}{bundled_str}")
        
        # Check for hardware acceleration (avoiding duplicate logs)
        encoders_result = run_command([ffmpeg_path, "-encoders"])
        if encoders_result["success"]:
            # Track which ones we've already logged
            logged_encoders = set()
            
            for line in encoders_result["stdout"].split("\n"):
                # Check for NVENC (NVIDIA)
                if "nvenc" in line and not results["hardware_accel"]["nvenc"]:
                    results["hardware_accel"]["nvenc"] = True
                    if "nvenc" not in logged_encoders:
                        logging.info("NVENC hardware encoding available")
                        logged_encoders.add("nvenc")
                    
                # Check for HEVC_NVENC (NVIDIA H.265)
                if "hevc_nvenc" in line:
                    results["hardware_accel"]["hevc_nvenc"] = True
                
                # Check for QSV (Intel QuickSync)
                if "qsv" in line and not results["hardware_accel"]["qsv"]:
                    results["hardware_accel"]["qsv"] = True
                    if "qsv" not in logged_encoders:
                        logging.info("Intel QuickSync hardware encoding available")
                        logged_encoders.add("qsv")
                
                # Check for VAAPI (Linux VA-API)
                if "vaapi" in line and not results["hardware_accel"]["vaapi"]:
                    results["hardware_accel"]["vaapi"] = True
                    if "vaapi" not in logged_encoders:
                        logging.info("VAAPI hardware encoding available")
                        logged_encoders.add("vaapi")
                
                # Check for AMF (AMD)
                if "amf" in line and not results["hardware_accel"]["amf"]:
                    results["hardware_accel"]["amf"] = True
                    if "amf" not in logged_encoders:
                        logging.info("AMD AMF hardware encoding available")
                        logged_encoders.add("amf")
    else:
        logging.warning("❌ FFmpeg not found")
    
    # Check for FFprobe
    ffprobe_path = find_executable("ffprobe")
    if ffprobe_path:
        results["ffprobe"]["available"] = True
        results["ffprobe"]["path"] = ffprobe_path
        
        # Check if using bundled version
        results["ffprobe"]["is_bundled"] = app_dir in ffprobe_path
        bundled_str = " (bundled)" if results["ffprobe"]["is_bundled"] else ""
        
        logging.info(f"FFprobe found: {ffprobe_path}{bundled_str}")
    else:
        logging.warning("❌ FFprobe not found")
    
    return results

def run_command(cmd):
    """Run a command and return its output"""
    try:
        # Use subprocess.CREATE_NO_WINDOW flag on Windows to prevent command window flashing
        extra_args = {}
        if sys.platform == "win32":
            extra_args["creationflags"] = 0x08000000  # CREATE_NO_WINDOW
        
        result = subprocess.run(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True, 
            timeout=10,
            **extra_args
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e)
        }

def is_in_system_path(path_to_check):
    """Check if a path is in the system PATH via registry"""
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_READ) as key:
            current_path, _ = winreg.QueryValueEx(key, "Path")
            return path_to_check.lower() in current_path.lower()
    except Exception:
        return False

def add_to_system_path(path_to_add):
    """Add a path to the system PATH via registry"""
    try:
        import winreg
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

def is_path_in_env(path_to_check):
    """Checks if a path or its parents are in the current session PATH (fuzzy match)."""
    check = str(Path(path_to_check).resolve()).lower()
    env_paths = [str(Path(p).resolve()).lower() for p in os.environ["PATH"].split(os.pathsep) if p.strip()]
    return any(check in p or p in check for p in env_paths)

def ensure_ffmpeg_installed():
    """Ensure FFmpeg is available, using bundled versions"""
    try:
        print("Checking for ffmpeg and ffprobe...")

        # Check if ffmpeg is already available (bundled or in PATH)
        ffmpeg_ok = is_tool_available("ffmpeg")
        ffprobe_ok = is_tool_available("ffprobe")

        if ffmpeg_ok and ffprobe_ok:
            print("✓ ffmpeg and ffprobe are available.")
            return True

        # Check bundled ffmpeg
        ffmpeg_dir_str = str(FFMPEG_DIR)
        bundled_ffmpeg = os.path.join(ffmpeg_dir_str, "ffmpeg.exe")
        bundled_ffprobe = os.path.join(ffmpeg_dir_str, "ffprobe.exe")
        
        if os.path.exists(bundled_ffmpeg) and os.path.exists(bundled_ffprobe):
            print("✓ Found bundled ffmpeg and ffprobe.")
            
            # Add to current session PATH if not already present
            if not is_path_in_env(ffmpeg_dir_str):
                os.environ["PATH"] += os.pathsep + ffmpeg_dir_str
                print("✓ Added bundled FFmpeg to current session PATH.")
            
            return True
        
        # If we get here, we couldn't find ffmpeg
        print("❌ ffmpeg and/or ffprobe not found.")
        print("This application requires ffmpeg and ffprobe to function.")
        print("Please ensure the application was properly installed with all bundled components.")
        
        return False

    except Exception as e:
        print(f"\n❌ Error checking ffmpeg: {e}")
        return False

def is_tool_available(tool_name, fallback_path=None):
    """Check if a command-line tool is available"""
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