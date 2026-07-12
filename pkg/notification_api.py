from flask import Blueprint, jsonify, session

from pkg.notification_service import NotificationService
from pkg.utils.time_helper import time_ago

notification_api = Blueprint(
    "notification_api",
    __name__
)


@notification_api.route("/api/notifications/")
def notifications():

    user_id = session.get("useronline")

    if not user_id:
        return jsonify([])

    notifications = NotificationService.get_notifications(user_id)

    return jsonify([
        {
            "id": n.notification_id,
            "title": n.notification_title,
            "message": n.notification_message,
            "icon": n.notification_icon,
            "type": n.notification_type,
            "link": n.notification_link,
            "is_read": n.notification_is_read,
            "time": time_ago(n.notification_timecreated)
        }
        for n in notifications
    ])
@notification_api.route("/api/notifications/unread-count/")
def unread_count():

    user_id = session.get("useronline")

    if not user_id:
        return jsonify({"count": 0})

    return jsonify({
        "count": NotificationService.unread_count(user_id)
    })
@notification_api.route(
    "/api/notifications/<int:notification_id>/read/",
    methods=["POST"]
)
def mark_read(notification_id):

    user_id = session.get("useronline")

    NotificationService.mark_as_read(
        notification_id,
        user_id
    )

    return jsonify({
        "success": True
    })
