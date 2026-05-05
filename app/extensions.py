"""
Shared extension instances.
Initialized here to avoid circular imports; bound to the app in create_app().
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()
