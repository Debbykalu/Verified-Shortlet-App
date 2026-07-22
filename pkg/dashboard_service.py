import os
import uuid
from decimal import Decimal
from datetime import datetime, date
from sqlalchemy import or_, and_, func
from sqlalchemy.orm import joinedload
from flask import current_app
from pkg.models import (
    User,
    Property,
    PropertyType,
    PropertyState,
    PropertyLGA,
    Amenity,
    PropertyAmenity,
    BookingDetail,
    PropertyImage,
    BookingPayment,
    db,
)


class DashboardService:
    def __init__(self):
        self.db = db

    def get_user_context(self, user_id, payments_page=1, payments_per_page=5):
        user = User.query.get(user_id)
        if not user:
            return None

        bookings_query = (
            BookingDetail.query.options(joinedload(BookingDetail.property))
            .filter_by(booking_userid=user_id)
            .order_by(BookingDetail.created_at.desc())
        )

        bookings_pagination = bookings_query.paginate(
            page=payments_page,
            per_page=payments_per_page,
            error_out=False,
        )

        bookings = bookings_pagination.items

        total_bookings = bookings_query.count()
        paid_bookings = bookings_query.filter(BookingDetail.booking_status == "paid").all()

        saved_properties_count = (
            db.session.query(func.count(func.distinct(BookingDetail.booking_propid)))
            .filter(BookingDetail.booking_userid == user_id)
            .scalar()
            or 0
        )

        saved_property_ids = [
            prop_id
            for (prop_id,) in (
                db.session.query(BookingDetail.booking_propid)
                .filter(BookingDetail.booking_userid == user_id)
                .distinct()
                .all()
            )
            if prop_id
        ]

        saved_properties = []
        if saved_property_ids:
            saved_properties = (
                Property.query.filter(Property.prop_id.in_(saved_property_ids))
                .order_by(Property.prop_id.desc())
                .all()
            )

        total_spent = sum(
            (booking.total_amount or Decimal("0"))
            for booking in paid_bookings
        )
        active_reservations = BookingDetail.query.filter_by(
            booking_userid=user_id,
            booking_status="paid",
        ).count()

        payments = (
            BookingPayment.query.options(joinedload(BookingPayment.booking_detail).joinedload(BookingDetail.property))
            .filter_by(booking_userid=user_id)
            .order_by(BookingPayment.booking_payment_date.desc())
            .all()
        )

        return {
            "deets": user,
            "bookings": bookings,
            "bookings_pagination": bookings_pagination,
            "saved_properties": saved_properties,
            "payments": payments,
            "stats": {
                "total_bookings": total_bookings,
                "active_reservations": active_reservations,
                "total_spent": total_spent,
                "saved_properties": saved_properties_count,
                "membership": "Host" if user.user_role == "host" else "Customer",
            },
        }

    def get_host_context(
        self,
        user_id,
        reservations_page=1,
        reservations_per_page=5,
        properties_page=1,
        properties_per_page=5,
        reservation_search=None,
        reservation_status=None,
        property_search=None,
        property_status=None,
    ):
        user = User.query.get(user_id)
        if not user:
            return None

        verification_status = user.verification_status
        if verification_status not in ("Pending", "Verified", "Suspended"):
            verification_status = "Verified" if user.is_verified else "Pending"

        host_can_manage_properties = verification_status == "Verified"

        host_properties_query = (
            Property.query.filter_by(prop_userid=user_id)
            .order_by(Property.prop_id.desc())
        )

        if property_search:
            property_search_like = f"%{property_search.strip()}%"
            host_properties_query = host_properties_query.filter(
                or_(
                    Property.prop_title.ilike(property_search_like),
                    Property.prop_address.ilike(property_search_like),
                    Property.prop_city.ilike(property_search_like),
                )
            )

        if property_status:
            normalized_property_status = property_status.strip().lower()
            if normalized_property_status == "approved":
                host_properties_query = host_properties_query.filter(Property.is_verified.is_(True))
            elif normalized_property_status == "pending":
                host_properties_query = host_properties_query.filter(Property.is_verified.is_(False))
            elif normalized_property_status in ("available", "booked", "inactive"):
                host_properties_query = host_properties_query.filter(
                    Property.prop_availability_status == normalized_property_status
                )

        host_properties_pagination = host_properties_query.paginate(
            page=properties_page,
            per_page=properties_per_page,
            error_out=False,
        )

        host_properties = host_properties_pagination.items

        host_bookings_query = (
            Booking.query.options(
                joinedload(Booking.user),
                joinedload(Booking.property),
            )
            .join(Property, Booking.booking_propid == Property.prop_id)
            .filter(Property.prop_userid == user_id)
            .order_by(Booking.created_at.desc())
        )

        if reservation_search:
            reservation_search_like = f"%{reservation_search.strip()}%"
            host_bookings_query = host_bookings_query.filter(
                or_(
                    Property.prop_title.ilike(reservation_search_like),
                    Booking.booking_status.ilike(reservation_search_like),
                )
            )

        if reservation_status:
            normalized_reservation_status = reservation_status.strip().lower()
            if normalized_reservation_status in ("pending", "confirmed", "cancelled", "completed"):
                host_bookings_query = host_bookings_query.filter(
                    Booking.booking_status == normalized_reservation_status
                )

        host_bookings_pagination = host_bookings_query.paginate(
            page=reservations_page,
            per_page=reservations_per_page,
            error_out=False,
        )

        host_bookings = host_bookings_pagination.items
        all_host_bookings = host_bookings_query.all()

        pending_properties = host_properties_query.filter_by(is_verified=False).count()
        confirmed_earnings = sum(
            (booking.total_amount or Decimal("0"))
            for booking in all_host_bookings
            if booking.booking_status in ("confirmed", "completed")
        )

        property_types = PropertyType.query.order_by(PropertyType.prop_typename).all()
        property_states = PropertyState.query.order_by(PropertyState.state_name).all()
        amenities = Amenity.query.order_by(Amenity.amenity_name).all()

        return {
            "deets": user,
            "host_verification_status": verification_status,
            "host_can_manage_properties": host_can_manage_properties,
            "host_properties": host_properties,
            "recent_reservations": host_bookings,
            "host_properties_pagination": host_properties_pagination,
            "host_reservations_pagination": host_bookings_pagination,
            "stats": {
                "total_properties": host_properties_query.count(),
                "pending_properties": pending_properties,
                "reservations": host_bookings_query.count(),
                "earnings": confirmed_earnings,
            },
            "property_types": property_types,
            "property_states": property_states,
            "amenities": amenities,
            "filters": {
                "reservation_search": reservation_search or "",
                "reservation_status": reservation_status or "",
                "property_search": property_search or "",
                "property_status": property_status or "",
            },
        }

    def get_search_metadata(self):
        property_types = ["Apartment", "Studio", "Duplex", "Villa", "Resort", "Hostel"]
        bedrooms = [1, 2, 3, 4, 5]
        sort_options = [
            {"key": "recommended", "label": "Recommended"},
            {"key": "lowest", "label": "Lowest Price"},
            {"key": "highest", "label": "Highest Price"},
        ]
        return {
            "property_types": property_types,
            "bedrooms": bedrooms,
            "sort_options": sort_options,
        }

    def serialize_property(self, prop):
        return {
            "prop_id": prop.prop_id,
            "title": prop.prop_title,
            "description": prop.prop_description,
            "category": prop.prop_category,
            "address": prop.prop_address,
            "city": prop.prop_city,
            "state": getattr(prop.state, "state_name", ""),
            "lga": getattr(prop.lga, "lga_name", ""),
            "price_per_night": float(prop.price_per_night or 0),
            "max_guest": prop.max_guest,
            "bedrooms": prop.bedrooms,
            "bathrooms": prop.bathrooms,
            "amenities": [
                pa.amenity.amenity_name for pa in getattr(prop, "property_amenities", []) if getattr(pa, "amenity", None)
            ],
            "is_verified": prop.is_verified,
            "main_image_url": prop.prop_mainimage_url or "/static/images/rooms/patrick-perkins-iRiVzALa4pI-unsplash.jpg",
        }

    def search_properties(
        self,
        location=None,
        checkin_date=None,
        checkout_date=None,
        guests=None,
        verified_only=False,
        property_type=None,
        min_bedrooms=None,
        sort_by=None,
    ):
        query = Property.query

        if Property.prop_availability_status is not None:
            query = query.filter(Property.prop_availability_status != "inactive")

        if location:
            normalized_location = f"%{location.strip()}%"
            location_filters = [
                Property.prop_title.ilike(normalized_location),
                Property.prop_description.ilike(normalized_location),
                Property.prop_address.ilike(normalized_location),
                Property.prop_city.ilike(normalized_location),
            ]

            try:
                query = query.filter(or_(*location_filters))
            except Exception:
                query = query.filter(
                    or_(
                        Property.prop_title.ilike(normalized_location),
                        Property.prop_description.ilike(normalized_location),
                        Property.prop_address.ilike(normalized_location),
                        Property.prop_city.ilike(normalized_location),
                    )
                )

        if verified_only:
            query = query.filter(Property.is_verified == True)

        if guests:
            try:
                guests = int(guests)
            except (ValueError, TypeError):
                guests = None
            if guests:
                query = query.filter(Property.max_guest >= guests)

        if min_bedrooms:
            try:
                min_bedrooms = int(min_bedrooms)
            except (ValueError, TypeError):
                min_bedrooms = None
            if min_bedrooms:
                query = query.filter(Property.bedrooms >= min_bedrooms)

        if property_type:
            query = query.filter(Property.prop_category.ilike(f"%{property_type.strip()}%"))

        if checkin_date and checkout_date:
            try:
                start_date = date.fromisoformat(checkin_date)
                end_date = date.fromisoformat(checkout_date)
                if end_date >= start_date:
                    overlapping = (
                        BookingDetail.query.with_entities(BookingDetail.booking_propid)
                        .filter(
                            BookingDetail.booking_status.in_(["pending_payment", "paid"]),
                            BookingDetail.checkin_date <= end_date,
                            BookingDetail.checkout_date >= start_date,
                        )
                        .subquery()
                    )
                    query = query.filter(~Property.prop_id.in_(overlapping))
            except ValueError:
                pass

        if sort_by == "lowest":
            query = query.order_by(Property.price_per_night.asc())
        elif sort_by == "highest":
            query = query.order_by(Property.price_per_night.desc())
        elif sort_by == "recommended":
            query = query.order_by(Property.is_verified.desc(), Property.prop_id.desc())
        else:
            query = query.order_by(Property.is_verified.desc(), Property.prop_id.desc())

        return query.all()

    def save_host_property(
        self,
        host_id,
        prop_title,
        prop_description,
        prop_typeid,
        prop_category,
        prop_address,
        price_per_night,
        prop_stateid=None,
        prop_lgaid=None,
        prop_city=None,
        bedrooms=0,
        bathrooms=0,
        max_guest=1,
        prop_availability_status="inactive",
        featured_image=None,
        gallery_images=None,
        selected_amenities=None,
    ):
        host = User.query.get(host_id)
        if not host or host.user_role != "host":
            raise ValueError("Unauthorized host account.")

        verification_status = host.verification_status
        if verification_status not in ("Pending", "Verified", "Suspended"):
            verification_status = "Verified" if host.is_verified else "Pending"

        if verification_status != "Verified":
            if verification_status == "Suspended":
                raise ValueError("Your host account is suspended. Property actions are disabled.")
            raise ValueError("Your host account is not verified yet. Property actions are disabled.")

        if not prop_title:
            raise ValueError("Property title is required.")
        if not prop_typeid:
            raise ValueError("Property type is required.")
        if not price_per_night:
            raise ValueError("Price per night is required.")

        if prop_stateid is None or prop_stateid == "":
            first_state = PropertyState.query.first()
            if not first_state:
                raise ValueError("No property states available.")
            prop_stateid = first_state.state_id

        if prop_lgaid is None or prop_lgaid == "":
            first_lga = PropertyLGA.query.filter_by(state_id=prop_stateid).first()
            if not first_lga:
                raise ValueError("No LGA available for the selected state.")
            prop_lgaid = first_lga.lga_id

        property_item = Property(
            prop_userid=host_id,
            prop_title=prop_title,
            prop_description=prop_description,
            prop_typeid=int(prop_typeid),
            prop_stateid=int(prop_stateid),
            prop_lgaid=int(prop_lgaid),
            prop_category=prop_category or "Apartment",
            prop_address=prop_address,
            prop_city=prop_city or "",
            price_per_night=Decimal(price_per_night),
            bedrooms=int(bedrooms) if bedrooms else 0,
            bathrooms=int(bathrooms) if bathrooms else 0,
            max_guest=int(max_guest) if max_guest else 1,
            prop_availability_status=prop_availability_status,
            is_verified=False,
        )

        self.db.session.add(property_item)
        self.db.session.flush()

        if featured_image and getattr(featured_image, "filename", ""):
            filename = self._save_image_file(featured_image)
            property_item.prop_mainimage_url = filename
            featured = PropertyImage(
                img_propid=property_item.prop_id,
                image_url=filename,
                is_featured=True,
            )
            self.db.session.add(featured)

        gallery_images = gallery_images or []
        for image in gallery_images:
            if not image or not getattr(image, "filename", ""):
                continue
            filename = self._save_image_file(image)
            gallery = PropertyImage(
                img_propid=property_item.prop_id,
                image_url=filename,
                is_featured=False,
            )
            self.db.session.add(gallery)

        selected_amenities = selected_amenities or []
        for amenity_id in selected_amenities:
            try:
                amenity_id_int = int(amenity_id)
            except (ValueError, TypeError):
                continue
            property_amenity = PropertyAmenity(
                prop_id=property_item.prop_id,
                amenity_id=amenity_id_int,
            )
            self.db.session.add(property_amenity)

        self.db.session.commit()
        return property_item

    def apply_for_host(self, user_id):
        user = User.query.get(user_id)
        if not user:
            return None
        user.user_role = "host"
        user.is_verified = False
        self.db.session.commit()
        return user

    def _save_image_file(self, image):
        if not image or not image.filename:
            return None

        extension = image.filename.rsplit(".", 1)[1].lower()
        if extension not in {"jpg", "jpeg", "png", "webp"}:
            raise ValueError("Unsupported image format.")

        filename = f"{uuid.uuid4().hex}.{extension}"
        upload_folder = os.path.join(current_app.root_path, "static", "uploads", "properties")
        os.makedirs(upload_folder, exist_ok=True)
        image.save(os.path.join(upload_folder, filename))
        return filename
