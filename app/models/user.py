from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(20), nullable=False)  # Role: Doctor, Nurse, Patient, Admin
    username = db.Column(db.String(80), unique=True, nullable=False)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    gender = db.Column(db.String(10))  # Male, Female
    phone = db.Column(db.String(20))
    emergency_contact_name = db.Column(db.String(100))   
    emergency_contact_phone = db.Column(db.String(20))
    date_of_birth = db.Column(db.Date)
    marital_status = db.Column(db.String(20))  # Single, Married, etc.
    address = db.Column(db.String(255))
    nic = db.Column(db.String(20), unique=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(), nullable=False)

    # Role-specific
    specialization = db.Column(db.String(100))  # doctor

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == 'admin'
