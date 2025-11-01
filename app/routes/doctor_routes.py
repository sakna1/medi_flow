from flask import Blueprint, render_template,jsonify,request,session
from flask_login import login_required
from flask_login import current_user
from app import db
from app.models import Patient , PatientLog ,PatientReport,DiseaseDesc,DoctorLog,HospitalNotification
from datetime import datetime,date
from flask import url_for, send_from_directory
from sqlalchemy import cast, Date ,func
import pytz

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
    colombo_tz = pytz.timezone("Asia/Colombo")
    today_colombo = datetime.now(colombo_tz).date()

    # --- Fetch latest log with today's scan_time (Colombo time) ---
    log = (
        PatientLog.query
        .filter(
            PatientLog.patient_id == patient_id,
            PatientLog.end_time.is_(None),
            func.date(
                func.timezone('Asia/Colombo', func.timezone('UTC', PatientLog.scan_time))
            ) == today_colombo
        )
        .order_by(PatientLog.id.desc())
        .first()
    )

    if not log:
        return jsonify({"error": "No active log found for today"}), 404

    # --- Update start time and status ---
    log.start_time = datetime.utcnow()
    log.status = "In Consultation"
    db.session.commit()

    return jsonify({
        "message": "Appointment started!",
        "scan_time": str(log.scan_time)
    })


@doctor.route("/complete_appointment/<int:patient_id>", methods=["POST"])
def complete_appointment(patient_id):
    colombo_tz = pytz.timezone("Asia/Colombo")

    # --- Get today's date in Colombo ---
    today_colombo = datetime.now(colombo_tz).date()

    # --- Fetch latest log with today's scan time (Colombo) ---
    log = (
        PatientLog.query
        .filter(
            PatientLog.patient_id == patient_id,
            PatientLog.end_time.is_(None),
            func.date(
                func.timezone('Asia/Colombo', func.timezone('UTC', PatientLog.scan_time))
            ) == today_colombo
        )
        .order_by(PatientLog.id.desc())
        .first()
    )

    if not log:
        return jsonify({"error": "No active log found for today"}), 404

    # --- Complete appointment ---
    log.end_time = datetime.utcnow()
    log.status = "completed"
    db.session.commit()

    return jsonify({
        "message": "Appointment completed!",
        "scan_time": str(log.scan_time)
    })

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

@doctor.route("/doctor/past-appointments")
@login_required
def doctor_past_appointments():
    doctor_id = session.get("doctor_id") or current_user.id
    if not doctor_id:
        return jsonify({"error": "Not logged in"}), 401

    today = datetime.now()

    # Join PatientLog + Patient + DiseaseDesc
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
            DiseaseDesc.name.label("disease_name"),
            Patient.treatment_status,
        )
        .join(Patient, PatientLog.patient_id == Patient.id)
        .outerjoin(DiseaseDesc, Patient.disease_id == DiseaseDesc.id)
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
            "disease": r.disease_name or "-",  # show disease name
            "treatment_status": r.treatment_status or "-",
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

@doctor.route('/assign-room', methods=['POST'])
def assign_room():
    data = request.get_json()
    doctor_id =current_user.id   # get logged in doctor id
    room_no = data.get('room_no')

    if not doctor_id or not room_no:
        return jsonify({'success': False, 'message': 'Missing data'}), 400

    # Check if room already assigned today
    existing_room = DoctorLog.query.filter_by(log_date=datetime.utcnow().date(), room_no=room_no).first()
    if existing_room:
        return jsonify({'success': False, 'message': f'Room {room_no} already assigned!'}), 400

    # Check if doctor already has a room today
    existing_doctor_log = DoctorLog.query.filter_by(log_date=datetime.utcnow().date(), doctor_id=doctor_id).first()
    if existing_doctor_log:
        existing_doctor_log.room_no = room_no
    else:
        new_log = DoctorLog(log_date=datetime.utcnow().date(), doctor_id=doctor_id, room_no=room_no)
        db.session.add(new_log)

    db.session.commit()
    return jsonify({'success': True, 'message': f'Room {room_no} assigned successfully'})

@doctor.route('/get-assigned-room', methods=['GET'])
def get_assigned_room():
    from flask_login import current_user
    from datetime import datetime

    if not current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'User not logged in'}), 401

    today = datetime.utcnow().date()
    log = DoctorLog.query.filter_by(log_date=today, doctor_id=current_user.id).first()

    if log:
        return jsonify({'success': True, 'room_no': log.room_no})
    else:
        return jsonify({'success': False, 'room_no': None})
    
@doctor.route('/hospital-updates', methods=["GET"])
def hospital_updates():
    today = date.today()
    updates = (
        HospitalNotification.query
        .filter(db.func.date(HospitalNotification.notification_date) == today)
        .filter_by(type="general")
        .order_by(HospitalNotification.notification_date.desc())
        .all()
    )

    return jsonify({
        "updates": [u.updates for u in updates]
    })
    

@doctor.route('/get_patient_reports/<int:patient_id>', methods=['GET'])
def get_patient_reports(patient_id):
    try:
        # Example query: fetch all reports related to the patient
        reports = PatientReport.query.filter_by(patient_id=patient_id).all()

        if not reports:
            return jsonify({"reports": []}), 200

        report_data = [
            {
                "id": report.id,
                "report_name": report.report_name,
                "file_path": report.file_path
            }
            for report in reports
        ]

        return jsonify({"reports": report_data}), 200

    except Exception as e:
        print("Error fetching reports:", e)
        return jsonify({"error": "Server error"}), 500


@doctor.route("/save-note", methods=["POST"])
@login_required
def save_note():
    data = request.get_json()
    log_id = data.get("log_id")
    notes = data.get("notes")

    if not log_id:
        return jsonify({"message": "Missing log_id"}), 400

    log = PatientLog.query.get(log_id)
    if not log:
        return jsonify({"message": "Log not found"}), 404

    log.notes = notes   
    db.session.commit()

    colombo_tz = pytz.timezone("Asia/Colombo")
    end_local = log.end_time.astimezone(colombo_tz).isoformat() if log.end_time else None

    return jsonify({
        "message": "Notes updated successfully!",
        "log": {
            "id": log.id,
            "scan_time": log.scan_time.isoformat() if log.scan_time else None,
            "end_time_utc": log.end_time.isoformat() if log.end_time else None,
            "end_time": end_local,
            "doctor_name": f"{log.doctor.first_name} {log.doctor.last_name}" if log.doctor else None,
            "notes": log.notes,
            "room_no": log.room_no
        }
    })

