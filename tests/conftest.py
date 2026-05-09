import pytest
from datetime import date
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
def seed_data(app):
    """RBAC data is seeded once in the app fixture."""
    return None


@pytest.fixture
def admin_token(client, app):
    with app.app_context():
        from app.auth.utils import hash_password
        from app.models.auth import Role, User
        from app.models.hrms import Employee

        admin_role = Role.query.filter_by(name='Admin').first()
        admin_user = User(
            email='admin@hirehub.com',
            password_hash=hash_password('adminpassword'),
            role_id=admin_role.id,
        )
        db.session.add(admin_user)
        db.session.flush()
        
        admin_emp = Employee(
            user_id=admin_user.id,
            first_name="Admin",
            last_name="User",
            date_of_joining=date(2024, 1, 1),
            department="Management",
            is_sales_agent=True,
        )
        db.session.add(admin_emp)
        db.session.commit()

    resp = client.post('/api/auth/login', json={
        'email': 'admin@hirehub.com',
        'password': 'adminpassword'
    })
    return resp.json['token']
