
from datetime import datetime, timedelta
import secrets

from flask import Flask, render_template, redirect, url_for, session, request, jsonify, abort
from authlib.integrations.flask_client import OAuth
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError

from config import Config
from models import db, User, Record, Entry

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
with app.app_context():
    # Try to add sheet_id column if missing
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
    client_kwargs={'scope': (
        'openid email profile '
        'https://www.googleapis.com/auth/drive.file '
        'https://www.googleapis.com/auth/spreadsheets'
    )}
)

def get_credentials(user: User):
    return Credentials(
        None,
        refresh_token=user.refresh_token,
        client_id=app.config['GOOGLE_CLIENT_ID'],
        client_secret=app.config['GOOGLE_CLIENT_SECRET'],
        token_uri='https://oauth2.googleapis.com/token'
    )

def ensure_personal_sheet(user: User):
    if getattr(user, 'sheet_id', None):
        return user.sheet_id
    creds = get_credentials(user)
    sheets_service = build('sheets', 'v4', credentials=creds)
    body = {'properties': {'title': app.config['SHEET_NAME']}}
    sheet = sheets_service.spreadsheets().create(body=body).execute()
    user.sheet_id = sheet['spreadsheetId']
    db.session.commit()
    return user.sheet_id

def append_entry_to_sheet(user: User, record_name: str, entry: Entry):
    creds = get_credentials(user)
    sheet_id = ensure_personal_sheet(user)
    service = build('sheets', 'v4', credentials=creds)
    body = {'values': [[
        record_name,
        entry.date.isoformat(),
        entry.start.strftime('%H:%M:%S'),
        str(timedelta(seconds=entry.duration_sec))
    ]]}
    try:
        service.spreadsheets().values().append(
            spreadsheetId=sheet_id,
            range='A:D',
            valueInputOption='RAW',
            body=body
        ).execute()
    except HttpError as e:
        app.logger.error(f'Sheets write error: {e}')

NORD_COLORS = ['#8FBCBB', '#88C0D0', '#81A1C1', '#5E81AC', '#BF616A',
               '#D08770', '#EBCB8B', '#A3BE8C', '#B48EAD']

@app.route('/')
def index():
    if 'user_id' not in session:
        return render_template('login.html')
    user = User.query.get(session['user_id'])
    records = Record.query.filter_by(user_id=user.id).all()
    return render_template('index.html', records=records, colors=NORD_COLORS)

@app.route('/login')
def login():
    redirect_uri = url_for('authorize', _external=True)
    nonce = secrets.token_urlsafe(16)
    session['oauth_nonce'] = nonce
    return oauth.google.authorize_redirect(redirect_uri, nonce=nonce)

@app.route('/authorize')
def authorize():
    token = oauth.google.authorize_access_token()
    nonce = session.pop('oauth_nonce', None)
    user_info = oauth.google.parse_id_token(token, nonce=nonce)
    email = user_info['email']
    google_id = user_info['sub']
    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(email=email, google_id=google_id, refresh_token=token.get('refresh_token'))
        db.session.add(user)
        db.session.commit()
    else:
        if token.get('refresh_token'):
            user.refresh_token = token['refresh_token']
            db.session.commit()
    session['user_id'] = user.id
    ensure_personal_sheet(user)
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/api/records', methods=['POST'])
def create_record():
    if 'user_id' not in session:
        abort(401)
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    if not name:
        abort(400)
    color = data.get('color') or secrets.choice(NORD_COLORS)
    record = Record(user_id=session['user_id'], name=name, color=color)
    db.session.add(record)
    db.session.commit()
    return jsonify({'id': record.id, 'name': record.name, 'color': record.color})

if __name__ == '__main__':
    app.run(debug=True)
