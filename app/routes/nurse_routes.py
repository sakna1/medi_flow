from flask import Blueprint, render_template, jsonify, request,redirect,flash
from flask_login import login_required
from flask_login import current_user
from app.models import PatientLog, Patient ,PatientReport,HospitalNotification,DiseaseDesc,DoctorLog
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

@nurse.route('/nurse/log_scan', methods=['POST'])
@login_required
def log_scan():
    # 1️⃣ Get data and robustly clean QR data
    data = request.get_json()
    qr_data = data.get("qr_data")

    if not qr_data:
        return jsonify({"message": "QR data missing"}), 400

    try:
        qr_data_str = str(qr_data)
        
        # LOGGING THE RAW DATA (Already done, confirming 'captain')
        print(f"DEBUG: Received RAW QR Data: [{qr_data_str}]")
        
        # Use regex to strip all non-digit characters
        numeric_part = re.sub(r'\D', '', qr_data_str) 
        
        # LOGGING THE CLEANED PART
        print(f"DEBUG: Cleaned Numeric Part: [{numeric_part}]") 
        
        if not numeric_part:
            # This is triggered if qr_data was "captain" or ""
            raise ValueError("QR code contains no numerical digits or is empty.")
            
        patient_id = int(numeric_part)

    except ValueError:
        # Returns the 400 error message you are seeing
        return jsonify({"message": "Invalid QR code. Please ensure it contains a valid patient ID."}), 400
    
    # Start transaction
    try:
        # 2️⃣ Create and commit new log
        log = PatientLog(
            patient_id=patient_id,
            nurse_id=current_user.id,        
            status="Waiting",
            notes="Awaiting AI assignment"
        )
        db.session.add(log)
        db.session.commit()  # Commit so AI can see the new patient

        # 3️⃣ Collect all waiting/assigned logs and Call AI for queue re-evaluation
        waiting_logs = PatientLog.query.filter(
            PatientLog.status.in_(["Waiting", "Assigned"])
        ).all()
        current_waiting_pids = [wl.patient_id for wl in waiting_logs]

        ai_full_result = call_gemini_for_queue(patient_id) 

        if not ai_full_result or "error" in ai_full_result:
            log.status = "Error"
            log.notes = f"AI failed: {ai_full_result.get('error', 'Unknown AI error')}"
            db.session.commit()
            return jsonify({
                'message': 'AI failed to assign queue. Patient logged as waiting.',
                'details': ai_full_result.get('error', 'Unknown error')
            }), 500

        # 4️⃣ Process AI results and predict wait times
        updated_patients = []
        today = date.today()

        for result_item in ai_full_result:
            pid = result_item.get("patient_id")
            
            if pid in current_waiting_pids:
                room_no = int(result_item.get("room_no") or 0)
                doctor_id = int(result_item.get("doctor_id") or 0)
                queue_number = int(result_item.get("queue_number") or 0)

                log_entry = (
                    PatientLog.query.filter_by(patient_id=pid)
                    .order_by(PatientLog.scan_time.desc())
                    .first()
                )

                if log_entry:
                    log_entry.room_no = room_no
                    log_entry.doctor_id = doctor_id
                    log_entry.queue_number = queue_number
                    log_entry.status = "Assigned"
                    log_entry.notes = "AI updated (queue reordered)"

                    # 🔹 Predict wait time for this patient
                    patient = log_entry.patient 
                    disease = DiseaseDesc.query.get(patient.disease_id) if patient and patient.disease_id else None
                    disease_est_time = disease.est_time if disease else 15 
                    
                    queue_length = PatientLog.query.filter(
                        PatientLog.status.in_(["Waiting", "Assigned"]),
                        PatientLog.patient.has(disease_id=patient.disease_id)
                    ).count()
                    
                    available_doctors = DoctorLog.query.filter_by(log_date=today).count()
                    staff_on_duty = 4 # Use a constant or retrieve dynamically

                    predicted_wait = predict_wait_time(
                        age=calculate_age(patient.dob),
                        disease_id=patient.disease_id,
                        queue_length=queue_length,
                        disease_est_time=disease_est_time,
                        treatment_status=patient.treatment_status,
                        available_doctors=available_doctors,
                        staff_on_duty=staff_on_duty,
                        scan_time=log_entry.scan_time 
                    )

                    log_entry.estimated_wait_time = predicted_wait
                    db.session.add(log_entry)

                    updated_patients.append({
                        "patient_id": pid,
                        "room_no": room_no,
                        "queue_number": queue_number,
                        "predicted_wait_time": predicted_wait
                    })

        # 5️⃣ Commit all updates
        db.session.commit()

    except Exception as e:
        print(f"Fatal error during AI update process: {e}")
        db.session.rollback()
        return jsonify({
            'message': 'Fatal System error during AI queue assignment. All changes rolled back.',
            'details': str(e)
        }), 500

    # 6️⃣ Prepare response for nurse
    latest_patient = next((p for p in updated_patients if p["patient_id"] == patient_id), None)

    return jsonify({
        'message': 'Scan logged, AI updated queues, and wait times predicted successfully.',
        'assigned_patient': latest_patient,
        'total_patients_recalculated': len(updated_patients)
    })

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

    

  










    

    