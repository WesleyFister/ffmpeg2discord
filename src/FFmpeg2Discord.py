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



class ffmpeg2discord(Ui_MainWindow, QObject):
    arguments = pyqtSignal(dict)

    def __init__(self, window):
        super().__init__()
        self.filePathList = ""
        self.mixAudio = False
        self.noAudio = False
        self.normalizezAudio = False
        self.startTime = "" 
        self.endTime = ""
        
        self.encode = encode()
        self.arguments.connect(self.encode.passData)
        
        QApplication.instance().aboutToQuit.connect(self.cancel)
        
        self.window = window
        self.setupUi(self.window)
        self.label.setText("0/0")
        self.label.setVisible(True)
        self.label_2.setVisible(True)
        self.lineEdit.setValidator(QRegExpValidator(QRegExp("([0-5][0-9]):([0-5][0-9]):([0-5][0-9]).([0-9][0-9])"))) ## Only allow time in HH:MM:SS.ms. It works but it is annoying to use.
        self.lineEdit_2.setValidator(QRegExpValidator(QRegExp("([0-5][0-9]):([0-5][0-9]):([0-5][0-9]).([0-9][0-9])")))
        self.lineEdit_3.setValidator(QRegExpValidator(QRegExp("^[1-9]\\d*$"))) # Only allow whole positive numbers starting from 1.
        self.progressBar.setMaximum(10000) # setting maximum value for 2 decimal points
        self.progressBar.setFormat("%.02f %%" % 0)
        self.pushButton.clicked.connect(self.fileOpen)
        self.checkBox.stateChanged.connect(self.checkboxToggled)
        self.checkBox_2.stateChanged.connect(self.checkbox_2Toggled)
        self.checkBox_3.stateChanged.connect(self.checkbox_3Toggled)
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

    @pyqtSlot(str)
    def updateLabel_6(self, data):
        self.label_6.setText(data)
        
    @pyqtSlot(float)
    def updateProgressBar(self, data):
        self.progressBar.setValue(int(data * 100))
        self.progressBar.setFormat("%.02f %%" % data) 

    # Get list of user selected files.
    def fileOpen(self):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_dialog.setViewMode(QFileDialog.Detail)
        file_dialog.exec_()
        self.filePathList = file_dialog.selectedFiles()
        
        # Display selected files in GUI.
        videos = ""
        for video in self.filePathList:
            videos += video + "\n"
        self.label_2.setText(str(videos))
        self.label_2.setVisible(True)
        self.label.setText("0/" + str(len(self.filePathList)))
        self.label.setVisible(True)

    # Mix audio.
    def checkboxToggled(self):
        if self.checkBox.isChecked():
            self.mixAudio = True
            self.checkBox_2.setChecked(False)
        
        else:
            self.mixAudio = False

    # Remove audio.
    def checkbox_2Toggled(self):
        if self.checkBox_2.isChecked():
            self.noAudio = True
            self.checkBox.setChecked(False)
            self.checkBox_3.setChecked(False)

        else:
            self.noAudio = False

    # Normalize audio.
    def checkbox_3Toggled(self):
        if self.checkBox_3.isChecked():
            self.normalizezAudio = True
            self.checkBox_2.setChecked(False)

        else:
            self.normalizezAudio = False
    
    def cancel(self):
        self.encode.stop()
        self.encode.wait()

    # Check that the program is in the "tools" directory or installed on the system's path.
    def checkForTools(self, tool):
        try:
            subprocess.check_call(["./tools/" + tool, "--help"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return "./tools/" + tool
            
        except FileNotFoundError:
            try:
                subprocess.check_call([tool, "--help"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return tool
                
            except FileNotFoundError:
                QMessageBox.warning(self.window, "Warning", f"\"{tool}\" is not installed or not found in the system's PATH.")
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
            imageFormat = self.comboBox_2.currentText()
            audioFormat = self.comboBox_3.currentText()
            videoFormat = self.comboBox_4.currentText()
            args = {
                "filePathList": self.filePathList,
                "mixAudio": self.mixAudio,
                "noAudio": self.noAudio,
                "normalizezAudio": self.normalizezAudio,
                "startTime": self.startTime,
                "endTime": self.endTime,
                "targetFileSize": targetFileSize,
                "ffmpeg": ffmpeg,
                "ffprobe": ffprobe,
                "jpegoptim": jpegoptim,
                "imageFormat": imageFormat,
                "audioFormat": audioFormat,
                "videoFormat": videoFormat
            }
            self.arguments.emit(args)
            
            # Connect methods for the encode class to use.
            self.encode.updateLabel.connect(self.updateLabel)
            self.encode.updateLabel_2.connect(self.updateLabel_2)
            self.encode.updateLabel_6.connect(self.updateLabel_6)
            self.encode.updateProgressBar.connect(self.updateProgressBar)
            
            # Start the run method in the encode class.
            self.encode.start()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    MainWindow = QMainWindow()
    ui = ffmpeg2discord(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())