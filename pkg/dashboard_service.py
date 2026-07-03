import os
import uuid
from decimal import Decimal
from datetime import datetime, date
from sqlalchemy import or_, and_
from flask import current_app
from pkg.models import (
    User,
    Property,
    PropertyType,
    PropertyState,
    PropertyLGA,
    Booking,
    PropertyImage,
    db,
)


class DashboardService:
    def __init__(self):
        self.db = db

    def get_user_context(self, user_id):
        user = User.query.get(user_id)
        if not user:
            return None

        bookings = (
            Booking.query.filter_by(booking_userid=user_id)
            .order_by(Booking.created_at.desc())
            .all()
        )

        total_bookings = len(bookings)
        total_spent = sum(
            (booking.total_amount or Decimal("0"))
            for booking in bookings
            if booking.booking_status in ("confirmed", "completed")
        )
        active_reservations = Booking.query.filter_by(
            booking_userid=user_id,
            booking_status="confirmed",
        ).count()

        return {
            "deets": user,
            "bookings": bookings,
            "stats": {
                "total_bookings": total_bookings,
                "active_reservations": active_reservations,
                "total_spent": total_spent,
                "membership": "Host" if user.user_role == "host" else "Customer",
            },
        }

    def get_host_context(self, user_id):
        user = User.query.get(user_id)
        if not user:
            return None

        host_properties = (
            Property.query.filter_by(prop_userid=user_id)
            .order_by(Property.prop_id.desc())
            .all()
        )

        host_bookings = (
            Booking.query.join(Property, Booking.booking_propid == Property.prop_id)
            .filter(Property.prop_userid == user_id)
            .order_by(Booking.created_at.desc())
            .all()
        )

        pending_properties = [p for p in host_properties if not p.is_verified]
        confirmed_earnings = sum(
            (booking.total_amount or Decimal("0"))
            for booking in host_bookings
            if booking.booking_status in ("confirmed", "completed")
        )

        property_types = PropertyType.query.order_by(PropertyType.prop_typename).all()
        property_states = PropertyState.query.order_by(PropertyState.state_name).all()

        return {
            "deets": user,
            "host_properties": host_properties,
            "recent_reservations": host_bookings[:5],
            "stats": {
                "total_properties": len(host_properties),
                "pending_properties": len(pending_properties),
                "reservations": len(host_bookings),
                "earnings": confirmed_earnings,
            },
            "property_types": property_types,
            "property_states": property_states,
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
        query = Property.query.join(PropertyState, Property.prop_stateid == PropertyState.state_id).join(
            PropertyLGA, Property.prop_lgaid == PropertyLGA.lga_id
        )

        if location:
            normalized_location = f"%{location.strip()}%"
            query = query.filter(
                or_(
                    Property.prop_title.ilike(normalized_location),
                    Property.prop_description.ilike(normalized_location),
                    Property.prop_address.ilike(normalized_location),
                    Property.prop_city.ilike(normalized_location),
                    PropertyState.state_name.ilike(normalized_location),
                    PropertyLGA.lga_name.ilike(normalized_location),
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
                        Booking.query.with_entities(Booking.booking_propid)
                        .filter(
                            Booking.booking_status.in_(["confirmed", "pending"]),
                            Booking.checkin_date <= end_date,
                            Booking.checkout_date >= start_date,
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
        else:
            query = query.order_by(Property.prop_id.desc())

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
        bedrooms=0,
        bathrooms=0,
        max_guest=1,
        prop_availability_status="inactive",
        featured_image=None,
    ):
        if not prop_title:
            raise ValueError("Property title is required.")
        if not prop_typeid:
            raise ValueError("Property type is required.")
        if not price_per_night:
            raise ValueError("Price per night is required.")

        if prop_stateid is None:
            first_state = PropertyState.query.first()
            if not first_state:
                raise ValueError("No property states available.")
            prop_stateid = first_state.state_id

        if prop_lgaid is None:
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
            price_per_night=Decimal(price_per_night),
            bedrooms=int(bedrooms) if bedrooms else 0,
            bathrooms=int(bathrooms) if bathrooms else 0,
            max_guest=int(max_guest) if max_guest else 1,
            prop_availability_status=prop_availability_status,
            is_verified=False,
        )

        self.db.session.add(property_item)
        self.db.session.flush()

        if featured_image and featured_image.filename:
            filename = self._save_image_file(featured_image)
            property_item.prop_mainimage_url = filename

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
