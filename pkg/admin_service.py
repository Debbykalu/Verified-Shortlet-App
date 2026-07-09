from datetime import datetime
from decimal import Decimal
from sqlalchemy import or_
from sqlalchemy.orm import joinedload

from pkg.models import Admin, BookingDetail, BookingPayment, Property, User, db


class AdminDashboardService:
    def __init__(self):
        self.db = db

    def get_dashboard_context(
        self,
        admin_id,
        host_page=1,
        host_per_page=10,
        host_search=None,
        host_status=None,
        property_page=1,
        property_per_page=10,
        property_search=None,
        property_status="pending",
        booking_page=1,
        booking_per_page=10,
        booking_search=None,
        booking_status=None,
        payment_page=1,
        payment_per_page=10,
        payment_search=None,
        payment_status=None,
    ):
        deets = Admin.query.get(admin_id)

        total_users = User.query.count()
        verified_hosts = User.query.filter(
            User.user_role == "host",
            or_(
                User.verification_status == "Verified",
                User.is_verified.is_(True),
            ),
        ).count()
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

        properties = Property.query.order_by(Property.prop_id.desc()).all()

        hosts_query = (
            User.query.filter(User.user_role == "host")
            .order_by(User.user_timecreated.desc())
        )
        if host_search:
            host_search_like = f"%{host_search.strip()}%"
            hosts_query = hosts_query.filter(
                or_(
                    User.user_firstname.ilike(host_search_like),
                    User.user_lastname.ilike(host_search_like),
                    User.user_email.ilike(host_search_like),
                    User.nin_number.ilike(host_search_like),
                )
            )
        if host_status in ("Pending", "Verified", "Suspended"):
            hosts_query = hosts_query.filter(User.verification_status == host_status)
        pending_hosts_pagination = hosts_query.paginate(page=host_page, per_page=host_per_page, error_out=False)
        pending_hosts = pending_hosts_pagination.items

        properties_query = Property.query.options(
            joinedload(Property.user),
            joinedload(Property.property_type),
        ).order_by(Property.prop_id.desc())
        if property_search:
            property_search_like = f"%{property_search.strip()}%"
            properties_query = properties_query.filter(
                or_(
                    Property.prop_title.ilike(property_search_like),
                    Property.prop_address.ilike(property_search_like),
                    Property.prop_city.ilike(property_search_like),
                )
            )
        normalized_property_status = (property_status or "").strip().lower()
        if normalized_property_status == "pending":
            properties_query = properties_query.filter(Property.is_verified.is_(False))
        elif normalized_property_status == "approved":
            properties_query = properties_query.filter(Property.is_verified.is_(True))
        elif normalized_property_status in ("available", "booked", "inactive"):
            properties_query = properties_query.filter(Property.prop_availability_status == normalized_property_status)
        pending_properties_pagination = properties_query.paginate(
            page=property_page,
            per_page=property_per_page,
            error_out=False,
        )
        pending_properties = pending_properties_pagination.items

        filtered_bookings_query = (
            BookingDetail.query.options(
                joinedload(BookingDetail.user),
                joinedload(BookingDetail.property),
                joinedload(BookingDetail.payments),
            )
            .order_by(BookingDetail.created_at.desc())
        )
        if booking_search:
            booking_search_like = f"%{booking_search.strip()}%"
            filtered_bookings_query = filtered_bookings_query.join(Property, BookingDetail.booking_propid == Property.prop_id).filter(
                or_(
                    Property.prop_title.ilike(booking_search_like),
                    BookingDetail.full_name.ilike(booking_search_like),
                    BookingDetail.full_email.ilike(booking_search_like),
                )
            )
        if booking_status in ("paid", "pending_payment", "cancelled"):
            filtered_bookings_query = filtered_bookings_query.filter(BookingDetail.booking_status == booking_status)
        recent_bookings_pagination = filtered_bookings_query.paginate(
            page=booking_page,
            per_page=booking_per_page,
            error_out=False,
        )
        recent_bookings = recent_bookings_pagination.items

        filtered_payments_query = (
            BookingPayment.query.options(
                joinedload(BookingPayment.user),
                joinedload(BookingPayment.booking_detail),
                joinedload(BookingPayment.booking_detail).joinedload(BookingDetail.property),
            )
            .order_by(BookingPayment.booking_payment_date.desc())
        )
        if payment_search:
            payment_search_like = f"%{payment_search.strip()}%"
            filtered_payments_query = filtered_payments_query.outerjoin(User, BookingPayment.booking_userid == User.user_id).filter(
                or_(
                    User.user_firstname.ilike(payment_search_like),
                    User.user_lastname.ilike(payment_search_like),
                    User.user_email.ilike(payment_search_like),
                )
            )
        if payment_status in ("paid", "pending", "failed"):
            filtered_payments_query = filtered_payments_query.filter(
                BookingPayment.booking_payment_status == payment_status
            )
        recent_payments_pagination = filtered_payments_query.paginate(
            page=payment_page,
            per_page=payment_per_page,
            error_out=False,
        )
        recent_payments = recent_payments_pagination.items

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
            "pending_hosts_pagination": pending_hosts_pagination,
            "pending_properties": pending_properties,
            "pending_properties_pagination": pending_properties_pagination,
            "recent_bookings": recent_bookings,
            "recent_bookings_pagination": recent_bookings_pagination,
            "recent_payments": recent_payments,
            "recent_payments_pagination": recent_payments_pagination,
            "filters": {
                "host_search": host_search or "",
                "host_status": host_status or "",
                "property_search": property_search or "",
                "property_status": normalized_property_status or "pending",
                "booking_search": booking_search or "",
                "booking_status": booking_status or "",
                "payment_search": payment_search or "",
                "payment_status": payment_status or "",
            },
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

    def get_host_verification_records(self):
        return (
            User.query.filter(User.user_role == "host")
            .order_by(User.user_timecreated.desc())
            .all()
        )

    def get_host_verification_status(self, user):
        if user.verification_status in ("Pending", "Verified", "Suspended"):
            return user.verification_status
        return "Verified" if user.is_verified else "Pending"

    def build_nimc_verification_payload(self, user):
        # Placeholder for future NIMC/NIMS integration.
        return {
            "host_user_id": user.user_id,
            "nin_number": user.nin_number,
            "full_name": f"{user.user_firstname} {user.user_lastname}",
            "registered_at": user.user_timecreated.isoformat() if user.user_timecreated else None,
        }

    def mark_host_verified(self, user_id, admin_id):
        user = User.query.get(user_id)
        if not user or user.user_role != "host":
            return None

        # Extension point for future NIMC/NIMS API integration.
        _nimc_payload = self.build_nimc_verification_payload(user)

        user.verification_status = "Verified"
        user.verified_at = datetime.utcnow()
        user.verified_by = admin_id
        user.verification_reason = None
        user.is_verified = True

        self.db.session.commit()
        return user

    def mark_host_suspended(self, user_id, admin_id, reason=None):
        user = User.query.get(user_id)
        if not user or user.user_role != "host":
            return None

        user.verification_status = "Suspended"
        user.verified_at = datetime.utcnow()
        user.verified_by = admin_id
        user.verification_reason = (reason or "").strip() or None
        user.is_verified = False

        self.db.session.commit()
        return user
