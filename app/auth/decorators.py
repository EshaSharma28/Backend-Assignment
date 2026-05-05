from functools import wraps
from flask import request, jsonify
from app.auth.utils import decode_jwt
from app.models.auth import User, RolePermission
from app.extensions import db

def require_auth(f):
    """Decorator to require a valid JWT token."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'message': 'Missing or invalid token'}), 401
        
        token = auth_header.split(' ')[1]
        payload = decode_jwt(token)
        if not payload:
            return jsonify({'message': 'Token is invalid or expired'}), 401
        
        user_id = payload.get('sub')
        user = db.session.get(User, user_id)
        if not user or not user.is_active:
            return jsonify({'message': 'User not found or inactive'}), 401
        
        # Attach the current user to the request object context implicitly
        # but the common way is to pass it as kwargs or use flask.g
        from flask import g
        g.current_user = user
        return f(*args, **kwargs)
    return decorated

def require_permission(scope, action):
    """
    Decorator to check if the current user has the required permission.
    Must be used AFTER @require_auth.
    scope: e.g. 'attendance', 'leave', 'leads', 'performance'
    action: 'can_read', 'can_write', 'can_delete'
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flask import g
            user = getattr(g, 'current_user', None)
            if not user:
                return jsonify({'message': 'Authentication required'}), 401
            
            # Check global 'all' scope first
            global_perm = RolePermission.query.filter_by(role_id=user.role_id, scope='all').first()
            if global_perm and getattr(global_perm, action):
                return f(*args, **kwargs)
            
            # Check specific scope
            perm = RolePermission.query.filter_by(role_id=user.role_id, scope=scope).first()
            if not perm or not getattr(perm, action):
                return jsonify({'message': f'Forbidden: Missing {action} permission for {scope}'}), 403
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator
