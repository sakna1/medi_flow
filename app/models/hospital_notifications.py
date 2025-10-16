from datetime import datetime
from app import db  

class HospitalNotification(db.Model):
    __tablename__ = "hospital_notifications"

    id = db.Column(db.Integer, primary_key=True)
    notification_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updates = db.Column(db.Text, nullable=False)
    created_by = db.Column(db.String(50), nullable=True)  # nurse/admin username or role
    type = db.Column(db.String(20), default="general")    # 'general' or 'patient'

    patient_id = db.Column(db.Integer, db.ForeignKey("patient.id"), nullable=True)
    patient = db.relationship("Patient", backref=db.backref("notifications", lazy=True))

    