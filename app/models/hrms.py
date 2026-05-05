"""
Module 2 — HRMS Models
Tables: employees, teams, team_members, daily_attendance, leave_requests, leave_balances
"""

from datetime import datetime, timezone

from sqlalchemy import Enum as PgEnum, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID

from app.extensions import db

# ──────────────────────────────────────────────
# PostgreSQL ENUMs
# ──────────────────────────────────────────────
LeaveType = PgEnum(
    'Casual', 'Sick', 'Earned', 'Unpaid',
    name='leave_type',
    create_type=True,
)

LeaveStatus = PgEnum(
    'Pending', 'Approved', 'Rejected', 'Cancelled',
    name='leave_status',
    create_type=True,
)


# ──────────────────────────────────────────────
# employees
# ──────────────────────────────────────────────
class Employee(db.Model):
    """
    Core HRMS profile table.

    Design decisions:
    - Linked 1:1 to users via user_id (auth is separate from HR data).
    - is_sales_agent flag bridges HRMS ↔ CRM: only employees with this flag
      can be assigned leads in the CRM module.
    - manager_id is a self-referential FK for reporting hierarchies.
    """
    __tablename__ = 'employees'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'),
                        nullable=False, unique=True,
                        comment='1:1 link to auth table')
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    department = db.Column(db.String(100), nullable=True)
    designation = db.Column(db.String(100), nullable=True)
    date_of_joining = db.Column(db.Date, nullable=False)
    is_sales_agent = db.Column(
        db.Boolean, default=False, nullable=False,
        comment='CRM bridge — TRUE means this employee can be assigned leads'
    )
    manager_id = db.Column(
        db.Integer, db.ForeignKey('employees.id'), nullable=True,
        comment='Self-referential FK for reporting hierarchy'
    )
    created_at = db.Column(db.DateTime(timezone=True),
                           default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime(timezone=True),
                           default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    user = db.relationship('User', back_populates='employee')
    manager = db.relationship('Employee', remote_side=[id],
                              backref='direct_reports')
    team_memberships = db.relationship('TeamMember', back_populates='employee',
                                       cascade='all, delete-orphan')
    attendance_records = db.relationship('DailyAttendance',
                                         back_populates='employee',
                                         cascade='all, delete-orphan')
    leave_requests = db.relationship('LeaveRequest',
                                     back_populates='employee',
                                     foreign_keys='LeaveRequest.employee_id',
                                     cascade='all, delete-orphan')
    leave_balances = db.relationship('LeaveBalance',
                                     back_populates='employee',
                                     cascade='all, delete-orphan')
    assigned_leads = db.relationship('Lead', back_populates='assigned_agent',
                                     foreign_keys='Lead.assigned_agent_id')
    interactions = db.relationship('Interaction', back_populates='employee')
    performance_records = db.relationship('PerformanceRecord',
                                          back_populates='employee',
                                          cascade='all, delete-orphan')

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    def __repr__(self):
        return f'<Employee {self.full_name}>'


# ──────────────────────────────────────────────
# teams
# ──────────────────────────────────────────────
class Team(db.Model):
    """
    Organizational unit (e.g. "North Sales", "HR Operations").
    Employees are linked via the team_members junction table (M:N).
    """
    __tablename__ = 'teams'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True),
                           default=lambda: datetime.now(timezone.utc))

    # Relationships
    members = db.relationship('TeamMember', back_populates='team',
                              cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Team {self.name}>'


# ──────────────────────────────────────────────
# team_members  (junction table)
# ──────────────────────────────────────────────
class TeamMember(db.Model):
    """
    Many-to-many junction: an employee can belong to multiple teams.
    is_lead flags team managers for reporting.
    """
    __tablename__ = 'team_members'
    __table_args__ = (
        db.UniqueConstraint('team_id', 'employee_id',
                            name='uq_team_employee'),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'),
                            nullable=False)
    is_lead = db.Column(db.Boolean, default=False, nullable=False,
                        comment='TRUE = this employee leads the team')
    joined_at = db.Column(db.DateTime(timezone=True),
                          default=lambda: datetime.now(timezone.utc))

    # Relationships
    team = db.relationship('Team', back_populates='members')
    employee = db.relationship('Employee', back_populates='team_memberships')

    def __repr__(self):
        return f'<TeamMember team={self.team_id} emp={self.employee_id}>'


# ──────────────────────────────────────────────
# daily_attendance
# ──────────────────────────────────────────────
class DailyAttendance(db.Model):
    """
    Clock-in / clock-out tracking.

    RBAC: Only HR and Admin roles can read/write this table.
    Sales agents have no access — enforced via role_permissions(scope='attendance').
    """
    __tablename__ = 'daily_attendance'
    __table_args__ = (
        db.UniqueConstraint('employee_id', 'date',
                            name='uq_employee_date'),
        CheckConstraint(
            'clock_out IS NULL OR clock_out > clock_in',
            name='ck_clockout_after_clockin'
        ),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'),
                            nullable=False)
    date = db.Column(db.Date, nullable=False)
    clock_in = db.Column(db.DateTime(timezone=True), nullable=True)
    clock_out = db.Column(db.DateTime(timezone=True), nullable=True)
    total_hours = db.Column(
        db.Numeric(4, 2), nullable=True,
        comment='Computed on clock-out: (clock_out - clock_in) in hours'
    )
    status = db.Column(db.String(20), default='Present', nullable=False,
                       comment='Present | Absent | Half-Day')
    created_at = db.Column(db.DateTime(timezone=True),
                           default=lambda: datetime.now(timezone.utc))

    # Relationships
    employee = db.relationship('Employee', back_populates='attendance_records')

    def __repr__(self):
        return f'<Attendance emp={self.employee_id} date={self.date}>'


# ──────────────────────────────────────────────
# leave_requests
# ──────────────────────────────────────────────
class LeaveRequest(db.Model):
    """
    Leave request with full approval workflow.

    Approval tracking: reviewed_by + reviewed_at + remarks = complete audit trail.
    State transitions enforced by leave_status ENUM:
        Pending → Approved | Rejected
        Pending → Cancelled  (by the employee themselves)
    """
    __tablename__ = 'leave_requests'
    __table_args__ = (
        CheckConstraint('end_date >= start_date',
                        name='ck_leave_dates'),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'),
                            nullable=False, comment='The requester')
    leave_type = db.Column(LeaveType, nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    total_days = db.Column(db.Integer, nullable=False,
                           comment='Computed: (end_date - start_date + 1)')
    reason = db.Column(db.Text, nullable=True)
    status = db.Column(LeaveStatus, default='Pending', nullable=False)
    reviewed_by = db.Column(
        db.Integer, db.ForeignKey('employees.id'), nullable=True,
        comment='HR manager or direct manager who approved/rejected'
    )
    reviewed_at = db.Column(db.DateTime(timezone=True), nullable=True,
                            comment='When the decision was made')
    remarks = db.Column(db.Text, nullable=True,
                        comment="Reviewer's comments")
    created_at = db.Column(db.DateTime(timezone=True),
                           default=lambda: datetime.now(timezone.utc))

    # Relationships
    employee = db.relationship('Employee', back_populates='leave_requests',
                               foreign_keys=[employee_id])
    reviewer = db.relationship('Employee', foreign_keys=[reviewed_by])

    def __repr__(self):
        return f'<LeaveRequest emp={self.employee_id} {self.status}>'


# ──────────────────────────────────────────────
# leave_balances
# ──────────────────────────────────────────────
class LeaveBalance(db.Model):
    """
    Tracks annual leave quota per employee per leave type.
    total_used is decremented on approval; remaining is derived.
    """
    __tablename__ = 'leave_balances'
    __table_args__ = (
        db.UniqueConstraint('employee_id', 'leave_type', 'year',
                            name='uq_emp_leavetype_year'),
        CheckConstraint('total_used <= total_allocated',
                        name='ck_leave_balance'),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'),
                            nullable=False)
    leave_type = db.Column(LeaveType, nullable=False)
    year = db.Column(db.Integer, nullable=False, comment='Fiscal year')
    total_allocated = db.Column(db.Integer, nullable=False,
                                comment='Annual quota')
    total_used = db.Column(db.Integer, default=0, nullable=False)

    # Relationships
    employee = db.relationship('Employee', back_populates='leave_balances')

    @property
    def remaining(self):
        """Derived field: available balance."""
        return self.total_allocated - self.total_used

    def __repr__(self):
        return (f'<LeaveBalance emp={self.employee_id} '
                f'{self.leave_type} remaining={self.remaining}>')
