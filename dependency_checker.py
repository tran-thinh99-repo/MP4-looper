#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Simple utility to check for video processing dependencies:
- FFmpeg and FFProbe availability
- NVIDIA drivers
- NVENC hardware encoding support
"""

import os
import sys
import re
import logging
from utils import is_running_in_debug_mode
from ffmpeg_utils import run_command, check_ffmpeg_availability

def setup_logging(log_file=None):
    """Set up basic logging"""
    # Check if logging is already configured (to avoid duplicate handlers)
    if len(logging.getLogger().handlers) > 0:
        return
        
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(levelname)s:%(message)s",
        handlers=[logging.StreamHandler()]
    )
    
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        logging.getLogger().addHandler(file_handler)

def check_nvidia():
    """Check if NVIDIA drivers are installed and GPU is available"""
    results = {
        "drivers_installed": False,
        "driver_version": None,
        "gpu_model": None
    }
    
    # Try to run nvidia-smi
    nvidia_smi = "nvidia-smi"
    if sys.platform == "win32":
        # Check common paths on Windows
        potential_paths = [
            os.path.join(os.environ.get("ProgramFiles", "C:\\Program Files"), "NVIDIA Corporation", "NVSMI", "nvidia-smi.exe"),
            os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "System32", "nvidia-smi.exe")
        ]
        
        for path in potential_paths:
            if os.path.isfile(path):
                nvidia_smi = path
                break
    
    # Run nvidia-smi to check for drivers and version
    result = run_command([nvidia_smi])
    if result["success"]:
        results["drivers_installed"] = True
        
        # Get driver version
        driver_match = re.search(r'Driver Version: (\d+\.\d+(?:\.\d+)?)', result["stdout"])
        if driver_match:
            results["driver_version"] = driver_match.group(1)
            logging.info(f"NVIDIA drivers found: version {driver_match.group(1)}")
        else:
            logging.info("NVIDIA drivers found, but couldn't determine version")
        
        # Try to get GPU model - clean up output for better logging
        for line in result["stdout"].split("\n"):
            if "|" in line and "%" in line:
                parts = line.split("|")
                if len(parts) >= 2:
                    gpu_model = parts[1].strip()
                    # Try to extract just the model name, not usage data
                    model_match = re.search(r'(NVIDIA\s+[A-Za-z0-9]+(?:\s+[A-Za-z0-9]+)*)', gpu_model)
                    if model_match:
                        gpu_model = model_match.group(1).strip()
                    if gpu_model:
                        results["gpu_model"] = gpu_model
                        logging.info(f"NVIDIA GPU: {gpu_model}")
                        break
    else:
        logging.warning("NVIDIA drivers not detected or not working")
    
    return results

def main():
    """Main function"""
    setup_logging()
    
    # Check for debug mode
    debug_mode = is_running_in_debug_mode()
    if debug_mode:
        logging.info("Running in debug mode")
    
    logging.info("Checking video processing dependencies...")
    
    # Check FFmpeg and FFprobe
    ffmpeg_results = check_ffmpeg_availability()
    
    # Check NVIDIA GPU
    nvidia_results = check_nvidia()
    
    # Flag to track critical issues
    critical_issues = False
    
    # Summary
    logging.info("\n----- Dependency Check Summary -----")
    
    # Check FFmpeg
    if ffmpeg_results["ffmpeg"]["available"]:
        bundled_str = " (bundled)" if ffmpeg_results["ffmpeg"]["is_bundled"] else ""
        logging.info(f"✅ FFmpeg: Available{bundled_str} ({ffmpeg_results['ffmpeg']['path']})")
    else:
        logging.error("❌ FFmpeg: Not found")
        critical_issues = True
        
    # Check FFprobe
    if ffmpeg_results["ffprobe"]["available"]:
        bundled_str = " (bundled)" if ffmpeg_results["ffprobe"]["is_bundled"] else ""
        logging.info(f"✅ FFprobe: Available{bundled_str} ({ffmpeg_results['ffprobe']['path']})")
    else:
        logging.error("❌ FFprobe: Not found")
        critical_issues = True
    
    # Hardware acceleration
    hw_accel = [k for k, v in ffmpeg_results["hardware_accel"].items() if v]
    if hw_accel:
        logging.info(f"✅ Hardware acceleration: {', '.join(hw_accel)}")
    else:
        logging.warning("⚠️ No hardware acceleration available")
    
    # NVIDIA - check driver version meets minimum requirements (576.02)
    MINIMUM_DRIVER_VERSION = "576.02"
    
    if nvidia_results["drivers_installed"]:
        if nvidia_results["driver_version"]:
            current_version = nvidia_results["driver_version"]
            
            # Compare versions
            if _compare_versions(current_version, MINIMUM_DRIVER_VERSION) >= 0:
                logging.info(f"✅ NVIDIA drivers: Available (version {current_version})")
            else:
                logging.error(f"❌ NVIDIA drivers: Version {current_version} is too old (minimum required: {MINIMUM_DRIVER_VERSION})")
                critical_issues = True
                
            # Check if NVENC is available
            if ffmpeg_results["hardware_accel"]["nvenc"]:
                logging.info("✅ NVENC hardware encoding is available")
            else:
                logging.warning("⚠️ NVIDIA GPU detected but NVENC encoding is not available in FFmpeg")
        else:
            logging.warning("⚠️ NVIDIA drivers found but version could not be determined")
    else:
        logging.warning("⚠️ NVIDIA drivers not detected")
    
    # Exit with error code if critical issues found
    if critical_issues:
        logging.error("\n❌ Critical dependency issues found. Application will exit.")
        return 1
        
    return 0

def _compare_versions(version1, version2):
    """Compare two version strings, returns:
    -1 if version1 < version2
     0 if version1 == version2
     1 if version1 > version2
    """
    v1_parts = [int(x) for x in version1.split('.')]
    v2_parts = [int(x) for x in version2.split('.')]
    
    # Pad with zeros to make lengths equal
    max_length = max(len(v1_parts), len(v2_parts))
    v1_parts += [0] * (max_length - len(v1_parts))
    v2_parts += [0] * (max_length - len(v2_parts))
    
    # Compare each part
    for i in range(max_length):
        if v1_parts[i] < v2_parts[i]:
            return -1
        elif v1_parts[i] > v2_parts[i]:
            return 1
            
    # If we get here, versions are equal
    return 0

if __name__ == "__main__":
    exit_code = main()
    if exit_code != 0:
        # If running as a script directly, exit with error code
        sys.exit(exit_code)
    
# Function that can be called from external applications
def check_dependencies(exit_on_error=True, show_popup=True):
    """Check if all required dependencies are available
    
    Args:
        exit_on_error: If True, exit the application if critical dependencies are missing
        show_popup: If True, show a message box for critical errors
        
    Returns:
        Tuple of (success, results) where:
            - success: True if all critical dependencies met, False otherwise
            - results: Dictionary with results of dependency checks
    """
    # Check for debug mode
    debug_mode = 'debugpy' in sys.modules or any('debug' in arg.lower() for arg in sys.argv)
    if debug_mode:
        logging.info("Running in debug mode")
    
    logging.info("Checking video processing dependencies...")
    
    # Check FFmpeg and FFprobe
    ffmpeg_results = check_ffmpeg_availability()
    
    # Check NVIDIA GPU
    nvidia_results = check_nvidia()
    
    # Create combined results
    results = {
        "ffmpeg": ffmpeg_results["ffmpeg"],
        "ffprobe": ffmpeg_results["ffprobe"],
        "hardware_accel": ffmpeg_results["hardware_accel"],
        "nvidia": nvidia_results
    }
    
    # Flag to track critical issues
    critical_issues = False
    error_message = "Critical dependency issues found:\n\n"
    
    # Summary
    logging.info("\n----- Dependency Check Summary -----")
    
    # Check FFmpeg - CRITICAL
    if ffmpeg_results["ffmpeg"]["available"]:
        bundled_str = " (bundled)" if ffmpeg_results["ffmpeg"]["is_bundled"] else ""
        logging.info(f"✅ FFmpeg: Available{bundled_str} ({ffmpeg_results['ffmpeg']['path']})")
    else:
        error_message += "❌ FFmpeg not found. Video processing will not work.\n"
        logging.error("❌ FFmpeg: Not found")
        critical_issues = True
        
    # Check FFprobe - CRITICAL
    if ffmpeg_results["ffprobe"]["available"]:
        bundled_str = " (bundled)" if ffmpeg_results["ffprobe"]["is_bundled"] else ""
        logging.info(f"✅ FFprobe: Available{bundled_str} ({ffmpeg_results['ffprobe']['path']})")
    else:
        error_message += "❌ FFprobe not found. Video analysis will not work.\n"
        logging.error("❌ FFprobe: Not found")
        critical_issues = True
    
    # Hardware acceleration
    hw_accel = [k for k, v in ffmpeg_results["hardware_accel"].items() if v]
    if hw_accel:
        logging.info(f"✅ Hardware acceleration: {', '.join(hw_accel)}")
    else:
        logging.warning("⚠️ No hardware acceleration available")
    
    # NVIDIA - check driver version meets minimum requirements (576.02) - CRITICAL
    MINIMUM_DRIVER_VERSION = "576.02"
    
    if nvidia_results["drivers_installed"]:
        if nvidia_results["driver_version"]:
            current_version = nvidia_results["driver_version"]
            
            # Compare versions
            if _compare_versions(current_version, MINIMUM_DRIVER_VERSION) >= 0:
                logging.info(f"✅ NVIDIA drivers: Available (version {current_version})")
            else:
                error_message += f"❌ NVIDIA driver version {current_version} is too old.\n"
                error_message += f"   Minimum required: {MINIMUM_DRIVER_VERSION}\n"
                error_message += f"   Please update your NVIDIA drivers.\n\n"
                logging.error(f"❌ NVIDIA drivers: Version {current_version} is too old (minimum required: {MINIMUM_DRIVER_VERSION})")
                critical_issues = True
                
            # Check if NVENC is available
            if ffmpeg_results["hardware_accel"]["nvenc"]:
                logging.info("✅ NVENC hardware encoding is available")
            else:
                logging.warning("⚠️ NVIDIA GPU detected but NVENC encoding is not available in FFmpeg")
        else:
            # If we can't determine driver version, treat as critical
            error_message += "❌ NVIDIA driver version could not be determined.\n"
            error_message += "   Please ensure NVIDIA drivers are properly installed.\n\n"
            logging.error("❌ NVIDIA drivers: Version could not be determined")
            critical_issues = True
    else:
        # No NVIDIA drivers at all - CRITICAL
        error_message += "❌ NVIDIA drivers not found.\n"
        error_message += "   This application requires NVIDIA GPU with hardware acceleration.\n"
        error_message += "   Please install NVIDIA drivers version {MINIMUM_DRIVER_VERSION} or higher.\n\n"
        logging.error("❌ NVIDIA drivers: Not detected")
        critical_issues = True
    
    # Handle critical issues
    if critical_issues:
        logging.error("\n❌ Critical dependency issues found.")
        
        # Add general instructions to error message
        error_message += "Please resolve these issues before running the application:\n"
        error_message += "1. Ensure NVIDIA drivers are installed and up to date\n"
        error_message += "2. Verify FFmpeg is properly bundled with the application\n"
        error_message += "3. Contact support if issues persist"
        
        # Show message box if requested
        if show_popup:
            try:
                import tkinter as tk
                from tkinter import messagebox
                
                # Create temporary root window
                root = tk.Tk()
                root.withdraw()  # Hide the root window
                
                # Show error message
                messagebox.showerror("Dependency Check Failed", error_message)
                
                # Destroy the root window
                root.destroy()
            except Exception as e:
                logging.error(f"Failed to show message box: {e}")
        
        # Exit if requested
        if exit_on_error:
            logging.error("Application will exit due to critical dependency issues.")
            sys.exit(1)
            
    return (not critical_issues, results)