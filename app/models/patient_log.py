from app import db
from datetime import datetime


class PatientLog(db.Model):
    __tablename__ = 'patient_log'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    nurse_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    scan_time = db.Column(db.DateTime, default=datetime.now)

    patient = db.relationship('Patient', backref='logs')