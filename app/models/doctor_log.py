from datetime import datetime
from app import db  

class DoctorLog(db.Model):
    __tablename__ = "doctor_log"

    id = db.Column(db.Integer, primary_key=True)
    log_date = db.Column(db.Date, nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) 
    room_no = db.Column(db.String(10), nullable=False)

    # relationship (if you have Doctor model defined)
    doctor = db.relationship('User', foreign_keys=[doctor_id], backref='doctor_logs')
