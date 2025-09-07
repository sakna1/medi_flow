from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file,jsonify
from flask_login import login_required, login_user, current_user
from app.models import Patient , PatientLog
import qrcode
import io
from zoneinfo import ZoneInfo
from datetime import datetime, date, timezone
from app import db
import pytz

patient = Blueprint('patient', __name__)

@patient.route('/user-login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        identifier = request.form['username']
        password = request.form['password']
        patient_id = Patient.query.filter((Patient.username == identifier) | (Patient.email == identifier)).first()

        if patient_id and patient_id.check_password(password):
            login_user(patient_id)
            return redirect(url_for("patient.dashboard"))

        flash("Invalid login credentials.")
    return render_template('login.html')

def get_patient_name():
    patient = Patient.query.filter(Patient.id == current_user.id).first()
    return patient.first_name if patient else ''

@patient.route('/patient/dashboard')
@login_required
def dashboard():    
    return render_template('patient/dashboard.html', user=get_patient_name())

@patient.route('/patient/appoinments')
@login_required
def appoinments():    
    return render_template('patient/appoinments.html',user=get_patient_name())

@patient.route('/patient/contact')
@login_required
def contact():
    return render_template('patient/contact.html')

@patient.route('/patient/faqpage')
@login_required
def faqpage():    
    return render_template('patient/faqpage.html',user=get_patient_name())

@patient.route('/patient/notification')
@login_required
def notification():    
    return render_template('patient/notification.html',user=get_patient_name())

@patient.route('/patient/dashboard/qr')
@login_required
def qr_code():
    login_patient_id = Patient.query.filter_by(id=current_user.id).first()
    qr_data = login_patient_id.username
    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        box_size=5,
        border=3
    )
    qr.add_data(qr_data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    # Save to memory buffer
    buffer = io.BytesIO()
    img.save(buffer, 'PNG')
    buffer.seek(0)

    return send_file(buffer, mimetype='image/png')

@patient.route("/search_patient", methods=["POST"])
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
            "disease": result.disease,
            "description": result.description,
            "treatment_status": result.treatment_status,
            "blood_type": result.blood_type
        })
    else:
        return jsonify({"error": "No patient found"})
    

@patient.route("/visit-history/<int:patient_id>", methods=["GET"])
def visit_history_api(patient_id):
    logs = (
        PatientLog.query
        .options(db.joinedload(PatientLog.doctor))
        .filter_by(patient_id=patient_id)
        .order_by(PatientLog.scan_time.desc())
        .limit(5)
        .all()
    )

    logs_data = []
    for log in logs:
        # scan_time safe
        scan_iso = log.scan_time.isoformat() if log.scan_time else None

        # end_time safe (convert to Colombo if possible)
        end_local = None
        if log.end_time:
            try:
                aware = (
                    log.end_time
                    if log.end_time.tzinfo
                    else log.end_time.replace(tzinfo=ZoneInfo("UTC"))
                )
                end_local = aware.astimezone(ZoneInfo("Asia/Colombo")).isoformat()
            except Exception:
                end_local = log.end_time.isoformat()

        # doctor name safe
        doctor_name = None
        if log.doctor:
            first = getattr(log.doctor, "first_name", None)
            last = getattr(log.doctor, "last_name", None)
            doctor_name = (f"{first or ''} {last or ''}").strip()

        logs_data.append({
            "id": log.id,
            "scan_time": scan_iso,
            "end_time": end_local,
            "room_no": log.room_no,
            "doctor_name": doctor_name,
            "notes": log.notes,
        })

    return jsonify({"logs": logs_data, "today": date.today().isoformat()})

@patient.route("/save-note", methods=["POST"])
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
    # mark appointment as closed
    log.end_time = datetime.now(timezone.utc) 
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
        
    