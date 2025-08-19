from flask import Blueprint, render_template
from flask_login import login_required
from flask_login import current_user

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

    