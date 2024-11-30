#!/bin/bash

virtualenv venv
./venv/bin/pip install -r requirements.txt
./venv/bin/pip install pyinstaller
./venv/bin/pyinstaller --onefile --noconsole ./src/FFmpeg2Discord.py

mv ./dist/FFmpeg2Discord .
rm -r build dist FFmpeg2Discord.spec
