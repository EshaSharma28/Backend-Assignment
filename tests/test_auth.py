import pytest
from app.models.auth import Role, User

def test_register_user(client, seed_data):
    # Get Admin role ID
    admin_role = Role.query.filter_by(name='Admin').first()
    
    response = client.post('/api/auth/register', json={
        'email': 'test@example.com',
        'password': 'password123',
        'role_id': admin_role.id
    })
    
    assert response.status_code == 201
    assert response.json['message'] == 'User registered successfully'
    assert response.json['user']['email'] == 'test@example.com'
    sales_role = Role.query.filter_by(name='Sales').first()
    assert response.json['user']['role_id'] == sales_role.id


def test_duplicate_email_rejected(client, seed_data):
    payload = {
        'email': 'duplicate@example.com',
        'password': 'password123'
    }

    first = client.post('/api/auth/register', json=payload)
    second = client.post('/api/auth/register', json=payload)

    assert first.status_code == 201
    assert second.status_code == 409

def test_login_user(client, seed_data):
    # Register first
    admin_role = Role.query.filter_by(name='Admin').first()
    client.post('/api/auth/register', json={
        'email': 'login@example.com',
        'password': 'password123',
        'role_id': admin_role.id
    })
    
    # Attempt login
    response = client.post('/api/auth/login', json={
        'email': 'login@example.com',
        'password': 'password123'
    })
    
    assert response.status_code == 200
    assert 'token' in response.json
    assert response.json['user']['email'] == 'login@example.com'

def test_get_me(client, seed_data):
    # Register and Login to get token
    admin_role = Role.query.filter_by(name='Admin').first()
    client.post('/api/auth/register', json={
        'email': 'me@example.com',
        'password': 'password123',
        'role_id': admin_role.id
    })
    
    login_res = client.post('/api/auth/login', json={
        'email': 'me@example.com',
        'password': 'password123'
    })
    token = login_res.json['token']
    
    # Access /me
    response = client.get('/api/auth/me', headers={
        'Authorization': f'Bearer {token}'
    })
    
    assert response.status_code == 200
    assert response.json['email'] == 'me@example.com'


def test_sales_user_cannot_list_users(client, sales_user):
    response = client.get('/api/auth/users', headers={
        'Authorization': f"Bearer {sales_user['token']}"
    })

    assert response.status_code == 403
