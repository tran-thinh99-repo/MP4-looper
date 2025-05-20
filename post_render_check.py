import subprocess
import logging
import os
import shutil

def get_mp4_duration(file_path):
    try:
        result = subprocess.run([
            "ffprobe", "-v", "error", "-show_entries",
            "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file_path
        ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        return float(result.stdout.strip())
    except Exception as e:
        logging.error(f"❌ Failed to read MP4 duration: {e}")
        return 0

def has_audio_stream(file_path):
    try:
        result = subprocess.run([
            "ffprobe", "-v", "error", "-select_streams", "a",
            "-show_entries", "stream=index", "-of", "csv=p=0", file_path
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return bool(result.stdout.strip())
    except Exception as e:
        logging.error(f"❌ Audio check failed: {e}")
        return False

def validate_render(file_path, expected_duration, min_tolerance=0.95):
    if not os.path.exists(file_path):
        logging.error(f"❌ Rendered file not found: {file_path}")
        return False

    duration = get_mp4_duration(file_path)
    if duration < expected_duration * min_tolerance:
        logging.warning(f"⚠️ File too short: {duration:.2f}s (expected: {expected_duration}s)")
        return False

    if not has_audio_stream(file_path):
        logging.warning("⚠️ No audio stream found.")
        return False

    logging.info("✅ Post-render check passed.")
    return True

def get_wav_duration(file_path, ffprobe_path="ffprobe"):
    if not os.path.exists(file_path):
        logging.error(f"❌ File not found: {file_path}")
        return 0

    # Check if ffprobe is available
    if not shutil.which(ffprobe_path):
        logging.error(f"❌ FFprobe binary not found: {ffprobe_path}")
        return 0

    try:
        result = subprocess.run([
            ffprobe_path, "-i", file_path,
            "-show_entries", "format=duration",
            "-v", "quiet", "-of", "csv=p=0"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.returncode != 0:
            logging.error(f"❌ FFprobe failed: {result.stderr.strip()}")
            return 0

        duration_str = result.stdout.strip()
        return float(duration_str)

    except Exception as e:
        logging.warning(f"⚠️ Exception reading duration of {file_path}: {e}")
        return 0
        
def log_audio_duration(file_path):
    dur = get_wav_duration(file_path)
    logging.info(f"🎧 Audio duration: {dur:.2f}s")