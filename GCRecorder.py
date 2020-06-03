import cv2
from collections import deque
from queue import Queue
from threading import Thread
from time import sleep
from datetime import datetime

class GCRecorder(object):
    fourcc = cv2.VideoWriter_fourcc(*"avc1")

    def __init__(self, backlogSize=20):
        self.backlogSize = backlogSize
        self.backlogFrames = deque(maxlen=backlogSize)
        self.recordingQueue = None
        self.writer = None
        self.recording = False
        self.thread = None
        self.framesCaptured = 0
        self.lastMovementFrame = 0
    
    def addFrame(self, frame, movement: bool):
        if self.thread is not None and self.thread.isAlive():
            return

        self.backlogFrames.append(frame)
        self.framesCaptured += 1
        if movement: self.lastMovementFrame = self.framesCaptured

        if not self.recording and movement:
            self._startRecording()
        elif self.recording and not movement and self.framesSinceLastMovement() > 10:
            self._stopRecording()
        elif self.recording:
            self.recordingQueue.put(frame)

    def _startRecording(self):
        self.recording = True
        self.recordingQueue = Queue()
        for frame in self.backlogFrames:
            self.recordingQueue.put(frame)

    def _stopRecording(self):
        self.recording = False
        self.thread = Thread(target=self._saveVideo)
        self.thread.setDaemon(True)
        self.thread.start()

    def _saveVideo(self):
        shape = (self.backlogFrames[0].shape[1], self.backlogFrames[0].shape[0])
        dateFormat = "%m-%d-%Y--%I-%M-%S-%p"
        fileName = datetime.now().strftime(dateFormat)
        self.writer = cv2.VideoWriter(f"static/clips/{fileName}.mp4", GCRecorder.fourcc, 10.0, shape)
        for frame in self.recordingQueue.queue:
            self.writer.write(frame)
        self.writer.release()
        print(f" * Clip \"{fileName}.mp4\" has been saved")
        self.backlogFrames.clear()

    def framesSinceLastMovement(self):
        return self.framesCaptured - self.lastMovementFrame


