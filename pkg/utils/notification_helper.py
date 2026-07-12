from flask import url_for


class NotificationHelper:

    @staticmethod
    def get_action(notification):

        ref_type = notification.notification_reference_type
        ref_id = notification.notification_reference_id

        if ref_type == "booking":

            return {

                "text": "View Booking",

                "url": url_for(
                    "booking_details",
                    booking_id=ref_id
                )

            }

        if ref_type == "property":

            return {

                "text": "View Property",

                "url": url_for(
                    "property_detail",
                    property_id=ref_id
                )

            }

        if ref_type == "review":

            return {

                "text": "View Review",

                "url": url_for(
                    "review_detail",
                    review_id=ref_id
                )

            }

        if ref_type == "dashboard":

            return {

                "text": "Go to Dashboard",

                "url": url_for("host_dashboard")

            }

        return {

            "text": "Back Home",

            "url": url_for("home")

        }