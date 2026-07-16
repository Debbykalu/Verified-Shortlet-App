import os
from dotenv import load_dotenv

load_dotenv()


class GeneralConfig(object):
    SECRET_KEY = os.getenv('SECRET_KEY', 'change-me-in-production').strip()
    TECH_SUPPORT="0809999999"


class ProConfig(GeneralConfig):
    SECRET_key="live_trMNfGHpxif25uzIYwU"
    ADMIN_EMAIL="live@admin.com"
    SQLALCHEMY_DATABASE_URI='mysql+mysqlconnector://root@localhost/shortletdb'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', '').strip()
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', GeneralConfig.SECRET_KEY).strip()
    JWT_ACCESS_TOKEN_EXPIRES_MINUTES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES_MINUTES', '15'))
    JWT_REFRESH_TOKEN_EXPIRES_DAYS = int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES_DAYS', '14'))
    JWT_ISSUER = os.getenv('JWT_ISSUER', 'verified-shortlet-api').strip()
    JWT_AUDIENCE = os.getenv('JWT_AUDIENCE', 'verified-shortlet-client').strip()
    JWT_CLOCK_SKEW_SECONDS = int(os.getenv('JWT_CLOCK_SKEW_SECONDS', '30'))
    # Request-wide payload cap (all files + form fields). Increased for multi-image property uploads.
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', str(30 * 1024 * 1024)))
    # Per-file cap used by strict upload validators (e.g. NIN docs).
    MAX_UPLOAD_FILE_BYTES = int(os.getenv('MAX_UPLOAD_FILE_BYTES', str(10 * 1024 * 1024)))
    ALLOWED_UPLOAD_EXTENSIONS = tuple(
        item.strip().lower() for item in os.getenv('ALLOWED_UPLOAD_EXTENSIONS', 'jpg,jpeg,png,webp').split(',') if item.strip()
    )
    ALLOWED_UPLOAD_MIME_TYPES = tuple(
        item.strip().lower() for item in os.getenv('ALLOWED_UPLOAD_MIME_TYPES', 'image/jpeg,image/png,image/webp').split(',') if item.strip()
    )
    PAYSTACK_SECRET_KEY = os.getenv('PAYSTACK_SECRET_KEY', '').strip()
    PAYSTACK_PUBLIC_KEY = os.getenv('PAYSTACK_PUBLIC_KEY', '').strip()
    PAYSTACK_CALLBACK_URL = os.getenv('PAYSTACK_CALLBACK_URL', '').strip()
    PAYSTACK_WEBHOOK_URL = os.getenv('PAYSTACK_WEBHOOK_URL', '').strip()
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'private_uploads').strip()

class TestConfig(GeneralConfig):
     ADMIN_EMAIL="test@admin.com"