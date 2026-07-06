from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Enum, Numeric, func

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    user_id = db.Column(db.Integer, primary_key=True)

    user_firstname = db.Column(db.String(200), nullable=False)
    user_lastname = db.Column(db.String(200), nullable=False)

    user_email = db.Column(
        db.String(150),
        unique=True,
        nullable=False
    )

    user_phoneno = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )

    user_password = db.Column(
        db.String(255),
        nullable=False
    )

    user_profileimage = db.Column(db.String(255))

    is_verified = db.Column(
        db.Boolean,
        default=False
    )

    user_status = db.Column(
        db.Enum(
            "active",
            "inactive",
            "suspended",
            name="user_status"
        ),
        default="active"
    )

    user_role = db.Column(
        db.Enum(
            "customer",
            "host",
            "admin",
            name="user_role"
        ),
        default="customer"
    )

    user_timecreated = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    user_timeupdated = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    properties = db.relationship(
        "Property",
        backref="user",
        lazy=True,
        cascade="all, delete-orphan"
    )
    reviews = db.relationship(
        "Review",
        backref="user",
        lazy=True,
        cascade="all, delete-orphan"
    )
    bookings = db.relationship(
        "Booking",
        backref="user",
        lazy=True,
        cascade="all, delete-orphan"
    )
class Admin(db.Model):
    __tablename__ = "admins"

    admin_id = db.Column(
        db.Integer,
        primary_key=True
    )
    admin_email = db.Column(
        db.String(150),
        unique=True,
        nullable=False
    )
    admin_password = db.Column(
        db.String(255),
        nullable=False
    )


class PropertyType(db.Model):
    __tablename__ = "property_types"

    prop_type_id = db.Column(
        db.Integer,
        primary_key=True
    )

    prop_typename = db.Column(
        db.String(100),
        nullable=False
    )

    properties = db.relationship(
        "Property",
        backref="property_type",
        lazy=True
    )


class PropertyState(db.Model):
    __tablename__ = "property_states"

    state_id = db.Column(
        db.Integer,
        primary_key=True
    )

    state_name = db.Column(
        db.String(100),
        nullable=False
    )

    lgas = db.relationship(
        "PropertyLGA",
        backref="state",
        lazy=True,
        cascade="all, delete-orphan"
    )

    properties = db.relationship(
        "Property",
        backref="state",
        lazy=True
    )


class PropertyLGA(db.Model):
    __tablename__ = "property_lgas"

    lga_id = db.Column(
        db.Integer,
        primary_key=True
    )

    lga_name = db.Column(
        db.String(100),
        nullable=False
    )

    state_id = db.Column(
        db.Integer,
        db.ForeignKey("property_states.state_id"),
        nullable=False
    )

    properties = db.relationship(
        "Property",
        backref="lga",
        lazy=True
    )

class Property(db.Model):
    __tablename__ = "properties"

    prop_id = db.Column(db.Integer, primary_key=True)

    prop_userid = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id"),
        nullable=False
    )

    prop_typeid = db.Column(
        db.Integer,
        db.ForeignKey("property_types.prop_type_id"),
        nullable=False
    )

    prop_stateid = db.Column(
        db.Integer,
        db.ForeignKey("property_states.state_id"),
        nullable=False
    )

    prop_lgaid = db.Column(
        db.Integer,
        db.ForeignKey("property_lgas.lga_id"),
        nullable=False
    )

    prop_title = db.Column(db.String(255), nullable=False)
    prop_description = db.Column(db.Text)
    prop_category = db.Column(db.String(100),nullable=False)
    prop_address = db.Column(db.String(255))
    prop_city = db.Column(db.String(150))

    price_per_night = db.Column(db.Numeric(12, 2), nullable=False)

    max_guest = db.Column(db.Integer)
    bedrooms = db.Column(db.Integer)
    bathrooms = db.Column(db.Integer)

    is_verified = db.Column(db.Boolean, default=False)

    prop_availability_status = db.Column(
        db.Enum(
            "available",
            "booked",
            "inactive",
            name="availability_status"
        ),
        default="available"
    )

    prop_mainimage_url = db.Column(db.String(255))

    images = db.relationship(
        "PropertyImage",
        backref="property",
        lazy=True,
        cascade="all, delete-orphan"
    )

    reviews = db.relationship(
        "Review",
        back_populates="property",
        lazy=True,
        cascade="all, delete-orphan"
    )

    bookings = db.relationship(
        "Booking",
        backref="property",
        lazy=True,
        cascade="all, delete-orphan"
    )

    property_amenities = db.relationship(
        "PropertyAmenity",
        backref="property",
        lazy=True,
        cascade="all, delete-orphan"
    )

    @property
    def amenities(self):
        return [
            pa.amenity.amenity_name
            for pa in self.property_amenities
            if getattr(pa, "amenity", None)
        ]

class Review(db.Model):
    __tablename__ = "reviews"

    review_id = db.Column(db.Integer, primary_key=True)

    review_propid = db.Column(
        db.Integer,
        db.ForeignKey("properties.prop_id"),
        nullable=False
    )

    review_bookingid = db.Column(
        db.Integer,
        db.ForeignKey("bookings.booking_id"),
        nullable=False
    )

    review_userid = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id"),
        nullable=False
    )

    review_rating = db.Column(db.Integer)
    review_comment = db.Column(db.Text)

    review_time = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    property = db.relationship(
        "Property",
        back_populates="reviews"
    )


class Amenity(db.Model):
    __tablename__ = "amenities"

    amenity_id = db.Column(db.Integer, primary_key=True)
    amenity_name = db.Column(db.String(100), nullable=False)

    property_amenities = db.relationship(
        "PropertyAmenity",
        backref="amenity",
        lazy=True,
        cascade="all, delete-orphan"
    )

class PropertyAmenity(db.Model):
    __tablename__ = "property_amenities"

    property_amenity_id = db.Column(db.Integer, primary_key=True)

    prop_id = db.Column(
        db.Integer,
        db.ForeignKey("properties.prop_id"),
        nullable=False
    )

    amenity_id = db.Column(
        db.Integer,
        db.ForeignKey("amenities.amenity_id"),
        nullable=False
    )


class BookingDetail(db.Model):
    __tablename__ = "booking_details"

    booking_detail_id = db.Column(db.Integer, primary_key=True)

    booking_userid = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id"),
        nullable=True
    )

    booking_propid = db.Column(
        db.Integer,
        db.ForeignKey("properties.prop_id"),
        nullable=False
    )

    full_name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(50), nullable=False)

    checkin_date = db.Column(db.Date, nullable=False)
    checkout_date = db.Column(db.Date, nullable=False)

    guests = db.Column(db.Integer, nullable=False, default=1)
    special_requests = db.Column(db.Text)
    terms_agreed = db.Column(db.Boolean, nullable=False, default=False)

    nights = db.Column(db.Integer, nullable=False, default=1)
    subtotal = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    cleaning_fee = db.Column(db.Numeric(12, 2), nullable=False, default=5000)
    service_fee = db.Column(db.Numeric(12, 2), nullable=False, default=3000)
    total_amount = db.Column(db.Numeric(12, 2), nullable=False, default=0)

    booking_status = db.Column(
        db.Enum(
            "pending_payment",
            "paid",
            "cancelled",
            name="booking_detail_status"
        ),
        default="pending_payment"
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    user = db.relationship("User", backref="booking_details")
    property = db.relationship("Property", backref="booking_details")

class Booking(db.Model):
    __tablename__ = "bookings"

    booking_id = db.Column(db.Integer, primary_key=True)

    booking_userid = db.Column(
        db.Integer,
        db.ForeignKey("users.user_id"),
        nullable=False
    )

    booking_propid = db.Column(
        db.Integer,
        db.ForeignKey("properties.prop_id"),
        nullable=False
    )

    checkin_date = db.Column(db.Date, nullable=False)
    checkout_date = db.Column(db.Date, nullable=False)

    total_amount = db.Column(db.Numeric(12, 2), nullable=False)

    booking_status = db.Column(
        db.Enum(
            "pending",
            "confirmed",
            "cancelled",
            "completed",
            name="booking_status"
        ),
        default="pending"
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

class Item(db.Model):
    item_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    item_name = db.Column(db.String(100), unique=True, nullable=False)
    item_amount = db.Column(Numeric(12, 2), nullable=False)

class PropertyImage(db.Model):

    __tablename__ = "properties_images"

    propimg_id = db.Column(
        db.Integer,
        primary_key=True
    )

    img_propid = db.Column(
        db.Integer,
        db.ForeignKey("properties.prop_id"),
        nullable=False
    )

    image_url = db.Column(
        db.String(255),
        nullable=False
    )

    is_featured = db.Column(
        db.Boolean,
        default=False
    )

    uploaded_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )
class BookingPayment(db.Model):
    __tablename__ = "booking_payments"
    payment_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    booking_amount = db.Column(Numeric(12, 2), nullable=False)

    booking_payment_date = db.Column(db.DateTime, nullable=False)

    booking_payment_status = db.Column(Enum("pending", "paid", "failed", "cancelled", name="payment_status"),
        nullable=False, index=True, server_default="pending")

    booking_userid = db.Column(db.Integer, db.ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False, index=True )

    booking_bookingid = db.Column(db.Integer, db.ForeignKey("booking_details.booking_detail_id", ondelete="CASCADE"),
        nullable=False, index=True )

    advert_payment_reference = db.Column(db.String(100), unique=True,
        nullable=False)

    user = db.relationship("User", backref="booking_payments")
    booking_detail = db.relationship("BookingDetail", backref="payments")