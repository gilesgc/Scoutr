from flask import (
   Flask,
   render_template,
   Response,
   session,
   redirect,
   url_for,
   request,
   flash
)
import cv2
import threading
from Crypto.Hash import SHA512
from GCCamera import GCCamera
from GCMotionDetector import GCMotionDetector
import time
from imutils.video import VideoStream
import imutils

outputframe = None
lock = threading.Lock()
motionDetector = GCMotionDetector(accumWeight=0.1)
#camera = GCCamera(32, lock)
password_hash_hex = '7ad4d51280e6e3f582ef51f1411f9852f5777ea1ddffc9192142a7872a9d159df3dd23946aee439e113e10ec49f833d452e59e847a44784f12ad71355ea3a376'


app = Flask(__name__)
app.secret_key = b'\xcd\x04=\x01e\r\x95\xf8\xa5\x9c@\x04\x85\xc2\xff\xcd'

videocapture = VideoStream(src=0).start()

time.sleep(2)

@app.route('/', methods=['GET', 'POST'])
def index():
   if request.method == 'POST':
      session.pop('logged_in', None)
      return redirect(url_for('login'))

   if 'logged_in' in session and session['logged_in'] == True:
      return render_template('index.html')
   else:
      return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
   if request.method == 'POST':
      password_plaintext = request.form['password']

      if SHA512.new(password_plaintext.encode('utf-8')).hexdigest() == password_hash_hex:
         session['logged_in'] = True
         return redirect(url_for('index'))
      else:
         flash("Wrong password.")
   
   if request.method == 'GET' and 'logged_in' in session and session['logged_in'] == True:
      return redirect(url_for('index'))

   return render_template('login.html')

def gen():
   global outputframe, lock
   while True:
      with lock:
         if outputframe is None:
            continue

         flag, encodedImage = cv2.imencode('.jpg', outputframe)

         if not flag:
            continue
      
      yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + bytearray(encodedImage) + b'\r\n')

@app.route('/video_feed')
def video_feed():
   return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')

def runInBackground():
   global outputframe, lock, videocapture
   total = 0
   motionDetector = GCMotionDetector(accumWeight=0.1)
   while True:
      frame = videocapture.read()

      gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
      gray = cv2.GaussianBlur(gray, (7, 7), 0)

      #timestamp = datetime.datetime.now()
      #cv2.putText(frame, timestamp.strftime("%A %d %B %Y %I:%M:%S%p"), (10, frame.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)

      if total > 64:
         print("DONE")
         motion = motionDetector.detect(gray)

         if motion is not None:
            (thresh, (minX, minY, maxX, maxY)) = motion
            cv2.rectangle(frame, (minX, minY), (maxX, maxY), (0, 255, 0), 2)
      
      motionDetector.update(gray)
      total += 1

      with lock:
         outputframe = frame.copy()
      
      time.sleep(0.1)


if __name__ == '__main__':
   thread = threading.Thread(target=runInBackground)
   thread.daemon = True
   thread.start()
   app.run(host='0.0.0.0', debug=True, threaded=True, use_reloader=False)
