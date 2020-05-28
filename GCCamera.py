import cv2
from GCMotionDetector import GCMotionDetector

class GCCamera(object):
    def __init__(self, frameCount, threadLock, src=0):
        self.frameCount = frameCount
        self.threadLock = threadLock
        self.videocapture = cv2.VideoCapture(src)
        self.motionDetector = GCMotionDetector(accumWeight=0.1)
        self.outputframe = None
        self.builtBackground = False

    def currentFrame(self):
        return self.outputframe

    def runInBackground(self):
        total = 0
        while True:
            rval, frame = self.videocapture.read()
            if frame is None: continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (7, 7), 0)

            #timestamp = datetime.datetime.now()
            #cv2.putText(frame, timestamp.strftime("%A %d %B %Y %I:%M:%S%p"), (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)

            if total > self.frameCount:
                if not self.builtBackground: self.builtBackground = True
                motion = self.motionDetector.detect(gray)

                if motion is not None:
                    (thresh, (minX, minY, maxX, maxY)) = motion
                    cv2.rectangle(frame, (minX, minY), (maxX, maxY), (0, 255, 0), 2)
            
            self.motionDetector.update(gray)
            total += 1

            with self.threadLock:
                self.outputframe = frame


        