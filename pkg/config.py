import os


class GeneralConfig(object):
    SECRET_KEY = 'trMNfGHpxif25uzIYwU'
    TECH_SUPPORT="0809999999"


class ProConfig(GeneralConfig):
    SECRET_key="live_trMNfGHpxif25uzIYwU"
    ADMIN_EMAIL="live@admin.com"
    SQLALCHEMY_DATABASE_URI='mysql+mysqlconnector://root@localhost/shortletdb'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PAYSTACK_SECRET_KEY = os.getenv('PAYSTACK_SECRET_KEY', '').strip()
    PAYSTACK_PUBLIC_KEY = os.getenv('PAYSTACK_PUBLIC_KEY', '').strip()
    PAYSTACK_CALLBACK_URL = os.getenv('PAYSTACK_CALLBACK_URL', '').strip()
    PAYSTACK_WEBHOOK_URL = os.getenv('PAYSTACK_WEBHOOK_URL', '').strip()


class TestConfig(GeneralConfig):
     ADMIN_EMAIL="test@admin.com"