from flask import (
   Flask,
   render_template,
   Response,
   session,
   redirect,
   url_for,
   request
)
import cv2
from Crypto.Hash import SHA512

app = Flask(__name__)
app.secret_key = 'grant_is_epic'

vc = cv2.VideoCapture(0)
password_hash_hex = '7ad4d51280e6e3f582ef51f1411f9852f5777ea1ddffc9192142a7872a9d159df3dd23946aee439e113e10ec49f833d452e59e847a44784f12ad71355ea3a376'

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
   
   if request.method == 'GET' and 'logged_in' in session and session['logged_in'] == True:
      return redirect(url_for('index'))

   return render_template('login.html')

def gen():
   while True:
       rval, frame = vc.read()
       byteArray = cv2.imencode('.jpg', frame)[1].tobytes()
       yield (b'--frame\r\n'
              b'Content-Type: image/jpeg\r\n\r\n' + byteArray + b'\r\n')

@app.route('/video_feed')
def video_feed():
   return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
	app.run(host='0.0.0.0', debug=True, threaded=True)
