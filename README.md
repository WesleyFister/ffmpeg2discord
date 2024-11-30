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

The easiest way to get up and running is to head over to the releases section and download the respective zip for your operating system. After that all you need to do it double click it!

Alternatively you can install the dependencies and run the Python script.

To do so, install FFmpeg and jpegoptim to your system's path.

Then:
`pip install -r requirements.txt`

### Build binaries

You can build static binaries with `build-linux.sh` or `build-windows.bat`
