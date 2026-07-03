from flask import render_template, request, url_for, redirect, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from pkg import app
from pkg.dashboard_service import DashboardService
from pkg.forms import RegisterForm, LoginForm
from pkg.models import User, Property, db

dashboard_service = DashboardService()

@app.route('/')
def home():
    deets = None
    if session.get('useronline'):
        id = session.get('useronline')
        deets = User.query.get(id)
    return render_template('user/index.html',deets=deets)


@app.route('/listing')
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

@app.route('/api/search-properties')
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

@app.route('/properties_details')
def properties_details():
    prop_id = request.args.get('prop_id', type=int)
    property_item = None
    if prop_id:
        property_item = Property.query.get(prop_id)
    return render_template('user/properties_details.html', property=property_item)

@app.route('/booking')
def booking():
    return render_template('user/booking.html') 
 
@app.route('/payment')
def payment():
    return render_template('payment.html')

@app.route('/confirmation')
def confirmation():
    return render_template('user/confirmation.html')

@app.route('/user-dashboard')
def user_dashboard():
    if session.get('useronline'):
        id = session.get('useronline')
        deets = User.query.get(id)
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
        if deets.user_role != 'host':
            return redirect(url_for('dashboard'))
        context = dashboard_service.get_host_context(id)
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
        try:
            prop_title = request.form.get('prop_title', '').strip()
            prop_description = request.form.get('prop_description', '').strip()
            prop_typeid = request.form.get('prop_typeid')
            prop_category = request.form.get('prop_category', 'Apartment')
            prop_stateid = request.form.get('prop_stateid')
            prop_lgaid = request.form.get('prop_lgaid')
            prop_address = request.form.get('prop_address', '').strip()
            price_per_night = request.form.get('price_per_night')
            bedrooms = request.form.get('bedrooms')
            bathrooms = request.form.get('bathrooms')
            max_guest = request.form.get('max_guest')
            featured_image = request.files.get('featured_image')

            property_item = dashboard_service.save_host_property(
                host_id=user_id,
                prop_title=prop_title,
                prop_description=prop_description,
                prop_typeid=prop_typeid,
                prop_category=prop_category,
                prop_address=prop_address,
                price_per_night=price_per_night,
                prop_stateid=prop_stateid,
                prop_lgaid=prop_lgaid,
                bedrooms=bedrooms,
                bathrooms=bathrooms,
                max_guest=max_guest,
                prop_availability_status='inactive',
                featured_image=featured_image,
            )
            return jsonify({"status": "success", "message": "Property created and submitted for verification.", "property_id": property_item.prop_id})
        except ValueError as exc:
            return jsonify({"status": "error", "message": str(exc)}), 400
        except Exception as exc:
            db.session.rollback()
            return jsonify({"status": "error", "message": str(exc)}), 500
    return jsonify({"status": "error", "message": "Unauthorized"}), 401

@app.route('/register/', methods=['GET', 'POST'])
def register():
    register_form = RegisterForm()
    if register_form.validate_on_submit():
        hashed = generate_password_hash(register_form.password.data)
        user = User(
            user_firstname=register_form.firstname.data,
            user_lastname=register_form.lastname.data,
            user_email=register_form.email.data,
            user_phoneno=register_form.phone.data,
            user_password=hashed,
            user_role=register_form.role.data,
        )
        db.session.add(user)
        db.session.commit()
        flash('Account created successfully!', category='success')
        return redirect(url_for('login'))
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
            stored_password = deets.user_password
            if check_password_hash(stored_password, password):
                session['useronline'] = deets.user_id
                session['userrole'] = deets.user_role
                if deets.user_role == 'host':
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










    