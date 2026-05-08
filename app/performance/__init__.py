from flask import Blueprint

performance_bp = Blueprint('performance', __name__, url_prefix='/api/performance')

from app.performance import routes
