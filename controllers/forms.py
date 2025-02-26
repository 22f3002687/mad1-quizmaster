from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, DateField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo

class UserRegistrationForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(max=100)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6, max=256)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(),EqualTo('password')])
    full_name = StringField("Full Name", validators=[DataRequired(), Length(max=100)])
    qualification = StringField("Qualification", validators=[DataRequired(), Length(max=100)])
    dob = DateField("Date of Birth", format='%Y-%m-%d', validators=[DataRequired()])
    
    submit = SubmitField("Register")

class UserLoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(),Email(),Length(max=120)])
    password = PasswordField("Password", validators=[DataRequired()])
    
    submit = SubmitField("Login")

class AdminLoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(),Email(),Length(max=120)])
    password = PasswordField("Password", validators=[DataRequired()])
    
    submit = SubmitField("Login")
