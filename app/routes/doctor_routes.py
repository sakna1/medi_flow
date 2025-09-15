from flask import Blueprint, render_template,jsonify,request
from flask_login import login_required
from flask_login import current_user
from app import db
from app.models import Patient , PatientLog
from datetime import datetime

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

@doctor.route("/save_next_appointment/<int:patient_id>", methods=["POST"])
def save_next_appointment(patient_id):
    data = request.get_json()
    next_appointment = data.get("next_appointment")

    patient = Patient.query.get(patient_id)
    if patient:
        patient.next_appointment_date = next_appointment
        db.session.commit()
        return jsonify({"message": "Next appointment saved!"})
    return jsonify({"error": "Patient not found"}), 404
    
@doctor.route("/start_appointment/<int:patient_id>", methods=["POST"])
def start_appointment(patient_id):
    log = PatientLog.query.filter_by(patient_id=patient_id, end_time=None).order_by(PatientLog.id.desc()).first()
    if not log:
        return jsonify({"error": "No active log found"}), 404
    
    log.start_time = datetime.utcnow()
    log.scan_time = datetime.utcnow().date()  # <-- sets today's date as scan_time
    db.session.commit()
    return jsonify({"message": "Appointment started!", "scan_time": str(log.scan_time)})


@doctor.route("/complete_appointment/<int:patient_id>", methods=["POST"])
def complete_appointment(patient_id):
    log = PatientLog.query.filter_by(patient_id=patient_id, end_time=None).order_by(PatientLog.id.desc()).first()
    if not log:
        return jsonify({"error": "No active log found"}), 404
    
    log.end_time = datetime.utcnow()
    log.scan_time = datetime.utcnow().date()  # <-- also set here if you want scan_time at completion
    db.session.commit()
    return jsonify({"message": "Appointment completed!", "scan_time": str(log.scan_time)})