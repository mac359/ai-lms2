from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_required, current_user
from models import User, Course, Enrollment, Assignment, Grade, Discussion, Announcement, Quiz, Outcome, Module, Attachment, Question, Meeting, Event, EmotionLog, QuizSubmission, QuizAnswer, AssignmentSubmission
from app import db
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, SelectField, FieldList, FormField, IntegerField, DateTimeField
from wtforms.validators import DataRequired
import os
from werkzeug.utils import secure_filename
import google.generativeai as genai
from services.gemini_service import GeminiService
import json
from datetime import datetime

instructor_bp = Blueprint('instructor', __name__, url_prefix='/instructor')

# Get the absolute path to the uploads directory
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'uploads')
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx', 'zip', 'rar'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@instructor_bp.route('/dashboard')
@login_required
def dashboard():
    # Fetch courses taught by the instructor
    courses = Course.query.filter_by(instructor_id=current_user.id).all()
    
    # Fetch announcements
    announcements = Announcement.query.join(Course).filter(Course.instructor_id == current_user.id).order_by(Announcement.created_at.desc()).limit(5).all()
    
    # Fetch assignments
    assignments = Assignment.query.join(Course).filter(Course.instructor_id == current_user.id).order_by(Assignment.due_date).limit(5).all()
    
    # Fetch grades
    grades = Grade.query.join(Assignment).join(Course).filter(Course.instructor_id == current_user.id).order_by(Grade.id.desc()).limit(5).all()
    
    # Fetch discussions
    discussions = Discussion.query.join(Course).filter(Course.instructor_id == current_user.id).order_by(Discussion.created_at.desc()).limit(5).all()
    
    return render_template('instructor_dashboard.html', 
                           courses=courses,
                           announcements=announcements,
                           assignments=assignments,
                           grades=grades,
                           discussions=discussions,
                           show_logout=True)

@instructor_bp.route('/courses')
@login_required
def courses():
    # Fetch courses taught by the instructor
    courses = Course.query.filter_by(instructor_id=current_user.id).all()
    return render_template('courses.html', courses=courses)

@instructor_bp.route('/calendar')
@login_required
def calendar():
    # Get all courses taught by the instructor
    instructor_courses = Course.query.filter_by(instructor_id=current_user.id).all()
    course_ids = [course.id for course in instructor_courses]
    
    # Fetch all events created by the instructor
    events = Event.query.filter_by(user_id=current_user.id).order_by(Event.event_date).all()
    
    # Fetch all meetings for instructor's courses
    meetings = Meeting.query.filter(Meeting.course_id.in_(course_ids)).order_by(Meeting.scheduled_time).all()
    
    # Fetch all assignments for instructor's courses
    assignments = Assignment.query.filter(Assignment.course_id.in_(course_ids)).order_by(Assignment.due_date).all()
    
    # Fetch all quizzes for instructor's courses
    quizzes = Quiz.query.filter(Quiz.course_id.in_(course_ids)).order_by(Quiz.start_time).all()
    
    # Combine all calendar items
    calendar_items = []
    
    # Add events
    for event in events:
        calendar_items.append({
            'id': event.id,
            'title': event.title,
            'description': event.description,
            'date': event.event_date,
            'type': 'event',
            'course_name': None,
            'color': 'primary'
        })
    
    # Add meetings
    for meeting in meetings:
        course = Course.query.get(meeting.course_id)
        calendar_items.append({
            'id': meeting.id,
            'title': meeting.title,
            'description': meeting.description,
            'date': meeting.scheduled_time,
            'type': 'meeting',
            'course_name': course.title if course else 'Unknown Course',
            'color': 'success',
            'meeting_link': meeting.meeting_link
        })
    
    # Add assignments
    for assignment in assignments:
        course = Course.query.get(assignment.course_id)
        calendar_items.append({
            'id': assignment.id,
            'title': f"Assignment: {assignment.title}",
            'description': assignment.instructions,
            'date': assignment.due_date,
            'type': 'assignment',
            'course_name': course.title if course else 'Unknown Course',
            'color': 'warning',
            'points': assignment.points
        })
    
    # Add quizzes
    for quiz in quizzes:
        course = Course.query.get(quiz.course_id)
        calendar_items.append({
            'id': quiz.id,
            'title': f"Quiz: {quiz.title}",
            'description': quiz.description,
            'date': quiz.start_time,
            'type': 'quiz',
            'course_name': course.title if course else 'Unknown Course',
            'color': 'info',
            'end_time': quiz.end_time,
            'time_limit': quiz.time_limit
        })
    
    # Sort all items by date
    calendar_items.sort(key=lambda x: x['date'])
    
    return render_template('calendar.html', 
                         calendar_items=calendar_items,
                         events=events,
                         meetings=meetings,
                         assignments=assignments,
                         quizzes=quizzes,
                         courses=instructor_courses)

@instructor_bp.route('/history')
@login_required
def history():
    return render_template('history.html')

@instructor_bp.route('/help')
@login_required
def help():
    return render_template('help.html')

@instructor_bp.route('/ai-chatbot')
@login_required
def ai_chatbot():
    return render_template('ai_chatbot.html')

@instructor_bp.route('/ai-chatbot', methods=['POST'])
@login_required
def ai_chatbot_api():
    from flask import current_app, request, jsonify
    data = request.get_json()
    message = data.get('message')
    if not message:
        return jsonify({'error': 'No message provided.'}), 400
    gemini = GeminiService(current_app.config['GEMINI_API_KEY'])
    ai_response = gemini.send_message(message)
    return jsonify({'response': ai_response})

@instructor_bp.route('/courses/delete/<int:course_id>', methods=['POST'])
@login_required
def delete_course(course_id):
    course = Course.query.filter_by(id=course_id, instructor_id=current_user.id).first()
    if not course:
        flash('Course not found or you do not have permission to delete this course.', 'danger')
        return redirect(url_for('instructor.courses'))
    db.session.delete(course)
    db.session.commit()
    flash('Course deleted successfully.', 'success')
    return redirect(url_for('instructor.courses'))

class CourseForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    submit = SubmitField('Create Course')

@instructor_bp.route('/courses/create', methods=['GET', 'POST'])
@login_required
def create_course():
    form = CourseForm()
    if form.validate_on_submit():
        course = Course(
            title=form.title.data,
            description=form.description.data,
            instructor_id=current_user.id
        )
        db.session.add(course)
        db.session.commit()
        flash('Course created successfully!', 'success')
        return redirect(url_for('instructor.courses'))
    return render_template('create_course.html', form=form)

@instructor_bp.route('/courses/<int:course_id>')
@login_required
def course_detail(course_id):
    course = Course.query.get_or_404(course_id)
    instructor = User.query.get(course.instructor_id)
    announcements = Announcement.query.filter_by(course_id=course_id).order_by(Announcement.created_at.desc()).all()
    assignments = Assignment.query.filter_by(course_id=course_id).order_by(Assignment.due_date).all()
    discussions = Discussion.query.filter_by(course_id=course_id).order_by(Discussion.created_at.desc()).all()
    grades = Grade.query.filter_by(course_id=course_id).all()
    quizzes = Quiz.query.filter_by(course_id=course_id).all()
    outcomes = Outcome.query.filter_by(course_id=course_id).all()
    modules = Module.query.filter_by(course_id=course_id).all()
    current_time = datetime.utcnow()
    return render_template('course_detail.html', course=course, instructor=instructor, announcements=announcements, assignments=assignments, discussions=discussions, grades=grades, quizzes=quizzes, outcomes=outcomes, modules=modules, current_time=current_time)

@instructor_bp.route('/courses/<int:course_id>/modules/create', methods=['GET', 'POST'])
@login_required
def create_module(course_id):
    course = Course.query.get_or_404(course_id)
    if course.instructor_id != current_user.id:
        flash('You do not have permission to create a module for this course.', 'danger')
        return redirect(url_for('instructor.courses'))
    form = ModuleForm()
    if form.validate_on_submit():
        module = Module(
            title=form.title.data,
            description=form.description.data,
            course_id=course_id
        )
        db.session.add(module)
        db.session.commit()
        flash('Module created successfully!', 'success')
        return redirect(url_for('instructor.course_detail', course_id=course_id))
    return render_template('create_module.html', form=form, course=course)

@instructor_bp.route('/courses/<int:course_id>/upload', methods=['POST'])
@login_required
def upload_attachment(course_id):
    course = Course.query.get_or_404(course_id)
    if course.instructor_id != current_user.id:
        flash('You do not have permission to upload attachments for this course.', 'danger')
        return redirect(url_for('instructor.course_detail', course_id=course_id))
    if 'file' not in request.files:
        flash('No file part', 'danger')
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(UPLOAD_FOLDER, filename))
        attachment = Attachment(filename=filename, course_id=course_id)
        db.session.add(attachment)
        db.session.commit()
        flash('File uploaded successfully', 'success')
    return redirect(url_for('instructor.course_detail', course_id=course_id))

@instructor_bp.route('/courses/<int:course_id>/upload_attachment_form', methods=['GET', 'POST'])
@login_required
def upload_attachment_form(course_id):
    course = Course.query.get_or_404(course_id)
    if course.instructor_id != current_user.id:
        flash('You do not have permission to upload attachments for this course.', 'danger')
        return redirect(url_for('instructor.courses'))
    
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            try:
                # Create uploads directory if it doesn't exist
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                
                # Secure the filename and save the file
                filename = secure_filename(file.filename)
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                file.save(file_path)
                
                # Create attachment record in database
                attachment = Attachment(
                    filename=filename,
                    file_path=file_path,
                    course_id=course_id
                )
                db.session.add(attachment)
                db.session.commit()
                
                flash('File uploaded successfully', 'success')
                return redirect(url_for('instructor.manage_course', course_id=course_id))
            except Exception as e:
                flash(f'Error uploading file: {str(e)}', 'danger')
                return redirect(request.url)
        else:
            flash('File type not allowed', 'danger')
            return redirect(request.url)
    
    return render_template('upload_attachment.html', course=course)

class QuizForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField('Description')
    time_limit = IntegerField('Time Limit (minutes)', validators=[DataRequired()])
    start_time = StringField('Start Time', validators=[DataRequired()])
    end_time = StringField('End Time', validators=[DataRequired()])
    submit = SubmitField('Create Quiz')

@instructor_bp.route('/courses/<int:course_id>/create_quiz', methods=['GET', 'POST'])
@login_required
def create_quiz(course_id):
    course = Course.query.get_or_404(course_id)
    if course.instructor_id != current_user.id:
        flash('You do not have permission to create quizzes for this course.', 'danger')
        return redirect(url_for('instructor.courses'))
    
    form = QuizForm()
    if form.validate_on_submit():
        try:
            # Convert string datetime to datetime object
            start_time = datetime.strptime(form.start_time.data, '%Y-%m-%dT%H:%M')
            end_time = datetime.strptime(form.end_time.data, '%Y-%m-%dT%H:%M')
            
            quiz = Quiz(
                title=form.title.data,
                description=form.description.data,
                course_id=course_id,
                time_limit=form.time_limit.data,
                start_time=start_time,
                end_time=end_time
            )
            db.session.add(quiz)
            db.session.commit()
            flash('Quiz created successfully!', 'success')
            return redirect(url_for('instructor.manage_course', course_id=course_id))
        except ValueError as e:
            flash('Invalid date/time format. Please use the datetime picker.', 'danger')
            return render_template('create_quiz.html', form=form, course=course)
    
    return render_template('create_quiz.html', form=form, course=course)

@instructor_bp.route('/courses/<int:course_id>/manage')
@login_required
def manage_course(course_id):
    course = Course.query.get_or_404(course_id)
    if course.instructor_id != current_user.id:
        flash('You do not have permission to manage this course.', 'danger')
        return redirect(url_for('instructor.courses'))
    instructor = User.query.get(course.instructor_id)
    modules = Module.query.filter_by(course_id=course_id).all()
    quizzes = Quiz.query.filter_by(course_id=course_id).all()
    assignments = Assignment.query.filter_by(course_id=course_id).all()
    announcements = Announcement.query.filter_by(course_id=course_id).all()
    attachments = Attachment.query.filter_by(course_id=course_id).all()
    meetings = Meeting.query.filter_by(course_id=course_id).all()
    return render_template('manage_course.html', course=course, instructor=instructor, modules=modules, quizzes=quizzes, assignments=assignments, announcements=announcements, attachments=attachments, meetings=meetings)

class MeetingForm(FlaskForm):
    title = StringField('Meeting Title', validators=[DataRequired()])
    description = TextAreaField('Description')
    scheduled_time = StringField('Scheduled Time (YYYY-MM-DD HH:MM)', validators=[DataRequired()])
    meeting_link = StringField('Meeting Link', validators=[DataRequired()])
    submit = SubmitField('Create Meeting')

@instructor_bp.route('/courses/<int:course_id>/create_meeting', methods=['GET', 'POST'])
@login_required
def create_meeting(course_id):
    course = Course.query.get_or_404(course_id)
    form = MeetingForm()
    if form.validate_on_submit():
        try:
            scheduled_time = datetime.strptime(form.scheduled_time.data, '%Y-%m-%d %H:%M')
        except ValueError:
            flash('Invalid date/time format. Use YYYY-MM-DD HH:MM', 'danger')
            return render_template('create_meeting.html', form=form, course=course)
        meeting = Meeting(
            course_id=course.id,
            title=form.title.data,
            description=form.description.data,
            scheduled_time=scheduled_time,
            meeting_link=form.meeting_link.data
        )
        db.session.add(meeting)
        db.session.commit()
        flash('Meeting created successfully!', 'success')
        return redirect(url_for('instructor.manage_course', course_id=course.id))
    return render_template('create_meeting.html', form=form, course=course)

class ModuleForm(FlaskForm):
    title = StringField('Module Title', validators=[DataRequired()])
    description = TextAreaField('Description')
    submit = SubmitField('Create Module')

class EventForm(FlaskForm):
    title = StringField('Event Title', validators=[DataRequired()])
    description = TextAreaField('Description')
    event_date = StringField('Event Date (YYYY-MM-DD HH:MM)', validators=[DataRequired()])
    submit = SubmitField('Create Event')

@instructor_bp.route('/events/create', methods=['GET', 'POST'])
@login_required
def create_event():
    form = EventForm()
    if form.validate_on_submit():
        try:
            event_date = datetime.strptime(form.event_date.data, '%Y-%m-%d %H:%M')
        except ValueError:
            flash('Invalid date/time format. Use YYYY-MM-DD HH:MM', 'danger')
            return render_template('create_event.html', form=form)
        event = Event(
            title=form.title.data,
            description=form.description.data,
            event_date=event_date,
            user_id=current_user.id
        )
        db.session.add(event)
        db.session.commit()
        flash('Event created successfully!', 'success')
        return redirect(url_for('instructor.calendar'))
    return render_template('create_event.html', form=form)

@instructor_bp.route('/events/delete/<int:event_id>', methods=['POST'])
@login_required
def delete_event(event_id):
    event = Event.query.filter_by(id=event_id, user_id=current_user.id).first_or_404()
    db.session.delete(event)
    db.session.commit()
    flash('Event deleted successfully.', 'success')
    return redirect(url_for('instructor.calendar'))

class QuestionForm(FlaskForm):
    question_text = StringField('Question', validators=[DataRequired()])
    option1 = StringField('Option 1', validators=[DataRequired()])
    option2 = StringField('Option 2', validators=[DataRequired()])
    option3 = StringField('Option 3')
    option4 = StringField('Option 4')
    correct_answer = StringField('Correct Answer', validators=[DataRequired()])
    difficulty = SelectField('Difficulty', choices=[('Easy', 'Easy'), ('Medium', 'Medium'), ('Hard', 'Hard')], validators=[DataRequired()])
    submit = SubmitField('Save Question')

@instructor_bp.route('/courses/<int:course_id>/quiz/<int:quiz_id>/manage', methods=['GET'])
@login_required
def manage_quiz(course_id, quiz_id):
    # Check if instructor owns the course
    course = Course.query.filter_by(id=course_id, instructor_id=current_user.id).first_or_404()
    quiz = Quiz.query.filter_by(id=quiz_id, course_id=course_id).first_or_404()
    questions = Question.query.filter_by(quiz_id=quiz.id).all()
    return render_template('manage_quiz.html', course=course, quiz=quiz, questions=questions)

@instructor_bp.route('/courses/<int:course_id>/quiz/<int:quiz_id>/add_question', methods=['GET', 'POST'])
@login_required
def add_question(course_id, quiz_id):
    # Check if instructor owns the course
    course = Course.query.filter_by(id=course_id, instructor_id=current_user.id).first_or_404()
    quiz = Quiz.query.filter_by(id=quiz_id, course_id=course_id).first_or_404()
    form = QuestionForm()
    if form.validate_on_submit():
        options = [form.option1.data, form.option2.data]
        if form.option3.data:
            options.append(form.option3.data)
        if form.option4.data:
            options.append(form.option4.data)
        question = Question(
            quiz_id=quiz.id,
            question_text=form.question_text.data,
            options=json.dumps(options),
            correct_answer=form.correct_answer.data,
            difficulty=form.difficulty.data
        )
        db.session.add(question)
        db.session.commit()
        flash('Question added!', 'success')
        return redirect(url_for('instructor.manage_quiz', course_id=course_id, quiz_id=quiz.id))
    return render_template('add_edit_question.html', form=form, course=course, quiz=quiz, action='Add')

@instructor_bp.route('/courses/<int:course_id>/quiz/<int:quiz_id>/edit_question/<int:question_id>', methods=['GET', 'POST'])
@login_required
def edit_question(course_id, quiz_id, question_id):
    # Check if instructor owns the course
    course = Course.query.filter_by(id=course_id, instructor_id=current_user.id).first_or_404()
    quiz = Quiz.query.filter_by(id=quiz_id, course_id=course_id).first_or_404()
    question = Question.query.get_or_404(question_id)
    form = QuestionForm(obj=question)
    if request.method == 'GET':
        opts = json.loads(question.options) if question.options else []
        if len(opts) > 0:
            form.option1.data = opts[0]
        if len(opts) > 1:
            form.option2.data = opts[1]
        if len(opts) > 2:
            form.option3.data = opts[2]
        if len(opts) > 3:
            form.option4.data = opts[3]
    if form.validate_on_submit():
        options = [form.option1.data, form.option2.data]
        if form.option3.data:
            options.append(form.option3.data)
        if form.option4.data:
            options.append(form.option4.data)
        question.question_text = form.question_text.data
        question.options = json.dumps(options)
        question.correct_answer = form.correct_answer.data
        question.difficulty = form.difficulty.data
        db.session.commit()
        flash('Question updated!', 'success')
        return redirect(url_for('instructor.manage_quiz', course_id=course_id, quiz_id=quiz.id))
    return render_template('add_edit_question.html', form=form, course=course, quiz=quiz, action='Edit')

@instructor_bp.route('/courses/<int:course_id>/quiz/<int:quiz_id>/delete_question/<int:question_id>', methods=['POST'])
@login_required
def delete_question(course_id, quiz_id, question_id):
    # Check if instructor owns the course
    course = Course.query.filter_by(id=course_id, instructor_id=current_user.id).first_or_404()
    quiz = Quiz.query.filter_by(id=quiz_id, course_id=course_id).first_or_404()
    question = Question.query.get_or_404(question_id)
    db.session.delete(question)
    db.session.commit()
    flash('Question deleted.', 'info')
    return redirect(url_for('instructor.manage_quiz', course_id=course_id, quiz_id=quiz_id))

@instructor_bp.route('/courses/<int:course_id>/delete_module/<int:module_id>', methods=['POST'])
@login_required
def delete_module(course_id, module_id):
    module = Module.query.get_or_404(module_id)
    db.session.delete(module)
    db.session.commit()
    flash('Module deleted.', 'info')
    return redirect(url_for('instructor.manage_course', course_id=course_id))

@instructor_bp.route('/courses/<int:course_id>/delete_quiz/<int:quiz_id>', methods=['POST'])
@login_required
def delete_quiz(course_id, quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # First, delete all quiz answers for this quiz's submissions
    quiz_submissions = QuizSubmission.query.filter_by(quiz_id=quiz_id).all()
    for submission in quiz_submissions:
        # Delete all answers for this submission
        QuizAnswer.query.filter_by(submission_id=submission.id).delete()
        # Delete the submission
        db.session.delete(submission)
    
    # Now delete the quiz (questions will be deleted automatically due to cascade)
    db.session.delete(quiz)
    db.session.commit()
    flash('Quiz deleted.', 'info')
    return redirect(url_for('instructor.manage_course', course_id=course_id))

@instructor_bp.route('/courses/<int:course_id>/delete_assignment/<int:assignment_id>', methods=['POST'])
@login_required
def delete_assignment(course_id, assignment_id):
    assignment = Assignment.query.get_or_404(assignment_id)
    db.session.delete(assignment)
    db.session.commit()
    flash('Assignment deleted.', 'info')
    return redirect(url_for('instructor.manage_course', course_id=course_id))

@instructor_bp.route('/courses/<int:course_id>/delete_announcement/<int:announcement_id>', methods=['POST'])
@login_required
def delete_announcement(course_id, announcement_id):
    announcement = Announcement.query.get_or_404(announcement_id)
    db.session.delete(announcement)
    db.session.commit()
    flash('Announcement deleted.', 'info')
    return redirect(url_for('instructor.manage_course', course_id=course_id))

@instructor_bp.route('/courses/<int:course_id>/delete_attachment/<int:attachment_id>', methods=['POST'])
@login_required
def delete_attachment(course_id, attachment_id):
    attachment = Attachment.query.get_or_404(attachment_id)
    db.session.delete(attachment)
    db.session.commit()
    flash('Attachment deleted.', 'info')
    return redirect(url_for('instructor.manage_course', course_id=course_id))

@instructor_bp.route('/courses/<int:course_id>/delete_meeting/<int:meeting_id>', methods=['POST'])
@login_required
def delete_meeting(course_id, meeting_id):
    meeting = Meeting.query.get_or_404(meeting_id)
    db.session.delete(meeting)
    db.session.commit()
    flash('Meeting deleted.', 'info')
    return redirect(url_for('instructor.manage_course', course_id=course_id))

class AssignmentForm(FlaskForm):
    title = StringField('Assignment Title', validators=[DataRequired()])
    instructions = TextAreaField('Instructions', validators=[DataRequired()])
    due_date = StringField('Due Date and Time', validators=[DataRequired()])
    points = StringField('Points', validators=[DataRequired()])
    submit = SubmitField('Create Assignment')

@instructor_bp.route('/courses/<int:course_id>/create_assignment', methods=['GET', 'POST'])
@login_required
def create_assignment(course_id):
    course = Course.query.get_or_404(course_id)
    if course.instructor_id != current_user.id:
        flash('You do not have permission to create assignments for this course.', 'error')
        return redirect(url_for('instructor.dashboard'))
    
    form = AssignmentForm()
    if form.validate_on_submit():
        try:
            due_date = datetime.strptime(form.due_date.data, '%Y-%m-%dT%H:%M')
            assignment = Assignment(
                title=form.title.data,
                instructions=form.instructions.data,
                due_date=due_date,
                course_id=course.id,
                points=form.points.data
            )
            db.session.add(assignment)
            db.session.commit()
            flash('Assignment created successfully!', 'success')
            return redirect(url_for('instructor.manage_course', course_id=course.id))
        except ValueError:
            flash('Invalid date format. Please use the date and time picker.', 'error')
    
    return render_template('create_assignment.html', form=form, course=course)

class AnnouncementForm(FlaskForm):
    title = StringField('Announcement Title', validators=[DataRequired()])
    message = TextAreaField('Message', validators=[DataRequired()])
    submit = SubmitField('Create Announcement')

@instructor_bp.route('/courses/<int:course_id>/create_announcement', methods=['GET', 'POST'])
@login_required
def create_announcement(course_id):
    course = Course.query.get_or_404(course_id)
    if course.instructor_id != current_user.id:
        flash('You do not have permission to create an announcement for this course.', 'danger')
        return redirect(url_for('instructor.courses'))
    form = AnnouncementForm()
    if form.validate_on_submit():
        announcement = Announcement(
            title=form.title.data,
            message=form.message.data,
            course_id=course_id
        )
        db.session.add(announcement)
        db.session.commit()
        flash('Announcement created successfully!', 'success')
        return redirect(url_for('instructor.manage_course', course_id=course_id))
    return render_template('create_announcement.html', form=form, course=course) 

@instructor_bp.route('/courses/<int:course_id>/quiz/<int:quiz_id>/results')
@login_required
def quiz_results(course_id, quiz_id):
    # Check if instructor owns the course
    course = Course.query.filter_by(id=course_id, instructor_id=current_user.id).first_or_404()
    quiz = Quiz.query.filter_by(id=quiz_id, course_id=course_id).first_or_404()
    
    # Get all submissions for this quiz
    submissions = QuizSubmission.query.filter_by(quiz_id=quiz_id).all()
    
    # Calculate statistics
    total_submissions = len(submissions)
    if total_submissions > 0:
        avg_score = sum(sub.score for sub in submissions) / total_submissions
        highest_score = max(sub.score for sub in submissions)
        lowest_score = min(sub.score for sub in submissions)
    else:
        avg_score = highest_score = lowest_score = 0
    
    # Get behavior statistics
    behavior_stats = []
    for submission in submissions:
        student = submission.student
        
        # Get behavior data during quiz
        behavior_logs = EmotionLog.query.filter(
            EmotionLog.student_id == student.id,
            EmotionLog.timestamp >= submission.start_time,
            EmotionLog.timestamp <= submission.end_time
        ).all()
        
        avg_focus = 0
        avg_frustration = 0
        
        if behavior_logs:
            avg_focus = sum(log.focus_score for log in behavior_logs) / len(behavior_logs)
            avg_frustration = sum(log.frustration_score for log in behavior_logs) / len(behavior_logs)
        
        # Calculate difficulty breakdown
        easy_questions = [answer for answer in submission.answers if answer.question.difficulty == 'Easy']
        medium_questions = [answer for answer in submission.answers if answer.question.difficulty == 'Medium']
        hard_questions = [answer for answer in submission.answers if answer.question.difficulty == 'Hard']
        
        easy_correct = sum(1 for answer in easy_questions if answer.is_correct)
        medium_correct = sum(1 for answer in medium_questions if answer.is_correct)
        hard_correct = sum(1 for answer in hard_questions if answer.is_correct)
        
        # Calculate time taken
        time_taken = submission.end_time - submission.start_time
        time_taken_minutes = round(time_taken.total_seconds() / 60, 1)
        
        behavior_stats.append({
            'student': student,
            'submission': submission,
            'avg_focus_percent': round(avg_focus * 100, 1),
            'avg_frustration_percent': round(avg_frustration * 100, 1),
            'easy_questions_count': len(easy_questions),
            'medium_questions_count': len(medium_questions),
            'hard_questions_count': len(hard_questions),
            'easy_correct_count': easy_correct,
            'medium_correct_count': medium_correct,
            'hard_correct_count': hard_correct,
            'time_taken_minutes': time_taken_minutes,
            'total_questions': len(submission.answers),
            'correct_answers_count': sum(1 for answer in submission.answers if answer.is_correct)
        })
    
    # Sort by score (highest first)
    behavior_stats.sort(key=lambda x: x['submission'].score, reverse=True)
    
    return render_template('instructor/quiz_results.html',
                         course=course,
                         quiz=quiz,
                         behavior_stats=behavior_stats,
                         total_submissions=total_submissions,
                         avg_score=round(avg_score, 1),
                         highest_score=round(highest_score, 1),
                         lowest_score=round(lowest_score, 1))

@instructor_bp.route('/courses/<int:course_id>/quiz/<int:quiz_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_quiz(course_id, quiz_id):
    # Check if instructor owns the course
    course = Course.query.filter_by(id=course_id, instructor_id=current_user.id).first_or_404()
    quiz = Quiz.query.filter_by(id=quiz_id, course_id=course_id).first_or_404()
    
    form = QuizForm(obj=quiz)
    if form.validate_on_submit():
        try:
            start_time = datetime.strptime(form.start_time.data, '%Y-%m-%dT%H:%M')
            end_time = datetime.strptime(form.end_time.data, '%Y-%m-%dT%H:%M')
            
            quiz.title = form.title.data
            quiz.description = form.description.data
            quiz.time_limit = form.time_limit.data
            quiz.start_time = start_time
            quiz.end_time = end_time
            
            db.session.commit()
            flash('Quiz updated successfully!', 'success')
            return redirect(url_for('instructor.manage_quiz', course_id=course_id, quiz_id=quiz.id))
        except ValueError:
            flash('Invalid date format. Please use the date and time picker.', 'error')
    
    # Pre-populate datetime fields
    if request.method == 'GET':
        if quiz.start_time:
            form.start_time.data = quiz.start_time.strftime('%Y-%m-%dT%H:%M')
        if quiz.end_time:
            form.end_time.data = quiz.end_time.strftime('%Y-%m-%dT%H:%M')
    
    return render_template('create_quiz.html', form=form, course=course, quiz=quiz, action='Edit')

@instructor_bp.route('/courses/<int:course_id>/assignment/<int:assignment_id>/grade/<int:submission_id>', methods=['POST'])
@login_required
def grade_assignment(course_id, assignment_id, submission_id):
    # Only instructors can grade
    if current_user.role != 'instructor':
        flash('Only instructors can grade assignments.', 'danger')
        return redirect(url_for('instructor.manage_course', course_id=course_id))
    submission = AssignmentSubmission.query.get_or_404(submission_id)
    grade = request.form.get('grade')
    feedback = request.form.get('feedback')
    try:
        submission.grade = float(grade)
    except (TypeError, ValueError):
        submission.grade = None
    submission.feedback = feedback
    db.session.commit()
    flash('Grade and feedback saved.', 'success')
    return redirect(url_for('instructor.manage_course', course_id=course_id))

@instructor_bp.route('/courses/<int:course_id>/assignment/<int:assignment_id>/submissions')
@login_required
def view_assignment_submissions(course_id, assignment_id):
    if current_user.role != 'instructor':
        flash('Only instructors can view assignment submissions.', 'danger')
        return redirect(url_for('instructor.manage_course', course_id=course_id))
    assignment = Assignment.query.get_or_404(assignment_id)
    submissions = assignment.submissions
    course = Course.query.get_or_404(course_id)
    return render_template('instructor/view_assignment_submissions.html', assignment=assignment, submissions=submissions, course=course) 