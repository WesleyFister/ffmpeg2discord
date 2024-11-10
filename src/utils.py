from platform import system
import subprocess
import mimetypes
import json
import sys
import os



def cleanUp(logFile, audioPath, audioExists): # Delete temporary files.
    if audioExists == True:
        if os.path.exists(audioPath):
            os.remove(audioPath)

    for file in os.listdir("."):
        if os.path.isfile(os.path.join(".", file)) and logFile in file:
            os.remove(file)

def convertTimeToSeconds(timeStr):
    timeStr = timeStr.split(":")
    while len(timeStr) < 3:
        timeStr.insert(0, 0)

    totalSeconds = int(timeStr[0]) * 3600 + int(timeStr[1]) * 60 + int(timeStr[2])

    return totalSeconds

def createNoWindow(): # Passes argument to subprocess calls to not create a terminal window when running a command on Windows systems
    kwargs = {}
    
    if system() == "Windows":
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
        
    return kwargs

def mimeType(filePath):
    mimeType = mimetypes.guess_type(filePath)
    mimeType = mimeType[0]
    if mimeType == None:
        fileType = None
        fileFormat = None

    else:
        fileType, fileFormat = mimeType.split("/")

    return fileType, fileFormat

def getFileInfo(filePath, mixAudio):
    fileInfo = {}
    
    fileInfo["fileType"], fileInfo["fileFormat"] = mimeType(filePath)
    dirName, file = os.path.split(filePath)
    fileInfo["fileName"], fileInfo["fileExtension"] = os.path.splitext(file)
    fileInfo["dirName"] = dirName + "/"

    fileInfo["videoStreams"] = 0
    fileInfo["audioStreams"] = 0
    if fileInfo["fileType"] == "audio" or fileInfo["fileType"] == "video":
        videoJsonData = subprocess.check_output(["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", "-select_streams", "v", "-count_packets", filePath], **createNoWindow())
        videoJsonData = json.loads(videoJsonData)

        for stream in videoJsonData["streams"]:
            if stream["codec_type"]:
                fileInfo["videoStreams"] += 1

        if fileInfo["videoStreams"] > 0:

            fileInfo["videoLength"] = float(videoJsonData["format"]["duration"])
            fileInfo["width"] = int(videoJsonData["streams"][0]["width"])
            fileInfo["height"] = int(videoJsonData["streams"][0]["height"])
            fileInfo["numberOfVideoPackets"] = int(videoJsonData["streams"][0]["nb_read_packets"])

            numerator, denominator = map(int, videoJsonData["streams"][0]["avg_frame_rate"].split("/"))

            try:
                framerate = numerator / denominator

            except ZeroDivisionError:
                framerate = 0
                
            fileInfo["framerate"] = framerate

        audioJsonData = subprocess.check_output(["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", "-select_streams", "a", "-count_packets", filePath], **createNoWindow())
        audioJsonData = json.loads(audioJsonData)

        for stream in audioJsonData["streams"]:
            if stream["codec_type"]:
                fileInfo["audioStreams"] += 1

        if fileInfo["audioStreams"] > 0:
            fileInfo["audioChannels"] = audioJsonData["streams"][0]["channels"]
            fileInfo["audioCodec"] = audioJsonData["streams"][0]["codec_name"]
            fileInfo["audioDuration"] = float(audioJsonData["format"]["duration"])
            fileInfo["numberOfAudioPackets"] = int(audioJsonData["streams"][0]["nb_read_packets"])

            if mixAudio == True:
                streams = "a"

            else:
                streams = "a:0"

            audioJsonData = subprocess.check_output(["ffprobe", "-v", "quiet", "-print_format", "json", "-select_streams", streams, "-show_entries", "packet=size", filePath], **createNoWindow())
            audioJsonData = json.loads(audioJsonData)
            audioSize = 0
            for audioJsonData in audioJsonData["packets"]:
                audioSize += int(audioJsonData["size"])
            
            fileInfo["audioBitrate"] = int((audioSize * 8) / fileInfo["audioDuration"])

    return fileInfo

def calculateTargetFileSize(fileSize, dataUnit):
    # In bits not bytes.
    mib = 8388608
    mb = 8000000

    if fileSize == "": # If the user inputs nothing.
        fileSize = 10 # Discord Default.

    else:
        fileSize = int(fileSize)

    if dataUnit == "MiB":
        targetFileSize = fileSize * mib

    else:
        targetFileSize = fileSize * mb

    return targetFileSize