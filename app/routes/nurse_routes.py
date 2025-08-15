from flask import Blueprint, render_template
from flask_login import login_required

nurse = Blueprint('nurse', __name__)

@nurse.route('/nurse/dashboard')
@login_required
def dashboard():
    return render_template('nurse/dashboard.html')

@nurse.route('/nurse/editprofile')
@login_required
def editprofile():
    return render_template('nurse/editprofile.html')

    