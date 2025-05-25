from datetime import datetime, timedelta
import secrets

from flask import Flask, render_template, redirect, url_for, session, request, jsonify, abort
from authlib.integrations.flask_client import OAuth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials

from config import Config
from models import db, User, Record, Entry

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
with app.app_context():
    # asegurar columna sheet_id si no existe
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
    return Credentials(None, refresh_token=user.refresh_token,
                       client_id=app.config['GOOGLE_CLIENT_ID'],
                       client_secret=app.config['GOOGLE_CLIENT_SECRET'],
                       token_uri='https://oauth2.googleapis.com/token')

HEADERS = [['Registro', 'Fecha', 'Inicio', 'Duración']]

def ensure_personal_sheet(user):
    creds = get_credentials(user)
    service = build('sheets', 'v4', credentials=creds)
    if user.sheet_id:
        # asegurar encabezados
        values = service.spreadsheets().values().get(
            spreadsheetId=user.sheet_id, range='A1:D1').execute().get('values')
        if not values:
            service.spreadsheets().values().update(
                spreadsheetId=user.sheet_id, range='A1',
                valueInputOption='RAW', body={'values': HEADERS}).execute()
        return user.sheet_id
    # crear hoja nueva
    resp = service.spreadsheets().create(body={'properties': {'title': Config.SHEET_NAME}}).execute()
    sid = resp['spreadsheetId']
    service.spreadsheets().values().update(
        spreadsheetId=sid, range='A1', valueInputOption='RAW',
        body={'values': HEADERS}).execute()
    user.sheet_id = sid
    db.session.commit()
    return sid

# resto de rutas...