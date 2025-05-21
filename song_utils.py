import os
import csv
import logging
import requests
import random
import unicodedata
import subprocess
from datetime import datetime
from utils import get_base_path, format_timestamp
from post_render_check import get_wav_duration

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
        # Use direct Google Sheet access
        logging.info(f"📊 Reading directly from Google Sheet: {sheet_url}")
        try:
            response = requests.get(sheet_url, timeout=10)
            response.raise_for_status()
            
            # Parse CSV directly from the response content
            csv_content = response.text.splitlines()
            reader = csv.reader(csv_content)
            header = next(reader, None)  # skip header
            
            songs_raw = []
            weeks_raw = []
            last_week = ""
            
            for row in reader:
                # Parse song and week information
                if len(row) >= 2:
                    a = row[0].strip()
                    b = row[1].strip()
                    if a.isdigit() and b:
                        song = f"{a}_{b}"
                    else:
                        song = ""
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
            
            logging.info(f"✅ Directly read {len(songs_raw)} songs from Google Sheet")
            
        except Exception as e:
            logging.error(f"❌ Failed to read directly from Google Sheet: {e}")
            return None
            
        if not weeks_raw or not songs_raw:
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
            ffmpeg_cmd = [
                "ffmpeg", "-y", "-f", "concat", "-safe", "0", 
                "-i", concat_file_path, "-c", "copy", temp_music_path
            ]
            
            logging.info(f"🔊 Generating music file: {' '.join(ffmpeg_cmd)}")
            result = subprocess.run(
                ffmpeg_cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True
            )
            
            if result.returncode != 0:
                logging.error(f"❌ FFMPEG Error: {result.stderr}")
                return False
            
            if os.path.exists(temp_music_path):
                logging.info(f"✅ Successfully created temp music file: {temp_music_path}")
            else:
                logging.error(f"❌ Failed to create temp music file despite successful command")
                return False
        except Exception as e:
            logging.error(f"❌ Exception creating temp music: {e}")
            return False

        logging.info(f"🎶 Final song count: {len(selected_songs)}")
        logging.info(f"⏱️ Final duration: {int(total_duration)} seconds")
        logging.info("-" * 40)
        return list_path

    except Exception as e:
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