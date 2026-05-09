import pytest
from app import create_app
from app.extensions import db

@pytest.fixture(scope='session')
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        from seed import seed_rbac
        seed_rbac()
        yield app
        # No drop_all here to avoid hangs, just clean up sessions
        db.session.remove()
        db.engine.dispose()

@pytest.fixture(autouse=True)
def cleanup(app):
    """Clean up tables between tests."""
    with app.app_context():
        # Iterate in reverse to avoid FK constraints
        for table in reversed(db.metadata.sorted_tables):
            # Keep roles and permissions as they are seeded once
            if table.name not in ['roles', 'permissions', 'role_permissions']:
                db.session.execute(table.delete())
        db.session.commit()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def admin_token(client, app):
    # Register and login admin
    with app.app_context():
        resp = client.post('/api/auth/register', json={
            'email': 'admin@hirehub.com',
            'password': 'adminpassword',
            'role_id': 1
        })
        user_id = resp.json['user']['id']
        
        # Create employee profile for admin
        from app.models.hrms import Employee
        admin_emp = Employee(
            user_id=user_id,
            first_name="Admin",
            last_name="User",
            date_of_joining="2024-01-01",
            department="Management"
        )
        db.session.add(admin_emp)
        db.session.commit()

    resp = client.post('/api/auth/login', json={
        'email': 'admin@hirehub.com',
        'password': 'adminpassword'
    })
    return resp.json['token']
