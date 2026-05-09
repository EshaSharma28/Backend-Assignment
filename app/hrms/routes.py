from datetime import datetime, date, timezone
from flask import request, jsonify, g
from app.hrms import hrms_bp
from app.extensions import db
from app.models.hrms import (
    Employee, DailyAttendance, LeaveRequest, 
    LeaveBalance, Team, TeamMember
)
from app.hrms.schemas import (
    EmployeeSchema, DailyAttendanceSchema, 
    LeaveRequestSchema, LeaveBalanceSchema,
    TeamSchema, TeamMemberSchema
)
from app.auth.decorators import require_auth, require_permission

employee_schema = EmployeeSchema()
employees_schema = EmployeeSchema(many=True)
attendance_schema = DailyAttendanceSchema()
attendances_schema = DailyAttendanceSchema(many=True)
leave_request_schema = LeaveRequestSchema()
leave_requests_schema = LeaveRequestSchema(many=True)
team_schema = TeamSchema()
teams_schema = TeamSchema(many=True)
team_member_schema = TeamMemberSchema()

@hrms_bp.route('/employees', methods=['GET'])
@require_auth
@require_permission('attendance', 'can_read')
def get_employees():
    employees = Employee.query.all()
    return jsonify(employees_schema.dump(employees)), 200

@hrms_bp.route('/employees/<int:id>', methods=['GET'])
@require_auth
@require_permission('attendance', 'can_read')
def get_employee(id):
    employee = db.session.get(Employee, id)
    if not employee:
        return jsonify({'message': 'Employee not found'}), 404
    return jsonify(employee_schema.dump(employee)), 200

@hrms_bp.route('/employees', methods=['POST'])
@require_auth
@require_permission('all', 'can_write')
def create_employee():
    data = request.get_json()
    errors = employee_schema.validate(data)
    if errors:
        return jsonify(errors), 400
    
    new_employee = Employee(
        user_id=data['user_id'],
        first_name=data['first_name'],
        last_name=data['last_name'],
        phone=data.get('phone'),
        department=data.get('department'),
        designation=data.get('designation'),
        date_of_joining=data['date_of_joining'],
        is_sales_agent=data.get('is_sales_agent', False),
        manager_id=data.get('manager_id')
    )
    
    db.session.add(new_employee)
    db.session.commit()
    
    return jsonify(employee_schema.dump(new_employee)), 201

@hrms_bp.route('/teams', methods=['GET'])
@require_auth
@require_permission('attendance', 'can_read')
def get_teams():
    teams = Team.query.all()
    return jsonify(teams_schema.dump(teams)), 200

@hrms_bp.route('/teams', methods=['POST'])
@require_auth
@require_permission('all', 'can_write')
def create_team():
    data = request.get_json()
    errors = team_schema.validate(data)
    if errors:
        return jsonify(errors), 400
    
    new_team = Team(
        name=data['name'],
        description=data.get('description')
    )
    
    db.session.add(new_team)
    db.session.commit()
    
    return jsonify(team_schema.dump(new_team)), 201

@hrms_bp.route('/teams/<int:team_id>/members', methods=['POST'])
@require_auth
@require_permission('all', 'can_write')
def add_team_member(team_id):
    team = db.session.get(Team, team_id)
    if not team:
        return jsonify({'message': 'Team not found'}), 404
    
    data = request.get_json()
    employee_id = data.get('employee_id')
    if not employee_id:
        return jsonify({'message': 'employee_id is required'}), 400
    
    # Check if already a member
    existing = TeamMember.query.filter_by(team_id=team_id, employee_id=employee_id).first()
    if existing:
        return jsonify({'message': 'Employee is already a member of this team'}), 400
    
    member = TeamMember(
        team_id=team_id,
        employee_id=employee_id,
        is_lead=data.get('is_lead', False)
    )
    
    db.session.add(member)
    db.session.commit()
    
    return jsonify(team_member_schema.dump(member)), 201

@hrms_bp.route('/attendance/clock-in', methods=['POST'])
@require_auth
@require_permission('attendance', 'can_write')
def clock_in():
    if not g.current_user.employee:
        return jsonify({'message': 'User has no employee profile'}), 400
    
    employee_id = g.current_user.employee.id
    today = date.today()
    
    # Check if already clocked in
    existing = DailyAttendance.query.filter_by(employee_id=employee_id, date=today).first()
    if existing:
        return jsonify({'message': 'Already clocked in for today'}), 400
    
    new_attendance = DailyAttendance(
        employee_id=employee_id,
        date=today,
        clock_in=datetime.now(timezone.utc),
        status='Present'
    )
    
    db.session.add(new_attendance)
    db.session.commit()
    
    return jsonify(attendance_schema.dump(new_attendance)), 201

@hrms_bp.route('/attendance/clock-out', methods=['POST'])
@require_auth
@require_permission('attendance', 'can_write')
def clock_out():
    if not g.current_user.employee:
        return jsonify({'message': 'User has no employee profile'}), 400
    
    employee_id = g.current_user.employee.id
    today = date.today()
    
    attendance = DailyAttendance.query.filter_by(employee_id=employee_id, date=today).first()
    if not attendance:
        return jsonify({'message': 'No clock-in record found for today'}), 404
    
    if attendance.clock_out:
        return jsonify({'message': 'Already clocked out for today'}), 400
    
    attendance.clock_out = datetime.now(timezone.utc)
    
    # Calculate total hours
    diff = attendance.clock_out - attendance.clock_in
    attendance.total_hours = round(diff.total_seconds() / 3600, 2)
    
    db.session.commit()
    
    return jsonify(attendance_schema.dump(attendance)), 200

@hrms_bp.route('/leaves', methods=['POST'])
@require_auth
@require_permission('leave', 'can_write')
def apply_leave():
    if not g.current_user.employee:
        return jsonify({'message': 'User has no employee profile'}), 400
    
    data = request.get_json()
    errors = leave_request_schema.validate(data)
    if errors:
        return jsonify(errors), 400
    
    # Validate dates
    start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
    end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
    
    if end_date < start_date:
        return jsonify({'message': 'End date cannot be before start date'}), 400
    
    total_days = (end_date - start_date).days + 1
    
    new_leave = LeaveRequest(
        employee_id=g.current_user.employee.id,
        leave_type=data['leave_type'],
        start_date=start_date,
        end_date=end_date,
        total_days=total_days,
        reason=data.get('reason'),
        status='Pending'
    )
    
    db.session.add(new_leave)
    db.session.commit()
    
    return jsonify(leave_request_schema.dump(new_leave)), 201

@hrms_bp.route('/leaves/init-balances', methods=['POST'])
@require_auth
@require_permission('leave', 'can_write')
def initialize_balances():
    if not g.current_user.employee:
        return jsonify({'message': 'User has no employee profile'}), 400
    
    employee_id = g.current_user.employee.id
    year = date.today().year
    leave_types = ['Casual', 'Sick', 'Earned', 'Unpaid']
    
    for lt in leave_types:
        existing = LeaveBalance.query.filter_by(
            employee_id=employee_id, leave_type=lt, year=year
        ).first()
        
        if not existing:
            # Default quotas
            quota = 12 if lt != 'Unpaid' else 99
            balance = LeaveBalance(
                employee_id=employee_id,
                leave_type=lt,
                year=year,
                total_allocated=quota,
                total_used=0
            )
            db.session.add(balance)
    
    db.session.commit()
    return jsonify({'message': f'Leave balances initialized for {year}'}), 201

@hrms_bp.route('/leaves', methods=['GET'])
@require_auth
@require_permission('leave', 'can_read')
def get_leaves():
    # HR/Admin can see all, Employees see their own
    if g.current_user.role.name in ['Admin', 'HR']:
        leaves = LeaveRequest.query.all()
    else:
        if not g.current_user.employee:
            return jsonify([]), 200
        leaves = LeaveRequest.query.filter_by(employee_id=g.current_user.employee.id).all()
        
    return jsonify(leave_requests_schema.dump(leaves)), 200

@hrms_bp.route('/leaves/<int:id>/review', methods=['PATCH'])
@require_auth
@require_permission('leave', 'can_write')
def review_leave(id):
    leave_req = db.session.get(LeaveRequest, id)
    if not leave_req:
        return jsonify({'message': 'Leave request not found'}), 404
    
    if leave_req.status != 'Pending':
        return jsonify({'message': 'Leave request is already processed'}), 400
    
    # Extra security: Only Admin or HR can review leaves
    if g.current_user.role.name not in ['Admin', 'HR']:
        return jsonify({'message': 'Forbidden: Only HR or Admin can review leaves'}), 403
    
    data = request.get_json()
    new_status = data.get('status') # 'Approved' or 'Rejected'
    if new_status not in ['Approved', 'Rejected']:
        return jsonify({'message': 'Invalid status. Use Approved or Rejected'}), 400
    
    leave_req.status = new_status
    leave_req.reviewed_by = g.current_user.employee.id if g.current_user.employee else None
    leave_req.reviewed_at = datetime.now(timezone.utc)
    leave_req.remarks = data.get('remarks')
    
    # If approved, deduct from balance
    if new_status == 'Approved':
        balance = LeaveBalance.query.filter_by(
            employee_id=leave_req.employee_id,
            leave_type=leave_req.leave_type,
            year=leave_req.start_date.year
        ).first()
        
        if not balance:
            return jsonify({'message': f'No leave balance found for {leave_req.leave_type} in {leave_req.start_date.year}'}), 400
        
        if balance.remaining < leave_req.total_days:
            return jsonify({'message': 'Insufficient leave balance'}), 400
        
        balance.total_used += leave_req.total_days
    
    db.session.commit()
    
    return jsonify(leave_request_schema.dump(leave_req)), 200
