import pytest
from app.models.hrms import Employee
from app.models.crm import Lead, Interaction
from datetime import date, timedelta

def test_lead_lifecycle_and_performance(client, admin_token):
    # Get admin employee
    admin_emp = Employee.query.filter_by(first_name="Admin").first()

    # Create Lead
    resp = client.post('/api/crm/leads', json={
        'company_name': 'Test Corp',
        'contact_name': 'HR Manager',
        'estimated_value': 10000,
        'assigned_agent_id': admin_emp.id
    }, headers={'Authorization': f'Bearer {admin_token}'})
    assert resp.status_code == 201
    lead_id = resp.json['id']

    # Log Interaction
    resp = client.post(f'/api/crm/leads/{lead_id}/interactions', json={
        'type': 'Call',
        'subject': 'Intro Call',
        'notes': 'Positive response',
        'duration_minutes': 15
    }, headers={'Authorization': f'Bearer {admin_token}'})
    assert resp.status_code == 201

    # Convert Lead
    resp = client.patch(f'/api/crm/leads/{lead_id}/status', json={
        'status': 'Customer',
        'actual_value': 12000,
        'notes': 'Deal closed!'
    }, headers={'Authorization': f'Bearer {admin_token}'})
    assert resp.status_code == 200
    assert resp.json['status'] == 'Customer'

    # Calculate Performance
    start = (date.today() - timedelta(days=1)).isoformat()
    end = (date.today() + timedelta(days=1)).isoformat()
    resp = client.post(f'/api/performance/calculate/{admin_emp.id}', json={
        'period_start': start,
        'period_end': end
    }, headers={'Authorization': f'Bearer {admin_token}'})
    
    assert resp.status_code == 200
    assert resp.json['leads_converted'] == 1
    assert resp.json['total_deal_value'] == '12000.00'
    assert resp.json['total_interactions'] == 1


def test_sales_cannot_access_another_agents_lead(
    client, admin_token, sales_user, second_sales_user
):
    resp = client.post('/api/crm/leads', json={
        'company_name': 'Restricted Corp',
        'assigned_agent_id': second_sales_user['employee'].id
    }, headers={'Authorization': f'Bearer {admin_token}'})
    assert resp.status_code == 201
    lead_id = resp.json['id']

    resp = client.get(f'/api/crm/leads/{lead_id}', headers={
        'Authorization': f"Bearer {sales_user['token']}"
    })
    assert resp.status_code == 403

    resp = client.patch(f'/api/crm/leads/{lead_id}/status', json={
        'status': 'Customer'
    }, headers={'Authorization': f"Bearer {sales_user['token']}"})
    assert resp.status_code == 403


def test_lead_cannot_be_assigned_to_non_sales_employee(client, admin_token, app):
    with app.app_context():
        from app.auth.utils import hash_password
        from app.models.auth import Role, User

        hr_role = Role.query.filter_by(name='HR').first()
        hr_user = User(
            email='hr@hirehub.com',
            password_hash=hash_password('password123'),
            role_id=hr_role.id,
        )
        from app.extensions import db
        db.session.add(hr_user)
        db.session.flush()
        non_sales = Employee(
            user_id=hr_user.id,
            first_name='HR',
            last_name='User',
            date_of_joining=date.today(),
            is_sales_agent=False,
        )
        db.session.add(non_sales)
        db.session.commit()
        non_sales_id = non_sales.id

    resp = client.post('/api/crm/leads', json={
        'company_name': 'Bad Assignment Inc',
        'assigned_agent_id': non_sales_id,
    }, headers={'Authorization': f'Bearer {admin_token}'})

    assert resp.status_code == 400
