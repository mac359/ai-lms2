from flask import Blueprint

instructor_bp = Blueprint('instructor', __name__, template_folder='../templates')
 
from . import views 