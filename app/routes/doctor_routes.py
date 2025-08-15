from flask import Blueprint, render_template
from flask_login import login_required
from flask_login import current_user

doctor = Blueprint('doctor', __name__)

@doctor.route('/doctor/dashboard')
@login_required
def dashboard():
    doctor_name = current_user.username 
    return render_template('doctor/dashboard.html',doctor_name=doctor_name)

@doctor.route('/doctor/appoinments')
@login_required
def appoinments():
    doctor_name = current_user.username 
    return render_template('doctor/appoinments.html',doctor_name=doctor_name)

@doctor.route('/doctor/editprofile')
@login_required
def editprofile():
    doctor_name = current_user.username 
    return render_template('doctor/editprofile.html',doctor_name=doctor_name)
    
    
    