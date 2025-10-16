from flask import Blueprint, render_template, request, redirect, url_for, flash,jsonify
from flask_login import login_required, current_user
from app.models import User, Patient , PatientLog ,DiseaseDesc
from app import db
from datetime import date
from sqlalchemy import func, text
import calendar
from sqlalchemy.orm import aliased

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
                disease_id=request.form.get('disease'),
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
@admin.route('/top-disease-monthly')
def top_disease_monthly():
    # Join Patient with DiseaseDesc to get disease name
    results = (
        db.session.query(
            func.extract('month', Patient.registered_at).label('month'),
            DiseaseDesc.name.label('disease_name'),
            func.count(Patient.id).label('count')
        )
        .join(DiseaseDesc, Patient.disease_id == DiseaseDesc.id)  # join on disease_id
        .group_by('month', DiseaseDesc.name)
        .all()
    )

    # Convert to dict: {month: {disease_name: count}}
    month_data = {}
    for r in results:
        m = int(r.month)  # numeric month
        if m not in month_data:
            month_data[m] = {}
        month_data[m][r.disease_name] = r.count  # use disease_name

    # For each month, get top disease
    final = []
    for m, diseases in sorted(month_data.items()):
        top_disease = max(diseases, key=diseases.get)
        final.append({
            "month": calendar.month_name[m],  # convert 4 → "April"
            "disease": top_disease,
            "count": diseases[top_disease]
        })

    return jsonify(final)

@admin.route('/dashboard-stats')
def dashboard_stats():
    # 1. Patient Registrations per Month
    registrations = (
        db.session.query(
            func.to_char(Patient.registered_at, 'FMMonth').label('month'),
            func.date_trunc('month', Patient.registered_at).label('month_order'),
            func.count(Patient.id).label('count')
        )
        .group_by('month', 'month_order')
        .order_by('month_order')
        .all()
    )

    reg_data = [{"month": r.month.strip(), "count": r.count} for r in registrations]

    # 2. Treatment counts per Month
    treatments = (
        db.session.query(
            func.to_char(Patient.registered_at, 'FMMonth').label('month'),
            func.date_trunc('month', Patient.registered_at).label('month_order'),
            Patient.treatment_type,
            func.count(Patient.id).label('count')
        )
        .group_by('month', 'month_order', Patient.treatment_type)
        .order_by('month_order')
        .all()
    )

    # Structure: month → { treatment_type: count }
    month_data = {}
    for r in treatments:
        m = r.month.strip()
        t_type = r.treatment_type or "Unknown"  # ✅ Handle None safely
        if m not in month_data:
            month_data[m] = {}
        month_data[m][t_type] = r.count

    treatment_data = [{"month": m, "treatments": t} for m, t in month_data.items()]

    return jsonify({
        "registrations": reg_data,
        "treatments": treatment_data
    })

@admin.route('/report/patient-demographics', methods=['GET'])
def patient_demographics():
    # Get date range from query params
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    # Query for age groups
    
    age_groups = [
        ('0-10', 0, 10),
        ('11-20', 11, 20),
        ('21-30', 21, 30),
        ('31-40', 31, 40),
        ('41-50', 41, 50),
        ('51-60', 51, 60),
        ('60+', 61, 200)
    ]

    age_counts = []

    for label, min_age, max_age in age_groups:
        query = Patient.query

        # Filter by date range if provided
        if start_date and end_date:
            query = query.filter(Patient.registered_at.between(start_date, end_date))

        # Use PostgreSQL interval to calculate DOB range
        query = query.filter(
            Patient.dob.between(
                func.now() - text(f"interval '{max_age} years'"),
                func.now() - text(f"interval '{min_age} years'")
            )
        )

        count = query.count()
        age_counts.append({'age_group': label, 'count': count})

    # Query top 5 diseases
    disease_alias = aliased(DiseaseDesc)

# Base query
    disease_counts_query = db.session.query(
        disease_alias.name.label("disease_name"),
        func.count(Patient.id).label("count")
    ).join(disease_alias, Patient.disease_id == disease_alias.id)

    # Apply date filter if provided
    if start_date and end_date:
        disease_counts_query = disease_counts_query.filter(Patient.registered_at.between(start_date, end_date))

    # Group, order, and limit
    disease_counts = (
        disease_counts_query
        .group_by(disease_alias.name)
        .order_by(func.count(Patient.id).desc())
        .limit(5)
        .all()
    )

    # Format for JSON
    top_diseases = [{'disease': d.disease_name, 'count': d.count} for d in disease_counts]

    return jsonify({'age_groups': age_counts, 'top_diseases': top_diseases})

@admin.route("/staff-workload-report")
def staff_workload_report():
    # Optional: allow filtering by start_date and end_date (scan_time)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    query = (
        db.session.query(
            User.first_name,
            func.count(PatientLog.id).label("patients")
        )
        .join(PatientLog, PatientLog.doctor_id == User.id)
        .filter(User.role == "Doctor")
    )

    # Apply date filter if provided
    if start_date and end_date:
        query = query.filter(PatientLog.scan_time.between(start_date, end_date))

    query = query.group_by(User.first_name)

    data = query.all()

    return jsonify([
        {"doctor": d[0], "patients": d[1]} for d in data
    ])

@admin.route("/api/diseases", methods=["GET"])
def get_diseases():
    diseases = DiseaseDesc.query.all()
    result = [{"id": d.id, "name": d.name} for d in diseases]
    return jsonify(result)





