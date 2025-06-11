from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    login_count = db.Column(db.Integer, default=0)
    student_profile = db.relationship('StudentProfile', backref='user', uselist=False)
    instructor_profile = db.relationship('InstructorProfile', backref='user', uselist=False)

class StudentProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    bio = db.Column(db.Text)
    student_id = db.Column(db.String(50))
    grade_level = db.Column(db.String(50))
    parent_email = db.Column(db.String(120))
    parent_phone = db.Column(db.String(20))
    subject_interests = db.Column(db.String(200))
    learning_style = db.Column(db.String(100))
    support_needs = db.Column(db.String(200))
    goal = db.Column(db.String(200))

class InstructorProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    bio = db.Column(db.Text)
    department = db.Column(db.String(100))
    office_location = db.Column(db.String(100))
    office_hours = db.Column(db.String(100))
    specialization = db.Column(db.String(200))
    area_of_expertise = db.Column(db.String(100))
    teaching_style = db.Column(db.String(100))
    years_of_experience = db.Column(db.Integer)
    subjects_taught = db.Column(db.String(200))
    student_feedback_summary = db.Column(db.Text)

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20))
    description = db.Column(db.Text)
    instructor_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    category = db.Column(db.String(50))
    level = db.Column(db.String(20))
    max_students = db.Column(db.Integer, default=50)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    meeting_days = db.Column(db.String(100))
    meeting_time = db.Column(db.Time)
    syllabus = db.Column(db.Text)
    prerequisites = db.Column(db.Text)
    learning_outcomes = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    allow_enrollment = db.Column(db.Boolean, default=True)
    enable_quizzes = db.Column(db.Boolean, default=True)
    enable_assignments = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    instructor = db.relationship('User', backref='courses', foreign_keys=[instructor_id])
    students = db.relationship('User', secondary='enrollment', backref='enrolled_courses')
    lessons = db.relationship('Lesson', backref='course', lazy=True)
    enrollments = db.relationship('Enrollment', backref='course', lazy=True)
    announcements = db.relationship('Announcement', backref='course', lazy=True)
    assignments = db.relationship('Assignment', backref='course', lazy=True)
    discussions = db.relationship('Discussion', backref='course', lazy=True)
    assessments = db.relationship('Assessment', backref='course', lazy=True)
    outcomes = db.relationship('Outcome', backref='course', lazy=True)
    quizzes = db.relationship('Quiz', backref='course', lazy=True)
    modules = db.relationship('Module', backref='course', lazy=True)
    attachments = db.relationship('Attachment', backref='course', lazy=True)
    meetings = db.relationship('Meeting', backref='course', lazy=True)
    materials = db.relationship('Material', backref='course', lazy=True)

class Lesson(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    title = db.Column(db.String(100))
    content = db.Column(db.Text)
    video_url = db.Column(db.String(200))
    order = db.Column(db.Integer)

class Enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    enrollment_date = db.Column(db.DateTime, default=datetime.utcnow)
    student = db.relationship('User', backref='enrollments', foreign_keys=[student_id])
    latest_focus_score = db.Column(db.Float, nullable=True)
    frustration_level = db.Column(db.Float, nullable=True)
    last_updated = db.Column(db.DateTime, nullable=True)
    is_monitoring = db.Column(db.Boolean, default=False)

class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    title = db.Column(db.String(100))
    message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    title = db.Column(db.String(100))
    instructions = db.Column(db.Text)
    due_date = db.Column(db.DateTime)
    file_upload = db.Column(db.String(200))
    points = db.Column(db.String(10))
    is_active = db.Column(db.Boolean, default=True)
    submissions = db.relationship('AssignmentSubmission', backref='assignment', lazy=True)
    grades = db.relationship('Grade', backref='assignment', lazy=True)

class AssignmentSubmission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id'))
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    file_path = db.Column(db.String(500))
    comments = db.Column(db.Text)
    grade = db.Column(db.Float, nullable=True)
    feedback = db.Column(db.Text)

class Discussion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    title = db.Column(db.String(100))
    thread = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    replies = db.relationship('DiscussionReply', backref='discussion', lazy=True)

class DiscussionReply(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    discussion_id = db.Column(db.Integer, db.ForeignKey('discussion.id'))
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    message = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Assessment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    title = db.Column(db.String(100))
    type = db.Column(db.String(20))  # MCQ/Text
    due_date = db.Column(db.DateTime)
    questions = db.relationship('Question', backref='assessment', lazy=True)
    submissions = db.relationship('Submission', backref='assessment', lazy=True)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey('assessment.id'), nullable=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id', ondelete='CASCADE'), nullable=False)
    question_text = db.Column(db.Text)
    options = db.Column(db.Text)  # JSON string
    correct_answer = db.Column(db.String(200))
    difficulty = db.Column(db.String(20))  # e.g., 'Easy', 'Medium', 'Hard'

class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(db.Integer, db.ForeignKey('assessment.id'))
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    answers = db.Column(db.Text)  # JSON string
    score = db.Column(db.Float)

class Grade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id'))
    grade_value = db.Column(db.String(10))
    feedback = db.Column(db.Text)

class Outcome(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    title = db.Column(db.String(100))
    description = db.Column(db.Text)
    achieved_by = db.Column(db.Text)  # JSON list of student IDs

class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    time_limit = db.Column(db.Integer, nullable=True)  # Time limit in minutes
    duration = db.Column(db.Integer, nullable=True)    # Duration in minutes
    start_time = db.Column(db.DateTime, nullable=True) # When the quiz becomes available
    end_time = db.Column(db.DateTime, nullable=True)   # When the quiz expires
    is_active = db.Column(db.Boolean, default=True)
    submissions = db.relationship('QuizSubmission', backref='quiz', lazy=True)
    questions = db.relationship('Question', backref='quiz', lazy=True, cascade='all, delete-orphan')

class Module(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)

class Material(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    title = db.Column(db.String(100))
    description = db.Column(db.Text)
    file_path = db.Column(db.String(500))
    file_type = db.Column(db.String(50))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

class Attachment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    filename = db.Column(db.String(200))
    file_path = db.Column(db.String(500))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

class Meeting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    scheduled_time = db.Column(db.DateTime, nullable=False)
    meeting_link = db.Column(db.String(255))

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    event_date = db.Column(db.DateTime, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class QuizSubmission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id', ondelete='CASCADE'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)
    score = db.Column(db.Float, nullable=True)
    answers = db.relationship('QuizAnswer', backref='submission', lazy=True)
    student = db.relationship('User', backref='quiz_submissions')

class QuizAnswer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey('quiz_submission.id', ondelete='CASCADE'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    answer = db.Column(db.Text, nullable=False)
    is_correct = db.Column(db.Boolean, nullable=True)
    question = db.relationship('Question', backref='answers')

class EmotionLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    focus_score = db.Column(db.Float)
    frustration_score = db.Column(db.Float)
    source_data_summary = db.Column(db.Text) 