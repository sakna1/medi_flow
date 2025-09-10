from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from config import Config
from sqlalchemy_utils import database_exists, create_database
import os

# Extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # File upload configuration
    UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads/reports")
    ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg"}
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
    app.config["ALLOWED_EXTENSIONS"] = ALLOWED_EXTENSIONS

    #Check the database existance
    if not database_exists(Config.SQLALCHEMY_DATABASE_URI):
        print("Initializing database...")
        create_database(Config.SQLALCHEMY_DATABASE_URI, encoding="utf8")
        print("Database created successfully.")

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    from app.models.user import User
    from app.auth.routes import auth
    from app.routes.admin_routes import admin
    from app.routes.doctor_routes import doctor
    from app.routes.nurse_routes import nurse
    from app.routes.patient_routes import patient

    app.register_blueprint(auth)
    app.register_blueprint(admin)
    app.register_blueprint(doctor)
    app.register_blueprint(nurse)
    app.register_blueprint(patient)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    return app