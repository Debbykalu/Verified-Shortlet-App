from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from wtforms import FileField, StringField, PasswordField, SelectField, SubmitField, DateField, IntegerField, TextAreaField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, Regexp


class RegisterForm(FlaskForm):
     firstname = StringField( "Fisrt Name", validators=[DataRequired(), Length(min=3, max=200)],    render_kw={"placeholder": "Enter your first name"} ) 
     lastname = StringField( "Last Name", validators=[DataRequired(), Length(min=3, max=200)],      render_kw={"placeholder": "Enter your last name"} ) 
     email = StringField( "Email Address", validators=[DataRequired(), Email()], render_kw={"placeholder": "Enter your email address"} ) 
     phone = StringField( "Phone Number", validators=[DataRequired(), Length(min=11, max=15)], render_kw={"placeholder": "Enter your phone number"} ) 
     password = PasswordField( "Password", validators=[DataRequired(), Length(min=6)], render_kw={"placeholder": "Enter your password"} ) 
     confirm_pass = PasswordField( "Confirm Password", validators=[ DataRequired(), EqualTo("password", message="Passwords must match.") ], render_kw={"placeholder": "Confirm your password"} ) 
     role = SelectField( "Role", choices=[ ("customer", "Customer"), ("host", "Host")], default="customer" ) 
     nin_number = StringField(
          "NIN Number",
          validators=[
               Optional(),
               Regexp(r"^\d{11}$", message="NIN must be exactly 11 digits."),
          ],
          render_kw={"placeholder": "Enter your NIN Number"},
     )
     nin_document = FileField(
          "NIN Document",
          validators=[Optional(), FileAllowed(["pdf", "jpg", "jpeg", "png"], "Only PDF, JPG, JPEG and PNG files are allowed.")],
     )
     submit = SubmitField("Register")


class AdminRegisterForm(FlaskForm):
     firstname = StringField( "Fisrt Name", validators=[DataRequired(), Length(min=3, max=200)],    render_kw={"placeholder": "Enter your first name"} ) 
     lastname = StringField( "Last Name", validators=[DataRequired(), Length(min=3, max=200)],      render_kw={"placeholder": "Enter your last name"} ) 
     email = StringField( "Email Address", validators=[DataRequired(), Email()], render_kw={"placeholder": "Enter your email address"} ) 
     password = PasswordField( "Password", validators=[DataRequired(), Length(min=6)], render_kw={"placeholder": "Enter your password"} ) 
     confirm_pass = PasswordField( "Confirm Password", validators=[ DataRequired(), EqualTo("password", message="Passwords must match.") ], render_kw={"placeholder": "Confirm your password"} ) 
     nin_number = StringField("NIN Number",validators=[Optional(), Length(min=11, max=20, message="Enter a valid NIN number.")], render_kw={"placeholder": "Enter your NIN Number"})
     nin_document = FileField("NIN Document",validators=[Optional(),FileAllowed(["pdf", "jpg", "jpeg", "png"],"Only PDF, JPG, JPEG and PNG files are allowed.")])
     submit = SubmitField("Register")


class LoginForm(FlaskForm):
    email = StringField("Email Address",validators=[DataRequired(), Email()])

    password = PasswordField("Password",validators=[DataRequired()])

    login = SubmitField("Login")



class AdminLoginForm(FlaskForm):
    email = StringField("Email Address",validators=[DataRequired(), Email()])

    password = PasswordField("Password",validators=[DataRequired()])

    login = SubmitField("Login")


class BookingDetailsForm(FlaskForm):
     full_name = StringField("Full Name", validators=[DataRequired(), Length(min=3, max=200)])
     email = StringField("Email Address", validators=[DataRequired(), Email()])
     phone = StringField("Phone Number", validators=[DataRequired(), Length(min=7, max=20)])
     checkin_date = DateField("Check In", format="%Y-%m-%d", validators=[DataRequired()])
     checkout_date = DateField("Check Out", format="%Y-%m-%d", validators=[DataRequired()])
     guests = SelectField("Number of Guests", coerce=int, validators=[DataRequired()])
     special_requests = TextAreaField("Special Requests", validators=[Length(max=1000)])
     terms_agreed = BooleanField(
          "I agree to the booking terms and cancellation policy",
          validators=[DataRequired(message="You must agree to the terms and conditions.")],
     )
     submit = SubmitField("Proceed to Payment")


