from flask import Flask, app, jsonify, request, session
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from dotenv import load_dotenv
from werkzeug.exceptions import RequestEntityTooLarge
from pkg.notification_routes import notification_bp
from pkg.notification_api import notification_api
from pkg.notification_service import NotificationService
from pkg.utils.time_helper import time_ago

from pkg.config import ProConfig

csrf = CSRFProtect()

def create_app():
    from pkg.models import db

    # Load .env values before app config objects are initialized.
    load_dotenv()

    app= Flask(__name__,instance_relative_config=True)
    app.config.from_pyfile('config.py')
    app.config.from_object(ProConfig)
    
    app.register_blueprint(notification_bp)
    app.register_blueprint(notification_api)
    app.jinja_env.globals["time_ago"] = time_ago
   
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
    @app.context_processor
    def inject_notifications():
        user_id = session.get("useronline")

        if not user_id:
            return dict(
                notifications=[],
                unread_notifications=0
            )

        notifications = NotificationService.get_notifications(user_id)
        unread = NotificationService.unread_count(user_id)

        return dict(
            notifications=notifications,
            unread_notifications=unread
        )

    return app
app = create_app()
from pkg import routes, user_routes, admin_routes, forms
