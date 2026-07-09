from flask import Flask, jsonify, request
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from dotenv import load_dotenv
from werkzeug.exceptions import RequestEntityTooLarge


from pkg.config import ProConfig

csrf = CSRFProtect()

def create_app():
    from pkg.models import db

    # Load .env values before app config objects are initialized.
    load_dotenv()

    app= Flask(__name__,instance_relative_config=True)
    app.config.from_pyfile('config.py')
    app.config.from_object(ProConfig)

   
    db.init_app(app)
    migrate  = Migrate(app,db)
    csrf.init_app(app)

    @app.errorhandler(RequestEntityTooLarge)
    def handle_request_entity_too_large(_error):
        max_bytes = int(app.config.get("MAX_CONTENT_LENGTH", 0) or 0)
        max_mb = max_bytes / (1024 * 1024) if max_bytes else 0
        message = (
            f"Upload too large. Maximum total upload size is {max_mb:.0f}MB. "
            "Please reduce image sizes or upload fewer files."
        )

        # Upload forms submit with AJAX and expect JSON.
        if request.path in ("/save-property/", "/host/property/add"):
            return jsonify({"status": "error", "message": message}), 413

        return message, 413

    return app
app = create_app()
from pkg import routes, user_routes, admin_routes, forms
