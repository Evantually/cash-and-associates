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
    OCTANE_NEWCOMER_WEBHOOK = os.environ.get('OCTANE_NEWCOMER_WEBHOOK')
    OCTANE_COMMUNITY_WEBHOOK = os.environ.get('OCTANE_COMMUNITY_WEBHOOK')
    OCTANE_ANNOUNCEMENTS_WEBHOOK = os.environ.get('OCTANE_ANNOUNCEMENTS_WEBHOOK')
    OCTANE_PROSPECT_ANNOUNCEMENT_WEBHOOK = os.environ.get('OCTANE_PROSPECT_ANNOUNCEMENT_WEBHOOK')
    OCTANE_NEWCOMER_ANNOUNCEMENT_WEBHOOK = os.environ.get('OCTANE_NEWCOMER_ANNOUNCEMENT_WEBHOOK')
    OCTANE_PROMOTIONAL_ANNOUNCEMENT_WEBHOOK = os.environ.get('OCTANE_PROMOTIONAL_ANNOUNCEMENT_WEBHOOK')
    OCTANE_CREW_WEBHOOK = os.environ.get('OCTANE_CREW_WEBHOOK')
    OCTANE_MEMBER_ANNOUNCEMENTS_WEBHOOK = os.environ.get('OCTANE_MEMBER_ANNOUNCEMENTS_WEBHOOK')
    OCTANE_MEMBER_CHAMPIONSHIP_WEBHOOK = os.environ.get('OCTANE_MEMBER_CHAMPIONSHIP_WEBHOOK')
    CALENDAR_WEBHOOK = os.environ.get('CALENDAR_WEBHOOK')
    ALERT_TESTING_WEBHOOK = os.environ.get('ALERT_TESTING_WEBHOOK')
    TESTING_WEBHOOK = os.environ.get('TESTING_WEBHOOK')
    TWOFOURNINE_OPEN_WEBHOOK = os.environ.get('TWOFOURNINE_OPEN_WEBHOOK')
    TWOFOURNINE_NB_WEBHOOK = os.environ.get('TWOFOURNINE_NB_WEBHOOK')
    TWOFOURNINE_OFFROAD_WEBHOOK = os.environ.get('TWOFOURNINE_OFFROAD_WEBHOOK')
    TWOFOURNINE_MOTO_WEBHOOK = os.environ.get('TWOFOURNINE_MOTO_WEBHOOK')
    IMGUR_ID = os.environ.get('IMGUR_ID')
    ADMINS = ['LucaPacioli@cashaccountancy.com']
    LANGUAGES = ['en', 'es']
    MS_TRANSLATOR_KEY = os.environ.get('MS_TRANSLATOR_KEY')
    POSTS_PER_PAGE = 25
