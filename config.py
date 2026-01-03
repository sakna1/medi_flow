import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    if SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv('SECRET_KEY', 'devsecret')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')    

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,    # check connection health
        "pool_recycle": 300,      # recycle connections every 5 minutes
        "pool_timeout": 10,       # wait max 10 seconds before raising timeout
        "pool_size": 10,          # number of persistent connections
        "max_overflow": 20        # extra connections allowed temporarily
    }
