# help_content_en.md
# MP4 Looper Help Guide

## Overview
MP4 Looper allows you to create extended-duration video loops with background music from your original MP4 files. It's designed for creating looping videos with background music tracks sourced from a Google Sheet playlist.

## Main Features
- Loop MP4 videos for specified durations (1h, 3h, 11h, or custom)
- Add automatically selected background music from a music library
- Export timestamped song lists
- Batch process multiple files
- Automatically upload to Google Drive

## Getting Started

### 1. Adding Files
- **Drag and Drop**: Drag MP4 files or folders directly into the application
- **Browse**: Click "Browse Files" to select MP4 files

### 2. Setting Duration
- Enter a custom duration in seconds
- Or use quick preset buttons: +1h (3600s), +3h (10800s), +11h (39600s)

### 3. Setting Folders
- **Output Folder**: Where processed videos will be saved
- **Music Folder**: Directory containing WAV music files for the background

### 4. Music Configuration
- **Google Sheet URL**: Spreadsheet containing your song database
- **Default Songs**: Use 5 newest songs from the playlist or set a custom number

### 5. Processing Options
- **Fade Audio**: Add a 5-second fade-out at the end
- **Export Timestamp**: Generate a song timestamp file
- **Auto-Upload**: Automatically upload to Google Drive after processing

### 6. Start Processing
Click "Start Processing" to begin. The app will:
1. Generate a song list for each video
2. Create extended loop videos with music
3. Export timestamp files for each video
4. Upload to Google Drive (if selected)

## Video Requirements
- Files must be MP4 format
- No special encoding requirements - the original video stream is reused

## Music Requirements
- WAV files in the music folder
- Filenames must match the format in the Google Sheet
- Example: "123_Song Title.wav"

## Using Google Drive Upload
1. Ensure you have valid Google API credentials (credentials.json)
2. Select "Auto-upload after render" or use the "Upload to Drive" button
3. Files will be organized by their numeric prefix in Google Drive

## Troubleshooting

### Missing Music Files
If you get a "Missing WAV Files" error:
- Check that your Music Folder contains all required WAV files
- Ensure filenames match the format in the sheet (e.g., "123_Song Title.wav")
- Try using a different sheet preset

### Render Failures
If rendering fails:
- Check the debug log for specific errors
- Ensure FFmpeg is properly installed
- Verify that input videos are valid MP4 files

### Upload Issues
If uploads fail:
- Check your internet connection
- Verify Google API credentials
- Use "Clean Canceled Uploads" to clear any stuck uploads

## Tips
- For best results, use high-quality source videos
- The application preserves the original video quality
- Use "Clean" buttons to manage disk space after processing
- Check the debug log for detailed information about operations