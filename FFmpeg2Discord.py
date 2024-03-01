#!/usr/bin/env python3
from os import getenv, path, remove
from platform import system
from mimetypes import guess_type
from moviepy.editor import VideoFileClip
from PyQt5.QtWidgets import QApplication, QFileDialog
#TODO Keep original video rotation and get codec information.

targetFileSize = 200000000
audioBitrate = 60000

filePaths = getenv("NAUTILUS_SCRIPT_SELECTED_FILE_PATHS")

if system() == "Windows":
	trash = "NUL"
	
elif system() == "Linux":
	trash = "/dev/null"

if filePaths == None:
	# File selection dialogue if not invoked through Nautilus file manager.
	app = QApplication([])
	file_dialog = QFileDialog()
	file_dialog.setFileMode(QFileDialog.ExistingFiles)
	file_dialog.setViewMode(QFileDialog.Detail)
	file_dialog.exec_()
	filePathList = file_dialog.selectedFiles()
	app.quit()
	
else:
	# If invoked through Nautilus file manager.
	filePathList = filePaths.split("\n")

for filePath in filePathList:
	mime = guess_type(filePath)
	fileType = mime[0].split("/")
	
	fileSize = path.getsize(filePath)
	
	if fileType[0] == "video":
	# If statement does not work, just proof of concept.
	# if fileSize > 25000000 or videoCodec != "h264":
		dirName, file = path.split(filePath)
		fileName, fileExtension = path.splitext(file)
		dirName = dirName + '/'
		output_file = dirName + fileName + "Discord" + ".mp4"
		
		# Calculates bitrate based on target file size.
		videoLength = VideoFileClip(filePath).duration
		bitrate = (targetFileSize/videoLength)-audioBitrate
		bitrate = int(bitrate)
		
		# Will only set FPS to 30 if video is greater than 50MB.
		videoFPS = VideoFileClip(filePath).fps
		if videoFPS > 30 and fileSize > 50000000:
			videoFPS = 30
		
		# Will only set resolution to 960 and auto calculate width or height if video is greater than 100MB.
		# Discord can embed VP9 but it will not work on ios.
		clip = VideoFileClip(filePath)
		width = clip.size[0]
		height = clip.size[1]
		resized_clip = clip.resize(1)
		if (width > 720 or height > 720) and fileSize > 100000000:
			print("yes")
			if width > height:
				resized_clip = clip.resize(width=720)
				
			else:
				resized_clip = clip.resize(height=720)
		
		# Write to file using 2 pass encoding and other FFmpeg options.
		ffmpeg_params = ["-pass", "1", "-r", str(videoFPS), "-strict", "-2", "-c:v", "libx264", "-c:a", "libopus", "-b:v", str(bitrate), "-b:a", str(audioBitrate), "-preset", "veryslow", "-f", "mp4", trash]
		resized_clip.write_videofile(output_file, ffmpeg_params=ffmpeg_params, verbose=False)
		ffmpeg_params = ["-pass", "2", "-r", str(videoFPS), "-strict", "-2", "-c:v", "libx264", "-c:a", "libopus", "-b:v", str(bitrate), "-b:a", str(audioBitrate), "-preset", "veryslow", "-f", "mp4"]
		resized_clip.write_videofile(output_file, ffmpeg_params=ffmpeg_params, verbose=False)
		
		# Remove files created by FFmpeg in the first pass.
		remove("ffmpeg2pass-0.log")
		remove("ffmpeg2pass-0.log.mbtree")
