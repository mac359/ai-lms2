from flask import Flask, render_template, redirect, url_for, flash, request, current_app, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user, login_required
from flask_migrate import Migrate
from flask_wtf import CSRFProtect
from config import Config
from models import db, Enrollment, EmotionLog
import json
import os
from flask_socketio import SocketIO, emit
import eventlet
try:
    from deepface import DeepFace
    DEEPFACE_AVAILABLE = True
except ImportError:
    DEEPFACE_AVAILABLE = False
    print("Warning: DeepFace not available. Emotion analysis will be disabled.")
import cv2
import numpy as np
import base64
from datetime import datetime
import math

# Extensions
login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()
socketio = SocketIO(async_mode='eventlet')

# Create uploads directory if it doesn't exist
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

user_activity = {}

def from_json_filter(s):
    try:
        return json.loads(s)
    except Exception:
        return []

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")

    from models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.context_processor
    def inject_csrf_token():
        from flask_wtf.csrf import generate_csrf
        return dict(csrf_token=generate_csrf)

    app.jinja_env.filters['from_json'] = from_json_filter

    # Import and register blueprints
    from auth.views import auth_bp
    from student.views import student_bp
    from instructor.views import instructor_bp
    from admin.views import admin_bp
    from lms_core.views import lms_core_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(instructor_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(lms_core_bp)

    # --- Redirects for legacy URLs ---
    @app.route('/dashboard')
    def dashboard_redirect():
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if current_user.role == 'student':
            return redirect(url_for('student.dashboard'))
        elif current_user.role == 'instructor':
            return redirect(url_for('instructor.dashboard'))
        elif current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('auth.login'))

    @app.route('/courses')
    def courses_redirect():
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if current_user.role == 'student':
            return redirect(url_for('student.courses'))
        elif current_user.role == 'instructor':
            return redirect(url_for('instructor.courses'))
        else:
            return redirect(url_for('auth.login'))

    @app.route('/courses/<int:course_id>')
    def course_detail_redirect(course_id):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if current_user.role == 'student':
            return redirect(url_for('student.course_detail', course_id=course_id))
        elif current_user.role == 'instructor':
            return redirect(url_for('instructor.course_detail', course_id=course_id))
        else:
            return redirect(url_for('auth.login'))

    @app.route('/help')
    def help_redirect():
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if current_user.role == 'student':
            return redirect(url_for('student.help'))
        elif current_user.role == 'instructor':
            return redirect(url_for('instructor.help'))
        else:
            return redirect(url_for('auth.login'))

    @app.route('/history')
    def history_redirect():
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if current_user.role == 'student':
            return redirect(url_for('student.history'))
        elif current_user.role == 'instructor':
            return redirect(url_for('instructor.history'))
        else:
            return redirect(url_for('auth.login'))

    @app.route('/calendar')
    def calendar_redirect():
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if current_user.role == 'student':
            return redirect(url_for('student.calendar'))
        elif current_user.role == 'instructor':
            return redirect(url_for('instructor.calendar'))
        else:
            return redirect(url_for('auth.login'))

    @app.route('/ai-chatbot')
    @login_required
    def ai_chatbot_redirect():
        if current_user.role == 'student':
            return redirect(url_for('student.ai_chatbot'))
        elif current_user.role == 'instructor':
            return redirect(url_for('instructor.ai_chatbot'))
        else:
            flash('Access denied.', 'danger')
            return redirect(url_for('main.index'))

    # Add route to serve uploaded files
    @app.route('/uploads/<filename>')
    def uploaded_file(filename):
        return send_from_directory(UPLOAD_FOLDER, filename)

    # WebSocket handler for video/audio data
    @socketio.on('activity_data')
    def handle_activity_data(data):
        if current_user.is_authenticated:
            user_activity[current_user.id] = data

    @socketio.on('media_frame')
    def handle_media_frame(data):
        print('Received media frame:', list(data.keys()))
        if 'video' in data:
            try:
                base64_img = data['video']
                if base64_img.startswith('data:image'):
                    base64_img = base64_img.split(',')[1]
                img_data = base64.b64decode(base64_img)
                np_arr = np.frombuffer(img_data, np.uint8)
                img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                # Analyze with DeepFace (get face region)
                if DEEPFACE_AVAILABLE:
                    result = DeepFace.analyze(img, actions=['emotion'], enforce_detection=False)
                    print('DeepFace result:', result)
                    if isinstance(result, list):
                        result = result[0]
                    face_region = result.get('region', {})
                    focus_score = 0.0
                    if face_region and all(k in face_region for k in ['x', 'y', 'w', 'h']):
                        # Crop face
                        x, y, w, h = face_region['x'], face_region['y'], face_region['w'], face_region['h']
                        face_img = img[y:y+h, x:x+w]
                        # Use OpenCV to detect landmarks and estimate head pose
                        gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
                        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
                        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
                        if len(faces) > 0:
                            # Use the first detected face
                            (fx, fy, fw, fh) = faces[0]
                            face_roi = gray[fy:fy+fh, fx:fx+fw]
                            # Use OpenCV's built-in facial landmark detector (if available)
                            # For simplicity, use the center of the face as the nose tip
                            image_points = np.array([
                                (fw/2, fh/2),     # Nose tip (approx)
                                (fw/2, fh*0.8),   # Chin (approx)
                                (fw*0.3, fh*0.35), # Left eye left corner (approx)
                                (fw*0.7, fh*0.35), # Right eye right corner (approx)
                                (fw*0.25, fh*0.7), # Left mouth corner (approx)
                                (fw*0.75, fh*0.7)  # Right mouth corner (approx)
                            ], dtype='double')
                            # 3D model points.
                            model_points = np.array([
                                (0.0, 0.0, 0.0),             # Nose tip
                                (0.0, -63.6, -12.5),         # Chin
                                (-43.3, 32.7, -26.0),        # Left eye left corner
                                (43.3, 32.7, -26.0),         # Right eye right corner
                                (-28.9, -28.9, -24.1),       # Left mouth corner
                                (28.9, -28.9, -24.1)         # Right mouth corner
                            ])
                            # Camera internals
                            size = face_roi.shape
                            focal_length = size[1]
                            center = (size[1]/2, size[0]/2)
                            camera_matrix = np.array(
                                [[focal_length, 0, center[0]],
                                 [0, focal_length, center[1]],
                                 [0, 0, 1]], dtype = 'double'
                            )
                            dist_coeffs = np.zeros((4,1)) # Assuming no lens distortion
                            success, rotation_vector, translation_vector = cv2.solvePnP(model_points, image_points, camera_matrix, dist_coeffs, flags=cv2.SOLVEPNP_ITERATIVE)
                            if success:
                                # Convert rotation vector to Euler angles
                                rmat, _ = cv2.Rodrigues(rotation_vector)
                                sy = math.sqrt(rmat[0,0] * rmat[0,0] +  rmat[1,0] * rmat[1,0])
                                singular = sy < 1e-6
                                if not singular:
                                    x_angle = math.atan2(rmat[2,1], rmat[2,2])
                                    y_angle = math.atan2(-rmat[2,0], sy)
                                    z_angle = math.atan2(rmat[1,0], rmat[0,0])
                                else:
                                    x_angle = math.atan2(-rmat[1,2], rmat[1,1])
                                    y_angle = math.atan2(-rmat[2,0], sy)
                                    z_angle = 0
                                # Convert radians to degrees
                                pitch = math.degrees(x_angle)
                                yaw = math.degrees(y_angle)
                                roll = math.degrees(z_angle)
                                print(f'Head pose: pitch={pitch:.2f}, yaw={yaw:.2f}, roll={roll:.2f}')
                                # If yaw and pitch are within ±20 degrees, consider focused
                                if abs(yaw) < 20 and abs(pitch) < 20:
                                    focus_score = 1.0
                                else:
                                    focus_score = 0.0
                    # Combine with recent activity
                    activity = user_activity.get(current_user.id, {'keypresses': 0, 'mousemoves': 0, 'mouseclicks': 0})
                    activity_score = min(1.0, (activity['keypresses'] + activity['mousemoves'] + activity['mouseclicks']) / 20.0)
                    final_focus_score = 0.7 * focus_score + 0.3 * activity_score
                    # Update DB for current user (if available)
                    if current_user.is_authenticated:
                        enrollment = Enrollment.query.filter_by(student_id=current_user.id).first()
                        if enrollment:
                            enrollment.latest_focus_score = final_focus_score
                            enrollment.last_updated = datetime.utcnow()
                            db.session.commit()
                            elog = EmotionLog(
                                student_id=current_user.id,
                                course_id=enrollment.course_id,
                                timestamp=datetime.utcnow(),
                                focus_score=final_focus_score,
                                frustration_score=result['emotion'].get('angry', 0) / 100.0,
                                source_data_summary=str(result['emotion'])
                            )
                            db.session.add(elog)
                            db.session.commit()
                            print('Updated enrollment and logged emotion for user:', current_user.id)
                else:
                    # DeepFace not available, use basic activity tracking only
                    activity = user_activity.get(current_user.id, {'keypresses': 0, 'mousemoves': 0, 'mouseclicks': 0})
                    activity_score = min(1.0, (activity['keypresses'] + activity['mousemoves'] + activity['mouseclicks']) / 20.0)
                    final_focus_score = activity_score
                    # Update DB for current user (if available)
                    if current_user.is_authenticated:
                        enrollment = Enrollment.query.filter_by(student_id=current_user.id).first()
                        if enrollment:
                            enrollment.latest_focus_score = final_focus_score
                            enrollment.last_updated = datetime.utcnow()
                            db.session.commit()
                            elog = EmotionLog(
                                student_id=current_user.id,
                                course_id=enrollment.course_id,
                                timestamp=datetime.utcnow(),
                                focus_score=final_focus_score,
                                frustration_score=0.0,  # No emotion data available
                                source_data_summary="DeepFace not available - activity only"
                            )
                            db.session.add(elog)
                            db.session.commit()
                            print('Updated enrollment with activity-only data for user:', current_user.id)
            except Exception as e:
                print('Media processing error:', e)
        emit('ack', {'status': 'received'})

    return app

if __name__ == '__main__':
    app = create_app()
    socketio.run(app, debug=True, port=5001) 