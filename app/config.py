import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR.parent / '.env')


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///signx.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    STORAGE_DIR = os.getenv('STORAGE_DIR', str(BASE_DIR / 'storage'))
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'localhost')
    MAIL_PORT = int(os.getenv('MAIL_PORT', '25'))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'false').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'no-reply@signx.local')
    SCHEDULER_API_ENABLED = True
    APSCHEDULER_JOBSTORES = {
        'default': {
            'type': 'sqlalchemy',
            'url': SQLALCHEMY_DATABASE_URI,
        }
    }
    APSCHEDULER_EXECUTORS = {
        'default': {'type': 'threadpool', 'max_workers': 5},
    }
    APSCHEDULER_JOB_DEFAULTS = {
        'coalesce': False,
        'max_instances': 1,
    }
    REMEMBER_COOKIE_DURATION = timedelta(days=14)


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


config_by_name = {
    'development': Config,
    'testing': TestingConfig,
    'production': Config,
}


def get_config(name: str | None = None):
    name = name or os.getenv('FLASK_ENV', 'development')
    return config_by_name.get(name, Config)
