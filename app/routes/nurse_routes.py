from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required
from flask_login import current_user
from app.models import PatientLog, Patient
from app import db

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
    patient_code = data.get('patient_code')

    patient = Patient.query.filter_by(username=patient_code).first()
    if not patient:
        return jsonify({'message': 'Invalid patient code'}), 400

    log = PatientLog(patient_id=patient.id, nurse_id=current_user.id)
    db.session.add(log)
    db.session.commit()

    return jsonify({'message': 'Scan logged successfully'})

    