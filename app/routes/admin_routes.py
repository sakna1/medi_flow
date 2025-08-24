from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import User, Patient
from app import db

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
            # return render_template('login.html')

        return render_template('register.html')
    else:
        return "Access denied", 403

@admin.route('/admin/dashboard')
@login_required
def dashboard():
    admin_name = current_user.username
    return render_template('admin/dashboard.html',admin_name=admin_name)

@admin.route('/admin/register', methods=['GET', 'POST'])
@login_required
def register_user():
    if current_user.role != 'Admin':
        return "Access denied", 403

    if request.method == 'POST':
        if request.form['role'].lower() == 'patient':
            user = Patient(
                username=request.form['username'],
                email=request.form['email'],
                first_name=request.form['first_name'],
                last_name=request.form['last_name'],
                gender=request.form['gender'],                
                )
        else:
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

        if request.form['role'].lower() == 'doctor':
            user.specialization = request.form['specialization']
        elif request.form['role'].lower() == 'patient':
            user.address = request.form['address']
            user.disease = request.form['disease'] if 'disease' in request.form else ''
            user.phone = request.form['phone']

        db.session.add(user)
        db.session.commit()
        flash("registered successfully.")
        return redirect(url_for('admin.dashboard'))

    return render_template('register.html')


@admin.route('/admin/editprofile')
@login_required
def editprofile():
    admin_name = current_user.username
    return render_template('admin/editprofile.html',admin_name=admin_name)