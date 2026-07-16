import json,secrets, datetime, requests
import re

from datetime import date
from decimal import Decimal
from sqlalchemy import func
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

from flask import render_template, request, url_for, redirect, flash, session, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from pkg import app
from pkg.dashboard_service import DashboardService
from pkg.forms import RegisterForm, LoginForm, BookingDetailsForm
from pkg.models import User, Property, Amenity, BookingDetail, BookingPayment, db
from pkg.notification_service import NotificationService
from pkg.utils.notification_constants import NotificationType
from pkg.utils.upload import save_nin_document

dashboard_service = DashboardService()


def _resolve_host_verification_status(user):
    if not user or user.user_role != 'host':
        return None

    if user.verification_status in ('Pending', 'Verified', 'Suspended'):
        return user.verification_status

    return 'Verified' if user.is_verified else 'Pending'


def _verification_badge_meta(status):
    if status == 'Verified':
        return {
            'text': 'Verified',
            'class': 'bg-success',
        }
    if status == 'Suspended':
        return {
            'text': 'Suspended',
            'class': 'bg-danger',
        }
    return {
        'text': 'Pending',
        'class': 'bg-warning text-dark',
    }


def _queue_host_status_notification(user):
    status = _resolve_host_verification_status(user)
    if status not in ('Verified', 'Suspended'):
        session['host_verification_status_seen'] = status
        return

    last_seen = session.get('host_verification_status_seen')
    if last_seen == status:
        return

    if status == 'Verified':
        flash("Congratulations! Your identity has been verified. You can now publish your properties.", 'successmsg')
    elif status == 'Suspended':
        flash("Your verification could not be completed. Please contact support or submit valid NIN documentation.", 'errormsg')

    session['host_verification_status_seen'] = status


def _booking_id_from_reference(ref):
    # Expected payment reference format: BK-<booking_detail_id>-<random>
    if not ref:
        return None
    parts = str(ref).split('-')
    if len(parts) >= 3 and parts[0] == 'BK' and parts[1].isdigit():
        return int(parts[1])
    return None


def _build_paystack_callback_url():
    configured_url = (current_app.config.get("PAYSTACK_CALLBACK_URL") or "").strip()
    if configured_url:
        parsed = urlparse(configured_url)
        host = (parsed.netloc or "").lower()
        if host and not any(host.startswith(value) for value in ("127.0.0.1", "localhost", "0.0.0.0")):
            return configured_url

    return f"{request.host_url.rstrip('/')}{url_for('paystack_landing')}"


@app.errorhandler(404)
def page_not_found(error):
    return render_template('user/404.html', error=error),404

@app.errorhandler(503)
def page_under_maintenance(error):
    return render_template('user/503.html', error=error),503

@app.route('/')
def home():
    deets = None
    if session.get('useronline'):
        id = session.get('useronline')
        deets = User.query.get(id)
    return render_template('user/index.html',deets=deets)


@app.route('/profile/')
def profile():
    if not session.get('useronline'):
        flash('Please login to access your profile.', category='errormsg')
        return redirect(url_for('login'))

    deets = User.query.get(session.get('useronline'))
    if not deets:
        session.clear()
        flash('Session expired, please login again.', category='errormsg')
        return redirect(url_for('login'))

    host_verification_status = _resolve_host_verification_status(deets) if deets.user_role == 'host' else None
    host_badge = _verification_badge_meta(host_verification_status) if host_verification_status else None

    return render_template(
        'user/profile.html',
        deets=deets,
        host_verification_status=host_verification_status,
        host_verification_badge=host_badge,
    )


@app.route('/profile/settings/')
def profile_settings():
    return redirect(url_for('profile'))

@app.route('/payment')
def payment():
    booking_detail_id = request.args.get('booking_detail_id', type=int)
    booking_detail = BookingDetail.query.get(booking_detail_id) if booking_detail_id else None
    if not booking_detail:
        flash('Booking details not found.', category='errormsg')
        return redirect(url_for('listing'))

    if booking_detail.booking_userid and session.get('useronline') != booking_detail.booking_userid:
        flash('You are not authorized to pay for this booking.', category='errormsg')
        return redirect(url_for('listing'))

    nightly_price = Decimal(booking_detail.property.price_per_night or 0)
    nights = booking_detail.nights or 1
    subtotal = nightly_price * nights
    service_fee = Decimal('5000')
    total_amount = subtotal + service_fee

    return render_template(
        'user/payment.html',
        booking_detail=booking_detail,
        subtotal=subtotal,
        service_fee=service_fee,
        total_amount=total_amount,
    )


@app.route('/pay/<int:booking_detail_id>/', methods=['GET', 'POST'])
def pay_booking(booking_detail_id):
    booking_detail = BookingDetail.query.get_or_404(booking_detail_id)
    if booking_detail.booking_userid and booking_detail.booking_userid != session.get('useronline'):
        if session.get('useronline') is None:
            flash('Please log in to pay for this booking.', category='errormsg')
            return redirect(url_for('login'))
        flash('This booking does not belong to you', category='errormsg')
        return redirect(url_for('listing'))

    if booking_detail.booking_status == 'paid':
        flash('This booking has already been paid for.', category='successmsg')
        return redirect(url_for('confirmation', booking_detail_id=booking_detail.booking_detail_id))

    return redirect(url_for('payment', booking_detail_id=booking_detail.booking_detail_id))


@app.route('/paystack-initialize/', methods=['POST'])
def paystack_init():
    logged_in_user = session.get("useronline")
    if logged_in_user:
        user_id = logged_in_user
    else:
        user_id = None

   
    booking_detail_id = request.form.get(
        "booking_detail_id",
        type=int
    )

    if not booking_detail_id:
        flash("Invalid booking.", "errormsg")
        return redirect(url_for("listing"))

    
    booking_detail = BookingDetail.query.get_or_404(
        booking_detail_id
    )

    
    if booking_detail.booking_userid and booking_detail.booking_userid != session.get("useronline"):
        flash("Unauthorized booking.", "errormsg")
        return redirect(url_for("listing"))

   
    if booking_detail.booking_status == "paid":
        flash("This booking has already been paid.", "successmsg")
        return redirect(url_for("confirmation", booking_detail_id=booking_detail.booking_detail_id))

    paystack_secret = current_app.config.get(
        "PAYSTACK_SECRET_KEY"
    )

    if not paystack_secret:
        flash("Paystack is not configured.", "errormsg")
        return redirect(
            url_for(
                "payment",
                booking_detail_id=booking_detail.booking_detail_id
            )
        )

    nightly_price = Decimal(
        booking_detail.property.price_per_night or 0
    )

    nights = booking_detail.nights or 1

    service_fee = Decimal("5000")

    total = (nightly_price * nights) + service_fee

    amount = int(total * 100)

    reference = f"BK-{booking_detail.booking_detail_id}-{secrets.token_hex(8)}"

    callback_url = _build_paystack_callback_url()

    separator = '&' if '?' in callback_url else '?'
    callback_url = f"{callback_url}{separator}booking_detail_id={booking_detail.booking_detail_id}"

    payload = {
        "email": booking_detail.email,
        "amount": amount,
        "reference": reference,
        "callback_url": callback_url,
        "currency": "NGN",
    }

    headers = {
        "Authorization": f"Bearer {paystack_secret}",
        "Content-Type": "application/json",
    }

    try:

        response = requests.post(
            "https://api.paystack.co/transaction/initialize",
            json=payload,
            headers=headers,
            timeout=20
        )

        rsp = response.json()

    except requests.exceptions.RequestException as e:

        flash(
            "Unable to connect to Paystack.",
            "errormsg"
        )

        return redirect(
            url_for(
                "payment",
                booking_detail_id=booking_detail.booking_detail_id
            )
        )

    if not rsp.get("status"):

        flash(
            rsp.get(
                "message",
                "Payment initialization failed."
            ),
            "errormsg"
        )

        return redirect(
            url_for(
                "payment",
                booking_detail_id=booking_detail.booking_detail_id
            )
        )
    logged_in_user = session.get("useronline")  # Returns None for guests
    payment = BookingPayment(

        booking_amount=total,

        booking_userid=logged_in_user,

        booking_bookingid=booking_detail.booking_detail_id,

        advert_payment_reference=reference,

        booking_payment_status="pending",

        booking_payment_date=datetime.datetime.utcnow()

    )

    db.session.add(payment)

    db.session.commit()

    session["payref"] = reference

    session["pay_booking_detail_id"] = booking_detail.booking_detail_id

    authorization_url = rsp["data"]["authorization_url"]

    return redirect(authorization_url)

@app.route('/paystack/landing/')
def paystack_landing():
    """Handle Paystack callback and verify payment."""

    ref = (
        request.args.get('reference')
        or request.args.get('trxref')
        or session.get('payref')
    )

    booking_detail_id = (
        request.args.get('booking_detail_id', type=int)
        or session.get('pay_booking_detail_id')
        or _booking_id_from_reference(ref)
    )

    if not ref or not booking_detail_id:
        flash('Payment could not be verified.', 'errormsg')
        return redirect(url_for('listing'))

    paystack_secret = app.config.get('PAYSTACK_SECRET_KEY')

    if not paystack_secret:
        flash('Paystack configuration is missing.', 'errormsg')
        return redirect(
            url_for('payment', booking_detail_id=booking_detail_id)
        )

    booking_detail = BookingDetail.query.get_or_404(booking_detail_id)

    try:
        response = requests.get(
            f"https://api.paystack.co/transaction/verify/{ref}",
            headers={
                "Authorization": f"Bearer {paystack_secret}"
            },
            timeout=20
        )

        rsp = response.json()

    except requests.RequestException:
        flash(
            'Unable to verify payment. Please try again.',
            'errormsg'
        )
        return redirect(
            url_for(
                'payment',
                booking_detail_id=booking_detail.booking_detail_id
            )
        )

    data = rsp.get("data", {})
    transaction_status = data.get("status", "").lower()

    if rsp.get("status") and transaction_status in ("success", "successful"):

        booking_detail.booking_status = "paid"

        payment = BookingPayment.query.filter_by(
            advert_payment_reference=ref
        ).first()

        if payment:
            payment.booking_payment_status = "paid"

        db.session.commit()

        if booking_detail.booking_userid:
            NotificationService.notify(
               user_id=booking_detail.booking_userid,
               title="Payment Successful",
               message=(
                 f"Your payment for "
                 f"{booking_detail.property.prop_title} "
                 f"was successful. Your booking has been confirmed."
                ),
               notification_type=NotificationType.PAYMENT_SUCCESS,
               reference_type="booking",
               reference_id=booking_detail.booking_detail_id
            )
        NotificationService.notify(
            user_id=booking_detail.property.prop_userid,
            title="New Paid Booking",
            message=(
                f"{booking_detail.full_name} has successfully "
                f"booked your property "
                f"{booking_detail.property.prop_title}."
            ),
            notification_type=NotificationType.HOST_NEW_BOOKING,
            reference_type="booking",
            reference_id=booking_detail.booking_detail_id
        )

        session["last_confirmed_booking_id"] = booking_detail.booking_detail_id
        session.pop("payref", None)
        session.pop("pay_booking_detail_id", None)

        flash(
            "Payment successful. Booking confirmed.",
            "successmsg"
        )

        return redirect(url_for("confirmation"))

    flash(
        data.get("gateway_response", "Payment verification failed."),
        "errormsg"
    )

    if booking_detail.booking_userid:
        NotificationService.notify(
        user_id=booking_detail.booking_userid,
        title="Payment Failed",
        message=data.get(
            "gateway_response",
            "Your payment could not be verified."
        ),
        notification_type=NotificationType.PAYMENT_FAILED,
         reference_type="booking",
         reference_id=booking_detail.booking_detail_id
        )

    return redirect(
        url_for(
            "payment",
            booking_detail_id=booking_detail.booking_detail_id
        )
    )

@app.route('/listing/')
def listing():
    search_values = {
        'location': request.args.get('location', '').strip(),
        'checkin_date': request.args.get('checkin_date', ''),
        'checkout_date': request.args.get('checkout_date', ''),
        'guests': request.args.get('guests', ''),
        'verified_only': request.args.get('verified_only') in ('on', 'true', '1'),
        'property_type': request.args.get('property_type', ''),
        'min_bedrooms': request.args.get('min_bedrooms', ''),
        'sort_by': request.args.get('sort_by', ''),
    }

    properties = dashboard_service.search_properties(
        location=search_values['location'],
        checkin_date=search_values['checkin_date'],
        checkout_date=search_values['checkout_date'],
        guests=search_values['guests'],
        verified_only=search_values['verified_only'],
        property_type=search_values['property_type'],
        min_bedrooms=search_values['min_bedrooms'],
        sort_by=search_values['sort_by'],
    )

    search_meta = dashboard_service.get_search_metadata()
    return render_template(
        'user/listing.html',
        properties=properties,
        search_meta=search_meta,
        search_values=search_values,
        total_results=len(properties),
    )

@app.route('/api/search-properties/')
def api_search_properties():
    search_values = {
        'location': request.args.get('location', '').strip(),
        'checkin_date': request.args.get('checkin_date', ''),
        'checkout_date': request.args.get('checkout_date', ''),
        'guests': request.args.get('guests', ''),
        'verified_only': request.args.get('verified_only') in ('on', 'true', '1'),
        'property_type': request.args.get('property_type', ''),
        'min_bedrooms': request.args.get('min_bedrooms', ''),
        'sort_by': request.args.get('sort_by', ''),
    }

    properties = dashboard_service.search_properties(
        location=search_values['location'],
        checkin_date=search_values['checkin_date'],
        checkout_date=search_values['checkout_date'],
        guests=search_values['guests'],
        verified_only=search_values['verified_only'],
        property_type=search_values['property_type'],
        min_bedrooms=search_values['min_bedrooms'],
        sort_by=search_values['sort_by'],
    )

    return jsonify(
        count=len(properties),
        properties=[dashboard_service.serialize_property(prop) for prop in properties],
    )

@app.route('/properties/<int:prop_id>')
def property_details(prop_id):
    property_item = Property.query.get(prop_id)
    if not property_item:
        flash('Property not found.', category='errormsg')
        return redirect(url_for('listing'))

    search_values = {
        'checkin_date': request.args.get('checkin_date', ''),
        'checkout_date': request.args.get('checkout_date', ''),
        'guests': request.args.get('guests', ''),
    }

    nights = 1
    try:
        checkin = date.fromisoformat(search_values['checkin_date']) if search_values['checkin_date'] else None
        checkout = date.fromisoformat(search_values['checkout_date']) if search_values['checkout_date'] else None
        if checkin and checkout and checkout > checkin:
            nights = (checkout - checkin).days
    except ValueError:
        nights = 1

    nightly_price = Decimal(property_item.price_per_night or 0)
    service_fee = Decimal('5000')
    subtotal = nightly_price * nights
    total_amount = subtotal + service_fee

    

    return render_template(
        'user/properties_details.html',
        property=property_item,
        search_values=search_values,
        nights=nights,
        subtotal=subtotal,
        service_fee=service_fee,
        total_amount=total_amount,
    )


@app.route('/properties_details')
def properties_details():
    prop_id = request.args.get('prop_id', type=int)
    if not prop_id:
        flash('Select a property to view details.', category='errormsg')
        return redirect(url_for('listing'))
    return redirect(url_for('property_details', prop_id=prop_id))

@app.route('/booking', methods=['GET', 'POST'])
def booking():
    prop_id = request.args.get('prop_id', type=int)
    if not prop_id:
        flash('Please select a property first.', category='errormsg')
        return redirect(url_for('listing'))

    property_item = Property.query.get(prop_id)
    if not property_item:
        flash('Property not found.', category='errormsg')
        return redirect(url_for('listing'))

    form = BookingDetailsForm()
    max_guest = property_item.max_guest or 1
    form.guests.choices = [(i, f"{i} Guest" if i == 1 else f"{i} Guests") for i in range(1, max_guest + 1)]

    user = None
    if session.get('useronline'):
        user = User.query.get(session.get('useronline'))

    if request.method == 'GET':
        if user:
            form.full_name.data = f"{user.user_firstname} {user.user_lastname}"
            form.email.data = user.user_email
            form.phone.data = user.user_phoneno

        checkin_str = request.args.get('checkin_date', '')
        checkout_str = request.args.get('checkout_date', '')
        guests_str = request.args.get('guests', '')

        if checkin_str:
            try:
                form.checkin_date.data = date.fromisoformat(checkin_str)
            except ValueError:
                pass
        if checkout_str:
            try:
                form.checkout_date.data = date.fromisoformat(checkout_str)
            except ValueError:
                pass
        if guests_str and guests_str.isdigit():
            guests_int = int(guests_str)
            if 1 <= guests_int <= max_guest:
                form.guests.data = guests_int

    nights = 1
    if form.checkin_date.data and form.checkout_date.data and form.checkout_date.data > form.checkin_date.data:
        nights = (form.checkout_date.data - form.checkin_date.data).days

    nightly_price = Decimal(property_item.price_per_night or 0)
    cleaning_fee = Decimal('0')
    service_fee = Decimal('5000')
    subtotal = nightly_price * nights
    total_amount = subtotal + cleaning_fee + service_fee

    if form.validate_on_submit():
        if form.checkout_date.data <= form.checkin_date.data:
            flash('Checkout date must be after check-in date.', category='errormsg')
            return render_template(
                'user/booking.html',
                form=form,
                property=property_item,
                nights=nights,
                subtotal=subtotal,
                cleaning_fee=cleaning_fee,
                service_fee=service_fee,
                total_amount=total_amount,
            )

        nights = (form.checkout_date.data - form.checkin_date.data).days
        subtotal = nightly_price * nights
        total_amount = subtotal + cleaning_fee + service_fee

        booking_detail = BookingDetail(
            booking_userid=user.user_id if user else None,
            booking_propid=property_item.prop_id,
            full_name=form.full_name.data.strip(),
            email=form.email.data.strip(),
            phone=form.phone.data.strip(),
            checkin_date=form.checkin_date.data,
            checkout_date=form.checkout_date.data,
            guests=form.guests.data,
            special_requests=(form.special_requests.data or '').strip(),
            terms_agreed=form.terms_agreed.data,
            nights=nights,
            subtotal=subtotal,
            cleaning_fee=cleaning_fee,
            service_fee=service_fee,
            total_amount=total_amount,
            booking_status='pending_payment',
        )

        db.session.add(booking_detail)
        db.session.commit()

        return redirect(url_for('payment', booking_detail_id=booking_detail.booking_detail_id))

    return render_template(
        'user/booking.html',
        form=form,
        property=property_item,
        nights=nights,
        subtotal=subtotal,
        cleaning_fee=cleaning_fee,
        service_fee=service_fee,
        total_amount=total_amount,
    )
 


@app.route('/confirmation')
@app.route('/confirmation/')
def confirmation():
    booking_detail_id = (
        request.args.get('booking_detail_id', type=int)
        or session.get('last_confirmed_booking_id')
    )
    if not booking_detail_id:
        flash('No booking selected for confirmation.', category='errormsg')
        return redirect(url_for('listing'))

    booking_detail = BookingDetail.query.get_or_404(booking_detail_id)
    if booking_detail.booking_userid and session.get('useronline') != booking_detail.booking_userid:
        flash('You are not authorized to view this confirmation.', category='errormsg')
        return redirect(url_for('listing'))

    nightly_price = Decimal(booking_detail.property.price_per_night or 0)
    nights = booking_detail.nights or 1
    subtotal = nightly_price * nights
    service_fee = Decimal('5000')
    total_amount = subtotal + service_fee

    payment = BookingPayment.query.filter_by(booking_bookingid=booking_detail.booking_detail_id).order_by(BookingPayment.payment_id.desc()).first()

    return render_template(
        'user/confirmation.html',
        booking_detail=booking_detail,
        payment=payment,
        subtotal=subtotal,
        service_fee=service_fee,
        total_amount=total_amount,
    )

@app.route('/user-dashboard')
def user_dashboard():
    if session.get('useronline'):
        id = session.get('useronline')
        deets = User.query.get(id)
        if deets and deets.user_role == 'admin':
            session.clear()
            flash('Admin accounts must use the admin login page.', category='errormsg')
            return redirect(url_for('admin_login'))
        if deets and deets.user_role == 'host':
            return redirect(url_for('host_dashboard'))
        context = dashboard_service.get_user_context(id)
        return render_template('user/users_admin.html', **context)
    flash('Please login to access your dashboard.', category='errormsg')
    return redirect(url_for('login'))

@app.route('/host-dashboard')
def host_dashboard():
    if session.get('useronline'):
        id = session.get('useronline')
        deets = User.query.get(id)
        if not deets:
            session.clear()
            flash('Session expired, please login again.', category='errormsg')
            return redirect(url_for('login'))
        if deets.user_role == 'admin':
            session.clear()
            flash('Admin accounts must use the admin login page.', category='errormsg')
            return redirect(url_for('admin_login'))
        if deets.user_role != 'host':
            return redirect(url_for('dashboard'))

        reservations_page = request.args.get('reservations_page', 1, type=int)
        properties_page = request.args.get('properties_page', 1, type=int)
        reservation_search = request.args.get('reservation_search', '').strip()
        reservation_status = request.args.get('reservation_status', '').strip()
        property_search = request.args.get('property_search', '').strip()
        property_status = request.args.get('property_status', '').strip()

        _queue_host_status_notification(deets)
        context = dashboard_service.get_host_context(
            id,
            reservations_page=reservations_page,
            properties_page=properties_page,
            reservation_search=reservation_search,
            reservation_status=reservation_status,
            property_search=property_search,
            property_status=property_status,
        )
        return render_template('user/host_dashboard.html', **context)
    flash('You must be logged in to view this page', category='errormsg')
    return redirect(url_for('login'))


@app.route('/dashboard/')
def dashboard():
    if session.get('useronline') != None:
        id = session.get('useronline')
        deets = User.query.get(id)
        if not deets:
            session.clear()
            flash('Session invalid, please login again.', category='errormsg')
            return redirect(url_for('login'))
        if deets.user_role == 'admin':
            session.clear()
            flash('Admin accounts must use the admin login page.', category='errormsg')
            return redirect(url_for('admin_login'))
        if deets.user_role == 'host':
            return redirect(url_for('host_dashboard'))
        context = dashboard_service.get_user_context(id)
        return render_template('user/users_admin.html', **context)
    else:
        flash('You must be logged in to view this page', category='errormsg')
        return redirect(url_for('login'))

@app.post('/dashboard/save/')
def save_dashboard():
    if session.get('useronline') != None:
        firstname = request.form.get('firstname')
        lastname = request.form.get('lastname')
        phone = request.form.get('phone')
        id = session.get('useronline')
        user = User.query.get(id)
        if not user:
            return 'Access Denied'
        user.user_firstname = firstname
        user.user_lastname = lastname
        user.user_phoneno = phone
        db.session.commit()
        return 'Profile updated successfully'
    else:
        return 'Access Denied'

@app.route('/dashboard/apply-host', methods=['POST'])
def apply_host():
    if session.get('useronline'):
        user_id = session.get('useronline')
        user = User.query.get(user_id)
        if not user:
            return jsonify({"status": "error", "message": "Unauthorized"}), 401
        if user.user_role == 'host':
            return jsonify({"status": "error", "message": "You are already a host."}), 400
        user.user_role = 'host'
        user.is_verified = False
        user.verification_status = 'Pending'
        db.session.commit()
        session['userrole'] = 'host'
        return jsonify({"status": "success", "message": "Host application submitted. Please wait for admin verification."})
    return jsonify({"status": "error", "message": "Unauthorized"}), 401

@app.route('/host/property/add', methods=['POST'])
def host_add_property():
    if session.get('useronline'):
        user_id = session.get('useronline')
        user = User.query.get(user_id)
        if not user or user.user_role != 'host':
            return jsonify({"status": "error", "message": "Unauthorized"}), 401
        verification_status = _resolve_host_verification_status(user)
        if verification_status != 'Verified':
            message = "Your host account is not verified yet. Property actions are disabled."
            if verification_status == 'Suspended':
                message = "Your host account is suspended. Property actions are disabled."
            return jsonify({"status": "error", "message": message}), 403
        try:
            prop_title = request.form.get('prop_title', '').strip()
            prop_description = request.form.get('prop_description', '').strip()
            prop_typeid = request.form.get('prop_typeid')
            prop_category = request.form.get('prop_category', 'Apartment')
            prop_stateid = request.form.get('prop_stateid')
            prop_lgaid = request.form.get('prop_lgaid')
            prop_city = request.form.get('prop_city', '').strip()
            prop_address = request.form.get('prop_address', '').strip()
            price_per_night = request.form.get('price_per_night')
            bedrooms = request.form.get('bedrooms')
            bathrooms = request.form.get('bathrooms')
            max_guest = request.form.get('max_guest')
            featured_image = request.files.get('featured_image')
            gallery_images = request.files.getlist('property_images')
            selected_amenities = request.form.getlist('amenities')

            property_item = dashboard_service.save_host_property(
                host_id=user_id,
                prop_title=prop_title,
                prop_description=prop_description,
                prop_typeid=prop_typeid,
                prop_category=prop_category,
                prop_address=prop_address,
                prop_city=prop_city,
                price_per_night=price_per_night,
                prop_stateid=prop_stateid,
                prop_lgaid=prop_lgaid,
                bedrooms=bedrooms,
                bathrooms=bathrooms,
                max_guest=max_guest,
                prop_availability_status='inactive',
                featured_image=featured_image,
                gallery_images=gallery_images,
                selected_amenities=selected_amenities,
            )
            return jsonify({"status": "success", "message": "Property created and submitted for verification.", "property_id": property_item.prop_id})
        except ValueError as exc:
            return jsonify({"status": "error", "message": str(exc)}), 400
        except Exception as exc:
            db.session.rollback()
            return jsonify({"status": "error", "message": str(exc)}), 500
    return jsonify({"status": "error", "message": "Unauthorized"}), 401


@app.route('/host/amenities', methods=['GET', 'POST'])
def host_amenities():
    if not session.get('useronline'):
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    user = User.query.get(session.get('useronline'))
    if not user or user.user_role != 'host':
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    verification_status = _resolve_host_verification_status(user)
    if verification_status != 'Verified':
        message = "Your host account is not verified yet. Amenities management is disabled."
        if verification_status == 'Suspended':
            message = "Your host account is suspended. Amenities management is disabled."
        return jsonify({"status": "error", "message": message}), 403

    if request.method == 'GET':
        amenities = Amenity.query.order_by(Amenity.amenity_name.asc()).all()
        return jsonify(
            {
                "status": "success",
                "amenities": [
                    {"amenity_id": amenity.amenity_id, "amenity_name": amenity.amenity_name}
                    for amenity in amenities
                ],
            }
        )

    amenity_name = (request.form.get('amenity_name') or '').strip()
    if not amenity_name:
        return jsonify({"status": "error", "message": "Amenity name is required."}), 400

    existing = Amenity.query.filter(
        func.lower(Amenity.amenity_name) == amenity_name.lower()
    ).first()
    if existing:
        return jsonify(
            {
                "status": "success",
                "message": "Amenity already exists.",
                "amenity": {
                    "amenity_id": existing.amenity_id,
                    "amenity_name": existing.amenity_name,
                },
            }
        ), 200

    amenity = Amenity(amenity_name=amenity_name)
    db.session.add(amenity)
    db.session.commit()

    return jsonify(
        {
            "status": "success",
            "message": "Amenity added successfully.",
            "amenity": {
                "amenity_id": amenity.amenity_id,
                "amenity_name": amenity.amenity_name,
            },
        }
    ), 201

@app.route('/register/', methods=['GET', 'POST'])
def register():
    register_form = RegisterForm()
    if register_form.validate_on_submit():
        role = (register_form.role.data or "").lower()
        if role not in ("customer", "host"):
            flash('Only customer and host accounts can register here.', category='errormsg')
            return redirect(url_for('register'))

        nin_number = None
        document_path = None
        verification_status = None

        if role == "host":
            nin_number = (register_form.nin_number.data or "").strip()
            if not nin_number:
                register_form.nin_number.errors.append("NIN Number is required for Hosts.")
                return render_template('user/registration.html', register=register_form)

            if not re.fullmatch(r"\d{11}", nin_number):
                register_form.nin_number.errors.append("NIN must be exactly 11 digits.")
                return render_template('user/registration.html', register=register_form)

            if not register_form.nin_document.data:
                register_form.nin_document.errors.append("Please upload your NIN document.")
                return render_template('user/registration.html', register=register_form)

            try:
                document_path = save_nin_document(register_form.nin_document.data)
            except ValueError as exc:
                register_form.nin_document.errors.append(str(exc))
                return render_template('user/registration.html', register=register_form)

            verification_status = "Pending"

        hashed = generate_password_hash(register_form.password.data)
        user = User(
            user_firstname=register_form.firstname.data,
            user_lastname=register_form.lastname.data,
            user_email=register_form.email.data,
            user_phoneno=register_form.phone.data,
            user_password=hashed,
            user_role=role,
            nin_number=nin_number,
            nin_document=document_path,
            verification_status=verification_status,
        )
        db.session.add(user)
        db.session.commit()

        session['useronline'] = user.user_id
        session['userrole'] = user.user_role

        flash('Account created successfully!', category='success')
        if user.user_role == 'host':
            return redirect(url_for('host_dashboard'))
        return redirect(url_for('dashboard'))

    return render_template('user/registration.html', register=register_form)


@app.route('/login/', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == 'GET':
        return render_template('user/login.html', form=form)
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        deets = User.query.filter(User.user_email == email).first()
        if deets:
            if deets.user_role == 'admin':
                flash('Admin accounts must log in from the admin login page.', category='errormsg')
                return redirect(url_for('admin_login'))
            if deets.user_role not in ('customer', 'host'):
                flash('This account cannot sign in from the user login page.', category='errormsg')
                return redirect(url_for('login'))
            stored_password = deets.user_password
            if check_password_hash(stored_password, password):
                session['useronline'] = deets.user_id
                session['userrole'] = deets.user_role
                if deets.user_role == 'host':
                    _queue_host_status_notification(deets)
                    return redirect(url_for('host_dashboard'))
                return redirect(url_for('dashboard'))
            flash('Invalid password', category='errormsg')
            return redirect(url_for('login'))
        flash('Invalid email', category='errormsg')
        return redirect(url_for('login'))
    return render_template('user/login.html', form=form)


@app.route('/check/email/', methods=['GET', 'POST'])
def check_email():
    email = request.args.get('email')
    check = User.query.filter(User.user_email == email).first()
    if check:
        return "<span class='text-danger'>Email has been taken</span>"
    return "<span class='text-success'>Email is available</span>"


@app.route('/logout/')
def logout():
    if session.get('useronline'):
        session.pop('useronline', None)
        session.pop('userrole', None)
        session.clear()
    return redirect('/')










    