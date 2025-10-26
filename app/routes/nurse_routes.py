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


def update_doctor_room_counts():
    """Recalculate and update how many patients are waiting per doctor's room (for today's date)."""
    today = date.today()
    doctor_logs = DoctorLog.query.filter_by(log_date=today).all()

    for dlog in doctor_logs:
        count = PatientLog.query.filter(
            PatientLog.room_no == dlog.room_no,
            PatientLog.status.in_(["waiting", "assigned"]),
            db.func.date(PatientLog.scan_time) == today
        ).count()
        dlog.patients_per_room = count

    db.session.commit()
    print("✅ DoctorLog patient counts updated for today.")


@nurse.route('/nurse/log_scan', methods=['POST'])
@login_required
def log_scan():
    """Handles nurse QR scan, patient log creation, AI reorder, and wait time prediction."""
    try:
        data = request.get_json()
        raw_qr = str(data.get("qr_data", "")).strip()
        print(f"DEBUG: Received RAW QR Data: [{raw_qr}]")

        # --- Clean QR ---
        cleaned_id = ''.join(ch for ch in raw_qr if ch.isalnum())
        if not cleaned_id.isdigit():
            return jsonify({"error": "Invalid QR code format"}), 400

        patient_id = int(cleaned_id)
        patient = Patient.query.get(patient_id)
        if not patient:
            return jsonify({"error": f"Patient {patient_id} not found"}), 404

        # --- Prevent duplicate queue entry for today ---
        today = date.today()
        existing_log = PatientLog.query.filter(
            PatientLog.patient_id == patient_id,
            PatientLog.status.in_(["waiting", "assigned"]),
            db.func.date(PatientLog.scan_time) == today
        ).first()

        if existing_log:
            return jsonify({"message": f"Patient {patient_id} is already queued for today"}), 400

        # --- Create new log ---
        new_log = PatientLog(
            patient_id=patient_id,
            nurse_id=current_user.id,
            scan_time=datetime.now(),
            status="waiting",
            notes="Scanned by nurse"
        )
        db.session.add(new_log)
        db.session.commit()

        print("✅ Patient scanned successfully. Calling AI reorder...")

        # --- 1️⃣ AI Queue Reorder ---
        ai_response = call_gemini_for_queue(patient_id)

        # Validate AI output
        if not isinstance(ai_response, list) or not ai_response:
            print("⚠️ Invalid AI response:", ai_response)
            return jsonify({"error": "Invalid AI response from model"}), 500

        # --- 2️⃣ Update Database from AI Output ---
        for record in ai_response:
            log = PatientLog.query.filter_by(patient_id=record["patient_id"])\
                .order_by(PatientLog.id.desc()).first()
            if log:
                log.room_no = record.get("room_no")
                log.doctor_id = record.get("doctor_id")
                log.queue_number = record.get("queue_number")
                log.status = "assigned"

        db.session.flush()
        print("✅ Queue numbers updated from AI output.")

        # --- 3️⃣ Update Doctor Log counts (today only) ---
        update_doctor_room_counts()

        # --- 4️⃣ Predict Estimated Wait Time ---
        disease_id = new_log.disease_id or 1
        queue_length = PatientLog.query.filter(
            PatientLog.room_no == new_log.room_no,
            PatientLog.status == 'waiting',
            db.func.date(PatientLog.scan_time) == today
        ).count()
        doctor_count = DoctorLog.query.filter_by(room_no=new_log.room_no, log_date=today).count()
        disease_est_time = 10  # placeholder, can fetch from DiseaseDesc table

        est_time = predict_wait_time(
            age=calculate_age(patient.dob),
            disease_id=disease_id,
            queue_length=queue_length,
            disease_est_time=disease_est_time,
            treatment_status=patient.treatment_status,
            available_doctors=doctor_count
        )

        new_log.estimated_wait_time = est_time
        db.session.commit()

        print(f"✅ Wait time predicted successfully: {est_time} mins")

        return jsonify({
            "message": f"Patient {patient_id} logged successfully",
            "room_no": new_log.room_no,
            "queue_number": new_log.queue_number,
            "estimated_wait_time": est_time
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

    

  










    

    