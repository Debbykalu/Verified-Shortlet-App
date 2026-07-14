from datetime import datetime

from pkg.models import db, Notification

from pkg.utils.notification_constants import NotificationType

class NotificationService:

    @staticmethod
    def notify(
        user_id,
        title,
        message,
        notification_type,
        reference_type=None,
        reference_id=None
    ):
     if not user_id:
         return None

     return NotificationService.create_notification(

        recipient_user_id=user_id,

        title=title,

        message=message,

        notification_type=notification_type,

        icon=NotificationService._get_icon(notification_type),

        reference_type=reference_type,

        reference_id=reference_id

    )
    
    @staticmethod
    def _get_icon(notification_type):
        """
        Returns the appropriate Font Awesome icon for a notification type.
        """
        icons = {

        NotificationType.BOOKING_CREATED: "calendar",
        NotificationType.BOOKING_CONFIRMED: "calendar-check",
        NotificationType.PAYMENT_SUCCESS: "circle-check",
        NotificationType.PAYMENT_FAILED: "circle-xmark",
        NotificationType.BOOKING_CANCELLED: "ban",
        NotificationType.BOOKING_COMPLETED: "star",
        NotificationType.HOST_NEW_BOOKING: "house",
        NotificationType.HOST_VERIFIED: "shield-halved",
        NotificationType.HOST_VERIFICATION_FAILED: "triangle-exclamation",
        NotificationType.PROPERTY_APPROVED: "house",
        NotificationType.PROPERTY_REJECTED: "house-circle-xmark",
        NotificationType.REVIEW_RECEIVED: "message",
        NotificationType.REFUND_PROCESSED: "money-bill-wave",
        NotificationType.SYSTEM: "bell"

        }
        return icons.get(notification_type, "bell")

    
    @staticmethod
    def payment_success(booking_detail):
     """
     Notify customer that payment was successful.
     """

     return NotificationService.notify(

    user_id=booking_detail.booking_userid,

    title="Payment Successful",

    message=(
        f"Your payment for "
        f"{booking_detail.property.prop_title} "
        f"was successful."
    ),

    notification_type=NotificationType.PAYMENT_SUCCESS,

    reference_type="booking",

    reference_id=booking_detail.booking_detail_id

)

    
    @staticmethod
    def payment_failed(booking_detail):
      """
      Notify customer that payment failed.
      """

      return NotificationService.notify(

        user_id=booking_detail.booking_userid,

        title="Payment Failed",

        message="Your payment could not be completed. Please try again.",

        notification_type=NotificationType.PAYMENT_FAILED,

        reference_type="booking",
        reference_id=booking_detail.booking_detail_id

    )
    @staticmethod
    def host_new_booking(booking_detail):
      """
      Notify the host that a new booking has been received.
      """

      return NotificationService.notify(

        user_id=booking_detail.property.prop_userid,

        title="New Booking",

        message=f"{booking_detail.full_name} booked your property '{booking_detail.property.prop_title}'.",

        notification_type=NotificationType.HOST_NEW_BOOKING,

        reference_type="booking",
        reference_id=booking_detail.booking_detail_id

    )

    @staticmethod
    def booking_created(booking_detail):
      """
      Notify customer that a booking has been created.
      """

      return NotificationService.notify(

        user_id=booking_detail.booking_userid,

        title="Booking Created",

        message=f"Your booking for {booking_detail.property.prop_title} has been created successfully.",

        notification_type=NotificationType.BOOKING_CREATED,

        reference_type="booking",
        reference_id=booking_detail.booking_detail_id

    )

    @staticmethod
    def create_notification(
        recipient_user_id,
        title,
        message,
        notification_type,
        icon="bell",
        reference_type=None,
        reference_id=None
    ):
        """
        Low-level method responsible for persisting notifications.
        """
        try:
            notification = Notification(
                recipient_user_id=recipient_user_id,
                notification_title=title,
                notification_message=message,
                notification_type=notification_type,
                notification_icon=icon,
                notification_reference_type=reference_type,
                notification_reference_id=reference_id
            )

            db.session.add(notification)
            db.session.commit()
            return notification

        except Exception:
            db.session.rollback()
            raise
    
    @staticmethod
    def get_notifications(user_id):
      """
      Returns all notifications for a user, newest first.
      """

      return Notification.query.filter_by(
        recipient_user_id=user_id
    ).order_by(
        Notification.notification_timecreated.desc()
    ).all()

    @staticmethod
    def unread_count(user_id):
      """
      Returns the number of unread notifications.
      """

      return Notification.query.filter_by(
        recipient_user_id=user_id,
        notification_is_read=False
    ).count()

    @staticmethod
    def mark_all_as_read(user_id):

        notifications = Notification.query.filter_by(
            recipient_user_id=user_id,
            notification_is_read=False
        ).all()

        for notification in notifications:
            notification.notification_is_read = True

        db.session.commit()
    
    @staticmethod
    def mark_as_read(notification_id, user_id):

       notification = Notification.query.filter_by(
            notification_id=notification_id,
            recipient_user_id=user_id
        ).first()

       if not notification:
          return None

       notification.notification_is_read = True
       notification.notification_read_at = datetime.utcnow()

       db.session.commit()

       return notification
    @staticmethod
    def host_verified(user):
      """
      Notify host that identity verification was approved.
      """

      return NotificationService.notify(

        user_id=user.user_id,

        title="Identity Verified",

        message="Congratulations! Your identity verification has been approved. You can now publish verified properties.",

        notification_type=NotificationType.HOST_VERIFIED,

        reference_type="dashboard",
        reference_id=None,
      )
    
    @staticmethod
    def host_verification_failed(user, reason=None):

      message = "Unfortunately your identity verification was rejected."

      if reason:
        message += f" Reason: {reason}"

      return NotificationService.notify(

        user_id=user.user_id,

        title="Verification Rejected",

        message=message,

        notification_type=NotificationType.HOST_VERIFICATION_FAILED,

        reference_type="verification",

        reference_id=None
      )
    @staticmethod
    def property_approved(property):

        return NotificationService.notify(

             user_id=property.prop_userid,

            title="Property Approved",

            message=f"'{property.prop_title}' has been approved and is now visible to guests.",

            notification_type=NotificationType.PROPERTY_APPROVED,

            reference_type="property",

            reference_id=property.prop_id
        )
    @staticmethod
    def property_rejected(property, reason=None):

         message = f"'{property.prop_title}' was not approved."

         if reason:
            message += f" Reason: {reason}"

         return NotificationService.notify(

            user_id=property.prop_userid,

            title="Property Rejected",

            message=message,

            notification_type=NotificationType.PROPERTY_REJECTED,

            reference_type="property",

            reference_id=property.prop_id
        )
    @staticmethod
    def booking_cancelled(booking):

        return NotificationService.notify(

             user_id=booking.booking_userid,

             title="Booking Cancelled",

             message=f"Your booking for {booking.property.prop_title} has been cancelled.",

             notification_type=NotificationType.BOOKING_CANCELLED,

             reference_type="booking",

             reference_id=booking.booking_detail_id
        )
    @staticmethod
    def booking_completed(booking):

           return NotificationService.notify(

                user_id=booking.booking_userid,

                title="Stay Completed",

                message=f"Thank you for staying at {booking.property.prop_title}.",

                notification_type=NotificationType.BOOKING_COMPLETED,

                reference_type="booking",

                reference_id=booking.booking_detail_id
            )
    @staticmethod
    def review_received(review):

        return NotificationService.notify(

            user_id=review.property.prop_userid,

            title="New Review",

            message=f"You received a new review for {review.property.prop_title}.",

            notification_type=NotificationType.REVIEW_RECEIVED,

          reference_type="property",

          reference_id=review.property.prop_id
        )