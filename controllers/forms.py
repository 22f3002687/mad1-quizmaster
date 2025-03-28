from flask_wtf import FlaskForm
from wtforms import RadioField, StringField, PasswordField, DateField, SubmitField, DateTimeLocalField, TimeField, TextAreaField, IntegerField
from wtforms.validators import DataRequired, Email, Length, EqualTo, NumberRange

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

class SubjectForm(FlaskForm):
    name = StringField("Subject Name", validators=[DataRequired(), Length(max=100)])
    description = StringField("Description", validators=[DataRequired(), Length(max=100)])

    submit = SubmitField("Add Subject")

class ChapterForm(FlaskForm):
    name = StringField("Chapter Name", validators=[DataRequired(), Length(max=100)])
    description = StringField("Description", validators=[DataRequired(), Length(max=100)])

    submit = SubmitField("Add Chapter")

class QuizForm(FlaskForm):
    date_of_quiz = DateTimeLocalField('Date of Quiz', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    time_duration = TimeField('Time Duration', format='%H:%M', validators=[DataRequired()])
    remarks = TextAreaField('Remarks')
    
    submit = SubmitField('Create Quiz')


class QuestionForm(FlaskForm):
    question_statement = StringField('Question', validators=[DataRequired()])
    option1 = StringField('Option 1', validators=[DataRequired()])
    option2 = StringField('Option 2', validators=[DataRequired()])
    option3 = StringField('Option 3', validators=[DataRequired()])
    option4 = StringField('Option 4', validators=[DataRequired()])
    correct_option = IntegerField('Correct Option (1-4)', validators=[DataRequired(), NumberRange(min=1, max=4)])
    
    submit = SubmitField('Save Question')
