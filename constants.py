import os
import pathlib

FLASK_SECRET_KEY = os.environ['FLASK_SECRET_KEY']
DB_USERNAME = os.environ['DB_USERNAME']
DB_PASSWORD = os.environ['DB_PASSWORD']
DATABASE_NAME = os.environ['DATABASE_NAME']
PASSWORD_SALT = os.environ['PASSWORD_SALT']
GOOGLEAPIKEY = os.environ['GOOGLEAPIKEY']
#fernet
EVENTS_DISPLAY_KEY = os.environ['EVENTS_DISPLAY_KEY']
CURRENT_WORKING_DIRECTORY = pathlib.Path(__file__).parent.resolve()
PORT = 6738
