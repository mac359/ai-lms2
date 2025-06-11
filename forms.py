from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, SelectField, IntegerField
from wtforms.validators import DataRequired, Email, EqualTo, Length

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class StudentRegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register as Student')

class InstructorRegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register as Instructor')

class StudentProfileForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    grade_level = StringField('Grade Level', validators=[DataRequired()])
    subject_interests = StringField('Subject Interests', validators=[DataRequired()])
    learning_style = StringField('Learning Style', validators=[DataRequired()])
    support_needs = StringField('Support Needed', validators=[DataRequired()])
    goal = StringField('Goal', validators=[DataRequired()])
    submit = SubmitField('Save Profile')

class InstructorProfileForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    bio = TextAreaField('Bio', validators=[DataRequired()])
    area_of_expertise = StringField('Area of Expertise', validators=[DataRequired()])
    teaching_style = StringField('Teaching Style', validators=[DataRequired()])
    years_of_experience = IntegerField('Years of Experience', validators=[DataRequired()])
    subjects_taught = StringField('Subjects Taught', validators=[DataRequired()])
    student_feedback_summary = TextAreaField('Student Feedback Summary')
    submit = SubmitField('Save Profile') 