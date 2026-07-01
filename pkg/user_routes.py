from flask import render_template,request, url_for, redirect,flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from pkg import app
from pkg.forms import RegisterForm, LoginForm
from pkg.models import User,db

@app.route('/')
def home():
    if session.get('useronline') != None:
        id = session.get('useronline')
        deets = User.query.get(id)
    return render_template('user/index.html',deets=deets)


@app.route('/listing')
def listing():
    return render_template('user/listing.html')

@app.route('/properties_details')
def properties_details():
    return render_template('user/properties_details.html')

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
    return render_template('user/users_admin.html')

@app.route('/register/', methods=['GET', 'POST'])
def register():
    register = RegisterForm()

    if register.validate_on_submit():

        hashed = generate_password_hash(register.password.data)

        user = User(
            user_firstname=register.firstname.data,
            user_lastname=register.lastname.data,
            user_email=register.email.data,
            user_phoneno=register.phone.data,
            user_password=hashed,
            user_role=register.role.data
        )

        db.session.add(user)
        db.session.commit()

        flash("Account created successfully!")
        return redirect(url_for("login"))

    return render_template("user/registration.html", register=register)

@app.route('/login/', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == "GET":
        return render_template("user/login.html", form=form)
    else:
        if form.validate_on_submit():
            email = form.email.data
            password = form.password.data
            deets = User.query.filter(User.user_email == email).first()
            if deets: #email is correct
                stored_password = deets.user_password
                rsp = check_password_hash(stored_password,password)
                if rsp:
                    session['useronline'] = deets.user_id
                    return redirect(url_for('dashboard'))
                    
                else:
                    flash('Invalid password', category='errormsg')
                    return redirect(url_for('login'))
            else: #measns the email and password is not found
                flash('Invalid email', category='errormsg')
                return redirect(url_for('login'))
        else:
            return render_template("user/login.html", form=form)
        


@app.route('/dashboard/')
def dashboard():
    if session.get('useronline') != None:
        id = session.get('useronline')
        deets = User.query.get(id)
        return render_template('user/users_admin.html', deets=deets)
    else:
        flash("You must be logged in to view this page", category='errormsg')
        return redirect(url_for('login'))
    


@app.post('/dashboard/save/')
def save_dashboard():
    if session.get('useronline') != None:
        firstname = request.form.get('firstname')
        lastname = request.form.get('lastname')
        phone = request.form.get('phone')
        id = User.query.get('useronline')
        user = User.query.get(id)
        user.user_firstname = firstname
        user.user_lastname = lastname
        user.phone = phone
        db.session.commit()
        return 'Profile updated succefully'
    else:
        return 'Access Denied'
    


@app.route('/check/email/', methods=['GET','POST'])
def check_email():
    email = request.args.get('email')
    check = User.query.filter(User.email == email).first()
    if check:
        return "<span class='text-danger'>Email has been taken</span>"
    else:
        return "<span class='text-success'>Email is available</span>"

@app.route('/logout/')
def logout():
    if session.get('useronline'):
        session.pop('useronline', None)
        session.clear()
    return redirect("/")










    