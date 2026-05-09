import pytest
from app.models.hrms import Employee, Team, TeamMember, DailyAttendance, LeaveRequest, LeaveBalance
from datetime import date, timedelta

def test_create_employee(client, admin_token):
    # Register a new user first
    resp = client.post('/api/auth/register', json={
        'email': 'new_emp@hirehub.com',
        'password': 'password123',
        'role_id': 2 # HR
    })
    user_id = resp.json['user']['id']

    # Create employee profile
    resp = client.post('/api/hrms/employees', json={
        'user_id': user_id,
        'first_name': 'New',
        'last_name': 'Employee',
        'date_of_joining': '2024-01-01',
        'department': 'HR'
    }, headers={'Authorization': f'Bearer {admin_token}'})

    assert resp.status_code == 201
    assert resp.json['first_name'] == 'New'
    assert Employee.query.filter_by(user_id=user_id).first() is not None

def test_team_management(client, admin_token):
    # Create Team
    resp = client.post('/api/hrms/teams', json={
        'name': 'Alpha Team',
        'description': 'Sales Force'
    }, headers={'Authorization': f'Bearer {admin_token}'})
    assert resp.status_code == 201
    team_id = resp.json['id']

    # Get employee ID (from seeded admin)
    admin_emp = Employee.query.first()
    
    # Add member
    resp = client.post(f'/api/hrms/teams/{team_id}/members', json={
        'employee_id': admin_emp.id,
        'is_lead': True
    }, headers={'Authorization': f'Bearer {admin_token}'})
    
    assert resp.status_code == 201
    assert TeamMember.query.filter_by(team_id=team_id, employee_id=admin_emp.id).first() is not None

def test_attendance_workflow(client, admin_token):
    # Need to be logged in as an employee to clock in
    # Login as admin user (who has an employee record via conftest)
    resp = client.post('/api/auth/login', json={
        'email': 'admin@hirehub.com',
        'password': 'adminpassword'
    })
    token = resp.json['token']

    # Clock In
    resp = client.post('/api/hrms/attendance/clock-in', headers={'Authorization': f'Bearer {token}'})
    assert resp.status_code == 201
    assert resp.json['status'] == 'Present'

    # Clock Out
    resp = client.post('/api/hrms/attendance/clock-out', headers={'Authorization': f'Bearer {token}'})
    assert resp.status_code == 200
    assert resp.json['clock_out'] is not None

def test_leave_approval(client, admin_token):
    # Login as admin
    resp = client.post('/api/auth/login', json={
        'email': 'admin@hirehub.com',
        'password': 'adminpassword'
    })
    token = resp.json['token']
    admin_emp = Employee.query.filter_by(first_name="Admin").first()

    # Init balances
    client.post('/api/hrms/leaves/init-balances', headers={'Authorization': f'Bearer {token}'})

    # Apply Leave
    start = date.today() + timedelta(days=5)
    end = start + timedelta(days=2)
    resp = client.post('/api/hrms/leaves', json={
        'leave_type': 'Sick',
        'start_date': start.isoformat(),
        'end_date': end.isoformat(),
        'reason': 'Medical'
    }, headers={'Authorization': f'Bearer {token}'})
    
    assert resp.status_code == 201
    leave_id = resp.json['id']

    # Approve Leave
    resp = client.patch(f'/api/hrms/leaves/{leave_id}/review', json={
        'status': 'Approved',
        'remarks': 'Get well soon'
    }, headers={'Authorization': f'Bearer {token}'})
    
    assert resp.status_code == 200
    assert resp.json['status'] == 'Approved'
    
    # Check balance deduction
    balance = LeaveBalance.query.filter_by(employee_id=admin_emp.id, leave_type='Sick').first()
    assert balance.total_used == 3 # 3 days total
