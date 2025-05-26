import subprocess
import logging
import os
import sys
import shutil
import json

def find_ffprobe():
    """Find FFprobe using the same detection logic as the rest of the app"""
    try:
        from ffmpeg_utils import find_executable
        ffprobe_path = find_executable("ffprobe")
        if ffprobe_path:
            return ffprobe_path
        else:
            logging.error("❌ FFprobe not found using ffmpeg_utils detection")
            return None
    except ImportError:
        # Fallback if ffmpeg_utils not available
        logging.warning("ffmpeg_utils not available, using fallback detection")
        return shutil.which("ffprobe")

def get_mp4_duration(file_path):
    """Get MP4 duration using proper FFprobe detection"""
    try:
        ffprobe_path = find_ffprobe()
        if not ffprobe_path:
            logging.error("❌ FFprobe not available for duration check")
            return 0
            
        # Use CREATE_NO_WINDOW flag on Windows to prevent command window flashing
        extra_args = {}
        if sys.platform == "win32":
            extra_args["creationflags"] = 0x08000000  # CREATE_NO_WINDOW
            
        result = subprocess.run([
            ffprobe_path, "-v", "error", "-show_entries",
            "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file_path
        ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, **extra_args)
        
        if result.returncode != 0:
            logging.error(f"❌ FFprobe failed: {result.stdout}")
            return 0
            
        return float(result.stdout.strip())
    except Exception as e:
        logging.error(f"❌ Failed to read MP4 duration: {e}")
        return 0

def has_audio_stream(file_path):
    """Check if file has audio stream using proper FFprobe detection"""
    try:
        ffprobe_path = find_ffprobe()
        if not ffprobe_path:
            logging.error("❌ FFprobe not available for audio check")
            return False
            
        # Use CREATE_NO_WINDOW flag on Windows to prevent command window flashing
        extra_args = {}
        if sys.platform == "win32":
            extra_args["creationflags"] = 0x08000000  # CREATE_NO_WINDOW
            
        result = subprocess.run([
            ffprobe_path, "-v", "error", "-select_streams", "a",
            "-show_entries", "stream=index", "-of", "csv=p=0", file_path
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, **extra_args)
        
        return bool(result.stdout.strip())
    except Exception as e:
        logging.error(f"❌ Audio check failed: {e}")
        return False

def validate_render(file_path, expected_duration, min_tolerance=0.95):
    """Validate rendered file meets requirements"""
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

def get_wav_duration(file_path):
    """Get WAV duration using proper FFprobe detection - FIXED VERSION"""
    if not os.path.exists(file_path):
        logging.error(f"❌ File not found: {file_path}")
        return 0

    # Use the same FFprobe detection as the rest of the app
    ffprobe_path = find_ffprobe()
    if not ffprobe_path:
        logging.error("❌ FFprobe not available for WAV duration check")
        return 0

    try:
        # Use CREATE_NO_WINDOW flag on Windows to prevent command window flashing
        extra_args = {}
        if sys.platform == "win32":
            extra_args["creationflags"] = 0x08000000  # CREATE_NO_WINDOW
            
        result = subprocess.run([
            ffprobe_path, "-i", file_path,
            "-show_entries", "format=duration",
            "-v", "quiet", "-of", "csv=p=0"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, **extra_args)

        if result.returncode != 0:
            logging.error(f"❌ FFprobe failed for {file_path}: {result.stderr.strip()}")
            return 0

        duration_str = result.stdout.strip()
        if not duration_str:
            logging.error(f"❌ No duration data returned for {file_path}")
            return 0
            
        return float(duration_str)

    except Exception as e:
        logging.warning(f"⚠️ Exception reading duration of {file_path}: {e}")
        return 0

def get_video_bitrate(video_path):
    """Get the bitrate of the source video for matching during render - FIXED VERSION"""
    try:
        # Use the same FFprobe detection as the rest of the app
        ffprobe_path = find_ffprobe()
        if not ffprobe_path:
            logging.error("❌ FFprobe not available for bitrate detection")
            return "8M"  # Safe fallback
        
        extra_args = {}
        if sys.platform == "win32":
            extra_args["creationflags"] = 0x08000000
        
        # Use ffprobe to get detailed video info
        result = subprocess.run([
            ffprobe_path, "-v", "quiet", "-print_format", "json",
            "-show_format", "-show_streams", video_path
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, **extra_args)
        
        if result.returncode != 0:
            logging.warning(f"Could not probe video bitrate: {result.stderr}")
            return "8M"  # Default fallback
        
        data = json.loads(result.stdout)
        
        # Try to get bitrate from format first (most reliable)
        if 'format' in data and 'bit_rate' in data['format']:
            bitrate_bps = int(data['format']['bit_rate'])
            # Convert to megabits and round sensibly
            bitrate_mbps = bitrate_bps / 1_000_000
            
            # Round to reasonable values for encoding
            if bitrate_mbps < 2:
                return "2M"
            elif bitrate_mbps > 50:
                return "50M"  # Cap at 50M for safety
            else:
                return f"{int(bitrate_mbps)}M"
        
        # Fallback: try to get from video stream
        for stream in data.get('streams', []):
            if stream.get('codec_type') == 'video' and 'bit_rate' in stream:
                bitrate_bps = int(stream['bit_rate'])
                bitrate_mbps = bitrate_bps / 1_000_000
                return f"{max(2, min(50, int(bitrate_mbps)))}M"
        
        # Final fallback - check file size as estimate
        try:
            file_size = os.path.getsize(video_path)
            duration = get_mp4_duration(video_path)
            if duration > 0:
                # Estimate bitrate from file size
                estimated_bps = (file_size * 8) / duration
                estimated_mbps = estimated_bps / 1_000_000
                logging.info(f"📊 Estimated bitrate from file size: {estimated_mbps:.1f}M")
                return f"{max(2, min(50, int(estimated_mbps)))}M"
        except:
            pass
        
        # Ultimate fallback
        logging.warning(f"Could not determine bitrate for {video_path}, using 8M default")
        return "8M"
        
    except Exception as e:
        logging.error(f"Error getting video bitrate: {e}")
        return "8M"  # Safe default

def get_video_info(video_path):
    """Get comprehensive video information for debugging"""
    try:
        ffprobe_path = find_ffprobe()
        if not ffprobe_path:
            logging.error("❌ FFprobe not available for video info")
            return None
            
        extra_args = {}
        if sys.platform == "win32":
            extra_args["creationflags"] = 0x08000000
        
        result = subprocess.run([
            ffprobe_path, "-v", "quiet", "-print_format", "json",
            "-show_format", "-show_streams", video_path
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, **extra_args)
        
        if result.returncode != 0:
            logging.error(f"Failed to get video info: {result.stderr}")
            return None
            
        return json.loads(result.stdout)
        
    except Exception as e:
        logging.error(f"Error getting video info: {e}")
        return None