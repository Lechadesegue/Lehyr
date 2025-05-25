import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
env_path = BASE_DIR / '.env'
if env_path.exists():
    load_dotenv(env_path)

class Config:
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-secret')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + str(BASE_DIR / 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
    OAUTHLIB_INSECURE_TRANSPORT = os.getenv('OAUTHLIB_INSECURE_TRANSPORT', '1')

    SHEET_NAME = 'Registros y horarios (read only)'
