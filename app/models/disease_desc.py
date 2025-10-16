from datetime import datetime
from app import db 
class DiseaseDesc(db.Model):
    __tablename__ = "disease_desc"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    est_time = db.Column(db.String(20))

    patients = db.relationship('Patient', backref='disease', lazy=True)