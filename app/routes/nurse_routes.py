from flask import Blueprint, render_template, jsonify, request,redirect,flash
from flask_login import login_required
from flask_login import current_user
from app.models import PatientLog, Patient ,PatientReport,HospitalNotification ,DiseaseDesc,DoctorLog,User
from app import db
from flask import current_app
import os
import re
from werkzeug.utils import secure_filename
from flask import url_for, send_from_directory
from datetime import date ,datetime
from sqlalchemy import func
from app.gemini_ai import call_gemini_for_queue , calculate_age
from app.wait_time_predictor import predict_wait_time


nurse = Blueprint('nurse', __name__)

@nurse.route('/nurse/dashboard')
@login_required
def dashboard():
    nurse_name = current_user.username 
    return render_template('nurse/dashboard.html',nurse_name=nurse_name)

@nurse.route('/nurse/editprofile')
@login_required
def editprofile():
    nurse_name = current_user.username 
    return render_template('nurse/editprofile.html',nurse_name=nurse_name)

def get_disease_est_time(disease_id):
    """Fallback service time lookup from DiseaseDesc (minutes)."""
    if not disease_id:
        return None
    d = DiseaseDesc.query.get(disease_id)
    if d and getattr(d, "est_time_minutes", None) is not None:
        return d.est_time_minutes
    return None


def update_doctor_room_counts_and_totals():
    """Recalculate patients_per_room and total_est_time for today's doctor logs."""
    today = date.today()
    doctor_logs = DoctorLog.query.filter_by(log_date=today).all()

    for dlog in doctor_logs:
        # count waiting+assigned today in this room + doctor
        count = PatientLog.query.filter(
            PatientLog.room_no == dlog.room_no,
            PatientLog.doctor_id == dlog.doctor_id,
            PatientLog.status.in_(["waiting", "assigned"]),
            func.date(PatientLog.scan_time) == today
        ).count()

        # sum the service_time for waiting+assigned patients (we store service_time on record if available,
        # otherwise we will have put a fallback in estimated_wait_time calc step below)
        total_est_time = db.session.query(
            func.coalesce(func.sum(PatientLog.service_time), 0)
        ).filter(
            PatientLog.room_no == dlog.room_no,
            PatientLog.doctor_id == dlog.doctor_id,
            PatientLog.status.in_(["waiting", "assigned"]),
            func.date(PatientLog.scan_time) == today
        ).scalar()

        # if your PatientLog model doesn't have 'service_time' column, compute from estimated_wait_time fallback:
        if total_est_time is None or total_est_time == 0:
            # Sum fallback: sum service_time field if exists else sum individual_service_time that we saved to estimated_service_time_column
            total_est_time = db.session.query(
                func.coalesce(func.sum(
                    func.coalesce(PatientLog.service_time, PatientLog.estimated_service_time, 0)
                ), 0)
            ).filter(
                PatientLog.room_no == dlog.room_no,
                PatientLog.doctor_id == dlog.doctor_id,
                PatientLog.status.in_(["waiting", "assigned"]),
                func.date(PatientLog.scan_time) == today
            ).scalar() or 0

        dlog.patients_per_room = count
        # ensure DoctorLog has a 'total_est_time' column (float/int)
        dlog.total_est_time = int(total_est_time or 0)

    db.session.commit()


@nurse.route('/nurse/log_scan', methods=['POST'])
@login_required
def log_scan():
    """Handles nurse QR scan, patient log creation, AI reorder, and per-patient wait-time calculation."""
    try:
        data = request.get_json() or {}
        raw_qr = str(data.get("qr_data", "")).strip()
        print(f"DEBUG: Received RAW QR Data: [{raw_qr}]")

        # --- Clean and validate QR ---
        cleaned_id = ''.join(ch for ch in raw_qr if ch.isalnum())
        if not cleaned_id.isdigit():
            return jsonify({"error": "Invalid QR code format"}), 400

        patient_id = int(cleaned_id)
        patient = Patient.query.get(patient_id)
        if not patient:
            return jsonify({"error": f"Patient {patient_id} not found"}), 404

        today = date.today()

        # --- Prevent duplicate queue entry for today (active entries only) ---
        existing_log = PatientLog.query.filter(
            PatientLog.patient_id == patient_id,
            PatientLog.status.in_(["waiting", "assigned"]),
            func.date(PatientLog.scan_time) == today
        ).first()
        if existing_log:
            return jsonify({"message": f"Patient {patient_id} is already queued for today"}), 400

        # --- Create initial PatientLog (no queue_number, AI will assign authoritative queue_number) ---
        new_log = PatientLog(
            patient_id=patient_id,
            nurse_id=current_user.id,
            scan_time=datetime.now(),
            status="waiting",
            notes="Scanned by nurse"
        )
        db.session.add(new_log)
        db.session.commit()
        print(f"✅ Patient {patient_id} scanned and saved as waiting (id={new_log.id}). Preparing AI payload...")

        # --- Prepare AI input: all today's patients + today's doctor rooms ---
        patients_today = PatientLog.query.filter(func.date(PatientLog.scan_time) == today).all()
        doctor_logs = DoctorLog.query.filter_by(log_date=today).all()

        ai_input = {
            "patients": [
                {
                    "patient_id": p.patient_id,
                    "age": calculate_age(p.patient.dob) if p.patient and getattr(p.patient, "dob", None) else 0,
                    "treatment_status": getattr(p.patient, "treatment_status", None),
                    # include current stored service/estimated fields if present:
                    "estimated_wait_time": p.estimated_wait_time or 0,
                    "queue_number": p.queue_number,
                    "scan_time": p.scan_time.isoformat() if p.scan_time else None,
                    "disease_id": p.disease_id
                } for p in patients_today
            ],
            "rooms": [
                {
                    "doctor_id": d.doctor_id,
                    "room_no": d.room_no,
                    "patients_per_room": d.patients_per_room or 0,
                    "total_est_time": int(getattr(d, "total_est_time", 0) or 0)
                } for d in doctor_logs
            ]
        }

        # --- Call Gemini AI: it must return a list of items for today's patients with room_no, doctor_id, queue_number
        ai_response = call_gemini_for_queue(ai_input)

        if not isinstance(ai_response, list):
            print("⚠️ AI returned non-list:", ai_response)
            return jsonify({"error": "Invalid AI response from model"}), 500
        if not ai_response:
            print("⚠️ AI returned empty list")
            return jsonify({"error": "AI returned empty assignment list"}), 500

        # --- Apply AI results to today's patient logs ---
        # We'll also capture per-patient service_time (duration) if AI returns it (preferred).
        # Allowed ai service fields: 'service_time', 'estimated_service_time', 'predicted_service_time'
        ai_map = {int(item["patient_id"]): item for item in ai_response if "patient_id" in item}

        # Apply assignments only to today's logs
        for pid, item in ai_map.items():
            log = PatientLog.query.filter(
                PatientLog.patient_id == pid,
                func.date(PatientLog.scan_time) == today
            ).order_by(PatientLog.id.desc()).first()

            if not log:
                continue

            # update assignment
            log.room_no = item.get("room_no") or log.room_no
            log.doctor_id = item.get("doctor_id") or log.doctor_id
            log.queue_number = item.get("queue_number") or log.queue_number
            # mark as assigned but still countable
            log.status = "assigned"

            # record service_time if AI provided (minutes)
            service_time = None
            for key in ("service_time", "estimated_service_time", "predicted_service_time", "service_duration"):
                if key in item and item.get(key) is not None:
                    try:
                        service_time = int(item.get(key))
                        break
                    except Exception:
                        # try float then int
                        try:
                            service_time = int(float(item.get(key)))
                            break
                        except Exception:
                            service_time = None

            # fallback: try disease lookup, else default (10)
            if service_time is None:
                service_time = get_disease_est_time(log.disease_id) or 10

            # store service_time on the record for later cumulative calculations.
            # If your PatientLog doesn't have 'service_time' column, create it in a migration.
            # We'll try to set attribute regardless; if column missing, we will still use service_time in memory calculations.
            try:
                log.service_time = service_time
            except Exception:
                # no column present; we'll still use local variable service_time in calculations below
                pass

            # reset per-patient estimated_wait_time for now; we'll set cumulative below
            log.estimated_wait_time = 0

        db.session.flush()
        print("✅ AI assignments applied to today's logs (room, doctor, queue_number, service_time).")

        # --- For each room, compute per-patient waiting times (cumulative of service_time of patients ahead) ---
        today_rooms = db.session.query(PatientLog.room_no).filter(
            func.date(PatientLog.scan_time) == today,
            PatientLog.room_no.isnot(None)
        ).distinct().all()
        # today_rooms is list of tuples; normalize
        room_list = [r[0] for r in today_rooms if r and r[0]]

        for room_no in room_list:
            # fetch patients in this room for today ordered by queue_number asc
            room_patients = PatientLog.query.filter(
                PatientLog.room_no == room_no,
                func.date(PatientLog.scan_time) == today,
                PatientLog.status.in_(["waiting", "assigned"])
            ).order_by(PatientLog.queue_number.asc(), PatientLog.scan_time.asc()).all()

            cumulative = 0
            # We'll compute service_time per patient reliably: either from DB column or fallback to disease/default
            for p in room_patients:
                # determine service_time value
                svc = getattr(p, "service_time", None)
                if svc is None:
                    # try any stored estimated_service_time or fallback to disease table
                    svc = getattr(p, "estimated_service_time", None) or get_disease_est_time(p.disease_id) or 10
                # p is at position: waiting_time = cumulative (sum of service_time of prior patients)
                p.estimated_wait_time = int(cumulative)
                cumulative += int(svc or 0)

            # after loop, update DoctorLog.total_est_time for this room (sum of service_time remaining)
            # find doctor log(s) matching the room for today, update their totals
            total_for_room = int(cumulative)
            # update all doctor_logs for that room (likely one)
            dlogs = DoctorLog.query.filter_by(room_no=room_no, log_date=today).all()
            for d in dlogs:
                d.patients_per_room = len(room_patients)
                d.total_est_time = total_for_room

        db.session.commit()
        print("✅ Per-patient waiting times and doctor room totals updated for today.")

        # fetch updated new_log to return
        updated_log = PatientLog.query.get(new_log.id)

        return jsonify({
            "message": f"Patient {patient_id} logged successfully",
            "patient_id": updated_log.patient_id,
            "room_no": updated_log.room_no,
            "queue_number": updated_log.queue_number,
            "estimated_wait_time": updated_log.estimated_wait_time
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"❌ Error in log_scan: {e}")
        return jsonify({"error": "Internal Server Error"}), 500


@nurse.route("/upload_report/<int:patient_id>", methods=["POST"])
@login_required
def upload_report(patient_id):
    if "file" not in request.files:
        return jsonify({"message": "No file part"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"message": "No file selected"}), 400

    ext = file.filename.rsplit(".", 1)[1].lower()
    if ext not in current_app.config["ALLOWED_EXTENSIONS"]:
        return jsonify({"message": "File type not allowed"}), 400

    # Secure + unique filename
    filename = secure_filename(file.filename)
    unique_filename = f"{patient_id}_{filename}"  # avoid overwrite
    file_path = os.path.join(current_app.config["UPLOAD_FOLDER"], unique_filename)

    # Save file
    file.save(file_path)

    # Save record in DB (assuming you have a `PatientReport` model)
    from app.models import PatientReport  # import your model

    report = PatientReport(
        patient_id=patient_id,
        report_name=filename,
        file_path=file_path
    )
    db.session.add(report)
    db.session.commit()

    return jsonify({"message": "Report uploaded successfully"})

@nurse.route("/get_patient_data/<int:patient_id>", methods=["GET"])
def get_patient_data(patient_id):
    patient = Patient.query.get(patient_id)
    if not patient:
        return jsonify({"error": "Patient not found"}), 404

    reports = PatientReport.query.filter_by(patient_id=patient_id).all()

    return jsonify({
        "patient": {
            "id": patient.id,
            "first_name": patient.first_name,
            "last_name": patient.last_name,
            "dob": str(patient.dob),
            "email": patient.email,
            "address": patient.address,
            "phone": patient.phone,
            "gender": patient.gender,
            "nic": patient.nic,
            "marital_status": patient.marital_status
        },
        "reports": [
            {
                "id": r.id,
                "file_name": r.report_name,
                "uploaded_at": r.uploaded_at.strftime("%Y-%m-%d"),
                "file_url": url_for("nurse.download_report", report_id=r.id)
            }
            for r in reports
        ]
    })


@nurse.route("/download_report/<int:report_id>")
def download_report(report_id):
    report = PatientReport.query.get_or_404(report_id)
    folder = current_app.config["UPLOAD_FOLDER"]
    filename = os.path.basename(report.file_path)
    return send_from_directory(folder, filename, as_attachment=True)

@nurse.route("/view_report/<int:report_id>")
def view_report(report_id):
    report = PatientReport.query.get_or_404(report_id)
    folder = current_app.config["UPLOAD_FOLDER"]
    filename = os.path.basename(report.file_path)
    return send_from_directory(folder, filename)  # 👈 No "as_attachment"

@nurse.route("/get_registered_count")
def get_registered_count():
    today = date.today()
    count = Patient.query.filter(func.date(Patient.registered_at) == today).count()
    return jsonify({"count": count})

@nurse.route("/update_patients_Nurse/<int:patient_id>", methods=["POST"])
@login_required
def update_patient(patient_id):
    data = request.get_json(force=True, silent=False)
    print("DEBUG:", data)
    print("Update payload received:", data)

    patient = Patient.query.get(patient_id)
    if not patient:
        return jsonify({"error": "Patient not found"}), 404

    # Handle other fields
    patient.first_name = data.get("first_name")
    patient.last_name = data.get("last_name")
    patient.marital_status = data.get("marital_status")
    patient.email = data.get("email")
    patient.gender = data.get("gender")
    patient.address = data.get("address")
    patient.nic = data.get("nic")
    patient.phone = data.get("phone")    
    db.session.commit()

    return jsonify({"message": "Patientrtry updated successfully!"}), 200


@nurse.route("/search_patientNurse", methods=["POST"])
@login_required
def search_patient():
    patient_name = request.form.get("patient_name")
    patient_id = request.form.get("patient_id")

    query = Patient.query

    if patient_name:
        query = query.filter(Patient.first_name.ilike(f"%{patient_name}%"))

    if patient_id:
        query = query.filter(Patient.id == patient_id)

    result = query.first()

    if result:
        return jsonify({
            "id": result.id,
            "first_name": result.first_name,
            "last_name": result.last_name,
            "email": result.email,
            "phone": result.phone,
            "dob": result.dob.strftime("%Y-%m-%d") if result.dob else "",
            "gender": result.gender,
            "address": result.address,
            "nic": result.nic,
            "marital_status": result.marital_status,            
        })
    else:
        return jsonify({"error": "No patient found"})
    
@nurse.route('/create_notification', methods=['GET', 'POST'])
def create_notification():
    if request.method == 'POST':
        updates = request.form.get('updates')
        notification_type = request.form.get('type')
        patient_id = request.form.get('patient_id')
        date = request.form.get('date')

        # validate required field
        if not updates:
            flash("Notification message is required!", "danger")
            return redirect(url_for('nurse.create_notification'))

        notification = HospitalNotification(
            updates=updates,
            notification_date=datetime.strptime(date, "%Y-%m-%d"),
            type=notification_type,
            patient_id=patient_id if patient_id else None,
            created_by=current_user.role
        )

        db.session.add(notification)
        db.session.commit()

        flash("✅ Notification added successfully!", "success")
        return redirect(url_for('nurse.create_notification'))

    return render_template('create_notification.html')

    

  










    

    