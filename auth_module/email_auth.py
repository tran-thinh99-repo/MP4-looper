import os
import logging
import hashlib
import time
import sys
import gspread

from .auth_storage import load_auth_data, save_auth_data, clear_auth_data, get_device_info, get_device_fingerprint
from google.oauth2 import service_account
from googleapiclient.discovery import build

from api_monitor_module import get_api_monitor, track_api_call_simple

# Import config from main app
from config import SERVICE_ACCOUNT_PATH, SCOPES, AUTH_SHEET_ID, AUTH_SHEET_NAME, MAX_AUTH_AGE

def _hash_password(password):
    """Create a simple hash of the password"""
    salt = "mp4_looper_salt"  # In production, use a better salt strategy
    return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()

def _validate_credentials_with_sheet(email, password_hash):
    """Validate credentials against Google Sheet"""
    # Debug environment
    logging.debug(f"Python executable: {sys.executable}")
    logging.debug(f"Working directory: {os.getcwd()}")
    logging.debug(f"Auth Sheet ID: {AUTH_SHEET_ID}")
    logging.debug(f"Env var AUTH_SHEET_ID: {os.getenv('AUTH_SHEET_ID')}")
    logging.debug(f"Credentials path: {SERVICE_ACCOUNT_PATH}")
    logging.debug(f"Credentials file exists: {os.path.exists(SERVICE_ACCOUNT_PATH)}")
    
    try:
        # Track the sheets API connection
        track_api_call_simple("sheets_connect", success=False)  # Will update to success if it works
        
        # Connect to Google Sheets
        logging.debug(f"Attempting to connect to auth sheet using service account")
        logging.debug(f"Using AUTH_SHEET_ID: {AUTH_SHEET_ID}")
        
        # Check if the credentials file exists
        if not os.path.exists(SERVICE_ACCOUNT_PATH):
            error_msg = f"Service account credentials file not found at: {SERVICE_ACCOUNT_PATH}"
            logging.error(error_msg)
            track_api_call_simple("sheets_connect", success=False, error_message="Credentials file not found")
            return False, error_msg
        
        # Try to load credentials
        try:
            credentials = service_account.Credentials.from_service_account_file(
                SERVICE_ACCOUNT_PATH, scopes=SCOPES)
            
            # Log service account email for debugging
            if hasattr(credentials, 'service_account_email'):
                logging.debug(f"Using service account: {credentials.service_account_email}")
            else:
                logging.debug("Service account email not available in credentials")
                
        except Exception as e:
            error_msg = f"Failed to load service account credentials: {e}"
            logging.error(error_msg)
            track_api_call_simple("sheets_connect", success=False, error_message="Failed to load credentials")
            return False, error_msg
        
        # Try to authorize with gspread
        try:
            client = gspread.authorize(credentials)
            track_api_call_simple("sheets_connect", success=True)  # Connection successful
        except Exception as e:
            error_msg = f"Failed to authorize with Google: {e}"
            logging.error(error_msg)
            track_api_call_simple("sheets_connect", success=False, error_message="Authorization failed")
            return False, error_msg
        
        # Try to open the spreadsheet
        try:
            logging.debug(f"Attempting to open spreadsheet with ID: {AUTH_SHEET_ID}")
            spreadsheet = client.open_by_key(AUTH_SHEET_ID)
            logging.debug(f"Successfully opened spreadsheet: {spreadsheet.title}")
            track_api_call_simple("sheets_open", success=True)
        except gspread.exceptions.SpreadsheetNotFound:
            error_msg = f"Spreadsheet not found. Check the spreadsheet ID: {AUTH_SHEET_ID}"
            logging.error(error_msg)
            track_api_call_simple("sheets_open", success=False, error_message="Spreadsheet not found")
            return False, error_msg
        except gspread.exceptions.APIError as e:
            if "403" in str(e):
                service_email = credentials.service_account_email if hasattr(credentials, 'service_account_email') else "Unknown"
                error_msg = f"Permission denied accessing spreadsheet. Make sure service account '{service_email}' has access to the spreadsheet."
                logging.error(error_msg)
                track_api_call_simple("sheets_open", success=False, error_message="Permission denied")
                return False, error_msg
            else:
                error_msg = f"API error accessing spreadsheet: {e}"
                logging.error(error_msg)
                track_api_call_simple("sheets_open", success=False, error_message="API error")
                return False, error_msg
        except Exception as e:
            error_msg = f"Failed to open auth spreadsheet: {e}"
            logging.error(error_msg)
            track_api_call_simple("sheets_open", success=False, error_message="Failed to open spreadsheet")
            return False, "Could not access authentication database"
            
        # Try to get the Auth worksheet
        try:
            sheet = spreadsheet.worksheet(AUTH_SHEET_NAME)
            logging.debug(f"Successfully opened auth worksheet")
            track_api_call_simple("sheets_worksheet", success=True)
        except gspread.exceptions.WorksheetNotFound:
            error_msg = f"Worksheet '{AUTH_SHEET_NAME}' not found in the spreadsheet. Please create this worksheet."
            logging.error(error_msg)
            track_api_call_simple("sheets_worksheet", success=False, error_message="Worksheet not found")
            return False, error_msg
        except Exception as e:
            error_msg = f"Failed to open auth worksheet: {e}"
            logging.error(error_msg)
            track_api_call_simple("sheets_worksheet", success=False, error_message="Failed to open worksheet")
            return False, error_msg
        
        # Try to get all records
        try:
            records = sheet.get_all_records()
            logging.debug(f"Retrieved {len(records)} user records from auth sheet")
            track_api_call_simple("sheets_read", success=True, records_count=len(records))
            
            # Debug: Print raw records to help diagnose problems
            logging.debug(f"Raw Records: {records}")
        except Exception as e:
            error_msg = f"Failed to read records from the worksheet: {e}"
            logging.error(error_msg)
            track_api_call_simple("sheets_read", success=False, error_message="Failed to read records")
            return False, error_msg
        
        # Check credentials - this part doesn't need API tracking since it's local processing
        for record in records:
            # Debug: Print current record being checked
            logging.debug(f"Checking record: {record}")
            
            # Check if 'Email' key exists and is not empty
            if 'Email' not in record:
                logging.warning(f"Record missing 'Email' field: {record}")
                continue
                
            # Debug: Compare emails
            logging.debug(f"Comparing email: '{record.get('Email', '')}' with '{email}'")
            
            if record.get('Email', '').lower() == email.lower():
                logging.debug(f"Email matched!")
                
                # Check if 'Password' key exists
                if 'Password' not in record:
                    logging.warning(f"Record missing 'Password' field: {record}")
                    track_api_call_simple("auth_validation", success=False, error_message="Invalid user record")
                    return False, "Invalid user record (missing password)"
                    
                stored_hash = record.get('Password', '')
                
                # Debug: Compare password hashes
                logging.debug(f"Stored hash: '{stored_hash}'")
                logging.debug(f"Generated hash: '{password_hash}'")
                logging.debug(f"Hashes match: {stored_hash == password_hash}")
                
                if stored_hash == password_hash:
                    access_level = record.get('AccessLevel', 'standard')
                    logging.debug(f"Authentication successful! Access level: {access_level}")
                    track_api_call_simple("auth_validation", success=True, access_level=access_level)
                    return True, access_level
                else:
                    logging.debug("Password mismatch")
                    track_api_call_simple("auth_validation", success=False, error_message="Invalid password")
                    return False, "Invalid password"
        
        # If we get here, email wasn't found
        logging.debug(f"Email '{email}' not found in authorized users")
        track_api_call_simple("auth_validation", success=False, error_message="Email not found")
        return False, "Email not found in authorized users"
    
    except Exception as e:
        error_msg = f"Authentication error: {e}"
        logging.error(error_msg)
        track_api_call_simple("auth_validation", success=False, error_message=str(e))
        return False, "Could not access authentication database"

def authenticate_user(email, password, remember=False):
    """Authenticate a user with email and password"""
    try:
        # Your existing authentication logic here
        success, message = _authenticate_user_impl(email, password, remember)
        
        # Simple tracking - just one line!
        track_api_call_simple("auth_login", success=success, 
                            error_message=message if not success else None)
        
        return success, message
        
    except Exception as e:
        track_api_call_simple("auth_login", success=False, error_message=str(e))
        raise

def _authenticate_user_impl(email, password, remember=False):
    """Original authentication implementation"""
    logging.debug(f"Authentication attempt - Email: '{email}'")
    
    if not email or not password:
        return False, "Email and password are required"
        
    # Hash the password to compare with stored hash
    password_hash = _hash_password(password)
    
    # Validate against Google Sheet
    success, message = _validate_credentials_with_sheet(email, password_hash)
    
    if success:
        # Get device info
        device_info = get_device_info()
        
        # Save authentication state if successful
        save_auth_data(email, remember, password_hash if remember else None)
        
        # Log device info to Google Sheets
        log_device_info_to_sheet(email, device_info, "manual")
        
        logging.info(f"User authenticated: {email}")
        return True, "Authentication successful"
    else:
        return False, message

def is_authenticated():
    """Check if user is currently authenticated"""
    auth_data = load_auth_data()
    
    if not auth_data:
        return False
        
    # Check if authenticated flag is set
    is_auth = auth_data.get('authenticated', False)
    
    # For security, we could also check age of auth data
    timestamp = auth_data.get('timestamp', 0)
    current_time = time.time()
    
    # If authentication is too old, require re-auth
    if current_time - timestamp > MAX_AUTH_AGE:
        clear_auth_data()
        return False
        
    return is_auth

def log_device_info_to_sheet(email, device_info, login_type="manual", include_debug_log=False):
    """Log device information to Google Sheets for monitoring, optionally include debug log"""
    try:
        from config import SERVICE_ACCOUNT_PATH, SCOPES, AUTH_SHEET_ID
        from google.oauth2 import service_account
        import gspread
        from datetime import datetime
        
        # Track the device logging operation
        track_api_call_simple("device_log_start", success=False)  # Will update if successful
        
        # Connect to Google Sheets
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_PATH, scopes=SCOPES)
        client = gspread.authorize(credentials)
        
        # Track successful connection
        track_api_call_simple("device_log_connect", success=True)
        
        # Open the spreadsheet and get/create the "Device_Log" worksheet
        spreadsheet = client.open_by_key(AUTH_SHEET_ID)
        
        try:
            sheet = spreadsheet.worksheet("Device_Log")
            # Check if the sheet has the debug log column, if not, add it
            existing_headers = sheet.row_values(1)
            if "Debug_Log" not in existing_headers:
                # Add the Debug_Log header if it doesn't exist
                sheet.update_cell(1, len(existing_headers) + 1, "Debug_Log")
                logging.debug("Added Debug_Log column to existing Device_Log sheet")
                track_api_call_simple("device_log_update_schema", success=True)
        except:
            # Create the worksheet if it doesn't exist
            sheet = spreadsheet.add_worksheet(title="Device_Log", rows="1000", cols="20")
            # Add headers including the new Debug_Log column
            headers = ["Timestamp", "Email", "Login_Type", "Computer_Name", "System", 
                      "Processor", "Machine", "Python_Version", "Device_Fingerprint", "Debug_Log"]
            sheet.insert_row(headers, 1)
            logging.debug("Created new Device_Log sheet with Debug_Log column")
            track_api_call_simple("device_log_create_sheet", success=True)
        
        # Get debug log content if requested
        debug_log_content = ""
        if include_debug_log:
            debug_log_content = get_debug_log_content()
            track_api_call_simple("debug_log_read", success=True, log_size=len(debug_log_content))
        
        # Prepare row data
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        fingerprint = get_device_fingerprint()[:16] + "..."  # Truncated for readability
        
        row_data = [
            timestamp,
            email,
            login_type,
            device_info.get("computer_name", "Unknown"),
            device_info.get("system", "Unknown"),
            device_info.get("processor", "Unknown"),
            device_info.get("machine", "Unknown"),
            device_info.get("python_version", "Unknown"),
            fingerprint,
            debug_log_content  # Add debug log content
        ]
        
        # Check if this device already has an entry (to update instead of creating new)
        if include_debug_log:
            # For debug log uploads, update existing row if device exists
            current_fingerprint = get_device_fingerprint()[:16] + "..."
            all_values = sheet.get_all_values()
            
            # Track the read operation
            track_api_call_simple("device_log_search", success=True, rows_checked=len(all_values))
            
            # Look for existing row with same email and device fingerprint
            updated = False
            for i, row in enumerate(all_values[1:], 2):  # Skip header row
                if len(row) >= 9 and row[1] == email and row[8] == current_fingerprint:
                    # Update existing row with new debug log
                    sheet.update(f"A{i}:J{i}", [row_data])
                    logging.debug(f"Updated existing Device_Log entry for {email}")
                    track_api_call_simple("device_log_update", success=True)
                    updated = True
                    break
            
            if not updated:
                # Add new row if no existing entry found
                sheet.insert_row(row_data, 2)  # Insert after header
                logging.debug(f"Added new Device_Log entry for {email}")
                track_api_call_simple("device_log_insert", success=True)
        else:
            # For regular login logs, always add new row
            sheet.insert_row(row_data, 2)  # Insert after header
            logging.debug(f"Device info logged to Google Sheets for {email}")
            track_api_call_simple("device_log_insert", success=True)
        
        # Mark overall operation as successful
        track_api_call_simple("device_log_start", success=True, login_type=login_type)
        
    except Exception as e:
        logging.error(f"Failed to log device info to sheet: {e}")
        track_api_call_simple("device_log_start", success=False, error_message=str(e))

def get_debug_log_content(max_lines=100):
    """Get the content of the debug log file, limited to most recent lines"""
    try:
        # Use the same directory logic as setup_logging() in utils.py
        if getattr(sys, 'frozen', False):
            # Running as a bundled executable - debug.log is next to the .exe
            log_dir = os.path.dirname(sys.executable)
        else:
            # Running as a script - debug.log is next to the main script
            # We need to go up from auth_module to the main script directory
            current_file_dir = os.path.dirname(os.path.abspath(__file__))  # auth_module directory
            log_dir = os.path.dirname(current_file_dir)  # Go up one level to main script directory
        
        log_path = os.path.join(log_dir, "debug.log")
        
        logging.debug(f"Looking for debug log at: {log_path}")
        
        if not os.path.exists(log_path):
            logging.warning(f"Debug log file not found at: {log_path}")
            return "Debug log file not found"
        
        # Read the log file and get the last N lines
        with open(log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Get the last max_lines lines
        recent_lines = lines[-max_lines:] if len(lines) > max_lines else lines
        
        # Join lines and truncate if too long for Google Sheets (max 50,000 characters)
        content = ''.join(recent_lines)
        if len(content) > 45000:  # Leave some buffer
            content = content[-45000:]
            content = "...[truncated]...\n" + content
        
        logging.debug(f"Successfully read debug log: {len(content)} characters")
        return content
        
    except Exception as e:
        logging.error(f"Error reading debug log: {e}")
        return f"Error reading debug log: {str(e)}"
    
def send_debug_info_to_support(email=None):
    """Send debug info with simple tracking"""
    try:
        # Your existing debug sending logic
        result = _send_debug_info_impl(email)
        
        # Simple tracking
        track_api_call_simple("debug_upload", success=True)
        
        return result
        
    except Exception as e:
        track_api_call_simple("debug_upload", success=False, error_message=str(e))
        raise
    
def send_debug_info_to_support_enhanced():
    """Enhanced debug info sending with better error handling"""
    try:
        # Get current user
        auth_data = load_auth_data()
        email = auth_data.get('email', 'unknown@user.com') if auth_data else 'unknown@user.com'
        
        # Get device info
        device_info = get_device_info()
        
        # Send debug info with enhanced tracking
        success = send_debug_info_to_support(email)
        
        if success:
            logging.info(f"Enhanced debug information sent successfully for {email}")
            return True
        else:
            logging.error(f"Failed to send enhanced debug information for {email}")
            return False
            
    except Exception as e:
        error_msg = f"Error in enhanced debug info sending: {str(e)}"
        logging.error(error_msg)
        return False

def _send_debug_info_impl(email=None):
    """Original debug info implementation"""
    try:
        if not email:
            # Get email from current auth data
            auth_data = load_auth_data()
            email = auth_data.get('email', 'unknown@user.com') if auth_data else 'unknown@user.com'
        
        device_info = get_device_info()
        log_device_info_to_sheet(email, device_info, "debug_upload", include_debug_log=True)
        
        logging.info(f"Debug information sent successfully for {email}")
        return True, "Debug information sent successfully"
        
    except Exception as e:
        error_msg = f"Error sending debug info: {str(e)}"
        logging.error(error_msg)
        return False, error_msg
    
def check_remembered_user():
    """Check if there's a remembered user and validate their credentials"""
    monitor = get_api_monitor()
    
    if monitor:
        @monitor.track("auth_remembered", max_calls=20, window_minutes=60)
        def _check_impl():
            return _check_remembered_user_impl()
        
        return _check_impl()
    else:
        return _check_remembered_user_impl()

def _check_remembered_user_impl():
    """Original remembered user check implementation"""
    # Your existing check_remembered_user code here
    auth_data = load_auth_data()
    
    if not auth_data or not auth_data.get('remember', False):
        return False, None
        
    email = auth_data.get('email')
    stored_hash = auth_data.get('password_hash')
    
    if not email or not stored_hash:
        return False, None
        
    # Check if auth data is too old
    timestamp = auth_data.get('timestamp', 0)
    current_time = time.time()
    
    if current_time - timestamp > MAX_AUTH_AGE:
        clear_auth_data()
        logging.warning("Remembered user authentication expired")
        return False, None
        
    # Validate the stored hash against the Google Sheet
    success, message = _validate_credentials_with_sheet(email, stored_hash)
    
    if success:
        # Log device info for remembered login
        device_info = auth_data.get('device_info', {})
        log_device_info_to_sheet(email, device_info, "remembered")
        
        logging.info(f"Auto-authenticated remembered user: {email}")
        return True, email
    else:
        # If validation fails, clear the stored auth data
        clear_auth_data()
        logging.warning(f"Remembered user validation failed: {message}")
        return False, None

def logout():
    """Log the user out by clearing auth data"""
    return clear_auth_data()

def get_current_user():
    """Get the currently authenticated user's email"""
    auth_data = load_auth_data()
    if auth_data and auth_data.get('authenticated', False):
        return auth_data.get('email', None)
    return None

def handle_authentication():
    """Handle complete authentication flow - check remembered user or show dialog"""
    try:
        # First try to authenticate with remembered user
        remembered, email = check_remembered_user()
        
        if remembered:
            logging.info(f"Auto-authenticated remembered user: {email}")
            return True
        
        # No remembered user or validation failed, show auth dialog
        from auth_module import show_auth_dialog
        
        if show_auth_dialog():
            logging.info("User authenticated via dialog")
            return True
        else:
            logging.warning("Authentication failed or cancelled")
            return False
            
    except Exception as e:
        logging.error(f"Authentication error: {e}")
        return False