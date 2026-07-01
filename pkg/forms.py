from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length


class RegisterForm(FlaskForm):
     firstname = StringField( "Fisrt Name", validators=[DataRequired(), Length(min=3, max=200)],    render_kw={"placeholder": "Enter your first name"} ) 
     lastname = StringField( "Last Name", validators=[DataRequired(), Length(min=3, max=200)],      render_kw={"placeholder": "Enter your last name"} ) 
     email = StringField( "Email Address", validators=[DataRequired(), Email()], render_kw={"placeholder": "Enter your email address"} ) 
     phone = StringField( "Phone Number", validators=[DataRequired(), Length(min=11, max=15)], render_kw={"placeholder": "Enter your phone number"} ) 
     password = PasswordField( "Password", validators=[DataRequired(), Length(min=6)], render_kw={"placeholder": "Enter your password"} ) 
     confirm_pass = PasswordField( "Confirm Password", validators=[ DataRequired(), EqualTo("password", message="Passwords must match.") ], render_kw={"placeholder": "Confirm your password"} ) 
     role = SelectField( "Role", choices=[ ("customer", "Customer"), ("host", "Host")], default="customer" ) 
     submit = SubmitField("Register")


class AdminRegisterForm(FlaskForm):
     firstname = StringField( "Fisrt Name", validators=[DataRequired(), Length(min=3, max=200)],    render_kw={"placeholder": "Enter your first name"} ) 
     lastname = StringField( "Last Name", validators=[DataRequired(), Length(min=3, max=200)],      render_kw={"placeholder": "Enter your last name"} ) 
     email = StringField( "Email Address", validators=[DataRequired(), Email()], render_kw={"placeholder": "Enter your email address"} ) 
     password = PasswordField( "Password", validators=[DataRequired(), Length(min=6)], render_kw={"placeholder": "Enter your password"} ) 
     confirm_pass = PasswordField( "Confirm Password", validators=[ DataRequired(), EqualTo("password", message="Passwords must match.") ], render_kw={"placeholder": "Confirm your password"} ) 
     submit = SubmitField("Register")




class LoginForm(FlaskForm):
    email = StringField("Email Address",validators=[DataRequired(), Email()])

    password = PasswordField("Password",validators=[DataRequired()])

    login = SubmitField("Login")



class AdminLoginForm(FlaskForm):
    email = StringField("Email Address",validators=[DataRequired(), Email()])

    password = PasswordField("Password",validators=[DataRequired()])

    login = SubmitField("Login")


