virtualenv venv
.\venv\Scripts\pip install pyqt5 ffmpeg_progress_yield pyinstaller
.\venv\Scripts\pyinstaller.exe --noconsole --onefile FFmpeg2Discord.py

move .\dist\FFmpeg2Discord.exe .
rmdir /s /q build
rmdir /s /q dist
del /f FFmpeg2Discord.spec