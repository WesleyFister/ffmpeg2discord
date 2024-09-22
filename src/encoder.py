from PyQt5.QtCore import QThread, pyqtSignal, QRunnable, pyqtSlot
from ffmpeg_progress_yield import FfmpegProgress
from platform import system
import subprocess
import mimetypes
import shutil
import json
import sys
import os



class encode(QThread):
	updateLabel = pyqtSignal(str)
	updateLabel_2 = pyqtSignal(list)
	updateProgressBar = pyqtSignal(float)
	
	def __init__(self):
		super().__init__()
		self.ffmpeg = self.checkForTools("ffmpeg")
		self.ffprobe = self.checkForTools("ffprobe")
		self.jpegoptim = self.checkForTools("jpegoptim")
	
	def passData(self, filePathList, ffmpegMode, mixAudio, noAudio, startTime, endTime, targetFileSize):
		self.filePathList = filePathList
		self.ffmpegMode = ffmpegMode
		self.mixAudio = mixAudio
		self.noAudio = noAudio
		self.startTime = startTime
		self.endTime = endTime
		self.targetFileSize = targetFileSize
		
	def stop(self):
		self.running = False
		
	def cleanUp(self, filePath, audioPath, videoTrimmed): # Delete temporary files.
		if os.path.exists(filePath) and videoTrimmed == True:
			os.remove(filePath)
			
		if os.path.exists(audioPath):
			os.remove(audioPath)
			
		if os.path.exists("ffmpeg2pass-0.log"):
			os.remove("ffmpeg2pass-0.log")
			
		if os.path.exists("ffmpeg2pass-0.log.mbtree"):
			os.remove("ffmpeg2pass-0.log.mbtree")
			
		if os.path.exists("ffmpeg2pass-0.log.temp"):
			os.remove("ffmpeg2pass-0.log.temp")
			
		if os.path.exists("ffmpeg2pass-0.log.mbtree.temp"):
			os.remove("ffmpeg2pass-0.log.mbtree.temp")
		
	def trimVideo(self, video, fileName, fileExtension):
		trimmedVideoFfmpegCommand = [self.ffmpeg, "-i", str(video), "-c", "copy"]
		
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
		subprocess.run(trimmedVideoFfmpegCommand, **self.createNoWindow())
		filePath = os.getcwd() + "/" + trimmedVideo
		
		return filePath
		
	def encodeAudio(self, video, videoLength, fileName):
		audioBitrate = ((self.targetFileSize / 10) / videoLength) * 0.97
		audioBitrate = int(audioBitrate)
		
		encodeAudioCommand = [self.ffmpeg, "-i", str(video), "-c:a", "libopus", "-vn"]
		
		if audioBitrate > 128000: # 128kbps Opus audio is considered transparent by many
			audioBitrate = 128000
			encodeAudioCommand.extend(["-ac", "2",])

		elif audioBitrate < 24000: # 24kbps is arbitrary
			encodeAudioCommand.extend(["-ac", "1",])

			if audioBitrate < 10000: # Opus quality degrades consideribly at 5kbps
				audioBitrate = 10000

		else:
			encodeAudioCommand.extend(["-ac", "2",])
				
		encodeAudioCommand.extend(["-b:a", str(audioBitrate)]) 
			
		if self.mixAudio == True:
			numAudioStreams = subprocess.run([self.ffprobe, "-loglevel", "error", "-select_streams", "a", "-show_entries", "stream=codec_type", "-of", "csv=p=0", video], **self.createNoWindow(), capture_output=True, text=True)
			numAudioStreams = len(numAudioStreams.stdout.strip().splitlines())
			encodeAudioCommand.extend(["-filter_complex", "[0:a]amerge=inputs={}[a]".format(numAudioStreams), '-map', '[a]'])
			
		else:
			encodeAudioCommand.extend(["-map", "0:a:0"])
			
		audio = fileName + os.urandom(8).hex() + ".mka" # Since the video container is Matroska the audio file should also use the same container format to get an accurate idea on the file size. This is because Matroska has a higher muxing overhead for audio than something like Opus.
		encodeAudioCommand.extend([str(audio), "-y"])
		subprocess.run(encodeAudioCommand, **self.createNoWindow())
		
		audioPath = os.getcwd() + "/" + audio
		
		return audioPath

	def createNoWindow(self): # Passes argument to subprocess calls to not create a terminal window when running a command on Windows systems
		kwargs = {}
		
		if system() == "Windows":
			kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
			
		return kwargs

	def checkForTools(self, tool):
		try:
			subprocess.check_call(["./tools/" + tool, "--help"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
			return "./tools/" + tool
			
		except FileNotFoundError:
			try:
				subprocess.check_call([tool, "--help"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
				return tool
				
			except FileNotFoundError:
				print(f"{tool} is not installed or not found in the system's PATH.") #TODO Make a popup letting the user know that the tools were not found.

	def mimeType(self, filePath):
		mimeType = mimetypes.guess_type(filePath)
		mimeType = mimeType[0]
		if mimeType == None:
			fileType = None
			fileFormat = None

		else:
			fileType, fileFormat = mimeType.split('/')

		return fileType, fileFormat

	def getFileInfo(self, filePath):
		json_object = subprocess.check_output(["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", filePath])
		json_object = json.loads(json_object)

		return json_object

	def run(self):
		videoProgress = 0
		self.running = True
		segment = ""
		displayFilePathList = []
		
		for displayFile in self.filePathList:
			displayFilePathList.extend([displayFile + '<br>'])
		
		for filePath in self.filePathList:
			if filePath:
				dirName, file = os.path.split(filePath)
				fileName, fileExtension = os.path.splitext(file)
				dirName = dirName + '/'

				# Update GUI.
				numOfVideos = len(self.filePathList)
				displayFilePath = filePath
				currentIndex = self.filePathList.index(filePath)
				displayFilePathList[currentIndex] = '<font color="orange">' + displayFilePath + '</font><br>'
				videoProgress += 1
				self.updateLabel.emit(str(videoProgress) + "/" + str(numOfVideos))
				self.updateLabel_2.emit(displayFilePathList)
				self.updateProgressBar.emit(0.00)

				fileType, fileFormat = self.mimeType(filePath)

				if fileType == "image" or fileType == "audio" or fileType == "video":
					fileInfo = getFileInfo(filePath)

					if fileType == "image": #TODO Allow the user to cancel.
						tempFilePath = os.getcwd() + "/" + fileName + fileExtension
						if self.ffmpegMode == "fastest":
							compression_level = 0

						elif self.ffmpegMode == "slow":
							compression_level = 4

						elif self.ffmpegMode == "slowest":
							compression_level = 6

						if fileFormat == "jpeg":
							shutil.copy(filePath, tempFilePath) # jpegoptim is unable to change the output file name so shutil must handle it.
							outputFile = dirName + fileName + "_FFmpeg2Discord_Lossless.jpg"
							subprocess.run([self.jpegoptim, "--strip-all", tempFilePath], **self.createNoWindow())

						elif fileFormat != "jpeg":
							outputFile = dirName + fileName + "_FFmpeg2Discord_Lossless.webp"
							subprocess.run([self.ffmpeg, "-i", filePath, "-map_metadata", "-1", "-compression_level", str(compression_level), "-c:v", "libwebp_anim", "-lossless", "1", tempFilePath, "-y"], **self.createNoWindow())

						if (os.path.getsize(tempFilePath) * 8) > self.targetFileSize:
							outputFile = dirName + fileName + "_FFmpeg2Discord.webp"
							high = 100
							middle = high / 2
							low = 0
							while True: # Used binary search to find optimial quality value. Not ideal but couldn't find a better way.
								if self.running == False:
									break

								print(f"Quality set to {middle}")
								previousMiddle = middle

								subprocess.run([self.ffmpeg, "-i", filePath, "-map_metadata", "-1", "-compression_level", str(compression_level), "-c:v", "libwebp_anim", "-quality", str(middle), tempFilePath, "-y"], **self.createNoWindow())

								tempFileSize = os.path.getsize(tempFilePath) * 8
								if tempFileSize > self.targetFileSize:
									high = middle - 1

								else:
									low = middle + 1

								middle = (high + low) // 2

								if previousMiddle == middle: # The binary search will converge on the optimal quality value after seven iterations. Once this happens the next middle value will be the same as the one before it.
									break

						if self.running == True:
							shutil.move(tempFilePath, outputFile)
	
							displayFilePathList[currentIndex] = '<font color="green">' + displayFilePath + '</font><br>'
							self.updateLabel_2.emit(displayFilePathList)

					if fileType == "audio":
						print("TODO")

					if fileType == "video":
						videoTrimmed = False
						ffmpegCommand = [self.ffmpeg]

						#TODO Create a function to get video data such as FPS, resolution and number of audio tracks.

						if self.startTime != "" or self.endTime != "":
							filePath = self.trimVideo(filePath, fileName, fileExtension)
							videoTrimmed = True

						command = [self.ffprobe, "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", filePath]
						videoLength = float(subprocess.check_output(command, **self.createNoWindow()))
						print("Video length:", videoLength)

						ffmpegCommand.extend(["-i", str(filePath)])

						if self.noAudio == True: # TODO Check if the file has audio as well
							videoBitrate = (self.targetFileSize / videoLength) * 0.97
							videoBitrate = int(videoBitrate)

							ffmpegCommand.extend(["-an"])

						else:
							audioPath = self.encodeAudio(filePath, videoLength, fileName)

							videoBitrate = ((self.targetFileSize - (os.path.getsize(audioPath) * 8)) / videoLength) * 0.97
							videoBitrate = int(videoBitrate)

							ffmpegCommand.extend(["-i", str(audioPath), "-map", "1:a:0", "-c:a", "copy"])

						fileSize = os.path.getsize(filePath)
						print("File size:", fileSize)

						command = [self.ffprobe, '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height', '-of', 'csv=s=x:p=0', filePath]
						process = subprocess.Popen(command, **self.createNoWindow(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
						output, _ = process.communicate()

						# Parse the output to get width and height
						heights = [2160, 2088, 2016, 1944, 1872, 1800, 1728, 1656, 1584, 1512, 1440, 1368, 1296, 1224, 1152, 1080, 1008, 936, 864, 792, 720, 648, 576, 504, 432, 360, 288, 144, 72] # Divisible by 8 16:9 resolutions
						dimensions = output.decode().strip().split('x')
						currentWidth = int(dimensions[0])
						currentHeight = int(dimensions[1])
						bitPerPixel = 0.02 # 0.02 is arbitrary
						pixelsPerSecond = videoBitrate / bitPerPixel
						print(f"Pixels per second allowed {pixelsPerSecond}")

						command = [self.ffprobe, "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate", "-of", "default=noprint_wrappers=1:nokey=1", filePath]
						output = subprocess.check_output(command, **self.createNoWindow(), universal_newlines=True)
						fps_str = output.strip()
						numerator, denominator = map(int, fps_str.split('/'))
						videoFPS = float(numerator) / float(denominator)

						currentPixelsPerSecond = (currentWidth * currentHeight) * videoFPS

						if currentPixelsPerSecond <= pixelsPerSecond:
							height = currentHeight

						elif currentPixelsPerSecond > pixelsPerSecond:
							if currentPixelsPerSecond >= (pixelsPerSecond * 4) and (videoFPS / 2) != 24: # 4 is arbitrary
								ffmpegCommand.extend(["-r", str(videoFPS / 2)])

							for testHeight in heights:
								testWidth = currentWidth * (testHeight / currentHeight)
								testPixelsPerSecond = testWidth * testHeight * videoFPS

								if testPixelsPerSecond <= pixelsPerSecond and testHeight < currentHeight:
									height = testHeight
									break

						'''
						if videoLength <= 30:
							filePathBlank =  os.getcwd() + "/" + "blank.mkv"

							command = [self.ffmpeg, "-f", "lavfi", "-i", "color=c=black:s=1920x1080:r=60:d=30", "-c:v", "libx264", filePathBlank, "-y"]
							subprocess.check_output(command, **self.createNoWindow())

							filePathBlankMerged =  os.getcwd() + "/" + fileName + "blank.mkv"

							command = [self.ffmpeg, "-i", filePath, "-i", filePathBlank, "-filter_complex", "concat=n=2:v=1:a=0", "-c:v", "libx264", filePathBlankMerged, "-y"]
							subprocess.check_output(command, **self.createNoWindow())

							filePath = filePathBlankMerged
						'''

						ffmpegCommand.extend(["-vf", "scale='trunc(oh*a/2)*2:{}':flags=bicubic,format=yuv420p".format(height)])

						# FFmpeg commands based on user selected options.
						if self.ffmpegMode == "fastest":
							ffmpegCommand.extend(["-preset", "veryfast", "-aq-mode", "3", "-c:v", "libx264"])
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

						outputFile = dirName + fileName + "_FFmpeg2Discord_" + self.ffmpegMode + ".webm" # Does not actually use the WebM container. Instead it uses Matroska because it is a lightweight container format taking up less space than something like MP4. Discord will not embed the video if the extension is mkv.

						ffmpegCommand.extend(["-map", "0:v", "-map_metadata", "-1", "-map_chapters", "-1", "-avoid_negative_ts", "make_zero", "-b:v", str(videoBitrate), "-pass", "1", "-f", "null", "-", "-y"])
						print(ffmpegCommand)
						ff = FfmpegProgress(ffmpegCommand)
						for progress in ff.run_command_with_progress(**self.createNoWindow()):
							if self.running == False:
								ff.quit()
								break

							self.updateProgressBar.emit(progress / progressPercent)
							print(f"Pass 1: {progress}/100, end=\r)

						if self.running == False:
							print("Operation was canceled by user")
							self.cleanUp(filePath, audioPath, videoTrimmed)
							break

						ffmpegCommand2.extend(["-map", "0:v", "-map_metadata", "-1", "-map_chapters", "-1", "-avoid_negative_ts", "make_zero", "-b:v", str(videoBitrate), "-pass", "2", "-f", "matroska", outputFile, "-y"])
						ff = FfmpegProgress(ffmpegCommand2)
						print(ffmpegCommand2)
						for progress in ff.run_command_with_progress(**self.createNoWindow()):
							if self.running == False:
								ff.quit()
								break

							self.updateProgressBar.emit((progress / progressPercent2) + progressPercent3)
							print(f"Pass 2: {progress}/100, end=\r)

						if self.running == False:
							print("Operation was canceled by user")
							self.cleanUp(filePath, audioPath, videoTrimmed)
							break

						self.cleanUp(filePath, audioPath, videoTrimmed)

						if os.path.exists(outputFile) == True:
							outputFileSize = os.path.getsize(outputFile)
							outputFileSize = outputFileSize * 8
							if outputFileSize > self.targetFileSize:
								displayFilePathList[currentIndex] = '<font color="red">' + displayFilePath + '</font><br>'
								self.updateLabel_2.emit(displayFilePathList)
								print(f"Compression failed for {outputFile} file is too large.")

							else:
								displayFilePathList[currentIndex] = '<font color="green">' + displayFilePath + '</font><br>'
								self.updateLabel_2.emit(displayFilePathList)
