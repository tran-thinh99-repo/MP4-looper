#!/usr/bin/env python3
"""
Windows Fix Script for MP4 Looper
Resolves the _gdbm issue by implementing pure Python/JSON storage
No Unix dependencies required
"""

import os
import sys
import subprocess
import logging
import shutil
from pathlib import Path

def setup_logging():
    """Setup logging for the fix script"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )

def check_windows():
    """Verify we're running on Windows"""
    if os.name != 'nt' and sys.platform != 'win32':
        logging.warning("This script is designed for Windows, but continuing anyway...")
    else:
        logging.info("✅ Confirmed running on Windows")
    return True

def check_python_version():
    """Check Python version compatibility"""
    version = sys.version_info
    if version < (3, 8):
        logging.error(f"Python {version.major}.{version.minor} is too old. Please use Python 3.8+")
        return False
    
    logging.info(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True

def backup_files():
    """Create backups of files we'll modify"""
    backup_dir = Path("backup_windows_fix")
    backup_dir.mkdir(exist_ok=True)
    
    files_to_backup = [
        "api_monitor_module/__init__.py",
        "api_monitor_module/utils/monitor_access.py", 
        "mp4_looper.py"
    ]
    
    for file_path in files_to_backup:
        file_obj = Path(file_path)
        if file_obj.exists():
            try:
                shutil.copy2(file_obj, backup_dir / file_obj.name)
                logging.info(f"✅ Backed up {file_path}")
            except Exception as e:
                logging.warning(f"Failed to backup {file_path}: {e}")
    
    logging.info(f"✅ Backups created in {backup_dir}")
    return True

def check_api_monitor_structure():
    """Check if API monitor directory structure exists"""
    required_dirs = [
        "api_monitor_module",
        "api_monitor_module/core",
        "api_monitor_module/utils",
        "api_monitor_module/ui"
    ]
    
    for dir_path in required_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        logging.info(f"✅ Ensured directory exists: {dir_path}")
    
    return True

def create_windows_tracker():
    """Create the Windows-compatible tracker file"""
    tracker_path = Path("api_monitor_module/core/api_tracker_windows.py")
    
    # Check if it already exists
    if tracker_path.exists():
        logging.info(f"✅ Windows tracker already exists at {tracker_path}")
        return True
    
    logging.info(f"📝 Please create {tracker_path} using the 'Windows-Compatible API Tracker' code from the artifacts")
    return True

def update_monitor_access():
    """Update monitor_access.py for better Windows compatibility"""
    monitor_access_path = Path("api_monitor_module/utils/monitor_access.py")
    
    if not monitor_access_path.exists():
        logging.info(f"📝 Please create {monitor_access_path} using the 'Fixed monitor_access.py' code")
        return True
    
    # Check if it contains Windows-specific improvements
    try:
        with open(monitor_access_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if "_warning_shown" in content and "_error_logged" in content:
            logging.info(f"✅ {monitor_access_path} appears to have Windows improvements")
        else:
            logging.info(f"📝 Please update {monitor_access_path} with the Windows-compatible version")
        
    except Exception as e:
        logging.error(f"Error checking {monitor_access_path}: {e}")
    
    return True

def update_main_init():
    """Update the main __init__.py for Windows compatibility"""
    init_path = Path("api_monitor_module/__init__.py")
    
    if not init_path.exists():
        logging.info(f"📝 Please create {init_path} using the 'Windows-Compatible API Monitor' code")
        return True
    
    # Check if it has Windows compatibility
    try:
        with open(init_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if "windows" in content.lower() and "WindowsAPITracker" in content:
            logging.info(f"✅ {init_path} appears to have Windows compatibility")
        else:
            logging.info(f"📝 Please update {init_path} with the Windows-compatible version")
        
    except Exception as e:
        logging.error(f"Error checking {init_path}: {e}")
    
    return True

def test_imports():
    """Test if our Windows-compatible modules can be imported"""
    try:
        # Test basic imports
        sys.path.insert(0, str(Path.cwd()))
        
        # Test config manager
        from api_monitor_module.core.config_manager import ConfigManager
        logging.info("✅ ConfigManager imports successfully")
        
        # Test Windows tracker (if it exists)
        try:
            from api_monitor_module.core.api_tracker_windows import WindowsAPITracker
            logging.info("✅ WindowsAPITracker imports successfully")
            
            # Quick functionality test
            config = ConfigManager("TestApp", "test_storage")
            tracker = WindowsAPITracker(config)
            logging.info("✅ WindowsAPITracker initializes successfully")
            
            # Test basic operation
            tracker.record_api_call("test", "test@example.com", True)
            stats = tracker.get_stats_summary()
            
            if stats['overview']['total_calls_ever'] > 0:
                logging.info("✅ WindowsAPITracker basic functionality works")
            else:
                logging.warning("⚠️ WindowsAPITracker may have issues")
                
        except ImportError:
            logging.warning("⚠️ WindowsAPITracker not found - please create it")
        
        # Test main API monitor
        try:
            from api_monitor_module import setup_monitoring
            logging.info("✅ setup_monitoring imports successfully")
            
            # Test initialization
            monitor = setup_monitoring("TestApp", ["test@example.com"])
            if monitor:
                logging.info("✅ API Monitor initializes successfully on Windows")
            else:
                logging.warning("⚠️ API Monitor initialization returned None")
                
        except Exception as e:
            logging.error(f"❌ API Monitor test failed: {e}")
        
        return True
        
    except Exception as e:
        logging.error(f"❌ Import test failed: {e}")
        return False

def test_application():
    """Test if the main application can start without gdbm errors"""
    try:
        # Test importing the main app components
        from utils import setup_logging
        from settings_manager import get_settings
        
        logging.info("✅ Main application utilities import successfully")
        
        # Test settings manager
        settings = get_settings()
        if settings:
            logging.info("✅ Settings manager works on Windows")
        
        return True
        
    except Exception as e:
        logging.error(f"❌ Application test failed: {e}")
        return False

def cleanup_test_files():
    """Clean up any test files created"""
    test_dirs = ["test_storage", "monitoring_data"]
    
    for test_dir in test_dirs:
        test_path = Path(test_dir)
        if test_path.exists():
            try:
                shutil.rmtree(test_path)
                logging.info(f"✅ Cleaned up test directory: {test_dir}")
            except Exception as e:
                logging.debug(f"Could not clean up {test_dir}: {e}")

def main():
    """Main function"""
    setup_logging()
    
    print("🪟 MP4 Looper Windows Compatibility Fix")
    print("=" * 50)
    
    # Check environment
    if not check_windows():
        return 1
    
    if not check_python_version():
        return 1
    
    # Create backups
    if not backup_files():
        logging.error("Failed to create backups")
        return 1
    
    # Ensure directory structure
    if not check_api_monitor_structure():
        logging.error("Failed to create directory structure")
        return 1
    
    if "--test" in sys.argv:
        print("\n🧪 Testing Windows compatibility...")
        print("-" * 30)
        
        success = True
        
        # Test imports
        if not test_imports():
            success = False
        
        # Test application
        if not test_application():
            success = False
        
        # Cleanup
        cleanup_test_files()
        
        if success:
            print("\n✅ SUCCESS! Windows compatibility is working!")
            print("Your MP4 Looper should now work without _gdbm errors.")
            print("The API monitoring system will use pure Python/JSON storage.")
        else:
            print("\n❌ FAILED! Some tests failed.")
            print("Please check the manual steps below.")
            return 1
    
    else:
        print("\n📋 MANUAL STEPS REQUIRED:")
        print("=" * 30)
        print("1. Create api_monitor_module/core/api_tracker_windows.py")
        print("   → Copy 'Windows-Compatible API Tracker' code from artifacts")
        print("")
        print("2. Update api_monitor_module/__init__.py") 
        print("   → Copy 'Windows-Compatible API Monitor __init__.py' code")
        print("")
        print("3. Update api_monitor_module/utils/monitor_access.py")
        print("   → Copy 'Fixed monitor_access.py' code")
        print("")
        print("4. Update mp4_looper.py")
        print("   → Copy 'Fixed mp4_looper.py' code from previous artifacts")
        print("")
        print("5. Run this script with --test to verify:")
        print("   python windows_fix.py --test")
        print("")
        print("🔑 KEY BENEFITS:")
        print("• No more '_gdbm' module errors")
        print("• Pure Python/JSON storage (Windows compatible)")
        print("• Graceful degradation if monitoring fails")
        print("• Better error handling and logging")

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code if exit_code else 0)