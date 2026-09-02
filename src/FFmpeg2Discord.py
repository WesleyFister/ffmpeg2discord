import os
import subprocess
import sys

from PyQt6 import uic
from PyQt6.QtCore import QObject, QRegularExpression, QSettings, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QRegularExpressionValidator
from PyQt6.QtWidgets import QApplication, QFileDialog, QMainWindow, QMessageBox

import utils
from encoder import encode

UI_PATH = os.path.join(os.path.dirname(__file__), "FFmpeg2DiscordUI.ui")
Ui_MainWindow, _ = uic.loadUiType(UI_PATH)


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
        QApplication.instance().aboutToQuit.connect(self.saveSettings)

        self.window = window
        self.setupUi(self.window)
        self.loadSettings()
        self.label.setText("0/0")
        self.label.setVisible(True)
        self.label_2.setVisible(True)
        self.lineEdit.setValidator(
            QRegularExpressionValidator(
                QRegularExpression(
                    "^(?:([0-5]?[0-9]):)?(?:([0-5]?[0-9]):)?([0-5]?[0-9])\\.([0-9]{1,2})$"
                )
            )
        )  ## Only allow time in HH:MM:SS.ms.
        self.lineEdit_2.setValidator(
            QRegularExpressionValidator(
                QRegularExpression(
                    "^(?:([0-5]?[0-9]):)?(?:([0-5]?[0-9]):)?([0-5]?[0-9])\\.([0-9]{1,2})$"
                )
            )
        )
        self.lineEdit_3.setValidator(
            QRegularExpressionValidator(QRegularExpression("^[1-9]\\d*$"))
        )  # Only allow whole positive numbers starting from 1.
        self.progressBar.setMaximum(10000)  # setting maximum value for 2 decimal points
        self.progressBar.setFormat("%.02f %%" % 0)  # noqa: UP031
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
        self.progressBar.setFormat("%.02f %%" % data)  # noqa: UP031

    # Get list of user selected files.
    def fileOpen(self):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        file_dialog.setViewMode(QFileDialog.ViewMode.Detail)
        file_dialog.exec()
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
            subprocess.check_call(
                ["./tools/" + tool, "--help"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                **utils.createNoWindow(),
            )
            return "./tools/" + tool

        except FileNotFoundError:
            try:
                subprocess.check_call(
                    [tool, "--help"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    **utils.createNoWindow(),
                )
                return tool

            except FileNotFoundError:
                QMessageBox.warning(
                    self.window,
                    "Warning",
                    f'"{tool}" is not installed or not found in the system\'s PATH.',
                )
                raise FileNotFoundError(
                    f"{tool} is not installed or not found in the system's PATH."
                )

    def loadSettings(self):
        settings = QSettings("ffmpeg2discord", "settings")
        self.checkBox.setChecked(settings.value("mixAudio", False, type=bool))
        self.checkBox_2.setChecked(settings.value("noAudio", False, type=bool))
        self.checkBox_3.setChecked(settings.value("normalizeAudio", False, type=bool))
        self.lineEdit.setText(settings.value("startTime", "", type=str))
        self.lineEdit_2.setText(settings.value("endTime", "", type=str))
        self.lineEdit_3.setText(settings.value("fileSize", "", type=str))
        self.comboBox.setCurrentText(settings.value("dataUnit", "", type=str))
        self.comboBox_2.setCurrentText(settings.value("imageFormat", "", type=str))
        self.comboBox_3.setCurrentText(settings.value("audioFormat", "", type=str))
        self.comboBox_4.setCurrentText(settings.value("videoFormat", "", type=str))

        # Update internal state based on checkboxes
        self.mixAudio = self.checkBox.isChecked()
        self.noAudio = self.checkBox_2.isChecked()
        self.normalizezAudio = self.checkBox_3.isChecked()

    def saveSettings(self):
        settings = QSettings("ffmpeg2discord", "settings")
        settings.setValue("mixAudio", self.checkBox.isChecked())
        settings.setValue("noAudio", self.checkBox_2.isChecked())
        settings.setValue("normalizeAudio", self.checkBox_3.isChecked())
        settings.setValue("startTime", self.lineEdit.text())
        settings.setValue("endTime", self.lineEdit_2.text())
        settings.setValue("fileSize", self.lineEdit_3.text())
        settings.setValue("dataUnit", self.comboBox.currentText())
        settings.setValue("imageFormat", self.comboBox_2.currentText())
        settings.setValue("audioFormat", self.comboBox_3.currentText())
        settings.setValue("videoFormat", self.comboBox_4.currentText())

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
                "videoFormat": videoFormat,
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
    sys.exit(app.exec())
