import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    # ================= SECURITY =================
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'change-this-in-production'

    # ================= DATABASE =================
    SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://root:root@localhost/zero_trust_db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ================= SESSION =================
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # ================= BANK SETTINGS =================
    BANK_NAME = "Zero Trust Bank"
    SUPPORT_EMAIL = "support@zerotrustbank.com"

    # ================= TRANSACTION LIMITS =================
    DAILY_TRANSACTION_LIMIT = {
        'basic': 1000,
        'premium': 5000,
        'business': 50000,
        'employee': 100
    }

    SINGLE_TRANSACTION_LIMIT = {
        'basic': 500,
        'premium': 2000,
        'business': 10000,
        'employee': 50
    }

    # ================= RISK ENGINE =================
    RISK_THRESHOLD_LOW = 30
    RISK_THRESHOLD_MEDIUM = 60
    RISK_THRESHOLD_HIGH = 80

    # ================= MFA =================
    MFA_ISSUER_NAME = "ZeroTrustBank"

    # ================= ACCOUNT SECURITY =================
    MAX_LOGIN_ATTEMPTS = 5
    ACCOUNT_LOCKOUT_TIME = timedelta(minutes=15)

    # ================= FRAUD DETECTION =================
    VELOCITY_CHECK_MINUTES = 10
    MAX_TRANSACTIONS_PER_VELOCITY = 5
    UNUSUAL_LOCATION_THRESHOLD = 30
    NEW_DEVICE_RISK_SCORE = 25

    # ================= EMAIL CONFIG =================
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True') == 'True'
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'False') == 'True'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = MAIL_USERNAME
    MAIL_MAX_EMAILS = None
    MAIL_ASCII_ATTACHMENTS = False

    # ================= TWILIO VERIFY CONFIG =================
    TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN  = os.environ.get('TWILIO_AUTH_TOKEN')
    TWILIO_VERIFY_SID  = os.environ.get('TWILIO_VERIFY_SID')