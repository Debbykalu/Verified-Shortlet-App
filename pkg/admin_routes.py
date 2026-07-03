from flask import render_template, request, url_for, redirect, flash, session, jsonify, current_app
from decimal import Decimal
import os, uuid
from werkzeug.security import generate_password_hash, check_password_hash
from pkg import app
from pkg.forms import AdminRegisterForm, AdminLoginForm
from pkg.models import Admin, db, Property, PropertyType, PropertyState, PropertyLGA, PropertyAmenity, Amenity, PropertyImage, User, Booking
from pkg.admin_service import AdminDashboardService

admin_service = AdminDashboardService()


@app.route('/admin-dashboard/')
def admin_dashboard():
    if 'adminonline' not in session:
        flash("Please login first.", "errormsg")
        return redirect(url_for('admin_login'))

    admin_id = session['adminonline']
    dashboard_context = admin_service.get_dashboard_context(admin_id)

    return render_template(
        'admin/admin_dashboard.html',
        **dashboard_context
    )

@app.route('/admin-register/', methods=['GET', 'POST'])
def admin_register():
    register = AdminRegisterForm()

    if register.validate_on_submit():

        hashed = generate_password_hash(register.password.data)

        admin = Admin(
            admin_firstname=register.firstname.data,
            admin_lastname=register.lastname.data,
            admin_email=register.email.data,
            admin_password=hashed,
        )

        db.session.add(admin)
        db.session.commit()

        flash("Account created successfully!")
        return redirect(url_for("admin_login"))

    return render_template("admin/admin_registration.html", register=register)

@app.route('/admin-login/', methods=['GET', 'POST'])
def admin_login():
    form = AdminLoginForm()

    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        deets = Admin.query.filter_by(admin_email=email).first()

        if deets and check_password_hash(deets.admin_password, password):
            session['adminonline'] = deets.admin_id
            return redirect(url_for('admin_dashboard'))

        flash("Invalid email or password", "errormsg")

    return render_template("admin/admin_login.html", form=form)


@app.route('/admin-logout/')
def admin_logout():
    session.pop('adminonline', None)
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for('admin_login'))


@app.route('/add-property/', methods=['GET'])
def add_property():
    property_types = PropertyType.query.order_by(PropertyType.prop_typename).all()
    property_states = PropertyState.query.order_by(PropertyState.state_name).all()
    amenities = Amenity.query.order_by(Amenity.amenity_name).all()
    return render_template(
        "admin/add_property.html",
        property_types=property_types,
        property_states=property_states,
        amenities=amenities
    )

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp'}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def parse_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes", "y")
    return bool(value)


def save_image(image):
    if image.filename == "":

        return None

    if not allowed_file(image.filename):

        raise ValueError("Unsupported image format.")

    extension = image.filename.rsplit(".",1)[1].lower()

    filename = f"{uuid.uuid4().hex}.{extension}"

    upload_folder = os.path.join(

        current_app.root_path,

        "static",

        "uploads",

        "properties"

    )

    os.makedirs(upload_folder, exist_ok=True)

    image.save(

        os.path.join(upload_folder, filename)

    )

    return filename

@app.route("/save-property/", methods=["POST"])
def save_property():
    try:
        prop_title = request.form.get("prop_title", "").strip()
        prop_description = request.form.get("prop_description", "").strip()
        prop_typeid = request.form.get("prop_typeid")
        prop_category = request.form.get("prop_category")
        prop_stateid = request.form.get("prop_stateid")
        prop_lgaid = request.form.get("prop_lgaid")
        prop_address = request.form.get("prop_address", "").strip()
        price_per_night = request.form.get("price_per_night")
        bedrooms = request.form.get("bedrooms")
        bathrooms = request.form.get("bathrooms")
        max_guest = request.form.get("max_guest")
        prop_availability_status = request.form.get(
            "prop_availability_status",
            "available"
        )


        if not prop_title:
            return jsonify({
                "status": "error",
                "message": "Property title is required."
            }), 400

        if not prop_typeid:
            return jsonify({
                "status": "error",
                "message": "Select a property type."
            }), 400

        if not prop_stateid:
            return jsonify({
                "status": "error",
                "message": "Select a state."
            }), 400

        if not prop_lgaid:
            return jsonify({
                "status": "error",
                "message": "Select a Local Government."
            }), 400

        if not price_per_night:
            return jsonify({
                "status": "error",
                "message": "Enter the property price."
            }), 400


        property = Property(

            # Replace 1 later with the selected host id
            prop_userid=1,

            prop_title=prop_title,
            prop_description=prop_description,

            prop_typeid=int(prop_typeid),
            prop_stateid=int(prop_stateid),
            prop_lgaid=int(prop_lgaid),

            prop_category=prop_category,
            prop_address=prop_address,

            price_per_night=Decimal(price_per_night),

            bedrooms=int(bedrooms) if bedrooms else 0,
            bathrooms=int(bathrooms) if bathrooms else 0,
            max_guest=int(max_guest) if max_guest else 1,

            prop_availability_status=prop_availability_status,

            is_verified=False

        )

        db.session.add(property)

        db.session.flush()


        featured_image = request.files.get("featured_image")

        if featured_image and featured_image.filename != "":

            filename = save_image(featured_image)

            featured = PropertyImage(

                img_propid=property.prop_id,

                image_url=filename,

                is_featured=True

            )

            db.session.add(featured)



        gallery_images = request.files.getlist("property_images")

        for image in gallery_images:

            if image.filename == "":
                continue

            filename = save_image(image)

            gallery = PropertyImage(

                img_propid=property.prop_id,

                image_url=filename,

                is_featured=False

            )

            db.session.add(gallery)


        selected_amenities = request.form.getlist("amenities")
        print(selected_amenities)

        for amenity_id in selected_amenities:

            amenity = PropertyAmenity(

                prop_id=property.prop_id,

                amenity_id=int(amenity_id)

            )

            db.session.add(amenity)


        db.session.commit()


        return jsonify({

            "status": "success",

            "message": "Property added successfully.",

            "property_id": property.prop_id

        }), 200


    except Exception as e:

        db.session.rollback()

        print(e)

        return jsonify({

            "status": "error",

            "message": str(e)

        }), 500

@app.route('/get-lgas/<int:state_id>', methods=['GET'])
def get_lgas(state_id):
    lgas = PropertyLGA.query.filter_by(
        state_id=state_id
    ).order_by(
        PropertyLGA.lga_name
    ).all()

    data = []
    for lga in lgas:
        data.append({
            "id": lga.lga_id,
            "name": lga.lga_name
        })

    return jsonify(data)


@app.route('/admin/properties/<int:property_id>', methods=['DELETE'])
def delete_property(property_id):
    if 'adminonline' not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    property_item = admin_service.delete_property(property_id)
    if not property_item:
        return jsonify({"status": "error", "message": "Property not found"}), 404

    return jsonify({"status": "success", "message": "Property deleted successfully"})


@app.route('/admin/properties/<int:property_id>/status', methods=['POST'])
def update_property_status(property_id):
    if 'adminonline' not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    status = request.json.get('status') if request.is_json else request.form.get('status')
    try:
        property_item = admin_service.update_property_status(property_id, status)
    except ValueError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 400

    if not property_item:
        return jsonify({"status": "error", "message": "Property not found"}), 404

    return jsonify({"status": "success", "message": "Status updated", "property_id": property_id})


@app.route('/admin/properties/<int:property_id>/verify', methods=['POST'])
def verify_property(property_id):
    if 'adminonline' not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    verified = request.json.get('verified', True) if request.is_json else request.form.get('verified', True)
    verified = parse_bool(verified)
    property_item = admin_service.verify_property(property_id, verified)

    if not property_item:
        return jsonify({"status": "error", "message": "Property not found"}), 404

    return jsonify({"status": "success", "message": "Property verification updated"})


@app.route('/admin/hosts/<int:user_id>/verify', methods=['POST'])
def verify_host(user_id):
    if 'adminonline' not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    verified = request.json.get('verified', True) if request.is_json else request.form.get('verified', True)
    verified = parse_bool(verified)
    user = admin_service.verify_host(user_id, verified)

    if not user:
        return jsonify({"status": "error", "message": "Host not found"}), 404

    return jsonify({"status": "success", "message": "Host verification updated"})


@app.route('/admin/bookings/<int:booking_id>/status', methods=['POST'])
def update_booking_status(booking_id):
    if 'adminonline' not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    status = request.json.get('status') if request.is_json else request.form.get('status')
    booking = Booking.query.get(booking_id)
    if not booking:
        return jsonify({"status": "error", "message": "Booking not found"}), 404

    allowed_statuses = {"pending", "confirmed", "cancelled", "completed"}
    if status not in allowed_statuses:
        return jsonify({"status": "error", "message": "Invalid booking status"}), 400

    booking.booking_status = status
    db.session.commit()
    return jsonify({"status": "success", "message": "Booking status updated"})
     