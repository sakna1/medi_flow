from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file,jsonify
from flask_login import login_required, login_user, current_user
from app.models import Patient , PatientLog , User ,DiseaseDesc,HospitalNotification
import qrcode
import io
from zoneinfo import ZoneInfo
from datetime import datetime, date, timezone ,time ,timedelta
from sqlalchemy import cast, Date ,func,text
from app import db
import pytz
import pytz
from flask_login import UserMixin
from sqlalchemy import or_
patient = Blueprint('patient', __name__)

from flask import session

@patient.route('/user-login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        identifier = request.form['username']
        password = request.form['password']

        patient_id = Patient.query.filter(
            (Patient.username == identifier) | (Patient.email == identifier)
        ).first()

        if patient_id and patient_id.check_password(password): 
            login_user(patient_id)
            session["login_type"] = "patient"   
            return redirect(url_for("patient.dashboard"))
       
        flash("Invalid login credentials.") 
        return render_template('login.html')
    
    return render_template('login.html')

@patient.route('/patient/dashboard')
@login_required
def dashboard():    
    return render_template('patient/dashboard.html', user=current_user.first_name)

@patient.route('/patient/appoinments')
@login_required
def appoinments():    
    return render_template('patient/appoinments.html',user=current_user.first_name)

@patient.route('/patient/contact')
def contact():
    return render_template('patient/contact.html')

@patient.route('/patient/faqpage')
@login_required
def faqpage():    
    return render_template('patient/faqpage.html',user=current_user.first_name)

@patient.route('/patient/notification')
@login_required
def notification():    
    return render_template('patient/notification.html' ,user=current_user.first_name)

@patient.route('/patient/dashboard/qr')
@login_required
def qr_code():
    login_patient_id = Patient.query.filter_by(id=current_user.id).first()
    qr_data = str(login_patient_id.id)
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

    if not result:
        return jsonify({"error": "No patient found"})

    # ✅ Get disease name from DiseaseDesc table
    disease_name = None
    if result.disease_id:
        disease = DiseaseDesc.query.get(result.disease_id)
        disease_name = disease.name if disease else None

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
        "disease_name": disease_name,  
        "description": result.description,
        "treatment_status": result.treatment_status,
        "blood_type": result.blood_type,
        "treatment_type": result.treatment_type
    })
    

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

        
@patient.route('/dashboard/today-appointment')
@login_required
def api_today_appointment():
    today_appointment = (
    PatientLog.query
    .filter(PatientLog.patient_id == current_user.id)
    .filter(cast(PatientLog.scan_time, Date) == date.today())
    .order_by(PatientLog.scan_time.desc())
    .first()
)
    if not today_appointment:
        return jsonify({"status": "none"})

    return jsonify({
        "clinic": today_appointment.doctor.first_name if today_appointment.doctor else "Unknown",
        "date": today_appointment.scan_time.strftime("%B %d, %Y"),
        "time": today_appointment.scan_time.strftime("%I:%M %p"),
        "room_no": today_appointment.room_no or "Not Assigned",
        "queue_number": today_appointment.queue_number or "Pending"
    })

@patient.route('/dashboard/next-appointment')
@login_required
def api_next_appointment():  
    patient = Patient.query.filter_by(id=current_user.id).first()
    if not patient or not patient.next_appointment_date:
        return jsonify({"status": "none"})

    return jsonify({
        "date": patient.next_appointment_date.strftime("%B %d, %Y")
    })


@patient.route("/patient/past-appointments")
@login_required
def patient_past_appointments():
    if not hasattr(current_user, "id"):
        return jsonify({"error": "Unauthorized"}), 403

    today = datetime.now()
    start_date = request.args.get("start")
    end_date = request.args.get("end")
    search = request.args.get("search", "").strip()

    # base query
    query = (
        db.session.query(
            PatientLog.id,
            PatientLog.room_no,
            PatientLog.start_time,
            PatientLog.end_time,
            PatientLog.status,
            PatientLog.notes,
            User.first_name.label("doctor_first"),
            User.last_name.label("doctor_last"),
            Patient.treatment_status
        )
        .join(Patient, PatientLog.patient_id == Patient.id)
        .join(User, PatientLog.doctor_id == User.id)
        .filter(
            PatientLog.patient_id == current_user.id,
            PatientLog.start_time.isnot(None),
            PatientLog.start_time < today
        )
    )

    # date filters
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(PatientLog.start_time >= start_dt)
        except ValueError:
            pass

    if end_date:
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            query = query.filter(PatientLog.start_time <= end_dt)
        except ValueError:
            pass

    # search filter (doctor name or treatment_status)
    if search:
        query = query.filter(
            db.or_(
                User.first_name.ilike(f"%{search}%"),
                User.last_name.ilike(f"%{search}%"),
                Patient.treatment_status.ilike(f"%{search}%")
            )
        )

    records = query.order_by(PatientLog.start_time.desc()).all()

    data = []
    for r in records:
        data.append({
            "log_id": r.id,
            "doctor_name": f"{r.doctor_first} {r.doctor_last}",
            "treatment_status": r.treatment_status,
            "room_no": r.room_no,
            "start_time": r.start_time.strftime("%Y-%m-%d %H:%M") if r.start_time else None,
            "end_time": r.end_time.strftime("%Y-%m-%d %H:%M") if r.end_time else None,
            "status": r.status,
            "notes": r.notes
        })

    return jsonify(data)

@patient.route('/view_notifications', methods=['GET'])
def view_notifications():
    """
    Fetch all hospital notifications relevant to the logged-in patient:
    - General updates (type='general')
    - Patient-specific updates (patient_id == current_user.id)
    """
    notifications = HospitalNotification.query.filter(
        or_(
            HospitalNotification.type == 'general',
            HospitalNotification.patient_id == current_user.id
        )
    ).order_by(HospitalNotification.notification_date.desc()).all()

    return render_template('patient/notification.html', notifications=notifications, user=current_user.username)


@patient.route('/get-waiting-time', methods=['GET'])
@login_required
def get_waiting_time():

    colombo_tz = pytz.timezone("Asia/Colombo")
    now_colombo = datetime.now(colombo_tz)

    start_of_day = now_colombo.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1)
    start_utc = start_of_day.astimezone(pytz.UTC)
    end_utc = end_of_day.astimezone(pytz.UTC)

    # Get current active log (waiting or assigned)
    current_log = (
        PatientLog.query
        .filter(
            PatientLog.patient_id == current_user.id,
            PatientLog.scan_time >= start_utc,
            PatientLog.scan_time < end_utc,
            func.lower(PatientLog.status).in_(["waiting", "assigned"])
        )
        .order_by(PatientLog.id.desc())
        .first()
    )

    if not current_log:
        return jsonify({
            "waiting_time": None,
            "message": "No active queue record found for today."
        })

    # Run SQL query to calculate total wait before current patient
    sql = text("""
        SELECT COALESCE(SUM(p2.estimated_wait_time), 0) AS total_wait_before
        FROM patient_log p2
        WHERE p2.room_no = :room_no
          AND p2.scan_time::date = :today
          AND p2.queue_number < :queue_number
          AND LOWER(p2.status) IN ('waiting', 'assigned')
    """)

    result = db.session.execute(sql, {
        "room_no": current_log.room_no,
        "today": now_colombo.date(),
        "queue_number": current_log.queue_number
    }).fetchone()

    total_wait_time = result.total_wait_before if result else 0

    # Create friendly message
    if total_wait_time == 0:
        message = "You are next to meet the doctor!"
    else:
        message = f"Estimated waiting time before your turn: {total_wait_time} minutes."

    return jsonify({
        "patient_id": current_user.id,
        "room_no": current_log.room_no,
        "queue_number": current_log.queue_number,
        "estimated_wait_time": current_log.estimated_wait_time,
        "waiting_time": total_wait_time,
        "message": message
    })


