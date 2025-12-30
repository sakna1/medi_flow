from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User, Patient 
from werkzeug.security import generate_password_hash
from app import db
from flask import session

auth = Blueprint('auth', __name__)

@auth.route('/')
def index():
    return render_template('index.html')

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form['username']
        password = request.form['password']

        # Check by username OR email
        user = User.query.filter(
            (User.username == identifier) | (User.email == identifier)
        ).first()

        if user and user.check_password(password):            
            login_user(user)

            # set login_type based on role
            if user.role.lower() == "patient":
                session["login_type"] = "patient"
            else:
                session["login_type"] = "user"

            return redirect(url_for(f"{user.role.lower()}.dashboard"))
        else:            
            flash("Invalid username or password.", "error")
            return redirect(url_for('auth.login'))

    return render_template('login.html')

@auth.route('/logout')
@login_required
def logout():
    login_type = session.get("login_type")
    logout_user()
    session.pop("login_type", None)

    if login_type == "patient":
        return redirect(url_for('patient.user_login'))
    else:
        return redirect(url_for('auth.login'))


@auth.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form.get('username')
        new_password = request.form.get('new_password')
        hashed_password = generate_password_hash(new_password)

        patient = Patient.query.filter_by(username=username).first()
        user = User.query.filter_by(username=username).first()

        if patient:
            patient.password_hash = hashed_password
            db.session.commit()
            flash("Password changed successfully.", "success")
            return redirect(url_for('patient.user_login'))

        elif user:
            user.password_hash = hashed_password
            db.session.commit()
            flash("Password changed successfully.", "success")
            return redirect(url_for('auth.login'))

        else:
            flash("Invalid username or password.", "error")
            return redirect(url_for('auth.forgot_password'))

    return render_template('forgot_password.html')
    