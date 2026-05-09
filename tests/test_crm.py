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
