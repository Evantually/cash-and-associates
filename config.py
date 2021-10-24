import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL2') or \
        'postgresql://postgres:10$Erpants@localhost:5432/cashassociates'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    OCTANE_MEMBER_WEBHOOK = os.environ.get('OCTANE_MEMBER_WEBHOOK')
    OCTANE_PROSPECT_WEBHOOK = os.environ.get('OCTANE_PROSPECT_WEBHOOK')
    OCTANE_ALERT_WEBHOOK = os.environ.get('OCTANE_ALERT_WEBHOOK')
    ALERT_TESTING_WEBHOOK = os.environ.get('ALERT_TESTING_WEBHOOK')
    TWOFOURNINE_OPEN_WEBHOOK = os.environ.get('TWOFOURNINE_OPEN_WEBHOOK')
    TWOFOURNINE_NB_WEBHOOK = os.environ.get('TWOFOURNINE_NB_WEBHOOK')
    TWOFOURNINE_OFFROAD_WEBHOOK = os.environ.get('TWOFOURNINE_OFFROAD_WEBHOOK')
    TWOFOURNINE_MOTO_WEBHOOK = os.environ.get('TWOFOURNINE_MOTO_WEBHOOK')
    ADMINS = ['your-email@example.com']
    LANGUAGES = ['en', 'es']
    MS_TRANSLATOR_KEY = os.environ.get('MS_TRANSLATOR_KEY')
    POSTS_PER_PAGE = 25
