from PyQt5.QtCore import QObject, QThread, pyqtSignal, pyqtSlot, QRegExp
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtGui import QRegExpValidator
from PyQt5.QtWidgets import QFileDialog
from ui import Ui_MainWindow
from encoder import encode
import sys
# TODO
# Newly selected files when confirmed should be put into a queue
# Detect that the input file is infact a video
# Allow the user to input target file size in MiB and MB
# Compress audio files
# Check video codec, audio codec and original file size to see if it already complies with Discord
# Make the the file list in the GUI colored with Green for done videos, yellow for in progress ones and red for failed or non-videos
# Make the GUI scale based on monitor scaling
# Make the GUI follow dark or white themes



class ffmpeg2discord(Ui_MainWindow, QObject):	
	arguments = pyqtSignal(list, str, str, str, str, int)
	
	def __init__(self, window):
		super().__init__()
		self.filePathList = ""
		self.ffmpegMode = "slow"
		self.mergeAudio = ""
		self.startTime = "" 
		self.endTime = ""
		self.mib = 8388608
		self.targetFileSize = 25 * self.mib
		
		self.encode = encode()
		self.arguments.connect(self.encode.passData)
		
		QApplication.instance().aboutToQuit.connect(self.cancel)
		
		self.setupUi(window)
		self.label.setText("0/0")
		self.label_2.setVisible(False)
		self.label.setVisible(False)
		self.startTime = self.lineEdit.setValidator(QRegExpValidator(QRegExp("([0-5][0-9]):([0-5][0-9]):([0-5][0-9]).([0-9][0-9])")))
		self.endTime = self.lineEdit_2.setValidator(QRegExpValidator(QRegExp("([0-5][0-9]):([0-5][0-9]):([0-5][0-9]).([0-9][0-9])")))
		self.pushButton.clicked.connect(self.fileOpen)
		self.radioButton.clicked.connect(lambda: self.radioOptions("fastest"))
		self.radioButton_2.clicked.connect(lambda: self.radioOptions("slow"))
		self.radioButton_3.clicked.connect(lambda: self.radioOptions("slowest"))
		self.checkBox.stateChanged.connect(self.checkboxToggled)
		self.buttonBox.rejected.connect(self.cancel)
		self.buttonBox.accepted.connect(self.confirm)
		
	@pyqtSlot(list)
	def updateLabels(self, data):
		self.label.setText(data[0])
		self.label_2.setText(data[1])
		
	@pyqtSlot(float)
	def updateProgressBar(self, data):
		self.progressBar.setValue(int(data))
	
	def fileOpen(self):
		file_dialog = QFileDialog()
		file_dialog.setFileMode(QFileDialog.ExistingFiles)
		file_dialog.setViewMode(QFileDialog.Detail)
		file_dialog.exec_()
		self.filePathList = file_dialog.selectedFiles()
		
		videos = ""
		for video in self.filePathList:
			videos += video + "\n"
		self.label_2.setText(str(videos))
		self.label_2.setVisible(True)
		self.label.setText("0/" + str(len(self.filePathList)))
		self.label.setVisible(True)
	
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
		self.encode.stop()
		self.encode.wait()
		
	def confirm(self):
		if self.filePathList:
			self.startTime = self.lineEdit.text()
			self.endTime = self.lineEdit_2.text()
			self.arguments.emit(self.filePathList, self.ffmpegMode, self.mergeAudio, self.startTime, self.endTime, self.targetFileSize)
			self.encode.updateLabel.connect(self.updateLabels)
			self.encode.updateProgressBar.connect(self.updateProgressBar)
			self.encode.start()
		
if __name__ == "__main__":
	app = QApplication(sys.argv)
	MainWindow = QMainWindow()
	ui = ffmpeg2discord(MainWindow)
	MainWindow.show()
	sys.exit(app.exec_())
