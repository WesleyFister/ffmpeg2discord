Frustrated by manually using ffmpeg to compress videos to get around Discord's 10 MiB file size limit, I wrote a simple Python program to automate the process. This program works for both Windows and Linux systems, assuming that you have Python and the dependencies installed.

### Warning
This program is very CPU intensive and on my i7 8086k it took about 3 minutes to compress a 1 minute 1080p 60 FPS video.

### Features
- 100% offline, opensource and private
- Ability to compress videos, images and audio
- Set desired file size in MiB or MB
- Trim videos and audio
- Remove audio
- Mix audio tracks (if you record your gameplay and mic audio seperately)
- Removes metadata
- Batch processing

### Install

You can either download the standalone binary for your system which contains everything needed to run. Alternatively you can install the dependencies and run the script.

Install FFmpeg and jpegoptim to your system's path.

Then:
`pip install -r requirements.txt`

### Build binaries

Windows
```
virtualenv FFmpeg2Discord
.\FFmpeg2Discord\Scripts\activate.ps1
pip install pyqt5 ffmpeg_progress_yield pyinstaller
.\FFmpeg2Discord\Scripts\pyinstaller.exe --noconsole --windowed --onedir --contents-directory libraries FFmpeg2Discord.py
```
Linux
```
virtualenv FFmpeg2Discord
source FFmpeg2Discord/bin/activate
pip install pyqt5 ffmpeg_progress_yield pyinstaller
./FFmpeg2Discord/bin/pyinstaller --onefile FFmpeg2Discord.py
```
