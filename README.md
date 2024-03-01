Frustrated by manually using ffmpeg to compress videos to get around Discord's 25 MiB file size limit, I wrote a simple Python script that should automate the process. It could use some work; however, for now, it gets the job done. This script works for both Windows and Linux systems, assuming that you have Python and the dependencies installed.

### Warning
This script is very CPU intensive and on my i7 8086k it took about 5 minutes to compress a 1 minute 1080p 60 FPS video.

### Known Issues
Does not preserve portrait videos and attempting to will distort them. Bug in moviepy? 

### Install

You can either download the standalone binary for your system which contains everything needed to run or install the dependencies and run the script.

`pip install -r requirements.txt`

Binaries are built with the following commands.

Linux
```
virtualenv FFmpeg2Discord
.\FFmpeg2Discord\Scripts\activate.ps1
pip install moviepy pyqt5 opencv-python-headless pyinstaller
.\FFmpeg2Discord\Scripts\pyinstaller.exe --onefile FFmpeg2Discord.py
```
Windows
```
virtualenv FFmpeg2Discord
source FFmpeg2Discord/bin/activate
pip install moviepy pyqt5 opencv-python-headless pyinstaller
./FFmpeg2Discord/bin/pyinstaller --onefile FFmpeg2Discord.py
```
