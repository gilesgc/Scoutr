# Scoutr
Scoutr is lightweight webserver made using Python and Flask that can turn any USB camera into a security camera.

## Features
- View your live camera feed from anywhere
- Password protected webpages
- Save clips when movement is detected
- Customize clip requirements such as minimum length
- View, rename, delete, and search through saved clips with the web interface

## Dependencies
- Flask
- Flask SQLAlchemy
- opencv-python
- pycryptodome
- timeago
- numpy
- imutils

## How to use
Once you have installed the dependencies and cloned the project, go into the database folder and run remake.bat to create an empty database.
<br>
Or if on Unix, run in shell:
```
python -c "from Scoutr import db; db.create_all();"
```
<br>
If you are on Unix, you will need the openh264 1.8.0 for your system from here: https://github.com/cisco/openh264/releases/tag/v1.8.0
<br>
Extract the file into the main Scoutr directory and do not rename it.
<br>
<br>
Next, you will need to generate a password. In the main Scoutr directory, open a python shell and run:

```
import Scoutr
Scoutr.generate_password_hash("your_password_plaintext")
```
The function will generate your hash and salt, which you should copy and paste into their respective places in settings/settings.ini
<br>
<br>
Finally, to run the webserver, simply open Scoutr.py and navigate to localhost:5000 in your browser. The password you should enter is the one that you set earlier.
