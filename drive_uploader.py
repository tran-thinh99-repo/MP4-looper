#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Google Drive Uploader Module - Direct integration for the MP4 batch processor
"""

import os
import re
import sys
import time
import logging
import threading
import gspread
from queue import Queue

from config import GOOGLE_DRIVE_ROOT_FOLDER_ID, GOOGLE_SPREADSHEET_ID, GOOGLE_SPREADSHEET_NAME, SCOPES
from api_monitor_module import get_api_monitor

# Google API imports
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from gspread.utils import a1_to_rowcol

from google_services import get_drive_service, get_sheets_service, get_gspread_client

# Mapping for file suffixes to Google Sheet columns
COLUMN_MAP = {
    "_1h.mp4": "H",
    "_3h.mp4": "I",
    "_11h.mp4": "J",
    "_3m.mp4": "AG"  # Column for 3-minute test videos
}

# First data row in the sheet (rows before this are headers)
FIRST_DATA_ROW = 5  # Start at row 5 (skipping rows 1-4)
class DriveUploader:
    """Handles Google Drive uploads directly in the application"""
    
    def __init__(self, service_account_path=None, root_folder_id=None, 
                 spreadsheet_id=None, sheet_name=None):
        # Configuration
        self.service_account_path = service_account_path or "credentials.json"
        self.root_folder_id = root_folder_id or GOOGLE_DRIVE_ROOT_FOLDER_ID
        self.spreadsheet_id = spreadsheet_id or GOOGLE_SPREADSHEET_ID
        self.sheet_name = sheet_name or GOOGLE_SPREADSHEET_NAME
        
        # State variables
        self.is_uploading = False
        self.should_stop = False
        self.queue = Queue()
        self.failed_uploads = []
        self.current_file = None
        self.upload_thread = None
        self.folder_cache = {}
        
        # Progress reporting
        self.progress_callback = None
        self.status_callback = None
        self.uploaded_files = []
        
        # API services - will be obtained from centralized manager
        self.drive_service = None
        self.sheets_service = None
        self.gspread_client = None

        # Get API monitor for tracking
        self.api_monitor = get_api_monitor()
    
    def set_callbacks(self, progress_callback=None, status_callback=None):
        """Set callback functions for progress reporting"""
        self.progress_callback = progress_callback
        self.status_callback = status_callback
    
    def connect(self):
        """Initialize Google API connections using centralized manager"""
        try:
            self._log("Connecting to Google services using centralized manager...")
            
            # Get services from centralized manager
            self.drive_service = get_drive_service()
            self.sheets_service = get_sheets_service()
            self.gspread_client = get_gspread_client()
            
            # Check if all services are available
            if not all([self.drive_service, self.sheets_service, self.gspread_client]):
                self._log("Failed to get one or more Google services")
                return False
            
            # Test drive access
            try:
                about = self.drive_service.about().get(fields="user").execute()
                email = about.get("user", {}).get("emailAddress", "unknown")
                self._log(f"Connected to Google Drive as {email}")
            except Exception as e:
                self._log(f"Failed to test Drive access: {e}")
                return False
            
            # Test sheet access
            try:
                sheet = self.gspread_client.open_by_key(self.spreadsheet_id).worksheet(self.sheet_name)
                test_value = sheet.acell("A1").value
                self._log(f"Connected to sheet: {self.sheet_name}")
            except Exception as e:
                self._log(f"Warning: Failed to access sheet: {e}")
                # Don't fail connection for sheet access issues
            
            return True
            
        except Exception as e:
            self._log(f"Error connecting to Google services: {e}")
            return False
    
    def upload_folder(self, folder_path, only_file=None):
        """Add files from a folder to the upload queue"""
        if not os.path.isdir(folder_path):
            self._log(f"Error: {folder_path} is not a valid directory")
            return False
        
        # Make sure we're connected first
        if not self.drive_service:
            if not self.connect():
                self._log("Failed to connect to Google Drive")
                return False
        
        try:
            # Group files by base name
            files_by_base = self._group_files_by_base(folder_path, only_file)
            
            # Add each group to the queue
            for base_name, files in files_by_base.items():
                self.queue.put((base_name, files))
            
            total_files = sum(len(files) for files in files_by_base.values())
            self._log(f"Added {total_files} files to upload queue ({len(files_by_base)} groups)")
            
            return True
        except Exception as e:
            self._log(f"Error adding files to queue: {e}")
            return False
    
    def start_upload(self):
        """Start the upload process in a background thread"""
        if self.is_uploading:
            self._log("Upload already in progress")
            return False
        
        if self.queue.empty():
            self._log("No files in upload queue")
            return False
        
        # Reset state
        self.is_uploading = True
        self.should_stop = False
        self.failed_uploads = []
        
        # Start the upload thread
        self.upload_thread = threading.Thread(target=self._upload_worker, daemon=True)
        self.upload_thread.start()
        
        self._log("Upload process started")
        return True
    
    def stop_upload(self):
        """Signal the upload thread to stop"""
        if not self.is_uploading:
            return
        
        self.should_stop = True
        self._log("Stopping upload process (will complete current file)...")
    
    def retry_failed(self, output_folder):
        """Retry previously failed uploads"""
        # Check for failed uploads log
        log_path = os.path.join(output_folder, "upload_failures.txt")
        if not os.path.exists(log_path):
            self._log("No failed uploads log found")
            return False
        
        try:
            # Read failed uploads
            with open(log_path, "r", encoding="utf-8") as f:
                failed_files = {}
                for line in f:
                    if "|" in line:
                        filename = line.split("|")[0].strip()
                        file_path = os.path.join(output_folder, filename)
                        
                        if os.path.exists(file_path):
                            # Group by base name with leading zeros preserved
                            match = re.match(r"(\d+)", filename)
                            if match:
                                base_name = match.group(1)
                                if base_name not in failed_files:
                                    failed_files[base_name] = []
                                failed_files[base_name].append(file_path)
            
            if not failed_files:
                self._log("No valid failed uploads found to retry")
                return False
            
            # Add to queue
            for base_name, files in failed_files.items():
                self.queue.put((base_name, files))
            
            total_files = sum(len(files) for files in failed_files.values())
            self._log(f"Added {total_files} previously failed uploads to queue")
            
            # Start uploading if not already
            if not self.is_uploading:
                self.start_upload()
                
            return True
        except Exception as e:
            self._log(f"Error retrying failed uploads: {e}")
            return False
    
    def _upload_worker(self):
        """Background worker thread that processes the upload queue"""
        try:
            total_groups = self.queue.qsize()
            completed_groups = 0
            
            while not self.queue.empty() and not self.should_stop:
                base_name, files = self.queue.get()
                
                completed_groups += 1
                self._log(f"Processing group {completed_groups}/{total_groups}: {base_name}")
                
                # Use full folder name with leading zeros (e.g., "0430" not "430")
                folder_name = base_name
                
                # Create or get folder for this base name
                folder_id = self._get_or_create_folder(folder_name)
                if not folder_id:
                    self._log(f"Failed to create/find folder for {folder_name}")
                    continue
                
                # Process all files in this group
                self._process_file_group(base_name, files, folder_id)
                
                # Mark the queue task as done
                self.queue.task_done()
            
            # Log any failed uploads
            if self.failed_uploads:
                self._log_failed_uploads(os.path.dirname(self.failed_uploads[0][0]))
                self._log(f"Completed with {len(self.failed_uploads)} failed uploads")
            else:
                self._log("All uploads completed successfully")
                
        except Exception as e:
            self._log(f"Upload worker error: {e}")
        finally:
            self.is_uploading = False
            self.current_file = None
            
            # Call completion callback if provided
            if hasattr(self, 'completion_callback') and self.completion_callback:
                try:
                    # Use tkinter's after method to safely call from a background thread
                    import tkinter as tk
                    if tk._default_root:  # Check if tkinter is still running
                        tk._default_root.after(0, self.completion_callback)
                except Exception as e:
                    self._log(f"Error in completion callback: {e}")
    
    def _process_file_group(self, base_name, files, folder_id):
        """Process all files in a group"""
        # Extract song list content for later use
        song_list_content = {}
        for file_path in files:
            if file_path.endswith("_song_list_timestamp.txt"):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read().strip()
                        song_base = os.path.basename(file_path).replace("_song_list_timestamp.txt", "")
                        song_list_content[song_base] = content
                except Exception as e:
                    self._log(f"Failed to read song list file {os.path.basename(file_path)}: {e}")
        
        # Upload each file
        for file_path in files:
            filename = os.path.basename(file_path)
            self.current_file = filename
            
            try:
                if self.should_stop:
                    self._log("Upload stopped by user")
                    return
                
                self._log(f"Uploading: {filename}")
                
                # Upload the file
                file_id = self._upload_file(file_path, folder_id)
                
                if not file_id:
                    self._log(f"Failed to upload {filename}")
                    continue
                
                # For MP4 files, make public and update sheet
                if filename.lower().endswith(".mp4"):
                    # Make file publicly accessible
                    self._make_file_public(file_id)
                    
                    # Get web link
                    web_link = self._get_web_link(file_id)
                    if web_link:
                        # Update Google Sheet
                        self._update_sheet_with_link(filename, web_link, song_list_content)
                
                # Add to uploaded files list
                self.uploaded_files.append(filename)
                
            except Exception as e:
                self._log(f"Error processing {filename}: {e}")
                self.failed_uploads.append((file_path, str(e)))
    
    def _upload_file(self, file_path, folder_id, max_retries=3):
        """Upload a file to Google Drive with retries and monitoring metrics"""
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        start_time = time.time()  # Track upload duration
        
        for attempt in range(1, max_retries + 1):
            try:
                self._log(f"Upload attempt {attempt}/{max_retries} for {file_name} ({self._format_size(file_size)})")
                
                # Create file metadata
                file_metadata = {
                    "name": file_name,
                    "parents": [folder_id]
                }
                
                # Create media upload object with appropriate chunk size
                # Larger files use larger chunks for better performance
                chunk_size = 5 * 1024 * 1024  # 5MB default
                if file_size > 100 * 1024 * 1024:  # > 100MB
                    chunk_size = 20 * 1024 * 1024  # 20MB for large files
                
                media = MediaFileUpload(file_path, resumable=True, chunksize=chunk_size)
                
                # Create the request
                request = self.drive_service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields="id",
                    supportsAllDrives=True
                )
                
                # Execute the request with progress reporting
                response = None
                last_progress = 0
                
                while response is None:
                    status, response = request.next_chunk()
                    if status:
                        progress = status.progress()
                        # Only report progress if it's changed significantly
                        if progress - last_progress > 0.05:
                            self._report_progress(file_name, progress)
                            last_progress = progress
                
                # Get the file ID
                file_id = response.get("id")
                if file_id:
                    upload_duration = time.time() - start_time
                    self._log(f"Successfully uploaded: {file_name}")
                    self._report_progress(file_name, 1.0)  # Mark as complete
                    
                    # Record custom metrics if monitoring is available
                    if self.api_monitor:
                        self.api_monitor.record_custom_metric("upload_duration", upload_duration, "seconds")
                        self.api_monitor.record_custom_metric("upload_file_size", file_size, "bytes")
                        self.api_monitor.record_custom_metric("upload_chunk_size", chunk_size, "bytes")
                        self.api_monitor.record_custom_metric("upload_attempts", attempt, "count")
                        
                        # Calculate upload speed (MB/s)
                        if upload_duration > 0:
                            upload_speed = (file_size / (1024 * 1024)) / upload_duration  # MB/s
                            self.api_monitor.record_custom_metric("upload_speed", upload_speed, "MB/s")
                    
                    return file_id
                else:
                    raise Exception("File ID not returned after upload")
                    
            except HttpError as e:
                if e.resp.status in [403, 429, 500, 502, 503, 504] and attempt < max_retries:
                    # Exponential backoff for retryable errors
                    wait_time = min(2 ** attempt * 10, 120)  # Max 2 minutes
                    self._log(f"Upload attempt {attempt} failed with status {e.resp.status}, retrying in {wait_time}s: {file_name}")
                    
                    # Record retry metrics
                    if self.api_monitor:
                        self.api_monitor.record_custom_metric("upload_retries", 1, "count")
                        self.api_monitor.record_custom_metric("upload_error_status", e.resp.status, "http_status")
                    
                    time.sleep(wait_time)
                else:
                    error_msg = f"Upload failed after {attempt} attempts with HTTP {e.resp.status}: {file_name}"
                    self._log(error_msg)
                    self.failed_uploads.append((file_path, str(e)))
                    
                    # Record failure metrics
                    if self.api_monitor:
                        self.api_monitor.record_custom_metric("upload_failures", 1, "count")
                        self.api_monitor.record_custom_metric("failed_upload_size", file_size, "bytes")
                        self.api_monitor.record_custom_metric("final_error_status", e.resp.status, "http_status")
                    
                    return None
                    
            except Exception as e:
                error_msg = f"Upload error for {file_name}: {e}"
                self._log(error_msg)
                
                if attempt < max_retries:
                    wait_time = min(2 ** attempt * 5, 60)  # Max 1 minute
                    self._log(f"Upload error, retrying in {wait_time}s: {file_name}")
                    
                    # Record retry metrics
                    if self.api_monitor:
                        self.api_monitor.record_custom_metric("upload_retries", 1, "count")
                        self.api_monitor.record_custom_metric("upload_errors", 1, "count")
                    
                    time.sleep(wait_time)
                else:
                    self._log(f"Upload failed after {attempt} attempts: {file_name}")
                    self.failed_uploads.append((file_path, str(e)))
                    
                    # Record final failure metrics
                    if self.api_monitor:
                        upload_duration = time.time() - start_time
                        self.api_monitor.record_custom_metric("upload_failures", 1, "count")
                        self.api_monitor.record_custom_metric("failed_upload_duration", upload_duration, "seconds")
                        self.api_monitor.record_custom_metric("failed_upload_size", file_size, "bytes")
                    
                    return None
        
        # This should never be reached, but just in case
        return None

    def _make_file_public(self, file_id):
        """Make a file publicly accessible with monitoring"""
        if self.api_monitor:
            @self.api_monitor.track("drive_make_public", max_calls=100, window_minutes=60)
            def _public_impl():
                return self._make_file_public_impl(file_id)
            
            return _public_impl()
        else:
            return self._make_file_public_impl(file_id)
    
    def _make_file_public_impl(self, file_id):
        """Implementation using centralized Drive service"""
        try:
            # Ensure we have a Drive service
            if not self.drive_service:
                self.drive_service = get_drive_service()
                if not self.drive_service:
                    self._log("Failed to get Drive service for making file public")
                    return False
            
            self.drive_service.permissions().create(
                fileId=file_id,
                body={"type": "anyone", "role": "reader"},
                supportsAllDrives=True
            ).execute()
            return True
        except Exception as e:
            logging.error(f"Failed to make file {file_id} public: {e}")
            return False
    
    def _get_web_link(self, file_id):
        """Get the web view link for a file using centralized service"""
        try:
            # Ensure we have a Drive service
            if not self.drive_service:
                self.drive_service = get_drive_service()
                if not self.drive_service:
                    self._log("Failed to get Drive service for web link")
                    return None
            
            file_meta = self.drive_service.files().get(
                fileId=file_id, 
                fields="webViewLink", 
                supportsAllDrives=True
            ).execute()
            return file_meta.get("webViewLink")
        except Exception as e:
            self._log(f"Failed to get web link for file {file_id}: {e}")
            return None
    
    def _update_sheet_with_link(self, filename, web_link, song_list_content):
        """Update Google Sheet with file link and song list note using centralized services"""
        try:
            # Check if filename matches expected pattern (preserve leading zeros in the ID)
            match = re.match(r"(\d+)(_1h\.mp4|_3h\.mp4|_11h\.mp4|_3m\.mp4)$", filename)
            if not match:
                self._log(f"Filename {filename} does not match expected pattern for sheet updates")
                return False
            
            # Get the ID part (with leading zeros preserved)
            target_id_with_zeros = match.group(1)
            # Also get the numeric version for comparison with sheet values
            target_id_numeric = str(int(target_id_with_zeros))
            
            # Get the suffix part
            suffix = match.group(2)
            
            # Get the column letter for this suffix
            col = COLUMN_MAP.get(suffix)
            if not col:
                self._log(f"No column mapping found for suffix: {suffix}")
                return False
            
            # Ensure we have gspread client and sheets service
            if not self.gspread_client:
                self.gspread_client = get_gspread_client()
                if not self.gspread_client:
                    self._log("Failed to get gspread client")
                    return False
            
            if not self.sheets_service:
                self.sheets_service = get_sheets_service()
                if not self.sheets_service:
                    self._log("Failed to get Sheets service")
                    return False
            
            # Open the spreadsheet and worksheet
            sheet = self.gspread_client.open_by_key(self.spreadsheet_id).worksheet(self.sheet_name)
            
            # Get all IDs from column A, starting from the first data row
            all_ids = sheet.col_values(1)[FIRST_DATA_ROW-1:]  # Adjust for 0-based indexing
            
            # Find the row with matching ID, excluding header rows
            row = None
            for idx, id_value in enumerate(all_ids, FIRST_DATA_ROW):  # Start from FIRST_DATA_ROW
                if id_value == target_id_numeric:
                    row = idx
                    break
            
            if not row:
                self._log(f"ID {target_id_with_zeros} not found in column A after row {FIRST_DATA_ROW}")
                return False
            
            self._log(f"Found ID {target_id_numeric} in column A at row {row}")
            
            # Construct the cell reference and formula
            cell = f"{col}{row}"
            formula = f'=HYPERLINK("{web_link}", "{filename}")'
            
            # Update the cell with the hyperlink formula
            sheet.update_acell(cell, formula)
            
            # Add note if song list content is available
            base_name = filename.replace(".mp4", "")
            note_text = (
                song_list_content.get(base_name) or
                song_list_content.get(base_name.replace("_1h", "")) or
                song_list_content.get(base_name.replace("_3h", "")) or
                song_list_content.get(base_name.replace("_11h", "")) or
                song_list_content.get(base_name.replace("_3m", ""))
            )
            
            if note_text:
                # Convert A1 notation to row/column indices
                from gspread.utils import a1_to_rowcol
                row_idx, col_idx = a1_to_rowcol(cell)
                
                # Get the sheet ID
                sheet_meta = self.sheets_service.spreadsheets().get(
                    spreadsheetId=self.spreadsheet_id
                ).execute()
                sheet_id = next(
                    s["properties"]["sheetId"] for s in sheet_meta["sheets"] 
                    if s["properties"]["title"] == self.sheet_name
                )
                
                # Create a batch update request to add the note
                note_request = {
                    "requests": [{
                        "repeatCell": {
                            "range": {
                                "sheetId": sheet_id,
                                "startRowIndex": row_idx - 1,
                                "endRowIndex": row_idx,
                                "startColumnIndex": col_idx - 1,
                                "endColumnIndex": col_idx
                            },
                            "cell": {
                                "note": note_text
                            },
                            "fields": "note"
                        }
                    }]
                }
                
                # Execute the batch update request
                self.sheets_service.spreadsheets().batchUpdate(
                    spreadsheetId=self.spreadsheet_id,
                    body=note_request
                ).execute()
                
            self._log(f"Updated sheet for {filename} in cell {cell}")
            return True
            
        except Exception as e:
            self._log(f"Failed to update sheet with link for {filename}: {e}")
    
    def _get_or_create_folder(self, folder_name):
        """Get or create a Google Drive folder with monitoring and centralized service"""
        if self.api_monitor:
            @self.api_monitor.track("drive_folder_create", max_calls=100, window_minutes=60)
            def _folder_impl():
                return self._get_or_create_folder_impl(folder_name)
            
            return _folder_impl()
        else:
            return self._get_or_create_folder_impl(folder_name)
    
    def _get_or_create_folder_impl(self, folder_name):
        """Implementation using centralized Drive service"""
        start_time = time.time()
        
        # Check cache first
        if folder_name in self.folder_cache:
            cache_hit_duration = time.time() - start_time
            self._log(f"Found existing folder '{folder_name}' in cache → {self.folder_cache[folder_name]}")
            
            # Record cache hit metrics
            if self.api_monitor:
                self.api_monitor.record_custom_metric("folder_cache_hits", 1, "count")
                self.api_monitor.record_custom_metric("folder_cache_lookup_time", cache_hit_duration, "seconds")
            
            return self.folder_cache[folder_name]
        
        try:
            # Ensure we have a Drive service
            if not self.drive_service:
                self.drive_service = get_drive_service()
                if not self.drive_service:
                    self._log("Failed to get Drive service")
                    return None
            
            # Search for folder with the given name in the parent folder
            query = (
                f"'{self.root_folder_id}' in parents and "
                f"mimeType = 'application/vnd.google-apps.folder' and "
                f"name = '{folder_name}' and "
                f"trashed = false"
            )
            
            search_start = time.time()
            results = self.drive_service.files().list(
                q=query,
                spaces="drive",
                fields="files(id, name)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True
            ).execute()
            search_duration = time.time() - search_start
            
            folders = results.get("files", [])
            
            if folders:
                # Folder found, cache and return ID
                folder_id = folders[0]["id"]
                self.folder_cache[folder_name] = folder_id
                total_duration = time.time() - start_time
                
                self._log(f"Found existing folder '{folder_name}' → {folder_id}")
                
                # Record folder found metrics
                if self.api_monitor:
                    self.api_monitor.record_custom_metric("folder_search_time", search_duration, "seconds")
                    self.api_monitor.record_custom_metric("folder_found", 1, "count")
                    self.api_monitor.record_custom_metric("folder_lookup_total_time", total_duration, "seconds")
                    self.api_monitor.record_custom_metric("folders_in_cache", len(self.folder_cache), "count")
                
                return folder_id
            
            # Folder not found, create new one
            self._log(f"Creating new folder '{folder_name}'...")
            
            file_metadata = {
                "name": folder_name,
                "mimeType": "application/vnd.google-apps.folder",
                "parents": [self.root_folder_id]
            }
            
            create_start = time.time()
            folder = self.drive_service.files().create(
                body=file_metadata,
                fields="id",
                supportsAllDrives=True
            ).execute()
            create_duration = time.time() - create_start
            
            folder_id = folder["id"]
            self.folder_cache[folder_name] = folder_id
            total_duration = time.time() - start_time
            
            self._log(f"Created new folder '{folder_name}' → {folder_id}")
            
            # Record folder creation metrics
            if self.api_monitor:
                self.api_monitor.record_custom_metric("folder_search_time", search_duration, "seconds")
                self.api_monitor.record_custom_metric("folder_create_time", create_duration, "seconds")
                self.api_monitor.record_custom_metric("folder_created", 1, "count")
                self.api_monitor.record_custom_metric("folder_total_time", total_duration, "seconds")
                self.api_monitor.record_custom_metric("folders_in_cache", len(self.folder_cache), "count")
            
            return folder_id
            
        except Exception as e:
            error_duration = time.time() - start_time
            error_msg = f"Failed to get or create folder '{folder_name}': {e}"
            self._log(error_msg)
            
            # Record folder error metrics
            if self.api_monitor:
                self.api_monitor.record_custom_metric("folder_errors", 1, "count")
                self.api_monitor.record_custom_metric("folder_error_time", error_duration, "seconds")
            
            return None
    
    def _group_files_by_base(self, folder_path, only_file=None):
        """Group files by their base name, preserving leading zeros"""
        files_by_base = {}
        
        if only_file:
            # Just group the specific file and its related files
            file_path = os.path.join(folder_path, only_file)
            if os.path.exists(file_path):
                # Extract the base name while preserving leading zeros
                match = re.match(r"(\d+)", os.path.basename(only_file))
                if match:
                    base_name = match.group(1)  # Keep leading zeros
                    files_by_base[base_name] = [file_path]
                    
                    # Also look for associated files
                    prefix = base_name
                    for f in os.listdir(folder_path):
                        if f.startswith(prefix) and f != only_file:
                            files_by_base[base_name].append(os.path.join(folder_path, f))
        else:
            # Group all files by their base prefix
            for f in os.listdir(folder_path):
                file_path = os.path.join(folder_path, f)
                if os.path.isfile(file_path) and not f.startswith('.'):
                    # Extract the base name with leading zeros preserved
                    match = re.match(r"(\d+)", f)
                    if match:
                        base_name = match.group(1)  # Keep leading zeros
                        
                        if base_name not in files_by_base:
                            files_by_base[base_name] = []
                        
                        files_by_base[base_name].append(file_path)
        
        return files_by_base
    
    def _log_failed_uploads(self, output_folder):
        """Log failed uploads to a file"""
        if not self.failed_uploads:
            return
        
        try:
            log_path = os.path.join(output_folder, "upload_failures.txt")
            with open(log_path, "w", encoding="utf-8") as f:
                for file_path, reason in self.failed_uploads:
                    filename = os.path.basename(file_path)
                    f.write(f"{filename} | {reason}\n")
            
            self._log(f"Logged {len(self.failed_uploads)} failed uploads to: {log_path}")
        except Exception as e:
            self._log(f"Failed to log failed uploads: {e}")
    
    def _log(self, message):
        """Log a message and call status callback if available"""
        # Only log to the standard logger, don't duplicate
        logging.info(message)
        
        # Call status callback if provided, but don't log again
        if self.status_callback:
            self.status_callback(message)
    
    def _report_progress(self, filename, progress):
        """Report progress via callback if available"""
        if self.progress_callback:
            self.progress_callback(filename, progress)
    
    def _format_size(self, size_bytes):
        """Format file size in human-readable format"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"