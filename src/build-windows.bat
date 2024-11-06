virtualenv FFmpeg2Discord
.\FFmpeg2Discord\Scripts\activate.ps1
pip install pyqt5 ffmpeg_progress_yield pyinstaller
.\FFmpeg2Discord\Scripts\pyinstaller.exe --noconsole --onefile FFmpeg2Discord.py

move .\dist\FFmpeg2Discord .
rmdir /s /q build
rmdir /s /q dist
del /f FFmpeg2Discord.spec