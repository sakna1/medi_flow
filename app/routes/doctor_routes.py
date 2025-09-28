from flask import Blueprint, render_template,jsonify,request,session
from flask_login import login_required
from flask_login import current_user
from app import db
from app.models import Patient , PatientLog ,PatientReport
from datetime import datetime,date
from flask import url_for, send_from_directory
from sqlalchemy import cast, Date

doctor = Blueprint('doctor', __name__)

@doctor.route('/doctor/dashboard')
@login_required
def dashboard():
    doctor_name = current_user.username     
    doctor_id =current_user.id 
    return render_template('doctor/dashboard.html',doctor_name=doctor_name,doctor_id=doctor_id)

@doctor.route('/doctor/appoinments')
@login_required
def appoinments():
    doctor_name = current_user.username 
    doctor_id =current_user.id 
    return render_template('doctor/appoinments.html',doctor_name=doctor_name,doctor_id=doctor_id)

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

@doctor.route("/doctor/past-appointments")
@login_required
def doctor_past_appointments():
    doctor_id = session.get("doctor_id") or current_user.id
    if not doctor_id:
        return jsonify({"error": "Not logged in"}), 401

    today = datetime.now()

    records = (
        db.session.query(
            PatientLog.id,
            PatientLog.patient_id,
            PatientLog.room_no,
            PatientLog.start_time,
            PatientLog.end_time,
            PatientLog.status,
            PatientLog.notes,
            Patient.first_name,
            Patient.last_name,
            Patient.disease,
            Patient.treatment_status,
        )
        .join(Patient, PatientLog.patient_id == Patient.id)
        .filter(
            PatientLog.doctor_id == doctor_id,
            PatientLog.start_time != None,
            PatientLog.start_time < today
        )
        .order_by(PatientLog.start_time.desc())
        .all()
    )

    data = []
    for r in records:
        data.append({
            "log_id": r.id,
            "patient_id": r.patient_id,
            "patient_name": f"{r.first_name} {r.last_name}",
            "disease": r.disease,
            "treatment_status": r.treatment_status,
            "room_no": r.room_no,
            "start_time": r.start_time.strftime("%Y-%m-%d %H:%M") if r.start_time else "-",
            "end_time": r.end_time.strftime("%Y-%m-%d %H:%M") if r.end_time else "-",
            "status": r.status or "-",
            "notes": r.notes or "-"
        })

    return jsonify(data)

@doctor.route("/dashboard-data", methods=["GET"])
def dashboard_data():
    today = date.today()

    #Total appointments for today
    today_count = PatientLog.query.filter(
        db.func.date(PatientLog.scan_time) == today
    ).count()

    #Next appointment (status = Waiting, not started yet)
    next_appointment = PatientLog.query.filter(
        db.func.date(PatientLog.scan_time) == today,
        PatientLog.status == "Waiting"
    ).order_by(PatientLog.scan_time.asc()).first()

    # ✅ Completed appointments today
    completed_count = PatientLog.query.filter(
        db.func.date(PatientLog.scan_time) == today,
        PatientLog.status == "Completed"
    ).count()

    #Latest hospital update (for now hardcoded, can fetch from another table if you have one)
    latest_update = "Radiology Unit closed on July 5th"  

    return jsonify({
        "today_appointments": today_count,
        "next_appointment": {
            "patient_id": next_appointment.patient_id if next_appointment else None,
            "time": (
                f"{next_appointment.start_time.strftime('%H:%M')} - {next_appointment.end_time.strftime('%H:%M')}"
                if next_appointment and next_appointment.start_time and next_appointment.end_time else None
            )
        },
        "completed_appointments": completed_count,
        "hospital_update": latest_update
    })


@doctor.route("/doctor/dash-schedule", methods=["GET"])
def doctor_dash_schedule():
    today = datetime.today().date()
    start = datetime.combine(today, datetime.min.time())
    end = datetime.combine(today, datetime.max.time())

    logs = PatientLog.query.filter(
        PatientLog.scan_time >= start,
        PatientLog.scan_time <= end,
        PatientLog.doctor_id == current_user.id 
    ).order_by(PatientLog.scan_time.asc()).all()   

    schedule = []
    for log in logs:
        schedule.append({
            "time": log.scan_time.strftime("%I:%M %p") if log.scan_time else "Not Scheduled",
            "patient_id": f"P{log.patient_id:03d}",
            "action_type": log.action_type or "Consultation",
            "room": getattr(log, "room", "N/A")
        })

    return jsonify(schedule)

    



