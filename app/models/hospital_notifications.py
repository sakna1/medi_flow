from datetime import datetime
from app import db  
class HospitalNotification(db.Model):
    __tablename__ = "hospital_notifications"

    id = db.Column(db.Integer, primary_key=True)
    notification_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey("patient.id"), nullable=True)
    updates = db.Column(db.Text, nullable=False)

    # relationship (if you have Patient model defined)
    patient = db.relationship("Patient", backref=db.backref("notifications", lazy=True))
  