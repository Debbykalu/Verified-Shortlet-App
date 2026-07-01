class GeneralConfig(object):
    SECRET_KEY = 'trMNfGHpxif25uzIYwU'
    TECH_SUPPORT="0809999999"
class ProConfig(GeneralConfig):
    SECRET_key="live_trMNfGHpxif25uzIYwU"
    ADMIN_EMAIL="live@admin.com"
    SQLALCHEMY_DATABASE_URI='mysql+mysqlconnector://root@localhost/shortletdb'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class TestConfig(GeneralConfig):
     ADMIN_EMAIL="test@admin.com"