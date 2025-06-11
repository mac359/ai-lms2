from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from models import User, Course, Enrollment, Assignment, Grade, Discussion, Announcement, Meeting, InstructorProfile, StudentProfile, Quiz, Question, QuizSubmission, Module, Attachment, QuizAnswer, EmotionLog, Event, AssignmentSubmission
from app import db
from services.gemini_service import GeminiService
from datetime import datetime, timedelta
from student_behavior_monitor import StudentBehaviorMonitor
import threading
import time
import json
from threading import Thread

student_bp = Blueprint('student', __name__, url_prefix='/student')

@student_bp.route('/dashboard')
@login_required
def dashboard():
    # Fetch enrolled courses
    enrollments = Enrollment.query.filter_by(student_id=current_user.id).all()
    enrolled_courses = [enrollment.course for enrollment in enrollments]
    
    # Fetch announcements
    announcements = Announcement.query.order_by(Announcement.created_at.desc()).limit(5).all()
    
    # Fetch assignments
    assignments = Assignment.query.join(Course).join(Enrollment).filter(Enrollment.student_id == current_user.id).order_by(Assignment.due_date).limit(5).all()
    
    # Fetch grades
    grades = Grade.query.select_from(Grade).join(Assignment, Grade.assignment_id == Assignment.id).join(Course, Assignment.course_id == Course.id).join(Enrollment, Course.id == Enrollment.course_id).filter(Enrollment.student_id == current_user.id).order_by(Grade.id.desc()).limit(5).all()
    
    # Fetch discussions
    discussions = Discussion.query.join(Course).join(Enrollment).filter(Enrollment.student_id == current_user.id).order_by(Discussion.created_at.desc()).limit(5).all()

    # Fetch upcoming events (next 5, from calendar logic)
    enrolled_course_ids = [enrollment.course_id for enrollment in enrollments]
    assignments_all = Assignment.query.filter(Assignment.course_id.in_(enrolled_course_ids)).all()
    quizzes = Quiz.query.filter(Quiz.course_id.in_(enrolled_course_ids)).all()
    meetings = Meeting.query.filter(Meeting.course_id.in_(enrolled_course_ids)).all()
    events = Event.query.all()  # Global events
    calendar_items = []
    for assignment in assignments_all:
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
    calendar_items.sort(key=lambda x: x['date'])
    current_date = datetime.utcnow()
    upcoming_events = [item for item in calendar_items if item['date'] >= current_date][:5]
    
    return render_template('student_dashboard.html', 
                           enrolled_courses=enrolled_courses,
                           announcements=announcements,
                           assignments=assignments,
                           grades=grades,
                           discussions=discussions,
                           upcoming_events=upcoming_events,
                           show_logout=True)

@student_bp.route('/courses', methods=['GET', 'POST'])
@login_required
def courses():
    all_courses = Course.query.all()
    if request.method == 'POST':
        course_id = request.form.get('course_id')
        if course_id:
            existing = Enrollment.query.filter_by(student_id=current_user.id, course_id=course_id).first()
            if not existing:
                enrollment = Enrollment(student_id=current_user.id, course_id=course_id)
                db.session.add(enrollment)
                db.session.commit()
                flash('Enrolled in course successfully!', 'success')
            else:
                flash('You are already enrolled in this course.', 'info')
        return redirect(url_for('student.courses'))
    # Get enrolled course ids for UI
    enrolled_course_ids = [e.course_id for e in Enrollment.query.filter_by(student_id=current_user.id).all()]
    return render_template('courses.html', courses=all_courses, enrolled_course_ids=enrolled_course_ids)

@student_bp.route('/courses/enroll/<int:course_id>', methods=['POST'])
@login_required
def enroll_course(course_id):
    existing = Enrollment.query.filter_by(student_id=current_user.id, course_id=course_id).first()
    if not existing:
        enrollment = Enrollment(student_id=current_user.id, course_id=course_id)
        db.session.add(enrollment)
        db.session.commit()
        flash('Enrolled in course successfully!', 'success')
    else:
        flash('You are already enrolled in this course.', 'info')
    return redirect(url_for('student.courses'))

@student_bp.route('/calendar')
@login_required
def calendar():
    # Get enrolled courses
    enrollments = Enrollment.query.filter_by(student_id=current_user.id).all()
    enrolled_course_ids = [enrollment.course_id for enrollment in enrollments]
    
    # Fetch all events for enrolled courses
    assignments = Assignment.query.filter(Assignment.course_id.in_(enrolled_course_ids)).all()
    quizzes = Quiz.query.filter(Quiz.course_id.in_(enrolled_course_ids)).all()
    meetings = Meeting.query.filter(Meeting.course_id.in_(enrolled_course_ids)).all()
    events = Event.query.all()  # Global events
    
    # Combine all calendar items
    calendar_items = []
    
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
    
    # Add global events
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
    
    # Sort all items by date
    calendar_items.sort(key=lambda x: x['date'])
    
    # Get upcoming events (next 30 days)
    current_date = datetime.utcnow()
    upcoming_date = current_date + timedelta(days=30)
    upcoming_events = [item for item in calendar_items if item['date'] <= upcoming_date and item['date'] >= current_date]
    
    # Get overdue assignments
    overdue_events = [item for item in calendar_items if item['type'] == 'assignment' and item['date'] < current_date]
    
    # Get courses for filtering
    courses = Course.query.filter(Course.id.in_(enrolled_course_ids)).all()
    
    return render_template('calendar.html', 
                         calendar_items=calendar_items,
                         events=events,
                         meetings=meetings,
                         assignments=assignments,
                         quizzes=quizzes,
                         courses=courses,
                         upcoming_events=upcoming_events,
                         overdue_events=overdue_events)

@student_bp.route('/history')
@login_required
def history():
    return render_template('history.html')

@student_bp.route('/help')
@login_required
def help():
    return render_template('help.html')

@student_bp.route('/ai-chatbot')
@login_required
def ai_chatbot():
    return render_template('ai_chatbot.html')

@student_bp.route('/ai-chatbot', methods=['POST'])
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

@student_bp.route('/courses/<int:course_id>')
@login_required
def course_detail(course_id):
    # Check if student is enrolled in the course
    enrollment = Enrollment.query.filter_by(student_id=current_user.id, course_id=course_id).first()
    if not enrollment:
        flash('You are not enrolled in this course.', 'danger')
        return redirect(url_for('student.courses'))
    
    # Get course details
    course = Course.query.get_or_404(course_id)
    instructor = User.query.get(course.instructor_id)
    
    # Get all course content
    modules = Module.query.filter_by(course_id=course_id).order_by(Module.id).all()
    quizzes = Quiz.query.filter_by(course_id=course_id).order_by(Quiz.id).all()
    assignments = Assignment.query.filter_by(course_id=course_id).order_by(Assignment.due_date).all()
    announcements = Announcement.query.filter_by(course_id=course_id).order_by(Announcement.created_at.desc()).all()
    attachments = Attachment.query.filter_by(course_id=course_id).order_by(Attachment.uploaded_at.desc()).all()
    meetings = Meeting.query.filter_by(course_id=course_id).order_by(Meeting.scheduled_time).all()
    
    # Get student's quiz submissions and scores
    quiz_submissions = QuizSubmission.query.filter_by(student_id=current_user.id).join(Quiz).filter(Quiz.course_id == course_id).all()
    quiz_scores = {sub.quiz_id: sub.score for sub in quiz_submissions if sub.score is not None}
    
    # Get student's assignment submissions
    assignment_submissions = AssignmentSubmission.query.join(Assignment).filter(
        AssignmentSubmission.student_id == current_user.id,
        Assignment.course_id == course_id
    ).all()
    assignment_grades = {sub.assignment_id: sub.grade for sub in assignment_submissions if sub.grade is not None}
    
    # Calculate course progress
    total_items = len(modules) + len(quizzes) + len(assignments)
    completed_items = 0
    
    # Count completed modules (assuming all modules are completed for now)
    completed_items += len(modules)
    
    # Count completed quizzes
    completed_quizzes = len([q for q in quizzes if q.id in quiz_scores])
    completed_items += completed_quizzes
    
    # Count completed assignments
    completed_assignments = len([a for a in assignments if a.id in assignment_grades])
    completed_items += completed_assignments
    
    course_progress = (completed_items / total_items * 100) if total_items > 0 else 0
    
    # Get upcoming deadlines
    current_time = datetime.utcnow()
    upcoming_deadlines = []
    
    for assignment in assignments:
        if assignment.due_date > current_time:
            upcoming_deadlines.append({
                'type': 'assignment',
                'title': assignment.title,
                'date': assignment.due_date,
                'color': 'warning'
            })
    
    for quiz in quizzes:
        if quiz.end_time and quiz.end_time > current_time:
            upcoming_deadlines.append({
                'type': 'quiz',
                'title': quiz.title,
                'date': quiz.end_time,
                'color': 'info'
            })
    
    # Sort upcoming deadlines by date
    upcoming_deadlines.sort(key=lambda x: x['date'])
    
    # Get overdue items
    overdue_items = []
    for assignment in assignments:
        if assignment.due_date < current_time and assignment.id not in assignment_grades:
            overdue_items.append({
                'type': 'assignment',
                'title': assignment.title,
                'date': assignment.due_date
            })
    
    # Get recent activity
    recent_activity = []
    
    # Add recent quiz submissions
    for submission in quiz_submissions[:5]:
        recent_activity.append({
            'type': 'quiz',
            'title': submission.quiz.title,
            'date': submission.end_time or submission.start_time,
            'score': submission.score
        })
    
    # Add recent assignment submissions
    for submission in assignment_submissions[:5]:
        recent_activity.append({
            'type': 'assignment',
            'title': submission.assignment.title,
            'date': submission.submitted_at,
            'grade': submission.grade
        })
    
    # Sort recent activity by date
    recent_activity.sort(key=lambda x: x['date'], reverse=True)
    
    # Get course statistics
    course_stats = {
        'total_students': len(course.students) if course.students else 0,
        'total_quizzes': len(quizzes),
        'total_assignments': len(assignments),
        'total_modules': len(modules),
        'total_resources': len(attachments),
        'total_meetings': len(meetings),
        'completed_quizzes': completed_quizzes,
        'completed_assignments': completed_assignments,
        'overdue_assignments': len(overdue_items),
        'upcoming_deadlines': len(upcoming_deadlines[:5])
    }
    
    # Get instructor profile information
    instructor_info = None
    if instructor and instructor.instructor_profile:
        instructor_info = {
            'name': instructor.instructor_profile.name,
            'department': instructor.instructor_profile.department,
            'bio': instructor.instructor_profile.bio,
            'office_location': instructor.instructor_profile.office_location,
            'office_hours': instructor.instructor_profile.office_hours,
            'specialization': instructor.instructor_profile.specialization
        }
    
    return render_template('student_course_detail.html',
                         course=course,
                         instructor=instructor,
                         instructor_info=instructor_info,
                         modules=modules,
                         quizzes=quizzes,
                         assignments=assignments,
                         announcements=announcements,
                         attachments=attachments,
                         meetings=meetings,
                         current_time=current_time,
                         quiz_scores=quiz_scores,
                         assignment_grades=assignment_grades,
                         course_progress=course_progress,
                         upcoming_deadlines=upcoming_deadlines,
                         overdue_items=overdue_items,
                         recent_activity=recent_activity,
                         course_stats=course_stats,
                         timedelta=timedelta,
                         show_logout=True)

@student_bp.route('/suggest_tutor', methods=['GET', 'POST'])
@login_required
def suggest_tutor():
    # Get student profile from related StudentProfile
    student_profile_obj = current_user.student_profile
    student_profile = {
        'student_name': student_profile_obj.name if student_profile_obj else '',
        'grade_level': student_profile_obj.grade_level if student_profile_obj else '',
        'subject_interests': student_profile_obj.subject_interests if student_profile_obj else '',
        'learning_style': student_profile_obj.learning_style if student_profile_obj else '',
        'support_needs': student_profile_obj.support_needs if student_profile_obj else '',
        'goal': student_profile_obj.goal if student_profile_obj else ''
    }
    
    # Get all instructors
    instructors = User.query.filter_by(role='instructor').all()
    instructor_data = []
    for inst in instructors:
        instructor_profile = inst.instructor_profile
        instructor_data.append({
            'name': instructor_profile.name if instructor_profile else '',
            'bio': instructor_profile.bio if instructor_profile else '',
            'area_of_expertise': instructor_profile.area_of_expertise if instructor_profile else '',
            'teaching_style': instructor_profile.teaching_style if instructor_profile else '',
            'years_of_experience': instructor_profile.years_of_experience if instructor_profile else '',
            'subjects_taught': instructor_profile.subjects_taught if instructor_profile else '',
            'student_feedback_summary': instructor_profile.student_feedback_summary if instructor_profile else ''
        })
    
    # Prepare prompt for Gemini with match scoring
    prompt = f"""
=======================
📘 Student Profile Input:
=======================
- Name: {student_profile['student_name']}
- Grade Level: {student_profile['grade_level']}
- Subject Interests: {student_profile['subject_interests']}
- Learning Style: {student_profile['learning_style']}
- Support Needed: {student_profile['support_needs']}
- Goal: {student_profile['goal']}

===========================
👨‍🏫 Instructor Data (List):
===========================
"""
    for i, inst in enumerate(instructor_data):
        prompt += f"""
Instructor {i+1}:
- Name: {inst['name']}
- Bio: {inst['bio']}
- Area of Expertise: {inst['area_of_expertise']}
- Teaching Style: {inst['teaching_style']}
- Years of Experience: {inst['years_of_experience']}
- Subjects Taught: {inst['subjects_taught']}
- Student Feedback Summary: {inst['student_feedback_summary']}
"""

    prompt += """
==============================
🎯 Task for the Gemini Model:
==============================
1. Analyze the student's needs, learning style, and preferences.
2. Evaluate each instructor based on:
   - Subject/Expertise Match (0-100%)
   - Teaching Style Compatibility (0-100%)
   - Experience Level Appropriateness (0-100%)
   - Student Feedback Quality (0-100%)
3. Calculate an overall match score for each instructor (0-100%).
4. Rank instructors by overall match score.
5. Provide detailed reasoning for each match score.
6. Select the top 2-3 most suitable instructors.

Output the results in the following JSON format:
{
  "recommended_instructors": [
    {
      "instructor_name": "Instructor Name",
      "overall_match_score": 85,
      "subject_match": 90,
      "teaching_style_match": 80,
      "experience_match": 85,
      "feedback_match": 85,
      "reasoning": "Detailed explanation of why this instructor is a good match",
      "strengths": ["Strength 1", "Strength 2", "Strength 3"],
      "recommendation_level": "Excellent/Good/Fair"
    }
  ],
  "analysis_summary": "Overall analysis of the matching process"
}
"""

    # Call Gemini API and parse response
    gemini_response = None
    parsed_recommendations = None
    
    if request.method == 'POST':
        try:
            gemini = GeminiService(current_app.config['GEMINI_API_KEY'])
            gemini_response = gemini.send_message(prompt)
            # Parse the JSON response
            import json
            import re
            # Clean up the response to extract JSON
            json_match = re.search(r'\{.*\}', gemini_response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                # Remove any markdown formatting
                json_str = json_str.replace('```json', '').replace('```', '').strip()
                parsed_recommendations = json.loads(json_str)
            else:
                # If no JSON found, create a fallback response
                parsed_recommendations = {
                    "recommended_instructors": [],
                    "analysis_summary": "Unable to parse AI response. Please try again.",
                    "raw_response": gemini_response
                }
        except Exception as e:
            current_app.logger.error(f"Error parsing Gemini response: {str(e)}")
            parsed_recommendations = {
                "recommended_instructors": [],
                "analysis_summary": f"Error processing AI response: {str(e)}",
                "raw_response": gemini_response
            }
    
    return render_template('suggest_tutor.html', 
                         student_profile=student_profile, 
                         instructors=instructor_data, 
                         gemini_response=gemini_response,
                         parsed_recommendations=parsed_recommendations)

@student_bp.route('/courses/<int:course_id>/quiz/<int:quiz_id>', methods=['GET', 'POST'])
@login_required
def take_quiz(course_id, quiz_id):
    # Check if student is enrolled
    enrollment = Enrollment.query.filter_by(student_id=current_user.id, course_id=course_id).first()
    if not enrollment:
        flash('You are not enrolled in this course.', 'danger')
        return redirect(url_for('student.courses'))
    
    quiz = Quiz.query.get_or_404(quiz_id)
    current_time = datetime.utcnow()
    
    # Check if quiz is available
    if quiz.start_time and current_time < quiz.start_time:
        flash('This quiz is not available yet.', 'warning')
        return redirect(url_for('student.course_detail', course_id=course_id))
    
    if quiz.end_time and current_time > quiz.end_time:
        flash('This quiz has expired.', 'warning')
        return redirect(url_for('student.course_detail', course_id=course_id))
    
    # Check if student has already submitted
    existing_submission = QuizSubmission.query.filter_by(
        quiz_id=quiz_id,
        student_id=current_user.id
    ).first()
    
    if existing_submission and existing_submission.end_time:
        flash('You have already submitted this quiz.', 'warning')
        return redirect(url_for('student.course_detail', course_id=course_id))
    
    # Get all questions for the quiz
    all_questions = Question.query.filter_by(quiz_id=quiz_id).all()
    
    if not all_questions:
        flash('This quiz has no questions.', 'warning')
        return redirect(url_for('student.course_detail', course_id=course_id))
    
    # Separate questions by difficulty
    easy_questions = [q for q in all_questions if q.difficulty == 'Easy']
    medium_questions = [q for q in all_questions if q.difficulty == 'Medium']
    hard_questions = [q for q in all_questions if q.difficulty == 'Hard']
    
    if request.method == 'POST':
        # Handle multi-part form submission
        current_part = int(request.form.get('current_part', 1))
        total_parts = int(request.form.get('total_parts', 1))
        answers = request.form.get('answers', '{}')
        question_start_time = float(request.form.get('question_start_time', '0'))
        now_timestamp = datetime.utcnow().timestamp()
        time_taken = now_timestamp - question_start_time if question_start_time else None

        try:
            answers_dict = json.loads(answers)
        except:
            answers_dict = {}

        # Get current question based on part
        current_question = None
        if current_part <= len(all_questions):
            current_question = all_questions[current_part - 1]

        # Process current answer
        if current_question:
            answer_letter = request.form.get(f'question_{current_question.id}')
            if answer_letter:
                answers_dict[str(current_question.id)] = answer_letter
                opts = json.loads(current_question.options) if current_question.options else []
                letter_map = dict(zip(['A', 'B', 'C', 'D'], opts))
                answer_text = letter_map.get(answer_letter, '')
                if answer_letter:  # Defensive check
                    quiz_answer = QuizAnswer(
                        submission_id=existing_submission.id,
                        question_id=current_question.id,
                        answer=answer_letter,  # store the letter
                        is_correct=(answer_text == current_question.correct_answer)
                    )
                    db.session.add(quiz_answer)

        # Check if this is the final submission
        if current_part >= total_parts:
            # Final submission - calculate score
            if not existing_submission:
                submission = QuizSubmission(
                    quiz_id=quiz_id,
                    student_id=current_user.id,
                    start_time=current_time
                )
                db.session.add(submission)
                db.session.commit()
            else:
                submission = existing_submission
            
            # Process all answers
            score = 0
            total_questions = len(all_questions)

            for question in all_questions:
                answer_letter = answers_dict.get(str(question.id))
                if not answer_letter:
                    continue  # Skip if no answer was selected
                opts = json.loads(question.options) if question.options else []
                letter_map = dict(zip(['A', 'B', 'C', 'D'], opts))
                answer_text = letter_map.get(answer_letter, '')
                if answer_letter:  # Defensive check
                    quiz_answer = QuizAnswer(
                        submission_id=submission.id,
                        question_id=question.id,
                        answer=answer_letter,  # store the letter
                        is_correct=(answer_text == question.correct_answer)
                    )
                    db.session.add(quiz_answer)
                    if answer_text == question.correct_answer:
                        score += 1
            
            # Update submission
            submission.end_time = current_time
            submission.score = (score / total_questions) * 100 if total_questions > 0 else 0
            db.session.commit()
            
            flash('Quiz submitted successfully!', 'success')
            return redirect(url_for('student.quiz_result', course_id=course_id, quiz_id=quiz_id))
        
        # Continue to next part
        next_part = current_part + 1

        # Determine next question difficulty based on behavior or time
        next_question = None
        debug_message = ''
        if next_part <= len(all_questions):
            # Get recent behavior data
            recent_logs = EmotionLog.query.filter_by(student_id=current_user.id)\
                .order_by(EmotionLog.timestamp.desc())\
                .limit(5)\
                .all()

            use_behavior = False
            if recent_logs:
                avg_focus = sum(log.focus_score for log in recent_logs) / len(recent_logs)
                avg_frustration = sum(log.frustration_score for log in recent_logs) / len(recent_logs)
                use_behavior = True
            else:
                avg_focus = avg_frustration = None

            # Adaptive difficulty logic
            if use_behavior and avg_focus is not None and avg_frustration is not None:
                if avg_focus >= 0.7 and avg_frustration <= 0.3:
                    debug_message = f'Behavior: High focus/low frustration, picking hard question.'
                    if hard_questions:
                        next_question = hard_questions.pop(0)
                    elif medium_questions:
                        next_question = medium_questions.pop(0)
                    else:
                        next_question = easy_questions.pop(0) if easy_questions else all_questions[next_part - 1]
                elif avg_focus <= 0.4 or avg_frustration >= 0.6:
                    debug_message = f'Behavior: Low focus/high frustration, picking easy question.'
                    if easy_questions:
                        next_question = easy_questions.pop(0)
                    elif medium_questions:
                        next_question = medium_questions.pop(0)
                    else:
                        next_question = hard_questions.pop(0) if hard_questions else all_questions[next_part - 1]
                else:
                    debug_message = f'Behavior: Medium state, picking medium question.'
                    if medium_questions:
                        next_question = medium_questions.pop(0)
                    elif easy_questions:
                        next_question = easy_questions.pop(0)
                    else:
                        next_question = hard_questions.pop(0) if hard_questions else all_questions[next_part - 1]
            else:
                # No behavior data - use time taken
                if time_taken is not None:
                    debug_message = f'Time taken: {time_taken:.2f} seconds. '
                    if time_taken < 20:
                        debug_message += 'Very quick, picking hard question.'
                        if hard_questions:
                            next_question = hard_questions.pop(0)
                        elif medium_questions:
                            next_question = medium_questions.pop(0)
                        else:
                            next_question = easy_questions.pop(0) if easy_questions else all_questions[next_part - 1]
                    elif time_taken < 60:
                        debug_message += 'Medium time, picking medium question.'
                        if medium_questions:
                            next_question = medium_questions.pop(0)
                        elif hard_questions:
                            next_question = hard_questions.pop(0)
                        else:
                            next_question = easy_questions.pop(0) if easy_questions else all_questions[next_part - 1]
                    else:
                        debug_message += 'Took a long time, picking easy question.'
                        if easy_questions:
                            next_question = easy_questions.pop(0)
                        elif medium_questions:
                            next_question = medium_questions.pop(0)
                        else:
                            next_question = hard_questions.pop(0) if hard_questions else all_questions[next_part - 1]
                else:
                    debug_message = 'No timing info, fallback to default order.'
                    next_question = all_questions[next_part - 1]

        print(debug_message)  # For server-side debugging
        return render_template('take_quiz_multipart.html', 
                             quiz=quiz,
                             current_question=next_question,
                             current_part=next_part,
                             total_parts=len(all_questions),
                             answers=json.dumps(answers_dict),
                             current_time=current_time,
                             question_start_time=now_timestamp,
                             debug_message=debug_message)
    
    # Initial quiz start
    if not existing_submission:
        submission = QuizSubmission(
            quiz_id=quiz_id,
            student_id=current_user.id,
            start_time=current_time
        )
        db.session.add(submission)
        db.session.commit()
    
    # Start with first question
    first_question = all_questions[0] if all_questions else None
    
    return render_template('take_quiz_multipart.html', 
                         quiz=quiz, 
                         current_question=first_question,
                         current_part=1,
                         total_parts=len(all_questions),
                         answers='{}',
                         current_time=current_time)

@student_bp.route('/courses/<int:course_id>/quiz/<int:quiz_id>/result')
@login_required
def quiz_result(course_id, quiz_id):
    # Check if student is enrolled
    enrollment = Enrollment.query.filter_by(student_id=current_user.id, course_id=course_id).first()
    if not enrollment:
        flash('You are not enrolled in this course.', 'danger')
        return redirect(url_for('student.courses'))
    
    quiz = Quiz.query.get_or_404(quiz_id)
    submission = QuizSubmission.query.filter_by(
        quiz_id=quiz_id,
        student_id=current_user.id
    ).first()
    
    if not submission or not submission.end_time:
        flash('No completed quiz submission found.', 'warning')
        return redirect(url_for('student.course_detail', course_id=course_id))
    
    # Calculate additional metrics
    total_questions = len(submission.answers)
    correct_answers = sum(1 for answer in submission.answers if answer.is_correct)
    
    # Calculate time taken
    time_taken = submission.end_time - submission.start_time
    time_taken_minutes = round(time_taken.total_seconds() / 60, 1)
    
    # Get behavior data during quiz
    quiz_start = submission.start_time
    quiz_end = submission.end_time
    
    behavior_logs = EmotionLog.query.filter(
        EmotionLog.student_id == current_user.id,
        EmotionLog.timestamp >= quiz_start,
        EmotionLog.timestamp <= quiz_end
    ).all()
    
    # Calculate average behavior metrics
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
    
    # Add calculated properties to submission object
    submission.correct_answers_count = correct_answers
    submission.total_questions = total_questions
    submission.time_taken_minutes = time_taken_minutes
    submission.avg_focus_percent = round(avg_focus * 100, 1)
    submission.avg_frustration_percent = round(avg_frustration * 100, 1)
    submission.easy_questions_count = len(easy_questions)
    submission.medium_questions_count = len(medium_questions)
    submission.hard_questions_count = len(hard_questions)
    submission.easy_correct_count = easy_correct
    submission.medium_correct_count = medium_correct
    submission.hard_correct_count = hard_correct
    
    return render_template('quiz_result.html',
                         quiz=quiz,
                         submission=submission,
                         course_id=course_id)

@student_bp.route('/start_behavior_monitor', methods=['POST'])
@login_required
def start_behavior_monitor():
    try:
        # Start monitoring in a background thread, passing the app instance
        monitor = StudentBehaviorMonitor()
        from flask import current_app
        app = current_app._get_current_object()
        thread = Thread(target=monitor.start_monitoring, args=(current_user.id, None, app))
        thread.daemon = True
        thread.start()
        
        return jsonify({'message': 'Monitoring started successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@student_bp.route('/stop_behavior_monitor', methods=['POST'])
@login_required
def stop_behavior_monitor():
    try:
        # Stop monitoring by setting a flag in the monitor instance
        if hasattr(current_app, 'behavior_monitor'):
            current_app.behavior_monitor.stop_monitoring()
        return jsonify({'message': 'Monitoring stopped successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@student_bp.route('/monitoring_status', methods=['GET'])
@login_required
def monitoring_status():
    from datetime import datetime, timedelta
    now = datetime.utcnow()
    one_minute_ago = now - timedelta(minutes=1)
    logs = EmotionLog.query.filter(
        EmotionLog.student_id == current_user.id,
        EmotionLog.timestamp >= one_minute_ago
    ).all()
    if logs:
        avg_focus = sum(log.focus_score for log in logs) / len(logs)
        avg_frustration = sum(log.frustration_score for log in logs) / len(logs)
        last_updated = max(log.timestamp for log in logs)
    else:
        avg_focus = None
        avg_frustration = None
        last_updated = None
    return jsonify({
        'is_monitoring': any(logs),
        'avg_focus': avg_focus,
        'avg_frustration': avg_frustration,
        'last_updated': last_updated.isoformat() if last_updated else None
    })

@student_bp.route('/behavior_tracking')
@login_required
def behavior_tracking():
    student_id = current_user.id
    logs = EmotionLog.query.filter_by(student_id=student_id).order_by(EmotionLog.timestamp.desc()).all()
    return render_template(
        'behavior_tracking.html',
        logs=logs
    )

@student_bp.route('/get_behavior_suggestions', methods=['POST'])
@login_required
def get_behavior_suggestions():
    student_id = current_user.id
    # Get live values from form
    live_focus = request.form.get('live_focus', 'N/A')
    live_frustration = request.form.get('live_frustration', 'N/A')
    
    # Get recent behavior logs
    recent_logs = EmotionLog.query.filter_by(student_id=student_id)\
        .order_by(EmotionLog.timestamp.desc())\
        .limit(10)\
        .all()
    
    # Get student profile (handle missing profile gracefully)
    try:
        student_profile = current_user.student_profile
        student_profile_data = {
            'name': student_profile.name if student_profile and hasattr(student_profile, 'name') else 'Unknown',
            'grade_level': student_profile.grade_level if student_profile and hasattr(student_profile, 'grade_level') else 'Unknown',
            'learning_style': student_profile.learning_style if student_profile and hasattr(student_profile, 'learning_style') else 'Unknown',
            'support_needs': student_profile.support_needs if student_profile and hasattr(student_profile, 'support_needs') else 'None specified'
        }
    except Exception as e:
        # If there's any error accessing student profile, use default values
        student_profile_data = {
            'name': 'Unknown',
            'grade_level': 'Unknown',
            'learning_style': 'Unknown',
            'support_needs': 'None specified'
        }
    
    # Get enrollment details for better suggestions
    enrollments = Enrollment.query.filter_by(student_id=student_id).all()
    enrollment_data = []
    for enrollment in enrollments:
        course = enrollment.course
        instructor = course.instructor if course else None
        instructor_profile = instructor.instructor_profile if instructor else None
        
        enrollment_data.append({
            'course_title': course.title if course else 'Unknown Course',
            'course_description': course.description if course else 'No description',
            'instructor_name': instructor_profile.name if instructor_profile and hasattr(instructor_profile, 'name') else 'Unknown Instructor',
            'instructor_teaching_style': instructor_profile.teaching_style if instructor_profile and hasattr(instructor_profile, 'teaching_style') else 'Unknown',
            'instructor_expertise': instructor_profile.area_of_expertise if instructor_profile and hasattr(instructor_profile, 'area_of_expertise') else 'Unknown',
            'latest_focus_score': enrollment.latest_focus_score,
            'frustration_level': enrollment.frustration_level,
            'last_updated': enrollment.last_updated.isoformat() if enrollment.last_updated else None
        })
    
    # Prepare data for Gemini
    behavior_data = {
        'recent_logs': [
            {
                'timestamp': log.timestamp.isoformat(),
                'focus_score': log.focus_score,
                'frustration_score': log.frustration_score
            } for log in recent_logs
        ],
        'student_profile': student_profile_data,
        'enrollments': enrollment_data
    }
    
    # Prepare prompt for Gemini
    prompt = f"""
Analyze the following student behavior data and provide suggestions:

Student Profile:
- Name: {behavior_data['student_profile']['name']}
- Grade Level: {behavior_data['student_profile']['grade_level']}
- Learning Style: {behavior_data['student_profile']['learning_style']}
- Support Needs: {behavior_data['student_profile']['support_needs']}

Current Enrollments and Performance:
{behavior_data['enrollments']}

Recent Behavior Logs:
{behavior_data['recent_logs']}

Live Focus Level: {live_focus}%
Live Frustration Level: {live_frustration}%

Please analyze this data and provide:
1. A focus analysis (is the student focused enough?)
2. Specific recommendations for improvement
3. Suggestions for potential course/instructor changes if needed
4. Learning environment recommendations based on the student's learning style

Format the response as JSON with the following structure:
{{
    "focus_analysis": {{
        "is_focused": boolean,
        "message": "detailed analysis message"
    }},
    "recommendations": [
        {{
            "title": "recommendation title",
            "description": "detailed recommendation"
        }}
    ],
    "course_suggestions": [
        {{
            "type": "course_change" or "instructor_change" or "learning_environment",
            "title": "suggestion title",
            "description": "detailed suggestion"
        }}
    ]
}}
"""
    
    # Get AI suggestions
    gemini = GeminiService(current_app.config['GEMINI_API_KEY'])
    response = gemini.send_message(prompt)
    
    # Parse the response
    try:
        # Clean up the response to ensure it's valid JSON
        response = response.replace('```json', '').replace('```', '').strip()
        ai_suggestions = json.loads(response)
    except Exception as e:
        current_app.logger.error(f"Error parsing Gemini response: {str(e)}")
        ai_suggestions = {
            'focus_analysis': {
                'is_focused': None,
                'message': 'Error analyzing behavior data. Please try again.'
            },
            'recommendations': [],
            'course_suggestions': []
        }
    
    # Get all logs for the template
    logs = EmotionLog.query.filter_by(student_id=student_id).order_by(EmotionLog.timestamp.desc()).all()
    
    return render_template('behavior_suggestions_with_camera.html', 
                         logs=logs, 
                         ai_suggestions=ai_suggestions,
                         live_focus=live_focus,
                         live_frustration=live_frustration)

@student_bp.route('/get_live_behavior_data', methods=['GET'])
@login_required
def get_live_behavior_data():
    """Get live behavior data for real-time updates"""
    student_id = current_user.id
    
    # Get the most recent behavior log
    latest_log = EmotionLog.query.filter_by(student_id=student_id)\
        .order_by(EmotionLog.timestamp.desc())\
        .first()
    
    # Get recent logs for trend analysis
    from datetime import datetime, timedelta
    now = datetime.utcnow()
    five_minutes_ago = now - timedelta(minutes=5)
    recent_logs = EmotionLog.query.filter(
        EmotionLog.student_id == student_id,
        EmotionLog.timestamp >= five_minutes_ago
    ).order_by(EmotionLog.timestamp.desc()).all()
    
    # Calculate averages
    if recent_logs:
        avg_focus = sum(log.focus_score for log in recent_logs) / len(recent_logs)
        avg_frustration = sum(log.frustration_score for log in recent_logs) / len(recent_logs)
        trend = 'stable'
        
        # Determine trend
        if len(recent_logs) >= 2:
            recent_avg = sum(log.focus_score for log in recent_logs[:len(recent_logs)//2]) / (len(recent_logs)//2)
            older_avg = sum(log.focus_score for log in recent_logs[len(recent_logs)//2:]) / (len(recent_logs)//2)
            if recent_avg > older_avg + 0.1:
                trend = 'improving'
            elif recent_avg < older_avg - 0.1:
                trend = 'declining'
    else:
        avg_focus = 0.5  # Default value
        avg_frustration = 0.3  # Default value
        trend = 'stable'
    
    return jsonify({
        'latest_focus': round(latest_log.focus_score * 100, 1) if latest_log else 50,
        'latest_frustration': round(latest_log.frustration_score * 100, 1) if latest_log else 30,
        'avg_focus': round(avg_focus * 100, 1),
        'avg_frustration': round(avg_frustration * 100, 1),
        'trend': trend,
        'last_updated': latest_log.timestamp.isoformat() if latest_log else None,
        'recent_logs_count': len(recent_logs)
    })

@student_bp.route('/get_quiz_behavior_data', methods=['GET'])
@login_required
def get_quiz_behavior_data():
    """Get real-time behavior data for adaptive quiz difficulty"""
    try:
        # Get recent behavior logs (last 5 minutes)
        recent_time = datetime.utcnow() - timedelta(minutes=5)
        recent_logs = EmotionLog.query.filter(
            EmotionLog.student_id == current_user.id,
            EmotionLog.timestamp >= recent_time
        ).order_by(EmotionLog.timestamp.desc()).limit(10).all()
        
        if recent_logs:
            # Calculate averages
            avg_focus = sum(log.focus_score for log in recent_logs) / len(recent_logs)
            avg_frustration = sum(log.frustration_score for log in recent_logs) / len(recent_logs)
            
            # Determine suggested difficulty
            if avg_focus >= 0.7 and avg_frustration <= 0.3:
                suggested_difficulty = 'Hard'
                difficulty_reason = 'High focus and low frustration detected'
            elif avg_focus <= 0.4 or avg_frustration >= 0.6:
                suggested_difficulty = 'Easy'
                difficulty_reason = 'Low focus or high frustration detected'
            else:
                suggested_difficulty = 'Medium'
                difficulty_reason = 'Moderate focus and frustration levels'
            
            return jsonify({
                'success': True,
                'focus_score': round(avg_focus, 3),
                'frustration_score': round(avg_frustration, 3),
                'focus_percent': round(avg_focus * 100, 1),
                'frustration_percent': round(avg_frustration * 100, 1),
                'suggested_difficulty': suggested_difficulty,
                'difficulty_reason': difficulty_reason,
                'timestamp': datetime.utcnow().isoformat()
            })
        else:
            return jsonify({
                'success': True,
                'focus_score': 0.5,
                'frustration_score': 0.3,
                'focus_percent': 50.0,
                'frustration_percent': 30.0,
                'suggested_difficulty': 'Medium',
                'difficulty_reason': 'No recent behavior data available',
                'timestamp': datetime.utcnow().isoformat()
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500 

@student_bp.route('/courses/<int:course_id>/assignment/<int:assignment_id>/submit', methods=['POST'])
@login_required
def submit_assignment(course_id, assignment_id):
    assignment = Assignment.query.get_or_404(assignment_id)
    # Only students can submit
    if current_user.role != 'student':
        flash('Only students can submit assignments.', 'danger')
        return redirect(url_for('student.course_detail', course_id=course_id))
    # Prevent duplicate submissions
    existing = AssignmentSubmission.query.filter_by(assignment_id=assignment_id, student_id=current_user.id).first()
    if existing:
        flash('You have already submitted this assignment.', 'info')
        return redirect(url_for('student.course_detail', course_id=course_id))
    comments = request.form.get('comments')
    if not comments:
        flash('Submission cannot be empty.', 'warning')
        return redirect(url_for('student.course_detail', course_id=course_id))
    submission = AssignmentSubmission(
        assignment_id=assignment_id,
        student_id=current_user.id,
        comments=comments,
        submitted_at=datetime.utcnow()
    )
    db.session.add(submission)
    db.session.commit()
    flash('Assignment submitted successfully!', 'success')
    return redirect(url_for('student.course_detail', course_id=course_id)) 