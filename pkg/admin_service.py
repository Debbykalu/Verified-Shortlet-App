from decimal import Decimal

from pkg.models import Admin, Booking, Property, User, db


class AdminDashboardService:
    def __init__(self):
        self.db = db

    def get_dashboard_context(self, admin_id):
        deets = Admin.query.get(admin_id)

        total_users = User.query.count()
        verified_hosts = User.query.filter_by(user_role="host", is_verified=True).count()
        total_properties = Property.query.count()
        total_revenue = sum(
            (booking.total_amount or Decimal("0")) for booking in Booking.query.filter(Booking.booking_status.in_(["confirmed", "completed"]))
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
        recent_bookings = (
            Booking.query.order_by(Booking.created_at.desc())
            .limit(5)
            .all()
        )
        recent_payments = (
            Booking.query.filter(Booking.booking_status.in_(["confirmed", "completed"]))
            .order_by(Booking.created_at.desc())
            .limit(5)
            .all()
        )

        return {
            "deets": deets,
            "properties": properties,
            "stats": {
                "total_users": total_users,
                "verified_hosts": verified_hosts,
                "total_properties": total_properties,
                "total_revenue": total_revenue,
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
        self.db.session.commit()
        return property_item

    def verify_host(self, user_id, verified=True):
        user = User.query.get(user_id)
        if not user:
            return None

        user.is_verified = verified
        self.db.session.commit()
        return user
