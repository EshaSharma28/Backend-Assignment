from flask import Blueprint

hrms_bp = Blueprint('hrms', __name__, url_prefix='/api/hrms')

from app.hrms import routes
