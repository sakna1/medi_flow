from flask import Blueprint, render_template, request, redirect, url_for, flash,jsonify
from flask_login import login_required, current_user
from app.models import User, Patient , PatientLog
from app import db
from datetime import date
from sqlalchemy import func

admin = Blueprint('admin', __name__)

@admin.route('/admin/create_admin', methods=['GET', 'POST'])
def create_admin_user():
    if User.query.first() is None:
        if request.method == 'POST' and request.form['role'] == 'Admin':
            user = User(
                username=request.form['username'],
                email=request.form['email'],
                first_name=request.form['first_name'],
                last_name=request.form['last_name'],
                gender=request.form.get('gender'),
                role=request.form['role'],
                phone=request.form.get('phone'),
                emergency_contact_first_name=request.form.get('emergency_contact_first_name'),
                emergency_contact_last_name=request.form.get('emergency_contact_last_name'),
                emergency_contact_phone=request.form.get('emergency_contact_phone'),
                date_of_birth=request.form.get('date_of_birth'),  
                marital_status=request.form.get('marital_status'),
                address=request.form.get('address'),
                nic=request.form.get('nic'),
            )
            user.set_password(request.form['password'])
            db.session.add(user)
            db.session.commit()
            flash(f"{user.role.capitalize()} admin registered successfully.")
            return render_template('login.html')

        return render_template('register.html')
    else:
        return "Access denied", 403

@admin.route('/admin/dashboard')
@login_required
def dashboard():
    admin_name = current_user.username
    return render_template('admin/dashboard.html',admin_name=admin_name)

@admin.route('/admin/register', methods=['GET', 'POST'])
# @login_required
def register_user():
    # Only Admins and Nurses can access
    if current_user.role not in ['Admin', 'Nurse']:
        return "Access denied", 403

    if request.method == 'POST':
        role = request.form.get('role', '').lower()

        if role == 'patient':
            user = Patient(
                username=request.form.get('username'),
                email=request.form.get('email'),
                first_name=request.form.get('first_name'),
                last_name=request.form.get('last_name'),
                gender=request.form.get('gender'),                
                phone=request.form.get('phone'),
                emergency_contact_name=request.form.get('emergency_contact_name'),
                emergency_phone=request.form.get('emergency_contact_phone'),
                dob=request.form.get('date_of_birth'),
                marital_status=request.form.get('marital_status'),
                address=request.form.get('address'),
                nic=request.form.get('nic'),
                disease=request.form.get('disease'),
                description=request.form.get('disease_description'),
                blood_type=request.form.get('blood'),
                treatment_status=request.form.get('treatment_status'),
            )
        else:
            user = User(
                username=request.form.get('username'),
                email=request.form.get('email'),
                first_name=request.form.get('first_name'),
                last_name=request.form.get('last_name'),
                gender=request.form.get('gender'),
                role=role,
                phone=request.form.get('phone'),
                emergency_contact_name=request.form.get('emergency_contact_name'),
                emergency_contact_phone=request.form.get('emergency_contact_phone'),
                date_of_birth=request.form.get('date_of_birth'),
                marital_status=request.form.get('marital_status'),
                address=request.form.get('address'),
                nic=request.form.get('nic'),
            )

        if role == 'doctor':
                user.specialization = request.form.get('specialization')

        # Set password securely
        user.set_password(request.form.get('password'))
        
        db.session.add(user)
        db.session.commit()
        flash("Registered successfully.")
        if current_user.role == 'Admin':
          return redirect(url_for('admin.dashboard'))
        elif current_user.role == 'Nurse':
          return redirect(url_for('nurse.dashboard'))

    return render_template('register.html')


@admin.route('/admin/editprofile')
@login_required
def editprofile():
    admin_name = current_user.username
    return render_template('admin/editprofile.html',admin_name=admin_name)

@admin.route("/search_user")
def search_user():
    name = request.args.get("name")
    user = User.query.filter(
        (User.username.ilike(f"%{name}%"))        
    ).first()

    if user:
        return jsonify({
            "id": user.id,
            "date_of_birth": user.date_of_birth.isoformat() if user.date_of_birth else None,
            "firstname": user.first_name,
            "lastname": user.last_name,
            "marital_status": user.marital_status,
            "email": user.email,
            "gender": user.gender,
            "address": user.address,
            "nic": user.nic,
            "phone": user.phone
        })
    else:
        return jsonify(None)

# 💾 Update User
@admin.route("/update_user/<int:user_id>", methods=["PATCH"])
def update_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    data = request.json

    # update only provided fields
    for field, value in data.items():
        if hasattr(user, field) and value is not None and value != "":
            setattr(user, field, value)

    db.session.commit()
    return jsonify({"message": "User updated successfully"})

@admin.route("/get_dashboard_counts")
def get_dashboard_counts():
    today = date.today()
    
    # Today's registered patients
    registered_count = Patient.query.filter(func.date(Patient.registered_at) == today).count()
    
    # Today's appointments
    appointments_count = PatientLog.query.filter(func.date(PatientLog.scan_time) == today).count()
    
    # Ongoing treatments
    ongoing_treatments_count = Patient.query.filter(Patient.treatment_status == 'In Progress').count()
    
    return jsonify({
        "registered_today": registered_count,
        "appointments_today": appointments_count,
        "ongoing_treatments": ongoing_treatments_count
    })


