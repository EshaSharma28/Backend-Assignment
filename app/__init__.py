"""
HireHub - Merged CRM + HRMS System
Application factory pattern.
"""

import os
from flask import Flask
from sqlalchemy.exc import DataError, IntegrityError, SQLAlchemyError, StatementError
from app.extensions import db, migrate
from config import config_by_name


def create_app(config_name=None):
    # App factory using the config_by_name map from config.py
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')

    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])
    if config_name == 'production' and not os.environ.get('SECRET_KEY'):
        raise RuntimeError('SECRET_KEY is required in production')

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Import all models so Alembic can detect them
    with app.app_context():
        from app.models import (  # noqa: F401
            Role, RolePermission, User,
            Employee, Team, TeamMember,
            DailyAttendance, LeaveRequest, LeaveBalance,
            Lead, LeadStatusHistory, Interaction,
            PerformanceRecord,
        )

    # Register blueprints
    from app.auth import auth_bp
    from app.hrms import hrms_bp
    from app.crm import crm_bp
    from app.performance import performance_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(hrms_bp)
    app.register_blueprint(crm_bp)
    app.register_blueprint(performance_bp)

    @app.errorhandler(IntegrityError)
    def handle_integrity_error(error):
        db.session.rollback()
        return {
            'message': 'Database integrity error',
            'detail': 'A unique, foreign key, or check constraint was violated',
        }, 409

    @app.errorhandler(DataError)
    def handle_data_error(error):
        db.session.rollback()
        return {'message': 'Invalid database input'}, 400

    @app.errorhandler(StatementError)
    def handle_bad_database_input(error):
        db.session.rollback()
        return {'message': 'Invalid database input'}, 400

    @app.errorhandler(SQLAlchemyError)
    def handle_database_error(error):
        db.session.rollback()
        return {'message': 'Database error'}, 500

    return app
