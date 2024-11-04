pyuic5 -x FFmpeg2DiscordUI.ui -o ui.py

virtualenv venv
source venv/bin/activate
pip install pyqt5 ffmpeg_progress_yield pyinstaller
./venv/bin/pyinstaller --onefile --noconsole FFmpeg2Discord.py
mv ./dist/FFmpeg2Discord ./
rm -r build dist FFmpeg2Discord.spec
