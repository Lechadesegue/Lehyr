from datetime import datetime, timedelta
import secrets

from flask import Flask, render_template, redirect, url_for, session, request, jsonify, abort
from authlib.integrations.flask_client import OAuth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials

from models import db, User, Record, Entry

class Config:
    SECRET_KEY = 'dev-secret'  # en Render usar variable FLASK_SECRET_KEY
    SQLALCHEMY_DATABASE_URI = 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    GOOGLE_CLIENT_ID = ''
    GOOGLE_CLIENT_SECRET = ''
    SHEET_NAME = 'Registros y horarios (read only)'

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
with app.app_context():
    try:
        db.engine.execute('ALTER TABLE user ADD COLUMN sheet_id TEXT')
    except Exception:
        pass
    db.create_all()

oauth = OAuth(app)
oauth.register(
    name='google',
    client_id=app.config['GOOGLE_CLIENT_ID'],
    client_secret=app.config['GOOGLE_CLIENT_SECRET'],
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    authorize_params={'access_type': 'offline', 'prompt': 'consent'},
    client_kwargs={'scope': ('openid email profile '
                             'https://www.googleapis.com/auth/drive.file '
                             'https://www.googleapis.com/auth/spreadsheets')}
)

def get_credentials(user):
    return Credentials(None,
                       refresh_token=user.refresh_token,
                       client_id=app.config['GOOGLE_CLIENT_ID'],
                       client_secret=app.config['GOOGLE_CLIENT_SECRET'],
                       token_uri='https://oauth2.googleapis.com/token')

HEADERS = [['Registro', 'Fecha', 'Inicio', 'Duración']]

def ensure_sheet(user):
    creds = get_credentials(user)
    service = build('sheets', 'v4', credentials=creds)
    if user.sheet_id:
        try:
            if not service.spreadsheets().values().get(
                    spreadsheetId=user.sheet_id, range='A1:D1').execute().get('values'):
                service.spreadsheets().values().update(
                    spreadsheetId=user.sheet_id, range='A1',
                    valueInputOption='RAW', body={'values': HEADERS}).execute()
        except HttpError:
            pass
        return user.sheet_id
    sheet = service.spreadsheets().create(body={'properties': {'title': Config.SHEET_NAME}}).execute()
    sid = sheet['spreadsheetId']
    service.spreadsheets().values().update(
        spreadsheetId=sid, range='A1',
        valueInputOption='RAW', body={'values': HEADERS}).execute()
    user.sheet_id = sid
    db.session.commit()
    return sid

@app.route('/')
def index():
    if 'user_id' not in session:
        return 'login placeholder', 200
    return 'home placeholder', 200

if __name__ == '__main__':
    app.run()