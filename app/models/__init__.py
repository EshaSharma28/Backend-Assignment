"""
Models package — imports all modules so Alembic can detect them.
"""

from app.models.auth import Role, RolePermission, User          # noqa: F401
from app.models.hrms import (                                     # noqa: F401
    Employee, Team, TeamMember,
    DailyAttendance, LeaveRequest, LeaveBalance,
)
from app.models.crm import Lead, LeadStatusHistory, Interaction   # noqa: F401
from app.models.performance import PerformanceRecord              # noqa: F401
