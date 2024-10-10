from PyQt5.QtCore import QObject, QThread, pyqtSignal, pyqtSlot, QRegExp
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt5.QtGui import QRegExpValidator
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtCore import Qt
from ui import Ui_MainWindow
from encoder import encode
import subprocess
import utils
import sys
# TODO
# Fix bitrate overshoot and guarantee the video is below the size limit
# Allow multiple instances of FFmpeg2Discord by changing the name of the ffmpeg2pass-1.log
# Catch any errors with ffmpeg or ffprobe
# Add option to normalize audio
# Make the GUI scale based on monitor scaling
# Make the GUI follow dark or white themes



class ffmpeg2discord(Ui_MainWindow, QObject):
    arguments = pyqtSignal(list, str, bool, bool, str, str, int, str, str, str)
    
    def __init__(self, window):
        super().__init__()
        self.filePathList = ""
        self.ffmpegMode = "slow"
        self.mixAudio = False
        self.noAudio = False
        self.startTime = "" 
        self.endTime = ""
        
        self.encode = encode()
        self.arguments.connect(self.encode.passData)
        
        QApplication.instance().aboutToQuit.connect(self.cancel)
        
        self.window = window
        self.setupUi(self.window)
        self.label.setText("0/0")
        self.label_2.setVisible(False)
        self.label.setVisible(False)
        self.lineEdit.setValidator(QRegExpValidator(QRegExp("([0-5][0-9]):([0-5][0-9]):([0-5][0-9]).([0-9][0-9])"))) ## Only allow time in HH:MM:SS.ms. It works but it is annoying to use.
        self.lineEdit_2.setValidator(QRegExpValidator(QRegExp("([0-5][0-9]):([0-5][0-9]):([0-5][0-9]).([0-9][0-9])")))
        self.lineEdit_3.setValidator(QRegExpValidator(QRegExp("^[1-9]\\d*$"))) # Only allow positive numbers starting from 1.
        self.progressBar.setMaximum(10000) # setting maximum value for 2 decimal points
        self.progressBar.setFormat("%.02f %%" % 0)
        self.pushButton.clicked.connect(self.fileOpen)
        self.radioButton.clicked.connect(lambda: self.radioOptions("fastest"))
        self.radioButton_2.clicked.connect(lambda: self.radioOptions("slow"))
        self.radioButton_3.clicked.connect(lambda: self.radioOptions("slowest"))
        self.checkBox.stateChanged.connect(self.checkboxToggled)
        self.checkBox_2.stateChanged.connect(self.checkbox_2Toggled)
        self.buttonBox.rejected.connect(self.cancel)
        self.buttonBox.accepted.connect(self.confirm)

    @pyqtSlot(str)
    def updateLabel(self, data):
        self.label.setText(data)
        
    @pyqtSlot(list)
    def updateLabel_2(self, filePaths):
        displayFilePaths = ""
        for filePath in filePaths:
            displayFilePaths += filePath
            
        self.label_2.setText(displayFilePaths)
        
    @pyqtSlot(float)
    def updateProgressBar(self, data):
        self.progressBar.setValue(int(data * 100))
        self.progressBar.setFormat("%.02f %%" % data) 

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
            self.mixAudio = True
            self.checkBox_2.setChecked(False)
        
        else:
            self.mixAudio = False

    def checkbox_2Toggled(self):
        if self.checkBox_2.isChecked():
            self.noAudio = True
            self.checkBox.setChecked(False)

        else:
            self.noAudio = False
    
    def cancel(self):
        self.encode.stop()
        self.encode.wait()
        
    def checkForTools(self, tool):
        try:
            subprocess.check_call(["./tools/" + tool, "--help"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return "./tools/" + tool
            
        except FileNotFoundError:
            try:
                subprocess.check_call([tool, "--help"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return tool
                
            except FileNotFoundError:
                QMessageBox.warning(self.window, 'Warning', f"\"{tool}\" is not installed or not found in the system's PATH.")
                raise FileNotFoundError(f"{tool} is not installed or not found in the system's PATH.")

    def confirm(self):
        ffmpeg = self.checkForTools("ffmpeg")
        ffprobe = self.checkForTools("ffprobe")
        jpegoptim = self.checkForTools("jpegoptim")
        
        if self.filePathList:
            fileSize = self.lineEdit_3.text()
            dataUnit = self.comboBox.currentText()
            targetFileSize = utils.calculateTargetFileSize(fileSize, dataUnit)
            self.startTime = self.lineEdit.text()
            self.endTime = self.lineEdit_2.text()
            self.arguments.emit(self.filePathList, self.ffmpegMode, self.mixAudio, self.noAudio, self.startTime, self.endTime, targetFileSize, ffmpeg, ffprobe, jpegoptim)
            
            self.encode.updateLabel.connect(self.updateLabel)
            self.encode.updateLabel_2.connect(self.updateLabel_2)
            self.encode.updateProgressBar.connect(self.updateProgressBar)
            self.encode.start()
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    MainWindow = QMainWindow()
    ui = ffmpeg2discord(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
