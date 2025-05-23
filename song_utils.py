import os
import logging
import requests
import random
import sys
import re
import time
import unicodedata
import subprocess

from datetime import datetime

from utils import get_base_path, format_timestamp
from post_render_check import get_wav_duration
from google_services import get_sheets_service, get_gspread_client
from api_monitor_module.utils.monitor_access import track_api_call_simple

logging.debug(f"✅ {os.path.basename(__file__)} loaded successfully")

def generate_song_list_from_google_sheet(
    sheet_url,
    output_filename,
    duration_in_seconds,
    music_folder,
    output_folder,
    new_song_count=5,
    export_song_list=True,
    export_timestamp=True
):
    logging.debug(f"🧪 generate_song_list_from_google_sheet() called")
    
    try:
        # Use Google Sheets API instead of direct HTTP request
        logging.info(f"📊 Reading from Google Sheet URL: {sheet_url}")
        
        # Extract sheet ID from URL
        sheet_id_match = re.search(r'/d/([a-zA-Z0-9_-]+)', sheet_url)
        if not sheet_id_match:
            track_api_call_simple("song_list_generation", success=False, error_message="Invalid sheet URL")
            logging.error(f"Invalid sheet URL format: {sheet_url}")
            return None
            
        sheet_id = sheet_id_match.group(1)
        
        # Extract gid from URL parameters or fragment
        gid_match = re.search(r'gid=(\d+)', sheet_url)
        gid = gid_match.group(1) if gid_match else "0"
        
        logging.info(f"📊 Reading from Google Sheet ID: {sheet_id}, Sheet gid: {gid}")
        
        # Use centralized Google Services Manager
        track_api_call_simple("sheets_song_connect", success=False)
        
        # Get Sheets service from manager
        sheets_service = get_sheets_service()
        if not sheets_service:
            track_api_call_simple("sheets_song_connect", success=False, error_message="Failed to get Sheets service")
            logging.error("Failed to get Google Sheets service")
            return None
        
        track_api_call_simple("sheets_song_connect", success=True)
        
        # Get sheet information to find the sheet name for the specified gid
        track_api_call_simple("sheets_song_info", success=False)
        
        try:
            spreadsheet_info = sheets_service.spreadsheets().get(
                spreadsheetId=sheet_id
            ).execute()
            track_api_call_simple("sheets_song_info", success=True)
        except Exception as e:
            track_api_call_simple("sheets_song_info", success=False, error_message=str(e))
            logging.error(f"Failed to get spreadsheet info: {e}")
            return None
        
        # Find the sheet name that corresponds to the gid
        sheet_name = None
        for sheet in spreadsheet_info.get('sheets', []):
            if str(sheet.get('properties', {}).get('sheetId', '')) == gid:
                sheet_name = sheet.get('properties', {}).get('title')
                break
        
        if not sheet_name:
            track_api_call_simple("song_list_generation", success=False, 
                                error_message=f"Sheet not found for gid={gid}")
            logging.error(f"Could not find sheet with gid={gid} in the spreadsheet")
            return None
            
        logging.info(f"✅ Found sheet name: {sheet_name} for gid {gid}")
        
        # Get data from the specific sheet
        track_api_call_simple("sheets_song_read", success=False)
        
        try:
            result = sheets_service.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range=f"'{sheet_name}'!A:E"
            ).execute()
            
            rows = result.get('values', [])
            if not rows:
                track_api_call_simple("sheets_song_read", success=False, error_message="No data in sheet")
                logging.error("No data found in sheet")
                return None
                
            track_api_call_simple("sheets_song_read", success=True, rows_read=len(rows))
            
        except Exception as e:
            track_api_call_simple("sheets_song_read", success=False, error_message=str(e))
            logging.error(f"Failed to read sheet data: {e}")
            return None
        
        # Process the rows to get song data
        songs_raw = []
        weeks_raw = []
        last_week = ""
        
        # Skip header row
        for row in rows[1:]:
            # Ensure row has enough columns
            if len(row) < 2:
                continue
                
            # Parse song and week information
            a = row[0].strip() if len(row) > 0 else ""
            b = row[1].strip() if len(row) > 1 else ""
            
            if a.isdigit() and b:
                song = f"{a}_{b}"
            else:
                song = ""

            week = row[4].strip() if len(row) > 4 else ""

            # Fill down the last known week if current is empty
            if not week and last_week:
                week = last_week
            elif week:
                last_week = week

            logging.debug(f"Parsed row (by index) - Week: '{week}', Song: '{song}'")
            
            # Filter to avoid garbage songs
            if (
                song and
                "_" in song and
                song.split("_")[0].isdigit()
            ):
                if len(songs_raw) < 5:  # Log first 5 only
                    logging.debug(f"✅ RAW SONG STRING: {repr(song)}")
                songs_raw.append(song)
                weeks_raw.append(week)
            else:
                logging.debug(f"⏭️ Skipped invalid parsed song: '{song}'")
            
        logging.info(f"✅ Successfully read {len(songs_raw)} songs from Google Sheet")
        
        if not weeks_raw or not songs_raw:
            track_api_call_simple("song_list_generation", success=False, error_message="No valid songs found")
            logging.error("No valid data available to generate song list.")
            return None

        week_dict = {}
        last_week = None
        for i, song in enumerate(songs_raw):
            song = song.strip()
            if not song or song in ("-", "_"):
                continue

            week = weeks_raw[i] or last_week
            if week:
                last_week = week
                week_dict.setdefault(week, []).append(song)

        sorted_weeks = sorted(week_dict.keys(), key=lambda x: datetime.strptime(x, "%d/%m/%Y"))
        newest_week = sorted_weeks[-1]
        old_weeks = sorted_weeks[:-1]

        selected_songs = []
        used_songs = set()
        missing_files = []

        # 1. Select newest week
        new_week_songs = week_dict.get(newest_week, []).copy()
        random.shuffle(new_week_songs)
        selected_songs += new_week_songs[:new_song_count]
        used_songs.update(selected_songs)

        logging.info(f"Added {len(selected_songs)} new songs from {newest_week}")

        base_dir = output_folder or get_base_path()
        list_path = os.path.join(base_dir, output_filename)

        # 2. Fill up duration
        total_duration = 0
        if duration_in_seconds and music_folder:
            def try_add(song):
                song = unicodedata.normalize("NFC", song)  # normalize the song name itself
                path = os.path.join(music_folder, f"{song}.wav")
                if not os.path.isfile(path):
                    missing_files.append(f"{song}.wav")
                    return 0
                return get_wav_duration(path)

            for song in selected_songs:
                total_duration += try_add(song)

            if total_duration >= duration_in_seconds:
                logging.info(f"⏹️ Initial selected songs already fill the duration ({total_duration:.2f}s)")
                goto_skip_fill = True
            else:
                goto_skip_fill = False

            if not goto_skip_fill:
                old_song_pool = [s for w in reversed(old_weeks) for s in week_dict[w]]
                random.shuffle(old_song_pool)

                for song in old_song_pool:
                    if song in used_songs:
                        continue
                    dur = try_add(song)
                    if dur:
                        selected_songs.append(song)
                        used_songs.add(song)
                        total_duration += dur
                        if total_duration >= duration_in_seconds:
                            break

            if not goto_skip_fill and total_duration < duration_in_seconds:
                chunk = selected_songs.copy()
                repeat_count = 0
                while total_duration < duration_in_seconds:
                    for song in chunk:
                        dur = try_add(song)
                        if dur == 0:
                            continue
                        selected_songs.append(song)
                        total_duration += dur
                        if total_duration >= duration_in_seconds:
                            break  # Stop after adding this song even if it overshoots
                    repeat_count += 1
                logging.info(f"Repeated song chunk {repeat_count} time(s) to fill duration.")

        if missing_files:
            logging.warning(f"⚠️ Missing {len(missing_files)} WAV files: {missing_files}")
            track_api_call_simple("song_list_generation", success=False, 
                                error_message=f"Missing {len(missing_files)} WAV files")
            return ("missing", sorted(set(missing_files)))  # Return for UI to handle safely

        # 3. Export list
        if export_song_list:
            # Save clean version for user display
            with open(list_path, "w", encoding="utf-8") as f:
                for song in selected_songs:
                    f.write(song + "\n")

            logging.info(f"✔️ Song list saved to: {list_path}")

        if export_timestamp:
            base_path = os.path.splitext(list_path)[0].replace("_song_list", "")
            timestamp_path = base_path + "_song_list_timestamp.txt"
            timestamp_full_path = base_path + "_song_list_timestamp_full.txt"

            with open(timestamp_path, "w", encoding="utf-8") as f_stripped, \
                open(timestamp_full_path, "w", encoding="utf-8") as f_full:

                current_time = 0
                for song in selected_songs:
                    song = unicodedata.normalize("NFC", song)  # normalize before using
                    path = os.path.join(music_folder, f"{song}.wav")

                    if not os.path.isfile(path):
                        continue

                    timestamp = format_timestamp(current_time)

                    # Stripped version (sheet note)
                    f_stripped.write(f"{timestamp} {song.split('_', 1)[-1]}\n")

                    # Full version (prefix kept, for Drive backup)
                    f_full.write(f"{timestamp} {song}\n")

                    current_time += get_wav_duration(path)

            logging.info(f"⏱️ Timestamps saved to: {timestamp_path}")
        
        # Create temp_music.wav file
        # Generate the concatenation file for ffmpeg
        concat_file_path = os.path.join(output_folder, "music_concat.txt")
        with open(concat_file_path, "w", encoding="utf-8") as f:
            for song in selected_songs:
                song = unicodedata.normalize("NFC", song)
                wav_path = os.path.join(music_folder, f"{song}.wav")
                if os.path.isfile(wav_path):
                    f.write(f"file '{wav_path.replace('\\', '/')}'\n")
                else:
                    logging.warning(f"⚠️ Skipping missing WAV file in concat: {wav_path}")
        
        # Create the temp_music.wav file by concatenating all the songs
        temp_music_path = os.path.join(output_folder, "temp_music.wav")
        try:
            # Use ffmpeg to concatenate the WAV files
            # Use CREATE_NO_WINDOW flag on Windows to prevent command window flashing
            extra_args = {}
            if sys.platform == "win32":
                extra_args["creationflags"] = 0x08000000  # CREATE_NO_WINDOW
                
            ffmpeg_cmd = [
                "ffmpeg", "-y", "-f", "concat", "-safe", "0", 
                "-i", concat_file_path, "-c", "copy", temp_music_path
            ]
            
            logging.info(f"🔊 Generating music file: {' '.join(ffmpeg_cmd)}")
            result = subprocess.run(
                ffmpeg_cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True,
                **extra_args
            )
            
            if result.returncode != 0:
                logging.error(f"❌ FFMPEG Error: {result.stderr}")
                track_api_call_simple("song_list_generation", success=False, error_message="FFmpeg failed")
                return False
            
            if os.path.exists(temp_music_path):
                logging.info(f"✅ Successfully created temp music file: {temp_music_path}")
            else:
                logging.error(f"❌ Failed to create temp music file despite successful command")
                track_api_call_simple("song_list_generation", success=False, error_message="Temp music file not created")
                return False
        except Exception as e:
            logging.error(f"❌ Exception creating temp music: {e}")
            track_api_call_simple("song_list_generation", success=False, error_message=f"Music creation failed: {str(e)}")
            return False

        # Track successful completion
        track_api_call_simple("song_list_generation", success=True, 
                            songs_selected=len(selected_songs),
                            total_duration=int(total_duration),
                            weeks_processed=len(week_dict),
                            newest_week=newest_week)

        logging.info(f"🎶 Final song count: {len(selected_songs)}")
        logging.info(f"⏱️ Final duration: {int(total_duration)} seconds")
        logging.info("-" * 40)
        return list_path

    except Exception as e:
        track_api_call_simple("song_list_generation", success=False, error_message=str(e))
        logging.error(f"❌ Failed to generate song list: {e}")
        return None

def validate_csv_rows(csv_lines):
    """Shared logic for both online and offline sources."""
    import csv
    mismatches = []
    reader = csv.reader(csv_lines)
    next(reader, None)  # skip header

    for row in reader:
        if len(row) < 3:
            continue
        a = row[0].strip()
        b = row[1].strip()
        c = row[2].strip()
        if not b:
            continue
        expected = f"{a}_{b}".strip()
        logging.debug(f"[CHECK] A='{a}', B='{b}', C='{c}', Expected='{expected}'")
        if c != expected:
            mismatches.append((a, b, c, expected))
    return mismatches

def validate_online_sheet(sheet_url):
    logging.info(f"🌐 Fetching Google Sheet for validation: {sheet_url}")
    try:
        response = requests.get(sheet_url)
        if response.status_code != 200:
            logging.error(f"❌ Failed to fetch online sheet: HTTP {response.status_code}")
            return None

        lines = response.text.splitlines()
        mismatches = validate_csv_rows(lines)
        return mismatches
    except Exception as e:
        logging.error(f"❌ Exception validating sheet: {e}")
        return None
    
class SongListGenerator:
    """Optimized song list generator for batch processing"""
    
    def __init__(self):
        self.sheets_service = None
        self.cached_song_data = {}
        self.last_sheet_url = None
        
    def _ensure_connection(self):
        """Ensure we have a Google Sheets connection using centralized manager"""
        if self.sheets_service is None:
            track_api_call_simple("sheets_song_connect", success=False)
            
            # Use centralized Google Services Manager
            self.sheets_service = get_sheets_service()
            
            if self.sheets_service:
                track_api_call_simple("sheets_song_connect", success=True)
                logging.info("📊 Google Sheets connection established for batch processing")
            else:
                track_api_call_simple("sheets_song_connect", success=False, 
                                    error_message="Failed to get Sheets service")
                logging.error("Failed to establish Google Sheets connection")
                raise Exception("Could not connect to Google Sheets")
    
    def _load_sheet_data(self, sheet_url):
        """Load song data from sheet (cached for batch processing)"""
        # Check if we already have this data cached
        if sheet_url == self.last_sheet_url and sheet_url in self.cached_song_data:
            logging.info("📊 Using cached song data (no API call needed)")
            return self.cached_song_data[sheet_url]
        
        # Extract sheet ID and gid
        sheet_id_match = re.search(r'/d/([a-zA-Z0-9_-]+)', sheet_url)
        if not sheet_id_match:
            raise ValueError(f"Invalid sheet URL format: {sheet_url}")
            
        sheet_id = sheet_id_match.group(1)
        gid_match = re.search(r'gid=(\d+)', sheet_url)
        gid = gid_match.group(1) if gid_match else "0"
        
        # Get sheet info (only if not cached)
        if sheet_url != self.last_sheet_url:
            track_api_call_simple("sheets_song_info", success=False)
            
            try:
                spreadsheet_info = self.sheets_service.spreadsheets().get(
                    spreadsheetId=sheet_id
                ).execute()
                track_api_call_simple("sheets_song_info", success=True)
            except Exception as e:
                track_api_call_simple("sheets_song_info", success=False, error_message=str(e))
                raise
            
            # Find sheet name
            sheet_name = None
            for sheet in spreadsheet_info.get('sheets', []):
                if str(sheet.get('properties', {}).get('sheetId', '')) == gid:
                    sheet_name = sheet.get('properties', {}).get('title')
                    break
            
            if not sheet_name:
                raise ValueError(f"Could not find sheet with gid={gid}")
        
        # Read sheet data (only if not cached)
        if sheet_url != self.last_sheet_url:
            track_api_call_simple("sheets_song_read", success=False)
            
            try:
                result = self.sheets_service.spreadsheets().values().get(
                    spreadsheetId=sheet_id,
                    range=f"'{sheet_name}'!A:E"
                ).execute()
                
                rows = result.get('values', [])
                if not rows:
                    raise ValueError("No data found in sheet")
                
                track_api_call_simple("sheets_song_read", success=True, rows_read=len(rows))
                
                # Cache the data
                self.cached_song_data[sheet_url] = rows
                self.last_sheet_url = sheet_url
                
                logging.info(f"📊 Loaded and cached {len(rows)} rows from Google Sheet")
            except Exception as e:
                track_api_call_simple("sheets_song_read", success=False, error_message=str(e))
                raise
        
        return self.cached_song_data[sheet_url]
    
    def generate_song_list_batch_optimized(self, sheet_url, output_filename, duration_in_seconds, 
                                         music_folder, output_folder, new_song_count=5, 
                                         export_song_list=True, export_timestamp=True):
        """Generate song list with batch optimization (reuses sheet data)"""
        from api_monitor_module.utils.monitor_access import track_api_call_simple
        
        try:
            
            # Ensure connection (only connects once per batch)
            self._ensure_connection()
            
            # Load sheet data (uses cache for subsequent calls)
            rows = self._load_sheet_data(sheet_url)
            
            # Call the existing generate_song_list_from_google_sheet logic
            # but with pre-loaded rows instead of making API calls
            return self._process_existing_data(rows, output_filename, duration_in_seconds, 
                                             music_folder, output_folder, new_song_count, 
                                             export_song_list, export_timestamp)
            
        except Exception as e:
            track_api_call_simple("song_list_generation_batch", success=False, error_message=str(e))
            logging.error(f"❌ Failed to generate song list (batch): {e}")
            return None
    
    def _process_existing_data(self, rows, output_filename, duration_in_seconds, 
                              music_folder, output_folder, new_song_count=5, 
                              export_song_list=True, export_timestamp=True):
        """Process pre-loaded song data using the same logic as the original function"""
        
        # This copies the exact same processing logic from your original function
        # but works with pre-loaded data instead of making new API calls
        
        songs_raw = []
        weeks_raw = []
        last_week = ""
        
        # Skip header row - same logic as original
        for row in rows[1:]:
            if len(row) < 2:
                continue
                
            a = row[0].strip() if len(row) > 0 else ""
            b = row[1].strip() if len(row) > 1 else ""
            
            if a.isdigit() and b:
                song = f"{a}_{b}"
            else:
                song = ""

            week = row[4].strip() if len(row) > 4 else ""

            if not week and last_week:
                week = last_week
            elif week:
                last_week = week
            
            if (song and "_" in song and song.split("_")[0].isdigit()):
                songs_raw.append(song)
                weeks_raw.append(week)
        
        if not weeks_raw or not songs_raw:
            logging.error("No valid data available to generate song list.")
            return None

        # Continue with the same logic as the original function...
        week_dict = {}
        last_week = None
        for i, song in enumerate(songs_raw):
            song = song.strip()
            if not song or song in ("-", "_"):
                continue

            week = weeks_raw[i] or last_week
            if week:
                last_week = week
                week_dict.setdefault(week, []).append(song)

        sorted_weeks = sorted(week_dict.keys(), key=lambda x: datetime.strptime(x, "%d/%m/%Y"))
        newest_week = sorted_weeks[-1]
        old_weeks = sorted_weeks[:-1]

        selected_songs = []
        used_songs = set()
        missing_files = []

        # Select newest week
        new_week_songs = week_dict.get(newest_week, []).copy()
        random.shuffle(new_week_songs)
        selected_songs += new_week_songs[:new_song_count]
        used_songs.update(selected_songs)

        base_dir = output_folder or get_base_path()
        list_path = os.path.join(base_dir, output_filename)

        # Fill up duration (same logic as original)
        total_duration = 0
        if duration_in_seconds and music_folder:
            def try_add(song):
                song = unicodedata.normalize("NFC", song)
                path = os.path.join(music_folder, f"{song}.wav")
                if not os.path.isfile(path):
                    missing_files.append(f"{song}.wav")
                    return 0
                return get_wav_duration(path)

            for song in selected_songs:
                total_duration += try_add(song)

            if total_duration < duration_in_seconds:
                old_song_pool = [s for w in reversed(old_weeks) for s in week_dict[w]]
                random.shuffle(old_song_pool)

                for song in old_song_pool:
                    if song in used_songs:
                        continue
                    dur = try_add(song)
                    if dur:
                        selected_songs.append(song)
                        used_songs.add(song)
                        total_duration += dur
                        if total_duration >= duration_in_seconds:
                            break

        if missing_files:
            logging.warning(f"⚠️ Missing {len(missing_files)} WAV files: {missing_files}")
            return ("missing", sorted(set(missing_files)))

        # Export list (same as original)
        if export_song_list:
            with open(list_path, "w", encoding="utf-8") as f:
                for song in selected_songs:
                    f.write(song + "\n")

        # Export timestamp (same as original)
        if export_timestamp:
            base_path = os.path.splitext(list_path)[0].replace("_song_list", "")
            timestamp_path = base_path + "_song_list_timestamp.txt"
            timestamp_full_path = base_path + "_song_list_timestamp_full.txt"

            with open(timestamp_path, "w", encoding="utf-8") as f_stripped, \
                open(timestamp_full_path, "w", encoding="utf-8") as f_full:

                current_time = 0
                for song in selected_songs:
                    song = unicodedata.normalize("NFC", song)
                    path = os.path.join(music_folder, f"{song}.wav")

                    if not os.path.isfile(path):
                        continue

                    timestamp = format_timestamp(current_time)
                    f_stripped.write(f"{timestamp} {song.split('_', 1)[-1]}\n")
                    f_full.write(f"{timestamp} {song}\n")
                    current_time += get_wav_duration(path)

        # Create temp_music.wav file (same as original)
        concat_file_path = os.path.join(output_folder, "music_concat.txt")
        with open(concat_file_path, "w", encoding="utf-8") as f:
            for song in selected_songs:
                song = unicodedata.normalize("NFC", song)
                wav_path = os.path.join(music_folder, f"{song}.wav")
                if os.path.isfile(wav_path):
                    f.write(f"file '{wav_path.replace('\\', '/')}'\n")

        temp_music_path = os.path.join(output_folder, "temp_music.wav")
        try:
            extra_args = {}
            if sys.platform == "win32":
                extra_args["creationflags"] = 0x08000000

            ffmpeg_cmd = [
                "ffmpeg", "-y", "-f", "concat", "-safe", "0", 
                "-i", concat_file_path, "-c", "copy", temp_music_path
            ]
            
            result = subprocess.run(
                ffmpeg_cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True,
                **extra_args
            )
            
            if result.returncode != 0:
                logging.error(f"❌ FFMPEG Error: {result.stderr}")
                return False
            
            if not os.path.exists(temp_music_path):
                logging.error(f"❌ Failed to create temp music file")
                return False
                
        except Exception as e:
            logging.error(f"❌ Exception creating temp music: {e}")
            return False

        from api_monitor_module.utils.monitor_access import track_api_call_simple
        track_api_call_simple("song_list_generation_batch", success=True, 
                            songs_selected=len(selected_songs),
                            total_duration=int(total_duration))

        return list_path

# Global instance for batch processing
_batch_generator = SongListGenerator()

def generate_song_list_for_batch(sheet_url, output_filename, duration_in_seconds, 
                                music_folder, output_folder, new_song_count=5, 
                                export_song_list=True, export_timestamp=True):
    """Batch-optimized version of song list generation using centralized services"""
    return _batch_generator.generate_song_list_batch_optimized(
        sheet_url, output_filename, duration_in_seconds, music_folder, 
        output_folder, new_song_count, export_song_list, export_timestamp
    )