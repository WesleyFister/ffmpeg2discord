Frustrated by manually using ffmpeg to compress videos to get around Discord's 25 MiB file size limit, I wrote a simple Python program to automate the process. This program works for both Windows and Linux systems, assuming that you have Python and the dependencies installed.

### Warning
This script is very CPU intensive and on my i7 8086k it took about 3 minutes to compress a 1 minute 1080p 60 FPS video.

### Install

You can either download the standalone binary for your system which contains everything needed to run. Alternatively you can install the dependencies and run the script.

`pip install -r requirements.txt`

Binaries are built with the following commands.

Windows
```
virtualenv FFmpeg2Discord
.\FFmpeg2Discord\Scripts\activate.ps1
pip install moviepy pyqt5 ffmpeg_progress_yield pyinstaller
.\FFmpeg2Discord\Scripts\pyinstaller.exe --onefile FFmpeg2Discord.py
```
Linux
```
virtualenv FFmpeg2Discord
source FFmpeg2Discord/bin/activate
pip install moviepy pyqt5 ffmpeg_progress_yield pyinstaller
./FFmpeg2Discord/bin/pyinstaller --onefile FFmpeg2Discord.py
```
