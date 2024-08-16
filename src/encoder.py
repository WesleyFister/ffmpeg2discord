from PyQt5.QtCore import QThread, pyqtSignal, QRunnable, pyqtSlot
from ffmpeg_progress_yield import FfmpegProgress
from platform import system
import subprocess
import sys
import os



class encode(QThread):
	updateLabel = pyqtSignal(list)
	updateProgressBar = pyqtSignal(float)
	
	def __init__(self):
		super().__init__()
		
	def stop(self):
		self.stopped = True
	
	def passData(self, filePathList, ffmpegMode, mergeAudio, startTime, endTime, targetFileSize):
		self.filePathList = filePathList
		self.ffmpegMode = ffmpegMode
		self.mergeAudio = mergeAudio
		self.startTime = startTime
		self.endTime = endTime
		self.targetFileSize = targetFileSize
		
	def stop(self):
		self.running = False
		
	def cleanUp(self, filePath, audioPath, videoTrimmed):
		if os.path.exists(filePath) and videoTrimmed == True: os.remove(filePath)
		if os.path.exists(audioPath): os.remove(audioPath)
		if os.path.exists("ffmpeg2pass-0.log"): os.remove("ffmpeg2pass-0.log")
		if os.path.exists("ffmpeg2pass-0.log.mbtree"): os.remove("ffmpeg2pass-0.log.mbtree")
		if os.path.exists("ffmpeg2pass-0.log"): os.remove("ffmpeg2pass-0.log.temp")
		if os.path.exists("ffmpeg2pass-0.log.mbtree"): os.remove("ffmpeg2pass-0.log.mbtree.temp")
		
	def trimVideo(self, video, fileName, fileExtension):
		trimmedVideoFfmpegCommand = ["./tools/ffmpeg", "-i", str(video), "-c", "copy"]
		
		if self.startTime != "" and self.endTime == "":
			trimmedVideoFfmpegCommand.insert(1, "-ss")
			trimmedVideoFfmpegCommand.insert(2, self.startTime)
			
		elif self.startTime == "" and self.endTime != "":
			trimmedVideoFfmpegCommand.insert(1, "-to")
			trimmedVideoFfmpegCommand.insert(2, self.endTime)
		
		elif self.startTime != "" and self.endTime != "":
			trimmedVideoFfmpegCommand.insert(1, "-ss")
			trimmedVideoFfmpegCommand.insert(2, self.startTime)
			trimmedVideoFfmpegCommand.insert(3, "-to")
			trimmedVideoFfmpegCommand.insert(4, self.endTime)
			
		trimmedVideo = fileName + "_" + os.urandom(8).hex() + fileExtension
		trimmedVideoFfmpegCommand.extend([str(trimmedVideo), "-y"])
		subprocess.run(trimmedVideoFfmpegCommand, creationflags=subprocess.CREATE_NO_WINDOW)
		filePath = os.getcwd() + "/" + trimmedVideo
		
		return filePath
		
	def encodeAudio(self, video, videoLength, fileName):
		audioBitrate = ((self.targetFileSize / 10) / videoLength) * 0.97
		audioBitrate = int(audioBitrate)
		
		encodeAudioCommand = ["./tools/ffmpeg", "-i", str(video), "-c:a", "libopus", "-vn"]
		
		if audioBitrate > 128000:
			audioBitrate = 128000
			encodeAudioCommand.extend(["-ac", "2",])
		elif audioBitrate < 24000:
			encodeAudioCommand.extend(["-ac", "1",])
		else:
			encodeAudioCommand.extend(["-ac", "2",])
				
		encodeAudioCommand.extend(["-b:a", str(audioBitrate)]) 
			
		if self.mergeAudio == "mergeAudio":
			numAudioStreams = subprocess.run(["./tools/ffprobe", "-loglevel", "error", "-select_streams", "a", "-show_entries", "stream=codec_type", "-of", "csv=p=0", video], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
			numAudioStreams = len(numAudioStreams.stdout.strip().splitlines())
			encodeAudioCommand.extend(["-filter_complex", "[0:a]amerge=inputs={}[a]".format(numAudioStreams), '-map', '[a]'])
			
		else:
			encodeAudioCommand.extend(["-map", "0:a:0"])
			
		audio = fileName + os.urandom(8).hex() + ".opus"
		encodeAudioCommand.extend([str(audio), "-y"])
		subprocess.run(encodeAudioCommand, creationflags=subprocess.CREATE_NO_WINDOW)
		
		audioPath = os.getcwd() + "/" + audio
		
		return audioPath

	def run(self):
		videoProgress = 0
		self.running = True
		segment = ""
		
		if system() == "Windows":
			trash = "NUL"
			
		elif system() == "Linux":
			trash = "/dev/null"
		
		for filePath in self.filePathList:
			if filePath:
				videoTrimmed = False
				dirName, file = os.path.split(filePath)
				fileName, fileExtension = os.path.splitext(file)
				dirName = dirName + '/'
				ffmpegCommand = ["./tools/ffmpeg"]
				numOfVideos = len(self.filePathList)
				
				if self.startTime != "" or self.endTime != "":
					filePath = self.trimVideo(filePath, fileName, fileExtension)
					videoTrimmed = True
				
				command = ["./tools/ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", filePath]
				videoLength = float(subprocess.check_output(command, creationflags=subprocess.CREATE_NO_WINDOW))
				print("Video length:", videoLength)
				
				audioPath = self.encodeAudio(filePath, videoLength, fileName)
				ffmpegCommand.extend(["-i", str(filePath), "-i", str(audioPath)])
				
				videoBitrate = ((self.targetFileSize - (os.path.getsize(audioPath) * 8)) / videoLength) * 0.97
				videoBitrate = int(videoBitrate)
				
				fileSize = os.path.getsize(filePath)
				print("File size:", fileSize)
				
				command = ['./tools/ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height', '-of', 'csv=s=x:p=0', filePath]
				process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW)
				output, _ = process.communicate()

				# Parse the output to get width and height
				heights = [2160, 1440, 1152, 1080, 900, 720, 648, 576, 540, 360, 288, 180, 144]
				dimensions = output.decode().strip().split('x')
				currentWidth = int(dimensions[0])
				currentHeight = int(dimensions[1])
				pixelsPerSecond = videoBitrate / 0.01
				print(f"Pixels per second allowed {pixelsPerSecond}")
				
				command = ["./tools/ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate", "-of", "default=noprint_wrappers=1:nokey=1", filePath]
				output = subprocess.check_output(command, universal_newlines=True, creationflags=subprocess.CREATE_NO_WINDOW)
				fps_str = output.strip()
				numerator, denominator = map(int, fps_str.split('/'))
				videoFPS = float(numerator) / float(denominator)
				
				currentPixelsPerSecond = (currentWidth * currentHeight) * videoFPS
				
				if currentPixelsPerSecond >= (pixelsPerSecond * 4) and (videoFPS / 2) != 24:
					ffmpegCommand.extend(["-r", str(videoFPS / 2)])
				
				for testHeight in heights:
					testWidth = currentWidth * (testHeight / currentHeight)
					testPixelsPerSecond = testWidth * testHeight * videoFPS
					
					if testPixelsPerSecond <= pixelsPerSecond and testHeight < currentHeight:
						height = testHeight
						break
				
				ffmpegCommand.extend(["-vf", "scale='trunc(oh*a/2)*2:{}':flags=bicubic,format=yuv420p".format(height)])
					
				# FFmpeg commands based on user selected options.
				if self.ffmpegMode == "fastest":
					ffmpegCommand.extend(["-preset", "fast", "-aq-mode", "3", "-c:v", "libx264"])
					ffmpegCommand2 = ffmpegCommand.copy()
					
					progressPercent = 2
					progressPercent2 = 2
					progressPercent3 = 50
					
				elif self.ffmpegMode == "slow":
					ffmpegCommand.extend(["-preset", "veryslow", "-aq-mode", "3", "-c:v", "libx264"])
					ffmpegCommand2 = ffmpegCommand.copy()
					
					progressPercent = 5
					progressPercent2 = (5/4)
					progressPercent3 = 20
					
				elif self.ffmpegMode == "slowest":
					ffmpegCommand.extend(["-deadline", "best", "-c:v", "libvpx-vp9", "-tile-columns", "0", "-auto-alt-ref", "1", "-lag-in-frames", "25", "-enable-tpl", "1"])
					ffmpegCommand2 = ffmpegCommand.copy()
					
					progressPercent = 5
					progressPercent2 = (5/4)
					progressPercent3 = 20
					
				outputFile = dirName + fileName + "_FFmpeg2Discord_" + self.ffmpegMode + ".webm" # Does not actually use the webm container. Instead it uses Matroska because it is a lightweight container format taking up less space than something like MP4. Discord will not embed the video if the extension is mkv.
					
				videoProgress += 1
				self.updateLabel.emit([str(videoProgress) + "/" + str(numOfVideos), filePath])
				ffmpegCommand.extend(["-map", "0:v", "-map", "0:a:0", "-map_metadata", "-1", "-map_chapters", "-1", "-avoid_negative_ts", "make_zero", "-f", "matroska", "-b:v", str(videoBitrate), "-c:a", "copy", "-pass", "1", str(trash), "-y"])
				print(ffmpegCommand)
				ff = FfmpegProgress(ffmpegCommand)
				for progress in ff.run_command_with_progress({ "creationflags": subprocess.CREATE_NO_WINDOW }):
					if self.running != True:
						ff.quit()
						break
						
					self.updateProgressBar.emit(int(progress / progressPercent))
					print(progress)
				
				if self.running != True:
					print("Operation was canceled by user")
					self.cleanUp(filePath, audioPath, videoTrimmed)
					break
				
				ffmpegCommand2.extend(["-map", "0:v", "-map", "1:a:0", "-map_metadata", "-1", "-map_chapters", "-1", "-avoid_negative_ts", "make_zero", "-f", "matroska", "-b:v", str(videoBitrate), "-c:a", "copy", "-pass", "2", outputFile, "-y"])
				ff = FfmpegProgress(ffmpegCommand2)
				print(ffmpegCommand2)
				for progress in ff.run_command_with_progress({ "creationflags": subprocess.CREATE_NO_WINDOW }):
					if self.running != True:
						ff.quit()
						break
						
					self.updateProgressBar.emit(int(progress / progressPercent2) + progressPercent3)
					print(progress)
				
				if self.running != True:
					print("Operation was canceled by user")
					self.cleanUp(filePath, audioPath, videoTrimmed)
					break
				
				self.cleanUp(filePath, audioPath, videoTrimmed)
				
				if os.path.exists(outputFile) == True:
					outputFileSize = os.path.getsize(outputFile)
					outputFileSize = outputFileSize * 8
					if outputFileSize > self.targetFileSize:
						print(f"Compression failed for {outputFile} file is too large.")
