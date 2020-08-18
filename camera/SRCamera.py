import cv2
from .SRMotionDetector import SRMotionDetector
from .SRRecorder import SRRecorder
import time
import logging

class SRCamera(object):
    def __init__(self, frameCount, threadLock, database, settings, src=0):
        self.frameCount = frameCount
        self.threadLock = threadLock
        self.capturesrc = src
        self.videocapture = cv2.VideoCapture(src)
        self.motionDetector = SRMotionDetector(accumWeight=0.1)
        self.recorder = SRRecorder(database, settings)
        self.settings = settings
        self.outputframe = None

        logging.basicConfig(level=logging.INFO, format='[%(module)s] %(message)s')
        self.logger = logging.getLogger(__name__)

        self.logger.info("Camera initialized.")

    def current_frame(self):
        return self.outputframe

    def start_surveillance(self):
        total = 0
        reloadingcamera = False
        while True:
            rval, frame = self.videocapture.read()
            if frame is None:
                self.logger.warning("Cannot grab the current frame. Reloading camera...")
                reloadingcamera = True
                self.videocapture = cv2.VideoCapture(self.capturesrc)
                time.sleep(2)
                continue
            elif reloadingcamera:
                self.logger.info("Found camera!")
                reloadingcamera = False

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (7, 7), 0)

            #timestamp = datetime.datetime.now()
            #cv2.putText(frame, timestamp.strftime("%A %d %B %Y %I:%M:%S%p"), (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)

            detectedMovement = False
            if total > self.frameCount:
                motion = self.motionDetector.detect(gray)

                if motion is not None:
                    detectedMovement = True
                    if self.settings.movement_box_enabled:
                        (thresh, (minX, minY, maxX, maxY)) = motion
                        cv2.rectangle(frame, (minX, minY), (maxX, maxY), (0, 255, 0), 1)

                self.recorder.addFrame(frame, detectedMovement)
            
            self.motionDetector.update(gray)
            total += 1

            with self.threadLock:
                self.outputframe = frame

            time.sleep(0.1)


        
