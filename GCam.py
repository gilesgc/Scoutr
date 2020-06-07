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
from flask_sqlalchemy import SQLAlchemy
import cv2
import threading
from Crypto.Hash import SHA512
from camera.GCCamera import GCCamera
import time
from datetime import datetime
import timeago
import os

password_hash_hex = '7ad4d51280e6e3f582ef51f1411f9852f5777ea1ddffc9192142a7872a9d159df3dd23946aee439e113e10ec49f833d452e59e847a44784f12ad71355ea3a376'

app = Flask(__name__)
app.secret_key = b'\xcd\x04=\x01e\r\x95\xf8\xa5\x9c@\x04\x85\xc2\xff\xcd'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database/db.sqlite3'

db = SQLAlchemy(app)

class Clip(db.Model):
   id = db.Column(db.Integer, primary_key=True)
   name = db.Column(db.String(100))
   video_path = db.Column(db.String(50))
   thumbnail_path = db.Column(db.String(50))
   date_created = db.Column(db.DateTime, default=datetime.now)
   length = db.Column(db.Integer)

   def timeAgo(self):
      return timeago.format(self.date_created, datetime.now())

   def formatLength(self):
      return str(int(self.length // 60)) + ":" + str(int(self.length % 60)).zfill(2)

lock = threading.Lock()
camera = GCCamera(64, lock, db)

time.sleep(2)

@app.route('/', methods=['GET', 'POST'])
def index():
   if request.method == 'POST':
      session.pop('logged_in', None)
      return redirect(url_for('login'))

   if isLoggedIn():
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
   
   if request.method == 'GET' and isLoggedIn():
      return redirect(url_for('index'))

   return render_template('login.html')

def gen():
   while True:
      with lock:
         outputframe = camera.currentFrame()
         if outputframe is None:
            continue

         flag, encodedImage = cv2.imencode('.jpg', outputframe)

         if not flag:
            continue
      
      yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + bytearray(encodedImage) + b'\r\n')

      time.sleep(0.1)

@app.route('/video_feed')
def video_feed():
   if isLoggedIn():
      return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')
   else:
      return redirect(url_for('index'))

@app.route('/latest_clip')
def latest_clip():
   import glob
   import os
   list_of_files = glob.glob('static/clips/*')
   latest_file = max(list_of_files, key=os.path.getctime)
   return render_template('latest_clip.html', url=url_for('static', filename=("clips/" + os.path.basename(latest_file))))

@app.route('/clips')
def clips():
   clips = Clip.query.all()
   return render_template('clips.html', clips=clips)

@app.route('/view_clip')
def view_clip():
   if request.args.get('clip_id') is None:
      return "You did something wrong!!!"
   
   clip = Clip.query.filter_by(id=int(request.args['clip_id'])).first()
   return render_template('view_clip.html', clip=clip)

@app.route('/delete_clip', methods=['POST'])
def delete_clip():
   if request.form.get('clip_id') is None:
      return "Missing the clip_id form data", 400

   clip_id = int(request.form.get('clip_id'))
   clip = Clip.query.filter_by(id=clip_id).first()
   if clip is None:
      return "No clip with that id found.", 400

   try:
      os.remove(clip.video_path[1:])
      os.remove(clip.thumbnail_path[1:])
   except Exception as e:
      print(" * Error when deleting local copy of clip\n" + str(e))

   db.session.delete(clip)
   db.session.commit()

   return "Success.", 200

@app.route('/rename_clip', methods=['POST'])
def rename_clip():
   if request.form.get('clip_id') is None or request.form.get('name') is None:
      return "Missing required form data", 400
   
   clip_id = int(request.form.get('clip_id'))
   clip = Clip.query.filter_by(id=clip_id).first()
   if clip is None:
      return "No clip with that id found.", 400
   
   new_name = request.form.get('name')

   clip.name = new_name
   db.session.commit()

   return "Success.", 200

def isLoggedIn():
   return 'logged_in' in session and session['logged_in'] == True

if __name__ == '__main__':
   thread = threading.Thread(target=GCCamera.runInBackground, args=(camera,))
   thread.setDaemon(True)
   thread.start()
   app.run(host='0.0.0.0', port=5000, debug=True, threaded=True, use_reloader=False)