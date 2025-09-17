from flask import Blueprint, render_template,jsonify,request
from flask_login import login_required
from flask_login import current_user
from app import db
from app.models import Patient , PatientLog ,PatientReport
from datetime import datetime,date
from flask import url_for, send_from_directory

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
    
    today = date.today()
    if log.scan_time and log.scan_time != today:
        return jsonify({"error": "Scan time is not today"}), 400

    log.start_time = datetime.utcnow()
    log.scan_time = today  # set to today if not set yet
    db.session.commit()
    return jsonify({"message": "Appointment started!", "scan_time": str(log.scan_time)})


@doctor.route("/complete_appointment/<int:patient_id>", methods=["POST"])
def complete_appointment(patient_id):
    log = PatientLog.query.filter_by(patient_id=patient_id, end_time=None).order_by(PatientLog.id.desc()).first()
    if not log:
        return jsonify({"error": "No active log found"}), 404
    
    today = date.today()
    if log.scan_time and log.scan_time != today:
        return jsonify({"error": "Scan time is not today"}), 400

    log.end_time = datetime.utcnow()
    log.scan_time = today  # ensure today's date
    db.session.commit()
    return jsonify({"message": "Appointment completed!", "scan_time": str(log.scan_time)})

@doctor.route("/update_patient/<int:patient_id>", methods=["POST"])
def update_patient(patient_id):
    data = request.get_json()
    treatment_status = data.get("treatment_status")
    treatment_type = data.get("treatment_type")

    patient = Patient.query.get(patient_id)
    if not patient:
        return jsonify({"error": "Patient not found"}), 404

    patient.treatment_status = treatment_status
    patient.treatment_type = treatment_type
    db.session.commit()

    return jsonify({"message": "Patient updated successfully!"}), 200

@doctor.route("/get_patient_reports/<int:patient_id>", methods=["GET"])
def get_patient_reports(patient_id):
    reports = PatientReport.query.filter_by(patient_id=patient_id).all()
    if not reports:
        return jsonify({"reports": []})

    report_list = [
        {
            "id": r.id,
            "report_name": r.report_name,
            "file_path": r.file_path,
            "uploaded_at": r.uploaded_at.strftime("%Y-%m-%d %H:%M")
        }
        for r in reports
    ]

    return jsonify({"reports": report_list})