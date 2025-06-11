from flask import render_template
from . import lms_core_bp
 
@lms_core_bp.route('/lms')
def lms_home():
    return 'LMS Core Home' 