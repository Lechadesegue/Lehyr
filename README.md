# Registro de horarios – MVP

Aplicación Flask que permite crear registros ("Cena", "Gimnasio"…), medir tiempo de cada día y sincronizar resultados en una hoja de cálculo personal de Google Sheets.

## Requisitos
- Python 3.11+
- Cuenta de Google
- Proyecto en Google Cloud (OAuth 2.0) con los scopes Drive File y Sheets.

## Instalación local
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
flask --app app init-db
FLASK_SECRET_KEY=dev \
GOOGLE_CLIENT_ID=<your_id> \
GOOGLE_CLIENT_SECRET=<your_secret> \
flask run -h 0.0.0.0 -p 5000
```

## Despliegue en Render
1. Subí este proyecto a GitHub.
2. Creá un Web Service en Render.
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn app:app`
5. Variables de entorno:
   - `FLASK_SECRET_KEY`
   - `GOOGLE_CLIENT_ID`
   - `GOOGLE_CLIENT_SECRET`
