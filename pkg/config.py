import os


class GeneralConfig:
    TECH_SUPPORT = "0809999999"

    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "change-me-in-production"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY")
    PAYSTACK_PUBLIC_KEY = os.getenv("PAYSTACK_PUBLIC_KEY")
    PAYSTACK_CALLBACK_URL = os.getenv("PAYSTACK_CALLBACK_URL")
    PAYSTACK_WEBHOOK_URL = os.getenv("PAYSTACK_WEBHOOK_URL")


class ProConfig(GeneralConfig):

    ADMIN_EMAIL = os.getenv(
        "ADMIN_EMAIL",
        "admin@example.com"
    )

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+mysqlconnector://"
        f"{os.getenv('MYSQL_USER', 'appuser')}:"
        f"{os.getenv('MYSQL_PASSWORD', 'appuserpass')}@"
        # `mysql` is a Compose-only DNS name.  Compose injects it for the
        # container; local Flask commands connect through the loopback port.
        f"{os.getenv('MYSQL_HOST', '127.0.0.1')}:"
        f"{os.getenv('MYSQL_PORT', '3307')}/"
        f"{os.getenv('MYSQL_DATABASE', 'shortletdb')}"
    )


class TestConfig(GeneralConfig):

    TESTING = True

    ADMIN_EMAIL = "test@admin.com"
