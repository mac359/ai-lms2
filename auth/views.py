from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from . import auth_bp
from app import db
from models import User, StudentProfile, InstructorProfile
from forms import LoginForm, StudentRegistrationForm, InstructorRegistrationForm, StudentProfileForm, InstructorProfileForm

@auth_bp.route('/')
def home():
    return render_template('home.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    role = request.args.get('role')
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            if user.role == 'student':
                return redirect(url_for('student.dashboard'))
            elif user.role == 'instructor':
                return redirect(url_for('instructor.dashboard'))
            elif user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            else:
                flash('Unknown user role.', 'danger')
                return redirect(url_for('auth.login'))
        else:
            flash('Invalid email or password', 'danger')
    return render_template('login.html', form=form, role=role)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.home'))

@auth_bp.route('/register/student', methods=['GET', 'POST'])
def register_student():
    form = StudentRegistrationForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('Email already registered. Please log in or use a different email.', 'danger')
            return redirect(url_for('auth.register_student'))
        user = User(email=form.email.data, password_hash=generate_password_hash(form.password.data), role='student')
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for('student.dashboard'))
    return render_template('register_student.html', form=form)

@auth_bp.route('/register/instructor', methods=['GET', 'POST'])
def register_instructor():
    form = InstructorRegistrationForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('Email already registered. Please log in or use a different email.', 'danger')
            return redirect(url_for('auth.register_instructor'))
        user = User(
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data),
            role='instructor',
            is_active=True
        )
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for('instructor.dashboard'))
    return render_template('register_instructor.html', form=form)

@auth_bp.route('/profile/student', methods=['GET', 'POST'])
@login_required
def student_profile():
    form = StudentProfileForm()
    if form.validate_on_submit():
        profile = StudentProfile(
            user_id=current_user.id,
            name=form.name.data,
            grade_level=form.grade_level.data,
            subject_interests=form.subject_interests.data,
            learning_style=form.learning_style.data,
            support_needs=form.support_needs.data,
            goal=form.goal.data
        )
        db.session.add(profile)
        db.session.commit()
        return redirect(url_for('student.dashboard'))
    return render_template('student_profile.html', form=form)

@auth_bp.route('/profile/instructor', methods=['GET', 'POST'])
@login_required
def instructor_profile():
    form = InstructorProfileForm()
    if form.validate_on_submit():
        profile = InstructorProfile(
            user_id=current_user.id,
            name=form.name.data,
            bio=form.bio.data,
            area_of_expertise=form.area_of_expertise.data,
            teaching_style=form.teaching_style.data,
            years_of_experience=form.years_of_experience.data,
            subjects_taught=form.subjects_taught.data,
            student_feedback_summary=form.student_feedback_summary.data
        )
        db.session.add(profile)
        db.session.commit()
        return redirect(url_for('instructor.dashboard'))
    return render_template('instructor_profile.html', form=form)

@auth_bp.route('/account')
@login_required
def account():
    if current_user.role == 'student':
        return redirect(url_for('auth.student_profile'))
    elif current_user.role == 'instructor':
        return redirect(url_for('auth.instructor_profile'))
    else:
        flash('No account page for this role.', 'warning')
        return redirect(url_for('auth.home')) 