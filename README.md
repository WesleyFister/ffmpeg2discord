Frustrated by manually using ffmpeg to compress videos to get around Discord's 25 MiB file size limit, I wrote a simple Python script that should automate the process. It could use some work; however, for now, it gets the job done. This script works for both Windows and Linux systems, assuming that you have Python and the dependencies installed.

Make sure to install the dependencies.

`pip install -r requirements.txt`

Optionally portable binaries can be built with pyinstaller.
```
virtualenv discord
source discord/bin/activate
pip install moviepy pyqt5 opencv-python-headless pyinstaller
./discord/bin/pyinstaller --onefile FFmpeg2Discord\ \(v3\).py
```
