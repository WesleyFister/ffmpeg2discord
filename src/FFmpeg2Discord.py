from ffmpeg_progress_yield import FfmpegProgress
from PyQt5 import QtCore, QtGui, QtWidgets
from moviepy.editor import VideoFileClip
from ui import Ui_MainWindow
from platform import system
import subprocess
import sys
import os



class ffmpeg2discord(Ui_MainWindow):	
	def __init__(self, window):
		self.filePathList = ""
		self.ffmpegMode = "slow"
		self.mergeAudio = ""
		self.startTime = "" 
		self.endTime = ""
		self.targetFileSize = 200000000
		self.audioBitrate = 60000
		
		self.setupUi(window)
		self.label.setText("0/0")
		self.startTime = self.lineEdit.setValidator(QtGui.QRegExpValidator(QtCore.QRegExp("([0-5][0-9]):([0-5][0-9]):([0-5][0-9]).([0-9][0-9])")))
		self.endTime = self.lineEdit_2.setValidator(QtGui.QRegExpValidator(QtCore.QRegExp("([0-5][0-9]):([0-5][0-9]):([0-5][0-9]).([0-9][0-9])")))
		self.pushButton.clicked.connect(self.fileOpen)
		self.radioButton.clicked.connect(lambda: self.radioOptions("fastest"))
		self.radioButton_2.clicked.connect(lambda: self.radioOptions("slow"))
		self.radioButton_3.clicked.connect(lambda: self.radioOptions("slowest"))
		self.checkBox.stateChanged.connect(self.checkboxToggled)
		self.buttonBox.rejected.connect(self.cancel)
		self.buttonBox.accepted.connect(self.confirm)
	
	def convertTimeToSeconds(self, timeStr):
		timeStr = timeStr.split(":")
		while len(timeStr) < 3:
			timeStr.insert(0, 0)
			
		totalSeconds = int(timeStr[0]) * 3600 + int(timeStr[1]) * 60 + int(timeStr[2])

		return totalSeconds
	
	def fileOpen(self):
		file_dialog = QtWidgets.QFileDialog()
		file_dialog.setFileMode(QtWidgets.QFileDialog.ExistingFiles)
		file_dialog.setViewMode(QtWidgets.QFileDialog.Detail)
		file_dialog.exec_()
		self.filePathList = file_dialog.selectedFiles()
	
	def radioOptions(self, optionType):
		if optionType == "fastest":
			self.ffmpegMode = "fastest"
		elif optionType == "slow":
			self.ffmpegMode = "slow"
		elif optionType == "slowest":
			self.ffmpegMode = "slowest"
		
	def checkboxToggled(self):
		if self.checkBox.isChecked():
			self.mergeAudio = "mergeAudio"
		
		else:
			self.mergeAudio = "noMergeAudio"
	
	def cancel(self):
		app.exit()
		
	def confirm(self):
		videoProgress = 0
		
		if system() == "Windows":
			trash = "NUL"
			
		elif system() == "Linux":
			trash = "/dev/null"
		
		for filePath in self.filePathList:
			if filePath:
				dirName, file = os.path.split(filePath)
				fileName, fileExtension = os.path.splitext(file)
				dirName = dirName + '/'
				outputFile = dirName + fileName + "Discord" + ".mp4"
				ffmpegCommand = ["./tools/ffmpeg", "-i", str(filePath)]
				numOfVideos = len(self.filePathList)
				
				self.startTime = self.lineEdit.text()
				self.endTime = self.lineEdit_2.text()
				print(self.startTime)
				
				# Determine bitrate based on length of video.
				videoLength = VideoFileClip(filePath).duration
				if self.startTime != "" and self.endTime == "":
					videoLength = videoLength - self.convertTimeToSeconds(self.startTime)
					ffmpegCommand.extend(["-ss", self.startTime])
					
				elif self.startTime == "" and self.endTime != "":
					videoLength = self.convertTimeToSeconds(self.endTime)
					ffmpegCommand.extend(["-to", self.endTime])
				
				elif self.startTime != "" and self.endTime != "":
					videoLength = self.convertTimeToSeconds(self.endTime) - self.convertTimeToSeconds(self.startTime)
					ffmpegCommand.extend(["-ss", self.startTime, "-to", self.endTime])
				
				bitrate = (self.targetFileSize/videoLength)-self.audioBitrate
				bitrate = int(bitrate)
				
				fileSize = os.path.getsize(filePath)
				
				videoFPS = VideoFileClip(filePath).fps
				if videoFPS > 30 and fileSize > 50000000:
					ffmpegCommand.extend(["-r", "30"])
				
				clip = VideoFileClip(filePath)
				width = clip.size[0]
				height = clip.size[1]
				if (width > 720 or height > 720) and fileSize > 100000000:
					if width > height:
						ffmpegCommand.extend(["-vf", "scale='trunc(oh*a/2)*2:720'"])
						
					else:
						ffmpegCommand.extend(["-vf", "scale='720:trunc(oh*a/2)*2'"])


					
				if self.mergeAudio == "mergeAudio":
					numAudioStreams = subprocess.run(["./tools/ffprobe", "-loglevel", "error", "-select_streams", "a", "-show_entries", "stream=codec_type", "-of", "csv=p=0", filePath], capture_output=True, text=True)
					numAudioStreams = len(numAudioStreams.stdout.strip().splitlines())
					ffmpegCommand.extend(["-filter_complex", "[0:a]amerge=inputs={}[a]".format(numAudioStreams), '-map', '[a]'])
					
				else:
					ffmpegCommand.extend(["-map", "0:a:0"])
				
				# FFmpeg commands based on user selected options.
				if self.ffmpegMode == "fastest":
					ffmpegCommand.extend(["-preset", "ultrafast", "-c:v", "libx264"])
					ffmpegCommand2 = ffmpegCommand.copy()
					
					ffmpegCommand.extend(["-pass", "1"])
					ffmpegCommand2.extend(["-pass", "2"])
					
					progressPercent = 2
					progressPercent2 = 2
					progressPercent3 = 50
					
				elif self.ffmpegMode == "slow":
					ffmpegCommand.extend(["-preset", "veryslow", "-c:v", "libx264"])
					ffmpegCommand2 = ffmpegCommand.copy()
					
					ffmpegCommand.extend(["-pass", "1"])
					ffmpegCommand2.extend(["-pass", "2"])
					
					progressPercent = 5
					progressPercent2 = (5/4)
					progressPercent3 = 20
					
				elif self.ffmpegMode == "slowest":
					ffmpegCommand.extend(["-deadline", "best", "-c:v", "libvpx-vp9", "-row-mt", "1"])
					ffmpegCommand2 = ffmpegCommand.copy()
					
					progressPercent = 2
					progressPercent2 = 2
					progressPercent3 = 50
					
					
				videoProgress += 1
				self.label.setText(str(videoProgress) + "/" + str(numOfVideos))
				ffmpegCommand.extend(["-ac", "2", "-map", "0:v", "-b:v", str(bitrate), "-b:a", str(self.audioBitrate), "-c:a", "libopus", "-f", "mp4", str(trash), "-y"])
				print(ffmpegCommand)
				ff = FfmpegProgress(ffmpegCommand)
				for progress in ff.run_command_with_progress():
					self.progressBar.setValue(int(progress / progressPercent))
					print(progress)
				
				ffmpegCommand2.extend(["-ac", "2", "-map", "0:v", "-b:v", str(bitrate), "-b:a", str(self.audioBitrate), "-c:a", "libopus", outputFile, "-y"])
				ff = FfmpegProgress(ffmpegCommand2)
				for progress in ff.run_command_with_progress():
					self.progressBar.setValue(int(progress / progressPercent2) + progressPercent3)
					print(progress)
				
if __name__ == "__main__":
	app = QtWidgets.QApplication(sys.argv)
	MainWindow = QtWidgets.QMainWindow()
	ui = ffmpeg2discord(MainWindow)
	MainWindow.show()
	sys.exit(app.exec_())
