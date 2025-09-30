from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.models.user import User
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
        user = User.query.filter((User.username == identifier) | (User.email == identifier)).first()

        if not user:
         flash("User not found. Please check your username or email.")
        elif not user.check_password(password):
         flash("Wrong password, try again.")
        else:
         login_user(user) 
         session["login_type"] = "user"          
         return redirect(url_for(f"{user.role.lower()}.dashboard"))
    return render_template('login.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop("login_type", None) 
    return redirect(url_for('auth.login'))
    