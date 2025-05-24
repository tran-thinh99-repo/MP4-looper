import os
import logging
import requests
import random
import sys
import re
import unicodedata
import subprocess

from datetime import datetime

from utils import get_base_path, format_duration
from post_render_check import get_wav_duration
from google_services import get_sheets_service
from api_monitor_module.utils.monitor_access import track_api_call_simple

logging.debug(f"✅ {os.path.basename(__file__)} loaded successfully")

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

                    timestamp = format_duration(current_time)
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

def generate_distributed_song_lists(sheet_url, distribution_settings, duration_in_seconds, 
                                music_folder, output_folder, export_timestamp=True):
    """Generate song lists for distributed mode where each video gets unique songs"""
    try:
        num_videos = distribution_settings['num_videos']
        distribution_method = distribution_settings['distribution_method']
        song_ranges = distribution_settings['song_distribution']
        
        # Load all songs once
        logging.info(f"Loading songs for distribution across {num_videos} videos")
        
        # Use the batch generator to load songs efficiently
        _batch_generator._ensure_connection()
        rows = _batch_generator._load_sheet_data(sheet_url)
        
        # Parse all songs
        all_songs = []
        all_weeks = []
        last_week = ""
        
        for row in rows[1:]:  # Skip header
            if len(row) < 2:
                continue
                
            a = row[0].strip() if len(row) > 0 else ""
            b = row[1].strip() if len(row) > 1 else ""
            
            if a.isdigit() and b:
                song = f"{a}_{b}"
                all_songs.append(song)
                
                week = row[4].strip() if len(row) > 4 else ""
                if not week and last_week:
                    week = last_week
                elif week:
                    last_week = week
                all_weeks.append(week)
        
        logging.info(f"Loaded {len(all_songs)} songs for distribution")
        
        # Shuffle if random distribution
        if distribution_method == "random":
            import random
            # Create pairs of (song, week) to maintain relationship
            song_week_pairs = list(zip(all_songs, all_weeks))
            random.shuffle(song_week_pairs)
            all_songs, all_weeks = zip(*song_week_pairs)
            all_songs = list(all_songs)
            all_weeks = list(all_weeks)
        
        # Generate song lists for each video
        video_song_lists = []
        
        for i, (start_idx, end_idx, count) in enumerate(song_ranges):
            video_num = i + 1
            
            # Get songs for this video (adjust for 0-based indexing)
            video_songs = all_songs[start_idx-1:end_idx]
            video_weeks = all_weeks[start_idx-1:end_idx]
            
            logging.info(f"Video {video_num}: {len(video_songs)} songs (range {start_idx}-{end_idx})")
            
            # Generate song list for this video
            # FIXED: Use proper base name instead of generic video_X name
            base_name = f"Part{video_num}"  # This will be combined with actual file name later
            output_filename = f"{base_name}_song_list.txt"
            
            # Create song list by repeating the chunk to fill duration
            selected_songs = []
            total_duration = 0
            
            # Check for missing WAV files first
            missing_files = []
            for song in video_songs:
                song_normalized = unicodedata.normalize("NFC", song)
                wav_path = os.path.join(music_folder, f"{song_normalized}.wav")
                if not os.path.isfile(wav_path):
                    missing_files.append(f"{song}.wav")
            
            if missing_files:
                logging.warning(f"Video {video_num}: Missing {len(missing_files)} WAV files")
                return ("missing", missing_files)
            
            # Fill duration by repeating the video's songs
            song_index = 0
            while total_duration < duration_in_seconds:
                song = video_songs[song_index % len(video_songs)]
                song_normalized = unicodedata.normalize("NFC", song)
                wav_path = os.path.join(music_folder, f"{song_normalized}.wav")
                
                duration = get_wav_duration(wav_path)
                if duration > 0:
                    selected_songs.append(song)
                    total_duration += duration
                
                song_index += 1
            
            # Save song list - use temporary filename for now
            list_path = os.path.join(output_folder, output_filename)
            with open(list_path, "w", encoding="utf-8") as f:
                for song in selected_songs:
                    f.write(song + "\n")
            
            # Create timestamp file if requested - use temporary filename for now
            timestamp_path = None
            if export_timestamp:
                timestamp_path = os.path.join(output_folder, f"{base_name}_song_list_timestamp.txt")
                with open(timestamp_path, "w", encoding="utf-8") as f:
                    current_time = 0
                    for song in selected_songs:
                        song_normalized = unicodedata.normalize("NFC", song)
                        wav_path = os.path.join(music_folder, f"{song_normalized}.wav")
                        
                        timestamp = format_duration(current_time)
                        f.write(f"{timestamp} {song.split('_', 1)[-1]}\n")
                        
                        current_time += get_wav_duration(wav_path)
            
            # Create temp_music.wav for this video
            concat_file_path = os.path.join(output_folder, f"{base_name}_music_concat.txt")
            with open(concat_file_path, "w", encoding="utf-8") as f:
                for song in selected_songs:
                    song_normalized = unicodedata.normalize("NFC", song)
                    wav_path = os.path.join(music_folder, f"{song_normalized}.wav")
                    f.write(f"file '{wav_path.replace('\\', '/')}'\n")
            
            # Generate temp music file
            temp_music_path = os.path.join(output_folder, f"{base_name}_temp_music.wav")
            
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
            
            if result.returncode != 0 or not os.path.exists(temp_music_path):
                logging.error(f"Failed to create temp music for video {video_num}")
                return False
            
            # Store info for this video
            video_song_lists.append({
                'video_num': video_num,
                'song_list_path': list_path,
                'temp_music_path': temp_music_path,
                'timestamp_path': timestamp_path,
                'concat_file_path': concat_file_path,
                'songs_count': len(video_songs),
                'loops': len(selected_songs) // len(video_songs),
                'base_name': base_name  # Store base name for later renaming
            })
        
        return video_song_lists
        
    except Exception as e:
        logging.error(f"Error in distributed song list generation: {e}")
        return None

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