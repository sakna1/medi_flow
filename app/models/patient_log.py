from app import db
from datetime import datetime


class PatientLog(db.Model):
    __tablename__ = 'patient_log'
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    nurse_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    scan_time = db.Column(db.DateTime, default=datetime.now)
    doctor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) 
    room_no = db.Column(db.String(20), nullable=True)
    queue_number = db.Column(db.Integer, nullable=True)
    action_type = db.Column(db.String(50), nullable=False)  # "Check-In", "Consultation", "Treatment"
    notes = db.Column(db.Text, nullable=True)
    start_time = db.Column(db.DateTime, nullable=True)        # when doctor starts
    end_time = db.Column(db.DateTime, nullable=True)          # when doctor ends
    status = db.Column(db.String(50), nullable=True)  # "Waiting", "In Progress", "Completed"
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)



    patient = db.relationship('Patient', backref='logs')
    nurse = db.relationship('User', foreign_keys=[nurse_id], backref='nurse_logs')
    doctor = db.relationship('User', foreign_keys=[doctor_id], backref='doctor_logs')