import cv2
from collections import deque
from queue import Queue
from threading import Thread
from time import sleep
from datetime import datetime

class GCRecorder(object):
    fourcc = cv2.VideoWriter_fourcc(*"avc1")

    def __init__(self, database, settings, backlogSize=20):
        self.backlogSize = backlogSize
        self.backlogFrames = deque(maxlen=backlogSize)
        self.database = database
        self.settings = settings
        self.recordingQueue = None
        self.writer = None
        self.recording = False
        self.thread = None
        self.framesCaptured = 0
        self.lastMovementFrame = 0
        self.Clip = None

        #Find the clip class in the database object
        #kind of messy but it works...
        for clazz in database.Model._decl_class_registry.values():
            try:
                if clazz.__tablename__ == "clip":
                    self.Clip = clazz
                    break
            except:
                pass
    
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
        if self.settings.save_clips_enabled:
            shape = (self.backlogFrames[0].shape[1], self.backlogFrames[0].shape[0])
            dateFormat = "%m-%d-%Y--%I-%M-%S-%p"
            fileName = datetime.now().strftime(dateFormat)
            videoPath = f"static/clips/{fileName}.mp4"
            self.writer = cv2.VideoWriter(videoPath, GCRecorder.fourcc, 10.0, shape)
            
            for frame in self.recordingQueue.queue:
                self.writer.write(frame)
            self.writer.release()

            thumbnailFrame = self.recordingQueue.queue[int(self.recordingQueue.qsize() / 2)]
            thumbnailPath = f"static/thumbnail/{fileName}.jpg"
            cv2.imwrite(thumbnailPath, thumbnailFrame)

            videoLength = self.recordingQueue.qsize() / 10.0

            self._writeClipToDatabase(fileName, "/" + videoPath, "/" + thumbnailPath, videoLength)

            print(f" * Clip \"{fileName}.mp4\" has been saved")
            
        self.backlogFrames.clear()
        self.recordingQueue.queue.clear()
        framesCaptured = 0
        lastMovementFrame = 0

    def _writeClipToDatabase(self, name, videoPath, thumbnailPath, videoLength):
        if self.Clip is None:
            print(" * ERROR: Class object for Clip not found")
            return
        clip = self.Clip(name=name, video_path=videoPath, thumbnail_path=thumbnailPath, length=videoLength)
        self.database.session.add(clip)
        self.database.session.commit()

    def framesSinceLastMovement(self):
        return self.framesCaptured - self.lastMovementFrame


