from flask import Blueprint

lms_core_bp = Blueprint('lms_core', __name__, template_folder='../templates')

from . import views 