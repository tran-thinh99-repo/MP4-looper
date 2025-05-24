# MP4 Looper

A powerful desktop application for creating extended-duration videos by combining MP4 video files with synchronized background music. Perfect for content creators, streamers, and anyone needing long-form ambient videos.

## ✨ Features

### Core Functionality
- **Video Looping**: Seamlessly loop MP4 videos for any duration
- **Music Integration**: Automatically sync background music from WAV files
- **Batch Processing**: Process multiple videos simultaneously
- **Duration Control**: Create videos from minutes to hours in length
- **Audio Fading**: Optional audio fade-out effects

### Advanced Features
- **Song Distribution**: Create multiple videos with different song combinations
- **Google Sheets Integration**: Manage music playlists via Google Sheets
- **Hardware Acceleration**: CUDA/NVENC support for faster processing
- **Progress Monitoring**: Real-time processing progress and status
- **File Management**: Built-in tools for organizing outputs

### User Experience
- **Drag & Drop Interface**: Intuitive file handling
- **Multi-language Support**: English and Vietnamese interfaces
- **Dark Theme**: Modern, eye-friendly interface
- **Help System**: Comprehensive built-in documentation
- **Error Recovery**: Robust error handling and recovery

## 🔧 System Requirements

### Minimum Requirements
- **OS**: Windows 10 64-bit or later
- **RAM**: 4 GB (8 GB recommended)
- **Storage**: 2 GB free space for installation
- **Additional Storage**: Varies based on video output sizes

### Recommended Requirements
- **OS**: Windows 11 64-bit
- **RAM**: 16 GB or more
- **GPU**: NVIDIA graphics card with CUDA support
- **Storage**: SSD with 50+ GB free space
- **Internet**: For Google Sheets integration and updates

### Dependencies (Bundled)
- **FFmpeg**: Video processing engine
- **Python Runtime**: Application runtime (embedded)
- **Audio Codecs**: WAV processing support

## 📥 Installation

### For End Users
1. **Download**: Get the latest release from the releases page
2. **Extract**: Unzip the downloaded file to your preferred location
3. **Run**: Double-click `MP4 Looper.exe` to start
4. **Setup**: Follow the first-time setup wizard

### For Developers
```bash
# Clone the repository
git clone https://github.com/tran-thinh99-repo/mp4-looper.git
cd mp4-looper

# Install dependencies
pip install -r requirements.txt

# Run from source
python mp4_looper.py
```

## 🚀 Quick Start Guide

### 1. Initial Setup
- Launch MP4 Looper
- Sign in with your credentials
- Configure output and music folder paths
- Set up your Google Sheets playlist (optional)

### 2. Prepare Your Files
- **Video Files**: Place MP4 files in an accessible folder
- **Music Files**: Organize WAV files in your music folder
- **Playlist**: Create a Google Sheet with your song list

### 3. Create Your First Video
1. Drag MP4 files into the application
2. Set desired video duration (in seconds)
3. Configure music and audio settings
4. Click "Start Processing"
5. Monitor progress and wait for completion

### 4. Find Your Output
- Processed videos appear in your configured output folder
- Look for files named like: `VideoName_1h.mp4`
- Additional files include song lists and timestamps

## 📋 File Organization

### Input Files
```
📁 Your Folders/
├── 📁 Videos/
│   ├── video1.mp4
│   ├── video2.mp4
│   └── video3.mp4
├── 📁 Music/
│   ├── Song1.wav
│   ├── Song2.wav
│   └── Song3.wav
```

### Output Files
```
📁 Output Folder/
├── video1_1h.mp4              # Main output video
├── video1_song_list.txt       # Songs used
├── video1_song_list_timestamp.txt  # Timing info
└── (temporary processing files - auto-deleted)
```

### Google Sheets Format
| A (Number) | B (Song Name) | C (Combined) | D | E (Week) |
|------------|---------------|--------------|---|----------|
| 1          | Amazing       | 1_Amazing    |   | 01/15/2024 |
| 2          | Wonderful     | 2_Wonderful  |   | 01/15/2024 |
| 3          | Beautiful     | 3_Beautiful  |   | 01/22/2024 |

## ⚙️ Configuration

### Basic Settings
- **Output Folder**: Where finished videos are saved
- **Music Folder**: Location of WAV music files
- **Duration**: Video length in seconds (3600 = 1 hour)
- **Song Count**: Number of songs to include

### Advanced Options
- **Fade Audio**: Gradually reduce volume at video end
- **Export Timestamps**: Create timing information files
- **Hardware Acceleration**: Use GPU for faster processing
- **Auto-upload**: Automatically upload finished videos (admin only)

### Google Sheets Integration
1. Create a Google Sheet with the required column format
2. Share the sheet publicly or with the service account
3. Copy the sheet URL into the application
4. Ensure WAV filenames match sheet entries exactly

## 🛠️ Troubleshooting

### Common Issues

**"Missing WAV files" Error**
- Check that your Music Folder path is correct
- Verify WAV file names match your Google Sheet exactly
- Ensure files are actually in WAV format

**Slow Processing**
- Close other applications to free up system resources
- Use an SSD for faster file access
- Enable hardware acceleration if available
- Process fewer files simultaneously

**Authentication Problems**
- Verify your login credentials
- Check internet connection for Google Sheets access
- Contact your administrator for access issues

**"Failed to generate song list"**
- Confirm Google Sheet URL is correct
- Check that the sheet is publicly accessible
- Verify the sheet follows the required column format

### Performance Optimization
- **Hardware**: Use NVIDIA GPU with recent drivers
- **Storage**: Store files on SSD drives when possible
- **Memory**: Close unnecessary applications during processing
- **Network**: Stable internet for Google Sheets access

### Getting Support
1. Use the built-in "Send Debug Info" feature
2. Check the application logs via "View Log" utility
3. Include specific error messages when reporting issues
4. Describe the steps that led to the problem

## 🔒 Privacy & Security

### Data Handling
- **Local Processing**: All video processing happens on your computer
- **No Cloud Storage**: Videos are not automatically stored online
- **Optional Upload**: Upload features require explicit user action
- **Secure Authentication**: Login credentials are encrypted

### File Access
- Application only accesses folders you specifically configure
- No automatic scanning of your computer
- Temporary files are automatically cleaned up
- Original files are never modified

### Network Activity
- **Google Sheets**: Optional feature for playlist management
- **Updates**: Periodic checks for application updates
- **Authentication**: Secure login verification
- **Debug Info**: Only sent when explicitly requested by user

## 📝 Version History

### v1.2.0 (Current)
- Added song distribution mode for multiple video variants
- Improved hardware acceleration support
- Enhanced error handling and recovery
- Updated user interface with better feedback
- Added comprehensive help system

### v1.1.0
- Added Google Sheets integration
- Implemented batch processing
- Added drag & drop file handling
- Improved audio processing quality

### v1.0.0
- Initial release
- Basic video looping functionality
- Simple audio overlay
- Manual file selection

## 🤝 Contributing

### For Developers
- **Language**: Python 3.8+
- **UI Framework**: CustomTkinter
- **Video Processing**: FFmpeg
- **Build System**: PyInstaller

### Development Setup
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/

# Build executable
python build_mp4_looper.bat
```

### Code Style
- Follow PEP 8 guidelines
- Use type hints where applicable
- Include docstrings for all functions
- Write unit tests for new features

## 📄 License

This project is proprietary software. All rights reserved.

### Usage Terms
- Licensed for use by authorized users only
- Commercial use requires separate licensing
- Redistribution is not permitted without authorization
- Source code access is limited to authorized developers

### Third-Party Components
- **FFmpeg**: GPL/LGPL licensed components
- **Python**: PSF licensed runtime
- **CustomTkinter**: MIT licensed UI framework
- Various other open-source components (see full attribution in NOTICES)

## 📞 Support

### Documentation
- **Built-in Help**: Press F1 or use Help menu
- **User Guide**: Available in English and Vietnamese
- **Video Tutorials**: Check the documentation folder

### Technical Support
- **Debug Information**: Use "Send Debug Info" feature
- **Log Files**: Available via "View Log" utility
- **System Information**: Included in debug reports

### Contact Information
- **Application Issues**: Use built-in support features
- **Feature Requests**: Contact through official channels
- **Business Inquiries**: Use designated business contacts

---

**MP4 Looper** - Professional video processing made simple.

*For the latest updates and information, check the application's built-in update system.*