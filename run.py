"""
Entry point for the Flask application.

Usage:
    python run.py                  # Development server
    flask db init                  # Initialize migrations
    flask db migrate -m "initial"  # Generate migration
    flask db upgrade               # Apply migration
"""

from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
