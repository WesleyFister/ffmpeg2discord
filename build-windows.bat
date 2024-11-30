virtualenv venv
.\venv\Scripts\pip install -r requirements.txt
.\venv\Scripts\pip install pyinstaller
.\venv\Scripts\pyinstaller.exe --noconsole --onefile .\src\FFmpeg2Discord.py

move .\dist\FFmpeg2Discord.exe .
rmdir /s /q build
rmdir /s /q dist
del /f FFmpeg2Discord.spec
