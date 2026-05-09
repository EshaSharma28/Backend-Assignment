"""
Seed script — populates roles and role_permissions with default RBAC matrix.

Usage:
    flask shell
    >>> exec(open('seed.py').read())

Or run directly:
    python seed.py
"""

from app import create_app
from app.extensions import db
from app.models.auth import Role, RolePermission

RBAC_MATRIX = {
    'Admin': {
        'description': 'Full system access — all modules',
        'permissions': {
            'all':         {'can_read': True, 'can_write': True, 'can_delete': True},
        },
    },
    'HR': {
        'description': 'Attendance, leave, and read-only performance/lead access',
        'permissions': {
            'attendance':  {'can_read': True, 'can_write': True, 'can_delete': False},
            'leave':       {'can_read': True, 'can_write': True, 'can_delete': False},
            'performance': {'can_read': True, 'can_write': True, 'can_delete': False},
            'leads':       {'can_read': True, 'can_write': False, 'can_delete': False},
        },
    },
    'Sales': {
        'description': 'CRM lead management and self-service HRMS access',
        'permissions': {
            'leads':       {'can_read': True, 'can_write': True, 'can_delete': False},
            'attendance':  {'can_read': True, 'can_write': True, 'can_delete': False},
            'leave':       {'can_read': True, 'can_write': True, 'can_delete': False},
            'performance': {'can_read': True, 'can_write': False, 'can_delete': False},
        },
    },
}


def seed_rbac():
    """Insert roles and permissions if they don't already exist."""
    for role_name, config in RBAC_MATRIX.items():
        role = Role.query.filter_by(name=role_name).first()
        if not role:
            role = Role(name=role_name, description=config['description'])
            db.session.add(role)
            db.session.flush()  # get role.id before adding permissions

        for scope, perms in config['permissions'].items():
            existing = RolePermission.query.filter_by(
                role_id=role.id, scope=scope
            ).first()
            
            if existing:
                existing.can_read = perms['can_read']
                existing.can_write = perms['can_write']
                existing.can_delete = perms['can_delete']
            else:
                perm = RolePermission(
                    role_id=role.id,
                    scope=scope,
                    can_read=perms['can_read'],
                    can_write=perms['can_write'],
                    can_delete=perms['can_delete'],
                )
                db.session.add(perm)

    db.session.commit()
    print('✅ RBAC seed data inserted successfully.')


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        seed_rbac()
