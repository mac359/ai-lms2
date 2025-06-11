from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user, login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import User, Course, Enrollment, StudentProfile, InstructorProfile, db
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, TextAreaField, SubmitField, BooleanField, IntegerField, DateField, TimeField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional
from functools import wraps
import os

admin_bp = Blueprint('admin', __name__)

# Admin authentication decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function

# Admin Login Form
class AdminLoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

# User Creation Form
class CreateUserForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Role', choices=[('student', 'Student'), ('instructor', 'Instructor'), ('admin', 'Admin')], validators=[DataRequired()])
    name = StringField('Name', validators=[DataRequired()])
    phone = StringField('Phone Number')
    bio = TextAreaField('Bio/Description')
    is_active = BooleanField('Account is active', default=True)
    send_welcome_email = BooleanField('Send welcome email', default=True)
    submit = SubmitField('Create User')

# User Edit Form
class EditUserForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    name = StringField('Name', validators=[DataRequired()])
    role = SelectField('Role', choices=[('student', 'Student'), ('instructor', 'Instructor'), ('admin', 'Admin')], validators=[DataRequired()])
    phone = StringField('Phone Number')
    bio = TextAreaField('Bio/Description')
    is_active = BooleanField('Account is active')
    send_notification = BooleanField('Send notification email')
    submit = SubmitField('Update User')

# Course Creation Form
class CreateCourseForm(FlaskForm):
    title = StringField('Course Title', validators=[DataRequired()])
    code = StringField('Course Code')
    description = TextAreaField('Course Description', validators=[DataRequired()])
    instructor_id = SelectField('Instructor', coerce=int, validators=[DataRequired()])
    category = SelectField('Category', choices=[
        ('', 'Select Category'),
        ('mathematics', 'Mathematics'),
        ('science', 'Science'),
        ('language', 'Language Arts'),
        ('history', 'History'),
        ('art', 'Art & Music'),
        ('technology', 'Technology'),
        ('physical', 'Physical Education'),
        ('other', 'Other')
    ])
    level = SelectField('Difficulty Level', choices=[
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced')
    ], default='intermediate')
    max_students = IntegerField('Maximum Students', default=50)
    start_date = DateField('Start Date')
    end_date = DateField('End Date')
    meeting_time = TimeField('Meeting Time')
    syllabus = TextAreaField('Syllabus')
    prerequisites = TextAreaField('Prerequisites')
    learning_outcomes = TextAreaField('Learning Outcomes')
    is_active = BooleanField('Course is active', default=True)
    allow_enrollment = BooleanField('Allow student enrollment', default=True)
    enable_quizzes = BooleanField('Enable quizzes', default=True)
    enable_assignments = BooleanField('Enable assignments', default=True)
    submit = SubmitField('Create Course')

# Course Edit Form
class EditCourseForm(FlaskForm):
    title = StringField('Course Title', validators=[DataRequired()])
    code = StringField('Course Code')
    description = TextAreaField('Course Description', validators=[DataRequired()])
    instructor_id = SelectField('Instructor', coerce=int, validators=[DataRequired()])
    category = SelectField('Category', choices=[
        ('', 'Select Category'),
        ('mathematics', 'Mathematics'),
        ('science', 'Science'),
        ('language', 'Language Arts'),
        ('history', 'History'),
        ('art', 'Art & Music'),
        ('technology', 'Technology'),
        ('physical', 'Physical Education'),
        ('other', 'Other')
    ])
    level = SelectField('Difficulty Level', choices=[
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced')
    ])
    max_students = IntegerField('Maximum Students')
    start_date = DateField('Start Date')
    end_date = DateField('End Date')
    meeting_time = TimeField('Meeting Time')
    syllabus = TextAreaField('Syllabus')
    prerequisites = TextAreaField('Prerequisites')
    learning_outcomes = TextAreaField('Learning Outcomes')
    is_active = BooleanField('Course is active')
    allow_enrollment = BooleanField('Allow student enrollment')
    enable_quizzes = BooleanField('Enable quizzes')
    enable_assignments = BooleanField('Enable assignments')
    submit = SubmitField('Update Course')

# Admin Login Route
@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated and current_user.role == 'admin':
        return redirect(url_for('admin.dashboard'))
    
    form = AdminLoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.role == 'admin' and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            flash('Welcome to Admin Panel!', 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Invalid email or password.', 'danger')
    
    return render_template('admin/login.html', form=form)

# Admin Logout Route
@admin_bp.route('/logout')
@login_required
@admin_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('admin.login'))

# Admin Dashboard
@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    # Get statistics
    total_students = User.query.filter_by(role='student').count()
    total_instructors = User.query.filter_by(role='instructor').count()
    total_courses = Course.query.count()
    total_enrollments = Enrollment.query.count()
    
    # Get recent users
    recent_students = User.query.filter_by(role='student').order_by(User.created_at.desc()).limit(5).all()
    recent_instructors = User.query.filter_by(role='instructor').order_by(User.created_at.desc()).limit(5).all()
    
    # Get recent courses
    recent_courses = Course.query.order_by(Course.created_at.desc()).limit(5).all()
    
    # Get user activity stats
    active_students = User.query.filter_by(role='student', is_active=True).count()
    active_instructors = User.query.filter_by(role='instructor', is_active=True).count()
    
    return render_template('admin/dashboard.html',
                         total_students=total_students,
                         total_instructors=total_instructors,
                         total_courses=total_courses,
                         total_enrollments=total_enrollments,
                         recent_students=recent_students,
                         recent_instructors=recent_instructors,
                         recent_courses=recent_courses,
                         active_students=active_students,
                         active_instructors=active_instructors,
                         show_logout=True)

# User Management
@admin_bp.route('/users')
@login_required
@admin_required
def users():
    role_filter = request.args.get('role', '')
    status_filter = request.args.get('status', '')
    search_filter = request.args.get('search', '')
    
    query = User.query
    
    if role_filter:
        query = query.filter_by(role=role_filter)
    
    if status_filter:
        is_active = status_filter == 'active'
        query = query.filter_by(is_active=is_active)
    
    if search_filter:
        query = query.filter(User.email.contains(search_filter))
    
    users = query.order_by(User.created_at.desc()).all()
    
    return render_template('admin/users.html', users=users, role_filter=role_filter, status_filter=status_filter)

# Create User
@admin_bp.route('/users/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_user():
    form = CreateUserForm()
    
    # Pre-populate role if provided in URL
    role_param = request.args.get('role', '')
    if role_param:
        form.role.data = role_param
    
    if form.validate_on_submit():
        # Check if user already exists
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('User with this email already exists.', 'danger')
            return render_template('admin/create_user.html', form=form)
        
        # Create new user
        user = User(
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data),
            role=form.role.data,
            is_active=form.is_active.data
        )
        db.session.add(user)
        db.session.commit()
        
        # Create profile based on role
        if form.role.data == 'student':
            profile = StudentProfile(
                user_id=user.id,
                name=form.name.data,
                phone=form.phone.data,
                bio=form.bio.data
            )
        elif form.role.data == 'instructor':
            profile = InstructorProfile(
                user_id=user.id,
                name=form.name.data,
                phone=form.phone.data,
                bio=form.bio.data
            )
        
        db.session.add(profile)
        db.session.commit()
        
        flash(f'{form.role.data.title()} created successfully!', 'success')
        return redirect(url_for('admin.users'))
    
    return render_template('admin/create_user.html', form=form)

# Edit User
@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = EditUserForm()
    
    if request.method == 'GET':
        # Pre-populate form with user data
        form.email.data = user.email
        form.role.data = user.role
        form.is_active.data = user.is_active
        
        # Pre-populate profile data
        if user.role == 'student' and user.student_profile:
            form.name.data = user.student_profile.name
            form.phone.data = user.student_profile.phone
            form.bio.data = user.student_profile.bio
        elif user.role == 'instructor' and user.instructor_profile:
            form.name.data = user.instructor_profile.name
            form.phone.data = user.instructor_profile.phone
            form.bio.data = user.instructor_profile.bio
    
    if form.validate_on_submit():
        # Check if email is already taken by another user
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user and existing_user.id != user.id:
            flash('Email is already taken by another user.', 'danger')
            return render_template('admin/edit_user.html', form=form, user=user)
        
        user.email = form.email.data
        user.role = form.role.data
        user.is_active = form.is_active.data
        
        # Update profile
        if user.role == 'student':
            if not user.student_profile:
                profile = StudentProfile(user_id=user.id)
                db.session.add(profile)
            else:
                profile = user.student_profile
            profile.name = form.name.data
            profile.phone = form.phone.data
            profile.bio = form.bio.data
        elif user.role == 'instructor':
            if not user.instructor_profile:
                profile = InstructorProfile(user_id=user.id)
                db.session.add(profile)
            else:
                profile = user.instructor_profile
            profile.name = form.name.data
            profile.phone = form.phone.data
            profile.bio = form.bio.data
        
        db.session.commit()
        flash('User updated successfully!', 'success')
        return redirect(url_for('admin.users'))
    
    return render_template('admin/edit_user.html', form=form, user=user)

# Delete User
@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('admin.users'))
    
    # Delete associated profiles
    if user.student_profile:
        db.session.delete(user.student_profile)
    if user.instructor_profile:
        db.session.delete(user.instructor_profile)
    
    # Delete user
    db.session.delete(user)
    db.session.commit()
    
    flash('User deleted successfully!', 'success')
    return redirect(url_for('admin.users'))

# Toggle User Status
@admin_bp.route('/users/<int:user_id>/toggle_status', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('You cannot deactivate your own account.', 'danger')
        return redirect(url_for('admin.users'))
    
    user.is_active = not user.is_active
    db.session.commit()
    
    status = 'activated' if user.is_active else 'deactivated'
    flash(f'User {status} successfully!', 'success')
    return redirect(url_for('admin.users'))

# Course Management
@admin_bp.route('/courses')
@login_required
@admin_required
def courses():
    instructor_filter = request.args.get('instructor', '')
    status_filter = request.args.get('status', '')
    search_filter = request.args.get('search', '')
    
    query = Course.query
    
    if instructor_filter:
        query = query.filter_by(instructor_id=instructor_filter)
    
    if status_filter:
        is_active = status_filter == 'active'
        query = query.filter_by(is_active=is_active)
    
    if search_filter:
        query = query.filter(Course.title.contains(search_filter) | Course.description.contains(search_filter))
    
    courses = query.order_by(Course.created_at.desc()).all()
    instructors = User.query.filter_by(role='instructor').all()
    
    return render_template('admin/courses.html', 
                         courses=courses, 
                         instructors=instructors,
                         instructor_filter=instructor_filter,
                         status_filter=status_filter)

# Create Course
@admin_bp.route('/courses/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_course():
    form = CreateCourseForm()
    
    # Populate instructor choices
    instructors = User.query.filter_by(role='instructor').all()
    form.instructor_id.choices = [(i.id, f"{i.instructor_profile.name if i.instructor_profile else 'No name'} ({i.email})") for i in instructors]
    
    if form.validate_on_submit():
        # Handle meeting days
        meeting_days = request.form.getlist('meeting_days')
        meeting_days_str = ','.join(meeting_days) if meeting_days else None
        
        course = Course(
            title=form.title.data,
            code=form.code.data,
            description=form.description.data,
            instructor_id=form.instructor_id.data,
            category=form.category.data,
            level=form.level.data,
            max_students=form.max_students.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            meeting_days=meeting_days_str,
            meeting_time=form.meeting_time.data,
            syllabus=form.syllabus.data,
            prerequisites=form.prerequisites.data,
            learning_outcomes=form.learning_outcomes.data,
            is_active=form.is_active.data,
            allow_enrollment=form.allow_enrollment.data,
            enable_quizzes=form.enable_quizzes.data,
            enable_assignments=form.enable_assignments.data
        )
        
        db.session.add(course)
        db.session.commit()
        
        flash('Course created successfully!', 'success')
        return redirect(url_for('admin.courses'))
    
    return render_template('admin/create_course.html', form=form, instructors=instructors)

# Edit Course
@admin_bp.route('/courses/<int:course_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_course(course_id):
    course = Course.query.get_or_404(course_id)
    form = EditCourseForm()
    
    # Populate instructor choices
    instructors = User.query.filter_by(role='instructor').all()
    form.instructor_id.choices = [(i.id, f"{i.instructor_profile.name if i.instructor_profile else 'No name'} ({i.email})") for i in instructors]
    
    if request.method == 'GET':
        # Pre-populate form with course data
        form.title.data = course.title
        form.code.data = course.code
        form.description.data = course.description
        form.instructor_id.data = course.instructor_id
        form.category.data = course.category
        form.level.data = course.level
        form.max_students.data = course.max_students
        form.start_date.data = course.start_date
        form.end_date.data = course.end_date
        form.meeting_time.data = course.meeting_time
        form.syllabus.data = course.syllabus
        form.prerequisites.data = course.prerequisites
        form.learning_outcomes.data = course.learning_outcomes
        form.is_active.data = course.is_active
        form.allow_enrollment.data = course.allow_enrollment
        form.enable_quizzes.data = course.enable_quizzes
        form.enable_assignments.data = course.enable_assignments
    
    if form.validate_on_submit():
        # Handle meeting days
        meeting_days = request.form.getlist('meeting_days')
        meeting_days_str = ','.join(meeting_days) if meeting_days else None
        
        course.title = form.title.data
        course.code = form.code.data
        course.description = form.description.data
        course.instructor_id = form.instructor_id.data
        course.category = form.category.data
        course.level = form.level.data
        course.max_students = form.max_students.data
        course.start_date = form.start_date.data
        course.end_date = form.end_date.data
        course.meeting_days = meeting_days_str
        course.meeting_time = form.meeting_time.data
        course.syllabus = form.syllabus.data
        course.prerequisites = form.prerequisites.data
        course.learning_outcomes = form.learning_outcomes.data
        course.is_active = form.is_active.data
        course.allow_enrollment = form.allow_enrollment.data
        course.enable_quizzes = form.enable_quizzes.data
        course.enable_assignments = form.enable_assignments.data
        
        db.session.commit()
        flash('Course updated successfully!', 'success')
        return redirect(url_for('admin.courses'))
    
    return render_template('admin/edit_course.html', form=form, course=course, instructors=instructors)

# View Course
@admin_bp.route('/courses/<int:course_id>')
@login_required
@admin_required
def view_course(course_id):
    course = Course.query.get_or_404(course_id)
    return render_template('admin/view_course.html', course=course)

# Delete Course
@admin_bp.route('/courses/<int:course_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_course(course_id):
    course = Course.query.get_or_404(course_id)
    
    # Delete course (cascade will handle related records)
    db.session.delete(course)
    db.session.commit()
    
    flash('Course deleted successfully!', 'success')
    return redirect(url_for('admin.courses'))

# Toggle Course Status
@admin_bp.route('/courses/<int:course_id>/toggle_status', methods=['POST'])
@login_required
@admin_required
def toggle_course_status(course_id):
    course = Course.query.get_or_404(course_id)
    
    course.is_active = not course.is_active
    db.session.commit()
    
    status = 'activated' if course.is_active else 'deactivated'
    flash(f'Course {status} successfully!', 'success')
    return redirect(url_for('admin.courses'))

# System Statistics API
@admin_bp.route('/api/stats')
@login_required
@admin_required
def api_stats():
    stats = {
        'total_students': User.query.filter_by(role='student').count(),
        'total_instructors': User.query.filter_by(role='instructor').count(),
        'total_courses': Course.query.count(),
        'total_enrollments': Enrollment.query.count(),
        'active_students': User.query.filter_by(role='student', is_active=True).count(),
        'active_instructors': User.query.filter_by(role='instructor', is_active=True).count(),
        'inactive_students': User.query.filter_by(role='student', is_active=False).count(),
        'inactive_instructors': User.query.filter_by(role='instructor', is_active=False).count()
    }
    return jsonify(stats)

# User Search API
@admin_bp.route('/api/users/search')
@login_required
@admin_required
def api_user_search():
    query = request.args.get('q', '')
    role = request.args.get('role', '')
    
    if not query:
        return jsonify([])
    
    search_query = User.query.filter(User.email.contains(query))
    
    if role:
        search_query = search_query.filter_by(role=role)
    
    users = search_query.limit(10).all()
    
    results = []
    for user in users:
        name = ''
        if user.role == 'student' and user.student_profile:
            name = user.student_profile.name
        elif user.role == 'instructor' and user.instructor_profile:
            name = user.instructor_profile.name
        
        results.append({
            'id': user.id,
            'email': user.email,
            'name': name,
            'role': user.role,
            'is_active': user.is_active,
            'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    
    return jsonify(results) 