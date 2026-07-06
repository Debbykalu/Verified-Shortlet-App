from decimal import Decimal
from sqlalchemy.orm import joinedload

from pkg.models import Admin, BookingDetail, BookingPayment, Property, User, db


class AdminDashboardService:
    def __init__(self):
        self.db = db

    def get_dashboard_context(self, admin_id):
        deets = Admin.query.get(admin_id)

        total_users = User.query.count()
        verified_hosts = User.query.filter_by(user_role="host", is_verified=True).count()
        total_properties = Property.query.count()

        bookings_query = (
            BookingDetail.query.options(
                joinedload(BookingDetail.user),
                joinedload(BookingDetail.property),
            )
            .order_by(BookingDetail.created_at.desc())
        )
        all_bookings = bookings_query.all()

        payments_query = (
            BookingPayment.query.options(
                joinedload(BookingPayment.user),
                joinedload(BookingPayment.booking_detail),
                joinedload(BookingPayment.booking_detail).joinedload(BookingDetail.property),
            )
            .order_by(BookingPayment.booking_payment_date.desc())
        )
        all_payments = payments_query.all()

        total_revenue = sum(
            (payment.booking_amount or Decimal("0"))
            for payment in all_payments
            if payment.booking_payment_status == "paid"
        )

        total_bookings = len(all_bookings)
        paid_bookings = sum(1 for booking in all_bookings if booking.booking_status == "paid")
        pending_payment_bookings = sum(
            1 for booking in all_bookings if booking.booking_status == "pending_payment"
        )
        paid_payments = sum(1 for payment in all_payments if payment.booking_payment_status == "paid")
        pending_payments = sum(
            1 for payment in all_payments if payment.booking_payment_status == "pending"
        )

        properties = (
            Property.query.order_by(Property.prop_id.desc())
            .all()
        )
        pending_hosts = (
            User.query.filter(User.user_role == "host", User.is_verified.is_(False))
            .order_by(User.user_timecreated.desc())
            .limit(5)
            .all()
        )
        pending_properties = (
            Property.query.filter_by(is_verified=False)
            .order_by(Property.prop_id.desc())
            .limit(5)
            .all()
        )
        recent_bookings = all_bookings
        recent_payments = all_payments

        return {
            "deets": deets,
            "properties": properties,
            "stats": {
                "total_users": total_users,
                "verified_hosts": verified_hosts,
                "total_properties": total_properties,
                "total_revenue": total_revenue,
                "total_bookings": total_bookings,
                "paid_bookings": paid_bookings,
                "pending_payment_bookings": pending_payment_bookings,
                "paid_payments": paid_payments,
                "pending_payments": pending_payments,
            },
            "pending_hosts": pending_hosts,
            "pending_properties": pending_properties,
            "recent_bookings": recent_bookings,
            "recent_payments": recent_payments,
        }

    def delete_property(self, property_id):
        property_item = Property.query.get(property_id)
        if not property_item:
            return None

        self.db.session.delete(property_item)
        self.db.session.commit()
        return property_item

    def update_property_status(self, property_id, status):
        property_item = Property.query.get(property_id)
        if not property_item:
            return None

        allowed_statuses = {"available", "booked", "inactive"}
        if status not in allowed_statuses:
            raise ValueError("Invalid status")

        property_item.prop_availability_status = status
        self.db.session.commit()
        return property_item

    def verify_property(self, property_id, verified=True):
        property_item = Property.query.get(property_id)
        if not property_item:
            return None

        property_item.is_verified = verified
        if verified:
            property_item.prop_availability_status = "available"
        else:
            property_item.prop_availability_status = "inactive"
        self.db.session.commit()
        return property_item

    def verify_host(self, user_id, verified=True):
        user = User.query.get(user_id)
        if not user:
            return None

        user.is_verified = verified
        self.db.session.commit()
        return user
