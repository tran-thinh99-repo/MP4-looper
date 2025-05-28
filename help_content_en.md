# MP4 Looper - User Guide

Welcome to MP4 Looper! This application helps you create long-duration videos by combining your video files with background music. Perfect for creating extended content for streaming or ambient videos.

## 🚀 Getting Started

### What You Need Before Starting
1. **Video Files**: MP4 video files you want to loop
2. **Music Files**: WAV audio files for background music
3. **Google Account**: For accessing music playlists and uploading (optional)
4. **Storage Space**: Enough disk space for output videos

### First Time Setup
1. **Launch the Application**: Double-click the MP4 Looper icon
2. **Sign In**: Enter your email and password when prompted
3. **Set Up Folders**: Configure your output and music directories

## 📁 Setting Up Your Folders

### Output Folder
- **What it is**: Where your finished videos will be saved
- **How to set**: Click "Browse" next to "Output Folder"
- **Tip**: Choose a folder with plenty of free space (videos can be large!)

### Music Folder
- **What it is**: Folder containing your WAV music files
- **File Format**: Only WAV files (.wav) are supported
- **Organization**: Keep all your music files in one folder for easy access

## 🎵 Setting Up Your Music Playlist

### Google Sheets Integration
The app can read music playlists from Google Sheets:

1. **Create a Google Sheet** with these columns:
   - Column A: Song numbers (1, 2, 3, etc.)
   - Column B: Song names (must match your WAV filenames)
   - Column C: Combined name (auto-generated: "1_SongName")
   - Column E: Week dates (MM/DD/YYYY format)

2. **Example Sheet Layout**:
   ```
   A    | B           | C           | D | E
   1    | Amazing     | 1_Amazing   |   | 01/15/2024
   2    | Wonderful   | 2_Wonderful |   | 01/15/2024
   3    | Beautiful   | 3_Beautiful |   | 01/22/2024
   ```

3. **Get Sheet URL**: Copy your Google Sheet's sharing URL
4. **Paste in App**: Put the URL in the "Google Sheet URL" field

### Song File Naming
Your WAV files must match the names in your Google Sheet:
- Sheet says "Amazing" → File should be "Amazing.wav"
- Sheet says "Wonderful" → File should be "Wonderful.wav"

## 🎬 Creating Your Videos

### Step 1: Add Video Files
**Drag and Drop Method** (Easiest):
1. Open the folder containing your MP4 files
2. Drag files directly into the app window
3. Files appear in the "Raw Preview" section

**Browse Method**:
1. Click "Browse Files" button
2. Select your MP4 files
3. Click "Open"

### Step 2: Set Video Duration
1. **Duration Box**: Enter time in seconds
   - 3600 = 1 hour
   - 7200 = 2 hours
   - 10800 = 3 hours
2. **Quick Buttons**: Use +1h, +3h, +11h buttons for common lengths
3. **Preview**: See the time conversion (e.g., "3600s (1h)")

### Step 3: Configure Settings

**Song Settings**:
- **"Use default (5) newest songs"**: App picks 5 most recent songs automatically
- **Custom count**: Uncheck the box and enter your preferred number

**Audio Options**:
- **"Fade audio out at end"**: Gradually reduces volume in last 5 seconds
- **"Export timestamp"**: Creates a text file showing when each song plays

**Upload Options** (Admin only):
- **"Auto-upload after render"**: Automatically uploads finished videos

### Step 4: Start Processing
1. **Review Settings**: Double-check all your settings
2. **Click "Start Processing"**: The magic begins!
3. **Monitor Progress**: Watch the progress bar and status messages
4. **Wait**: Processing time depends on video length and your computer speed

## 🔧 Advanced Features

### Song Distribution Mode
Create multiple videos with different song selections:

1. **Click "Song Distribution"**: Opens the distribution settings
2. **Set Number of Videos**: Choose how many different versions to create
3. **Distribution Method**:
   - **Sequential**: Songs divided in order (1-10, 11-20, etc.)
   - **Random**: Songs randomly mixed for each video
4. **Preview**: See exactly which songs each video will use
5. **Start Processing**: Creates multiple unique videos

### Video Transitions 🎬

The MP4 Looper now supports professional video transitions that are applied at the beginning and end of your videos:

**Available Transitions:**
- **None** - No transition (default)
- **Fade** - Smooth fade in/out effect
- **Slide Left/Right** - Video slides in from left or right
- **Zoom** - Zooms in at start, zooms out at end
- **Wipe Down/Up** - Video reveals from top or bottom
- **Blinds** - Horizontal blind effect
- **Pixelate** - Pixelates then reveals the video
- **Dissolve** - Random pixel dissolve effect
- **Expand Line** - Expands from center line

**Important Notes:**
- Transitions require NVIDIA GPU with NVENC support
- Each transition adds ~1.5 seconds to the start and end
- If GPU encoding is not available, processing continues without transitions
- Transitions work with all video durations (1h, 3h, 11h)

**How to use:**
1. Select your desired transition from the dropdown menu
2. The transition will be applied to all videos in the batch
3. Monitor the progress - you'll see "Applying [transition] transition..." during processing

### Utilities Window
Click the 🔧 button to access additional tools:

**Debug Tools**:
- **View Log**: See detailed app activity (for troubleshooting)
- **Clean Uploads**: Remove failed upload attempts

**Support Tools**:
- **Send Debug Info**: Share logs with support team (if needed)
- **Help**: Opens this help guide

**Admin Tools** (Admin users only):
- **Monitor**: View detailed usage statistics

## 📤 File Management

### Output Files
After processing, you'll find these files in your output folder:

**Video Files**:
- `VideoName_1h.mp4` - Your finished video
- `VideoName_3h.mp4` - If you made a 3-hour version

**Information Files**:
- `VideoName_song_list.txt` - List of songs used
- `VideoName_song_list_timestamp.txt` - When each song plays
- `temp_music.wav` - Combined audio track (automatically deleted)

### Managing Files
**Open Output Folder**: Click "Open" next to Output Folder to see your files
**Clean Output Folder**: Click "Clean" to remove old files (be careful!)

## ❗ Troubleshooting

### Common Issues and Solutions

**"No files queued for processing"**
- **Problem**: You haven't added any video files
- **Solution**: Drag and drop MP4 files into the app

**"Missing WAV files"**
- **Problem**: App can't find music files that match your playlist
- **Solution**: 
  1. Check your Music Folder path
  2. Verify WAV filenames match your Google Sheet exactly
  3. Ensure files are actually .wav format

**"Failed to generate song list"**
- **Problem**: Can't access your Google Sheet
- **Solution**:
  1. Check your internet connection
  2. Verify Google Sheet URL is correct
  3. Make sure the sheet is shared publicly

**"Output folder does not exist"**
- **Problem**: The output folder path is invalid
- **Solution**: Click "Browse" and select a valid folder

**"Authentication failed"**
- **Problem**: Login credentials are incorrect
- **Solution**: 
  1. Double-check your email and password
  2. Contact your administrator for access
  3. Wait a few minutes if you've tried too many times

**Processing takes forever**
- **Possible causes**: 
  1. Very long video duration
  2. Many large video files
  3. Computer running low on resources
- **Solutions**:
  1. Process fewer files at once
  2. Use shorter durations for testing
  3. Close other programs to free up memory

**"GPU not detected"**
- **Problem**: Hardware acceleration unavailable
- **Solution**: Processing will be slower but still work

### Getting Help
1. **Check the Log**: Use "View Log" in utilities for error details
2. **Send Debug Info**: Use "Send Debug Info" to share logs with support
3. **Contact Support**: Reach out with specific error messages

## 💡 Tips for Best Results

### Performance Tips
1. **Process in batches**: Don't queue too many large files at once
2. **Free up space**: Ensure plenty of disk space in output folder
3. **Close other apps**: Give MP4 Looper more system resources
4. **Use SSD storage**: Faster storage = faster processing

### Quality Tips
1. **Use high-quality source videos**: Output quality matches input quality
2. **Organize music well**: Keep WAV files organized and properly named
3. **Test with short durations**: Try 3-minute videos before making hour-long ones
4. **Regular backups**: Save your finished videos to external storage

### Workflow Tips
1. **Prepare files first**: Organize videos and music before starting
2. **Use consistent naming**: Keep file names simple and consistent
3. **Update playlists regularly**: Keep your Google Sheet current
4. **Save settings**: The app remembers your preferences

## 🔒 Privacy and Security

- **Local Processing**: Your videos are processed on your computer
- **Secure Login**: Authentication is encrypted and secure
- **Optional Upload**: You control if videos are uploaded anywhere
- **Log Privacy**: Debug logs contain file paths but no personal content

## 📋 Keyboard Shortcuts

- **Drag & Drop**: Add files by dragging from file explorer
- **Enter**: Confirm settings in dialog boxes
- **Escape**: Cancel operations or close dialogs

---

**Need more help?** Use the "Send Debug Info" feature to contact support with detailed information about any issues you're experiencing.