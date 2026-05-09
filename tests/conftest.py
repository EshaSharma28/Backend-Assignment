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
    user, _employee = create_user_with_employee(
        app=app,
        email='admin@hirehub.com',
        password='adminpassword',
        role_name='Admin',
        first_name='Admin',
        is_sales_agent=True,
    )

    resp = client.post('/api/auth/login', json={
        'email': user.email,
        'password': 'adminpassword'
    })
    return resp.json['token']


def create_user_with_employee(
    app,
    email,
    password,
    role_name,
    first_name,
    is_sales_agent=False,
):
    with app.app_context():
        from app.auth.utils import hash_password
        from app.models.auth import Role, User
        from app.models.hrms import Employee

        role = Role.query.filter_by(name=role_name).first()
        user = User(
            email=email,
            password_hash=hash_password(password),
            role_id=role.id,
        )
        db.session.add(user)
        db.session.flush()
        
        employee = Employee(
            user_id=user.id,
            first_name=first_name,
            last_name="User",
            date_of_joining=date(2024, 1, 1),
            department=role_name,
            is_sales_agent=is_sales_agent,
        )
        db.session.add(employee)
        db.session.commit()
        db.session.refresh(user)
        db.session.refresh(employee)
        db.session.expunge(user)
        db.session.expunge(employee)
        return user, employee


@pytest.fixture
def sales_user(client, app):
    user, employee = create_user_with_employee(
        app=app,
        email='sales@hirehub.com',
        password='salespassword',
        role_name='Sales',
        first_name='Sales',
        is_sales_agent=True,
    )
    resp = client.post('/api/auth/login', json={
        'email': user.email,
        'password': 'salespassword'
    })
    return {'token': resp.json['token'], 'user': user, 'employee': employee}


@pytest.fixture
def second_sales_user(client, app):
    user, employee = create_user_with_employee(
        app=app,
        email='sales2@hirehub.com',
        password='salespassword',
        role_name='Sales',
        first_name='SecondSales',
        is_sales_agent=True,
    )
    resp = client.post('/api/auth/login', json={
        'email': user.email,
        'password': 'salespassword'
    })
    return {'token': resp.json['token'], 'user': user, 'employee': employee}
