"""
Module 1 — Auth / Core Models
Tables: roles, role_permissions, users
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Enum as PgEnum
from sqlalchemy.dialects.postgresql import UUID

from app.extensions import db

# ──────────────────────────────────────────────
# PostgreSQL ENUMs
# ──────────────────────────────────────────────
RoleType = PgEnum(
    'Admin', 'HR', 'Sales',
    name='role_type',
    create_type=True,
)

PermissionScope = PgEnum(
    'attendance', 'leave', 'leads', 'performance', 'all',
    name='permission_scope',
    create_type=True,
)


# ──────────────────────────────────────────────
# roles
# ──────────────────────────────────────────────
class Role(db.Model):
    """
    Defines the three system roles: Admin, HR, Sales.
    Each user is assigned exactly one role, which drives RBAC.
    """
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(RoleType, nullable=False, unique=True,
                     comment='Admin | HR | Sales')
    description = db.Column(db.Text, nullable=True,
                            comment='Human-readable purpose of this role')
    created_at = db.Column(db.DateTime(timezone=True),
                           default=lambda: datetime.now(timezone.utc))

    # Relationships
    permissions = db.relationship('RolePermission', back_populates='role',
                                  cascade='all, delete-orphan', lazy='selectin')
    users = db.relationship('User', back_populates='role', lazy='dynamic')

    def __repr__(self):
        return f'<Role {self.name}>'


# ──────────────────────────────────────────────
# role_permissions
# ──────────────────────────────────────────────
class RolePermission(db.Model):
    """
    Maps each role to granular CRUD permissions per module scope.
    Flask middleware queries this table to authorize every request.
    Example row: role=HR, scope=attendance, can_read=True, can_write=True
    """
    __tablename__ = 'role_permissions'
    __table_args__ = (
        db.UniqueConstraint('role_id', 'scope', name='uq_role_scope'),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    scope = db.Column(PermissionScope, nullable=False,
                      comment='Module-level access gate')
    can_read = db.Column(db.Boolean, default=False, nullable=False)
    can_write = db.Column(db.Boolean, default=False, nullable=False)
    can_delete = db.Column(db.Boolean, default=False, nullable=False)

    # Relationships
    role = db.relationship('Role', back_populates='permissions')

    def __repr__(self):
        return f'<RolePermission role={self.role_id} scope={self.scope}>'


# ──────────────────────────────────────────────
# users
# ──────────────────────────────────────────────
class User(db.Model):
    """
    Authentication-only table.
    Profile data lives in employees (HRMS module) linked via user_id FK.
    This separation keeps auth concerns isolated from HR data.
    """
    __tablename__ = 'users'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = db.Column(db.String(255), nullable=False, unique=True,
                      comment='Login credential')
    password_hash = db.Column(db.String(255), nullable=False,
                              comment='bcrypt hash — never store plaintext')
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False,
                        comment='RBAC assignment')
    is_active = db.Column(db.Boolean, default=True, nullable=False,
                          comment='Soft-disable without deleting')
    last_login = db.Column(db.DateTime(timezone=True), nullable=True,
                           comment='Audit trail')
    created_at = db.Column(db.DateTime(timezone=True),
                           default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime(timezone=True),
                           default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    role = db.relationship('Role', back_populates='users')
    employee = db.relationship('Employee', back_populates='user',
                               uselist=False, lazy='joined')

    def __repr__(self):
        return f'<User {self.email}>'
