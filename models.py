from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    google_id = db.Column(db.String(255), unique=True, nullable=False)
    refresh_token = db.Column(db.Text, nullable=False)
    records = db.relationship('Record', backref='user', lazy=True)

class Record(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    color = db.Column(db.String(20), nullable=False)
    entries = db.relationship('Entry', backref='record', lazy=True)

class Entry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    record_id = db.Column(db.Integer, db.ForeignKey('record.id'), nullable=False)
    date = db.Column(db.Date, default=datetime.utcnow().date)
    start = db.Column(db.Time)
    duration_sec = db.Column(db.Integer)
    active = db.Column(db.Boolean, default=True)
