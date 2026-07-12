from datetime import datetime

from flask import (
    Blueprint,
    jsonify,
    render_template,
    session,
    redirect,
    url_for,
    abort
)

from pkg.notification_service import NotificationService
from pkg.models import Notification
from pkg.utils.notification_helper import NotificationHelper

notification_bp = Blueprint(
    "notification",
    __name__,
    url_prefix="/notifications"
)


@notification_bp.route("/")
def all_notifications():

    user_id = session.get("useronline")

    if not user_id:
        abort(403)

    notifications = NotificationService.get_notifications(user_id)

    return render_template(
        "user/notifications.html",
        notifications=notifications
    )
@notification_bp.route("/<int:notification_id>")
def notification_detail(notification_id):

    user_id = session.get("useronline")

    if not user_id:
        return redirect(url_for("login"))

    notification = Notification.query.filter_by(
        notification_id=notification_id,
        recipient_user_id=user_id
    ).first_or_404()

    if not notification.notification_is_read:

        notification.notification_is_read = True

        notification.notification_read_at = datetime.utcnow()

        from pkg.models import db

        db.session.commit()

    action = NotificationHelper.get_action(notification)

    return render_template(
        "user/notification_detail.html",
        notification=notification,
        action=action
    )
@notification_bp.route("/unread-count")
def unread_count():

    user_id = session.get("useronline")

    if not user_id:
        return jsonify({"count": 0})

    return jsonify({
        "count": NotificationService.unread_count(user_id)
    })

@notification_bp.route(
    "/<int:notification_id>/read",
    methods=["POST"]
)
def mark_read(notification_id):

    user_id = session.get("useronline")

    NotificationService.mark_as_read(
        notification_id,
        user_id
    )

    return jsonify({

        "success": True,

        "count": NotificationService.unread_count(user_id)

    })