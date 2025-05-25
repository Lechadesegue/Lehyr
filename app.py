
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
    return Credentials(
        None,
        refresh_token=user.refresh_token,
        client_id=app.config['GOOGLE_CLIENT_ID'],
        client_secret=app.config['GOOGLE_CLIENT_SECRET'],
        token_uri='https://oauth2.googleapis.com/token'
    )

HEADERS = [['Registro', 'Fecha', 'Inicio', 'Duración']]

def ensure_personal_sheet(user):
    creds = get_credentials(user)
    sheets_service = build('sheets', 'v4', credentials=creds)
    if user.sheet_id:
        # ensure headers exist
        try:
            resp = sheets_service.spreadsheets().values().get(
                spreadsheetId=user.sheet_id, range='A1:D1').execute()
            if not resp.get('values'):
                sheets_service.spreadsheets().values().update(
                    spreadsheetId=user.sheet_id,
                    range='A1',
                    valueInputOption='RAW',
                    body={'values': HEADERS}).execute()
        except HttpError:
            pass
        return user.sheet_id
    # create new sheet with headers
    sheet = sheets_service.spreadsheets().create(body={'properties': {'title': Config.SHEET_NAME}}).execute()
    sid = sheet['spreadsheetId']
    sheets_service.spreadsheets().values().update(
        spreadsheetId=sid, range='A1',
        valueInputOption='RAW', body={'values': HEADERS}).execute()
    user.sheet_id = sid
    db.session.commit()
    return sid

def append_entry_to_sheet(user, record_name, entry):
    creds = get_credentials(user)
    sheet_id = ensure_personal_sheet(user)
    service = build('sheets', 'v4', credentials=creds)
    body = {'values': [[record_name, entry.date.isoformat(),
                        entry.start.strftime('%H:%M:%S'),
                        str(timedelta(seconds=entry.duration_sec))]]}
    try:
        service.spreadsheets().values().append(
            spreadsheetId=sheet_id, range='A:D',
            valueInputOption='RAW', body=body).execute()
    except HttpError as e:
        app.logger.error(f'Sheets write error: {e}')

NORD_COLORS = ['#8FBCBB','#88C0D0','#81A1C1','#5E81AC','#BF616A',
               '#D08770','#EBCB8B','#A3BE8C','#B48EAD']

# ---------- Rutas ---------- #
@app.route('/')
def index():
    uid = session.get('user_id')
    if not uid:
        return render_template('login.html')
    user = User.query.get(uid)
    if not user:
        session.clear()
        return redirect(url_for('index'))
    records = Record.query.filter_by(user_id=user.id).all()
    return render_template('index.html', records=records, colors=NORD_COLORS)

@app.route('/login')
def login():
    nonce = secrets.token_urlsafe(16)
    session['nonce'] = nonce
    return oauth.google.authorize_redirect(url_for('authorize', _external=True), nonce=nonce)

@app.route('/authorize')
def authorize():
    token = oauth.google.authorize_access_token()
    info = oauth.google.parse_id_token(token, nonce=session.pop('nonce', None))
    user = User.query.filter_by(email=info['email']).first()
    if not user:
        user = User(email=info['email'], google_id=info['sub'], refresh_token=token.get('refresh_token'))
        db.session.add(user)
    elif token.get('refresh_token'):
        user.refresh_token = token['refresh_token']
    db.session.commit()
    session['user_id'] = user.id
    ensure_personal_sheet(user)
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# API endpoints (same as v7, omitted for brevity)...

if __name__ == '__main__':
    app.run(debug=True)
