import os
import json
import logging
import base64
import sys
import time
import platform
import uuid
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from paths import get_app_directory

def get_device_fingerprint():
    """Generate a unique fingerprint for this device"""
    try:
        # Combine multiple device identifiers
        machine_id = platform.node()  # Computer name
        processor = platform.processor()
        system = platform.system()
        release = platform.release()
        
        # Get MAC address
        mac_address = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) 
                               for elements in range(0,2*6,2)][::-1])
        
        # Create a hash of combined identifiers
        fingerprint_data = f"{machine_id}_{processor}_{system}_{release}_{mac_address}"
        fingerprint = hashlib.sha256(fingerprint_data.encode()).hexdigest()
        
        logging.debug(f"Device fingerprint generated: {fingerprint[:16]}...")
        return fingerprint
    except Exception as e:
        logging.error(f"Error generating device fingerprint: {e}")
        return "unknown_device"

def get_device_info():
    """Get human-readable device information"""
    try:
        return {
            "computer_name": platform.node(),
            "system": f"{platform.system()} {platform.release()}",
            "processor": platform.processor(),
            "machine": platform.machine(),
            "python_version": platform.python_version()
        }
    except Exception as e:
        logging.error(f"Error getting device info: {e}")
        return {"error": str(e)}
    
# Constants
AUTH_FILE = os.path.join(get_app_directory(), "auth_data.enc")
SALT = b'mp4_looper_salt_value'

def _get_encryption_key(app_id='mp4_looper_app'):
    """Generate encryption key from app ID"""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=SALT,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(app_id.encode()))
    return key

def save_auth_data(email, remember=False, password_hash=None):
    """Save authentication data to encrypted file with device binding"""
    try:
        # Build data to save
        data = {
            "authenticated": True,
            "email": email,
            "remember": remember,
            "device_fingerprint": get_device_fingerprint(),
            "device_info": get_device_info(),
            "timestamp": time.time()
        }
        
        # FIXED: Only save password hash if remember=True AND password_hash is provided
        if remember and password_hash:
            data["password_hash"] = password_hash
            logging.debug(f"Saving auth data with password hash (remember=True)")
        else:
            logging.debug(f"Saving session-only auth data (remember={remember})")
            # Don't include password_hash for session-only auth
        
        # Encrypt the data
        key = _get_encryption_key()
        fernet = Fernet(key)
        encrypted_data = fernet.encrypt(json.dumps(data).encode())
        
        # Save to file
        with open(AUTH_FILE, "wb") as f:
            f.write(encrypted_data)
        
        logging.debug(f"Authentication data saved to: {AUTH_FILE}")
        return True
    except Exception as e:
        logging.error(f"Failed to save authentication data: {e}")
        return False

def load_auth_data():
    """Load authentication data from encrypted file and validate device"""
    if not os.path.exists(AUTH_FILE):
        return None
        
    try:
        # Read encrypted data
        with open(AUTH_FILE, "rb") as f:
            encrypted_data = f.read()
        
        # Decrypt the data
        key = _get_encryption_key()
        fernet = Fernet(key)
        decrypted_data = fernet.decrypt(encrypted_data)
        
        # Parse JSON data
        data = json.loads(decrypted_data)
        
        # Validate device fingerprint
        stored_fingerprint = data.get('device_fingerprint')
        current_fingerprint = get_device_fingerprint()
        
        if stored_fingerprint != current_fingerprint:
            logging.warning("Device fingerprint mismatch - auth file from different device")
            return None
            
        logging.debug(f"Authentication data loaded and device validated from: {AUTH_FILE}")
        return data
    except Exception as e:
        logging.error(f"Failed to load authentication data: {e}")
        return None

def clear_auth_data():
    """Clear saved authentication data"""
    if os.path.exists(AUTH_FILE):
        try:
            os.remove(AUTH_FILE)
            logging.debug(f"Authentication data cleared from: {AUTH_FILE}")
            return True
        except Exception as e:
            logging.error(f"Failed to clear authentication data: {e}")
            return False
    return True