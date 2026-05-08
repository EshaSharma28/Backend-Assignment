from flask import Blueprint

crm_bp = Blueprint('crm', __name__, url_prefix='/api/crm')

from app.crm import routes
