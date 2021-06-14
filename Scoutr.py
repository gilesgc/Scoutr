if __name__ == "__main__":
   print("  ________________________  ")
   print(" |   WELCOME TO SCOUTR!   | ")
   print(" |        LOADING...      | ")
   print(" |________________________| ")
   print("                            ")

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
from camera.SRCamera import SRCamera
from camera.SRSettingsManager import SRSettingsManager
import time
from datetime import datetime
import timeago
import os
import json

settings = SRSettingsManager()

password_hash_hex = settings.password_hash
password_salt = settings.password_salt

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

   def jsonData(self):
      return {
         "id" : self.id,
         "name" : self.name,
         "video_path" : self.video_path,
         "thumbnail_path" : self.thumbnail_path,
         "length_formatted" : self.formatLength(),
         "time_ago" : self.timeAgo()
      }

lock = threading.Lock()
camera = SRCamera(64, lock, db, settings, Clip)

@app.route('/', methods=['GET', 'POST'])
def index():
   if request.method == 'POST':
      session.pop('logged_in', None)
      return redirect(url_for('login'))

   if isLoggedIn():
      return render_template('index.html', settings=settings)
   else:
      return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
   if request.method == 'POST':
      password_plaintext = request.form['password']

      if SHA512.new((password_plaintext + password_salt).encode('utf-8')).hexdigest() == password_hash_hex:
         session['logged_in'] = True
         return redirect(url_for('index'))
      else:
         print(" * Someone entered the wrong password")
         flash("Wrong password.")
   
   if request.method == 'GET' and isLoggedIn():
      return redirect(url_for('index'))

   return render_template('login.html')

def gen():
   while True:
      with lock:
         outputframe = camera.current_frame()
         if outputframe is None:
            continue

         flag, encodedImage = cv2.imencode('.jpg', outputframe)

         if not flag:
            continue
      
      yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + bytearray(encodedImage) + b'\r\n'

      time.sleep(0.1)

@app.route('/video_feed')
def video_feed():
   if isLoggedIn():
      return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')
   else:
      return redirect(url_for('index'))

@app.route('/clips')
def clips():
   if not isLoggedIn():
      return redirect(url_for('index'))

   clips = Clip.query.all()
   return render_template('clips.html', clips=clips_for_page(1))

@app.route('/delete_clip', methods=['POST'])
def delete_clip():
   if not isLoggedIn():
      return "Insufficient privileges.", 403

   if request.form.get('clip_id') is None:
      return "Missing the clip_id form data", 400

   try:
      clip_id = int(request.form.get('clip_id'))
   except:
      return "'clip_id' form data must be an integer.", 400

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
   if not isLoggedIn():
      return "Insufficient privileges.", 403

   if request.form.get('clip_id') is None or request.form.get('name') is None:
      return "Missing required form data", 400
   
   try:
      clip_id = int(request.form.get('clip_id'))
   except:
      return "'clip_id' form data must be an integer.", 400

   clip = Clip.query.filter_by(id=clip_id).first()
   if clip is None:
      return "No clip with that id found.", 400
   
   new_name = str(request.form.get('name'))

   clip.name = new_name
   db.session.commit()

   return "Success.", 200

@app.route('/update_settings', methods=['POST'])
def update_settings():
   if not isLoggedIn():
      return "Insufficient privileges.", 403

   for setting_key, setting_value in request.form.items():
      if hasattr(settings, setting_key):
         setattr(settings, setting_key, setting_value)

   return "Success.", 200

@app.route('/clips/page', methods=['POST'])
def page():
   if not isLoggedIn():
      return "Insufficient privileges.", 403

   if request.form.get('page') is None:
      return "Missing required form data", 400
   
   try:
      page_number = int(request.form.get('page'))
   except:
      return "'page' form data must be an integer.", 400

   clips = [clip.jsonData() for clip in clips_for_page(page_number)]
   return json.dumps(clips)

@app.route('/clips/search', methods=['POST'])
def search():
   if not isLoggedIn():
      return "Insufficient privileges.", 403
   
   if request.form.get('query') is None:
      return "Missing required form data", 400
   
   query = str(request.form.get('query'))
   clips = Clip.query.filter(Clip.name.contains(query))
   
   return json.dumps([clip.jsonData() for clip in clips])

def clips_for_page(page: int):
   clips_per_page = 20
   all_clips = Clip.query.all()[::-1]
   page = max(1, page)
   return all_clips[clips_per_page * (page - 1) : clips_per_page * page]

def isLoggedIn():
   return 'logged_in' in session and session['logged_in'] == True

def generate_password_hash(password_plaintext):
   from random import choice
   ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
   salt = ''.join(choice(ALPHABET) for i in range(16))
   salted = password_plaintext + salt
   pwhash = SHA512.new(salted.encode('utf-8')).hexdigest()
   print(f"\nYour password salt is:\n{salt}")
   print(f"\nYour password hash is:\n{pwhash}")
   print("\nPaste these values into their respective places in ./settings/settings.ini\n")

if __name__ == '__main__':
   thread = threading.Thread(target=SRCamera.start_surveillance, args=(camera,))
   thread.setDaemon(True)
   thread.start()
   app.run(host='0.0.0.0', port=5000, debug=False, threaded=True, use_reloader=False)
