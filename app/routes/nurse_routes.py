from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required
from flask_login import current_user
from app.models import PatientLog, Patient ,PatientReport
from app import db
from flask import current_app
import os
from werkzeug.utils import secure_filename

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
    if current_user.role.lower() != 'nurse':
        return jsonify({'message': 'Unauthorized'}), 403

    data = request.get_json()
    patient_code = data.get('qr_data')

    patient = Patient.query.filter_by(username=patient_code).first()
    if not patient:
        return jsonify({'message': 'Invalid patient code'}), 400

    log = PatientLog(patient_id=patient.id, nurse_id=current_user.id)
    db.session.add(log)
    db.session.commit()

    return jsonify({'message': 'Scan logged successfully'})

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
            "contact_no": patient.contact_no,
            "gender": patient.gender,
            "nic": patient.nic,
            "marital_status": patient.marital_status
        },
        "reports": [
            {"id": r.id, "file_name": r.file_name, "uploaded_at": r.uploaded_at.strftime("%Y-%m-%d")}
            for r in reports
        ]
    })


    

    