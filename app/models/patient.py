from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


class Patient(db.Model, UserMixin):
    __tablename__ = 'patient'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(), nullable=False)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    dob = db.Column(db.DateTime)
    gender = db.Column(db.String(10))
    address = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    disease_id = db.Column(db.Integer, db.ForeignKey('disease_desc.id'), nullable=True)
    description = db.Column(db.Text) 
    blood_type = db.Column(db.String(5))  
    treatment_status = db.Column(db.String(20)) 
    marital_status = db.Column(db.String(20))  
    emergency_contact_name = db.Column(db.String(100))    
    emergency_phone = db.Column(db.String(20))    
    nic = db.Column(db.String(20),)
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)    
    treatment_type = db.Column(db.String(50))  
    next_appointment_date = db.Column(db.Date)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)   
    