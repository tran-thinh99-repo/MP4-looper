# google_services.py
"""
Centralized Google Services Manager
Handles all Google API connections (Sheets, Drive) with caching and error handling
"""

import os
import logging
import threading
import time
from typing import Optional, Dict, Any
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import gspread

from config import SERVICE_ACCOUNT_PATH, SCOPES
from api_monitor_module.utils.monitor_access import track_api_call_simple

class GoogleServicesManager:
    """Singleton manager for all Google API services"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._credentials = None
            self._sheets_service = None
            self._drive_service = None
            self._gspread_client = None
            self._last_credential_check = 0
            self._credential_cache_ttl = 3600  # 1 hour
            self._service_cache_ttl = 1800     # 30 minutes
            self._last_service_refresh = {}
            self._connection_errors = 0
            self._max_connection_errors = 3
            self._initialized = True
            
            logging.debug("Google Services Manager initialized")
    
    def _load_credentials(self, force_reload: bool = False) -> Optional[service_account.Credentials]:
        """Load and cache Google service account credentials"""
        current_time = time.time()
        
        # Use cached credentials if available and not expired
        if (not force_reload and 
            self._credentials and 
            current_time - self._last_credential_check < self._credential_cache_ttl):
            return self._credentials
        
        try:
            track_api_call_simple("google_credentials_load", success=False)
            
            if not os.path.exists(SERVICE_ACCOUNT_PATH):
                logging.error(f"Service account file not found: {SERVICE_ACCOUNT_PATH}")
                track_api_call_simple("google_credentials_load", success=False, 
                                    error_message="Credentials file not found")
                return None
            
            # Load credentials
            self._credentials = service_account.Credentials.from_service_account_file(
                SERVICE_ACCOUNT_PATH, scopes=SCOPES
            )
            
            self._last_credential_check = current_time
            self._connection_errors = 0  # Reset error count on success
            
            track_api_call_simple("google_credentials_load", success=True)
            
            # Log service account email for debugging
            if hasattr(self._credentials, 'service_account_email'):
                logging.debug(f"Loaded credentials for: {self._credentials.service_account_email}")
            else:
                logging.debug("Service account credentials loaded successfully")
            
            return self._credentials
            
        except Exception as e:
            self._connection_errors += 1
            error_msg = f"Failed to load Google credentials: {e}"
            logging.error(error_msg)
            track_api_call_simple("google_credentials_load", success=False, error_message=str(e))
            return None
    
    def _should_refresh_service(self, service_name: str) -> bool:
        """Check if a service should be refreshed"""
        current_time = time.time()
        last_refresh = self._last_service_refresh.get(service_name, 0)
        return current_time - last_refresh > self._service_cache_ttl
    
    def get_sheets_service(self, force_refresh: bool = False):
        """Get Google Sheets API service with caching"""
        if (not force_refresh and 
            self._sheets_service and 
            not self._should_refresh_service('sheets')):
            return self._sheets_service
        
        try:
            track_api_call_simple("sheets_service_create", success=False)
            
            credentials = self._load_credentials()
            if not credentials:
                return None
            
            self._sheets_service = build('sheets', 'v4', credentials=credentials)
            self._last_service_refresh['sheets'] = time.time()
            
            track_api_call_simple("sheets_service_create", success=True)
            logging.debug("Google Sheets service created/refreshed")
            
            return self._sheets_service
            
        except Exception as e:
            error_msg = f"Failed to create Sheets service: {e}"
            logging.error(error_msg)
            track_api_call_simple("sheets_service_create", success=False, error_message=str(e))
            return None
    
    def get_drive_service(self, force_refresh: bool = False):
        """Get Google Drive API service with caching"""
        if (not force_refresh and 
            self._drive_service and 
            not self._should_refresh_service('drive')):
            return self._drive_service
        
        try:
            track_api_call_simple("drive_service_create", success=False)
            
            credentials = self._load_credentials()
            if not credentials:
                return None
            
            self._drive_service = build('drive', 'v3', credentials=credentials)
            self._last_service_refresh['drive'] = time.time()
            
            track_api_call_simple("drive_service_create", success=True)
            logging.debug("Google Drive service created/refreshed")
            
            return self._drive_service
            
        except Exception as e:
            error_msg = f"Failed to create Drive service: {e}"
            logging.error(error_msg)
            track_api_call_simple("drive_service_create", success=False, error_message=str(e))
            return None
    
    def get_gspread_client(self, force_refresh: bool = False):
        """Get gspread client with caching"""
        if (not force_refresh and 
            self._gspread_client and 
            not self._should_refresh_service('gspread')):
            return self._gspread_client
        
        try:
            track_api_call_simple("gspread_client_create", success=False)
            
            credentials = self._load_credentials()
            if not credentials:
                return None
            
            self._gspread_client = gspread.authorize(credentials)
            self._last_service_refresh['gspread'] = time.time()
            
            track_api_call_simple("gspread_client_create", success=True)
            logging.debug("gspread client created/refreshed")
            
            return self._gspread_client
            
        except Exception as e:
            error_msg = f"Failed to create gspread client: {e}"
            logging.error(error_msg)
            track_api_call_simple("gspread_client_create", success=False, error_message=str(e))
            return None
    
    def test_connections(self) -> Dict[str, bool]:
        """Test all Google service connections"""
        results = {
            'sheets': False,
            'drive': False,
            'gspread': False,
            'credentials': False
        }
        
        # Test credentials
        credentials = self._load_credentials()
        results['credentials'] = credentials is not None
        
        if not credentials:
            return results
        
        # Test Sheets service
        try:
            sheets_service = self.get_sheets_service()
            if sheets_service:
                # Try a simple API call
                sheets_service.spreadsheets().get(
                    spreadsheetId='1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms'  # Google's sample sheet
                ).execute()
                results['sheets'] = True
        except Exception as e:
            logging.debug(f"Sheets connection test failed: {e}")
        
        # Test Drive service
        try:
            drive_service = self.get_drive_service()
            if drive_service:
                # Try a simple API call
                drive_service.about().get(fields="user").execute()
                results['drive'] = True
        except Exception as e:
            logging.debug(f"Drive connection test failed: {e}")
        
        # Test gspread client
        try:
            gspread_client = self.get_gspread_client()
            if gspread_client:
                # gspread doesn't have a simple test method, so we'll assume it's working
                # if we got this far without exceptions
                results['gspread'] = True
        except Exception as e:
            logging.debug(f"gspread connection test failed: {e}")
        
        return results
    
    def refresh_all_services(self):
        """Force refresh all cached services"""
        try:
            logging.info("Refreshing all Google services...")
            
            # Clear cached services
            self._credentials = None
            self._sheets_service = None
            self._drive_service = None
            self._gspread_client = None
            self._last_service_refresh.clear()
            
            # Reload credentials
            credentials = self._load_credentials(force_reload=True)
            if not credentials:
                logging.error("Failed to refresh credentials")
                return False
            
            # Recreate services
            sheets_service = self.get_sheets_service(force_refresh=True)
            drive_service = self.get_drive_service(force_refresh=True)
            gspread_client = self.get_gspread_client(force_refresh=True)
            
            success = all([sheets_service, drive_service, gspread_client])
            
            if success:
                logging.info("All Google services refreshed successfully")
                track_api_call_simple("google_services_refresh", success=True)
            else:
                logging.error("Some Google services failed to refresh")
                track_api_call_simple("google_services_refresh", success=False)
                
            return success
            
        except Exception as e:
            error_msg = f"Error refreshing Google services: {e}"
            logging.error(error_msg)
            track_api_call_simple("google_services_refresh", success=False, error_message=str(e))
            return False
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get status of all services"""
        current_time = time.time()
        
        status = {
            'credentials': {
                'loaded': self._credentials is not None,
                'last_check': self._last_credential_check,
                'age_seconds': current_time - self._last_credential_check if self._last_credential_check else None
            },
            'sheets_service': {
                'available': self._sheets_service is not None,
                'last_refresh': self._last_service_refresh.get('sheets', 0),
                'age_seconds': current_time - self._last_service_refresh.get('sheets', 0)
            },
            'drive_service': {
                'available': self._drive_service is not None,
                'last_refresh': self._last_service_refresh.get('drive', 0),
                'age_seconds': current_time - self._last_service_refresh.get('drive', 0)
            },
            'gspread_client': {
                'available': self._gspread_client is not None,
                'last_refresh': self._last_service_refresh.get('gspread', 0),
                'age_seconds': current_time - self._last_service_refresh.get('gspread', 0)
            },
            'connection_errors': self._connection_errors,
            'max_errors': self._max_connection_errors
        }
        
        return status
    
    def is_healthy(self) -> bool:
        """Check if the service manager is in a healthy state"""
        return (self._connection_errors < self._max_connection_errors and
                self._credentials is not None)
    
    def clear_cache(self):
        """Clear all cached services and credentials"""
        logging.info("Clearing Google services cache...")
        
        self._credentials = None
        self._sheets_service = None
        self._drive_service = None
        self._gspread_client = None
        self._last_credential_check = 0
        self._last_service_refresh.clear()
        self._connection_errors = 0
        
        logging.debug("Google services cache cleared")


# Global instance
_google_services_manager = None

def get_google_services() -> GoogleServicesManager:
    """Get the global Google services manager instance"""
    global _google_services_manager
    if _google_services_manager is None:
        _google_services_manager = GoogleServicesManager()
    return _google_services_manager


# Convenience functions for easy access
def get_sheets_service():
    """Quick access to Sheets service"""
    return get_google_services().get_sheets_service()

def get_drive_service():
    """Quick access to Drive service"""
    return get_google_services().get_drive_service()

def get_gspread_client():
    """Quick access to gspread client"""
    return get_google_services().get_gspread_client()

def refresh_google_services():
    """Refresh all Google services"""
    return get_google_services().refresh_all_services()

def test_google_connections():
    """Test all Google service connections"""
    return get_google_services().test_connections()