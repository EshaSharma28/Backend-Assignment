"""
HireHub - Merged CRM + HRMS System
Application factory pattern.
"""

import os
from flask import Flask
from app.extensions import db, migrate
from config import config_by_name


def create_app(config_name=None):
    """
    Application factory.

    Args:
        config_name: One of 'development', 'production', or 'default'.
                     Falls back to FLASK_ENV env var, then 'default'.
    """
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')

    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

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
    app.register_blueprint(auth_bp)

    return app
