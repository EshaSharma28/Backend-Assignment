from marshmallow import Schema, fields, validate
from app.models.hrms import LeaveType, LeaveStatus

class EmployeeSchema(Schema):
    id = fields.Integer(dump_only=True)
    user_id = fields.UUID(required=True)
    first_name = fields.String(required=True, validate=validate.Length(min=1, max=100))
    last_name = fields.String(required=True, validate=validate.Length(min=1, max=100))
    phone = fields.String(validate=validate.Length(max=20))
    department = fields.String(validate=validate.Length(max=100))
    designation = fields.String(validate=validate.Length(max=100))
    date_of_joining = fields.Date(required=True)
    is_sales_agent = fields.Boolean(default=False)
    manager_id = fields.Integer(allow_none=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    full_name = fields.String(dump_only=True)

class TeamSchema(Schema):
    id = fields.Integer(dump_only=True)
    name = fields.String(required=True, validate=validate.Length(min=1, max=100))
    description = fields.String()
    created_at = fields.DateTime(dump_only=True)

class TeamMemberSchema(Schema):
    id = fields.Integer(dump_only=True)
    team_id = fields.Integer(required=True)
    employee_id = fields.Integer(required=True)
    is_lead = fields.Boolean(default=False)
    joined_at = fields.DateTime(dump_only=True)

class DailyAttendanceSchema(Schema):
    id = fields.Integer(dump_only=True)
    employee_id = fields.Integer(required=True)
    date = fields.Date(required=True)
    clock_in = fields.DateTime(allow_none=True)
    clock_out = fields.DateTime(allow_none=True)
    total_hours = fields.Decimal(dump_only=True, as_string=True)
    status = fields.String(validate=validate.OneOf(['Present', 'Absent', 'Half-Day']))
    created_at = fields.DateTime(dump_only=True)

class LeaveRequestSchema(Schema):
    id = fields.Integer(dump_only=True)
    employee_id = fields.Integer(dump_only=True)
    leave_type = fields.String(required=True, validate=validate.OneOf(['Casual', 'Sick', 'Earned', 'Unpaid']))
    start_date = fields.Date(required=True)
    end_date = fields.Date(required=True)
    total_days = fields.Integer(dump_only=True)
    reason = fields.String()
    status = fields.String(dump_only=True, validate=validate.OneOf(['Pending', 'Approved', 'Rejected', 'Cancelled']))
    reviewed_by = fields.Integer(dump_only=True, allow_none=True)
    reviewed_at = fields.DateTime(dump_only=True, allow_none=True)
    remarks = fields.String(dump_only=True)
    created_at = fields.DateTime(dump_only=True)

class LeaveBalanceSchema(Schema):
    id = fields.Integer(dump_only=True)
    employee_id = fields.Integer(dump_only=True)
    leave_type = fields.String(required=True, validate=validate.OneOf(['Casual', 'Sick', 'Earned', 'Unpaid']))
    year = fields.Integer(required=True)
    total_allocated = fields.Integer(required=True)
    total_used = fields.Integer(default=0)
    remaining = fields.Integer(dump_only=True)
