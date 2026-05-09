from flask import Blueprint, request, jsonify
from datetime import datetime, timezone
from app.extensions import db
from app.models.auth import User, Role
from app.auth.schemas import (
    LoginSchema, RegisterSchema, UserSchema,
    UserRoleUpdateSchema, UserStatusUpdateSchema,
)
from app.auth.utils import hash_password, check_password, generate_jwt
from app.auth.decorators import require_auth, require_permission

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

login_schema = LoginSchema()
register_schema = RegisterSchema()
user_schema = UserSchema()
users_schema = UserSchema(many=True)
role_update_schema = UserRoleUpdateSchema()
status_update_schema = UserStatusUpdateSchema()

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    errors = register_schema.validate(data)
    if errors:
        return jsonify(errors), 400

    email = data['email']
    password = data['password']
    # Security: Do not allow role_id from request. Default to the Sales role.
    # Only an Admin should be able to promote a user role via a separate endpoint.
    sales_role = Role.query.filter_by(name='Sales').first()
    if not sales_role:
        return jsonify({'message': 'Default Sales role is not configured'}), 500

    # Check if user exists
    if User.query.filter_by(email=email).first():
        return jsonify({'message': 'User with this email already exists'}), 409

    hashed_password = hash_password(password)
    new_user = User(
        email=email,
        password_hash=hashed_password,
        role_id=sales_role.id
    )
    
    db.session.add(new_user)
    db.session.commit()

    return jsonify({
        'message': 'User registered successfully',
        'user': user_schema.dump(new_user)
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    errors = login_schema.validate(data)
    if errors:
        return jsonify(errors), 400

    user = User.query.filter_by(email=data['email']).first()
    
    if not user or not check_password(data['password'], user.password_hash):
        return jsonify({'message': 'Invalid email or password'}), 401

    if not user.is_active:
        return jsonify({'message': 'Account is disabled'}), 403

    user.last_login = datetime.now(timezone.utc)
    db.session.commit()

    token = generate_jwt(user.id, user.role_id)

    return jsonify({
        'message': 'Login successful',
        'token': token,
        'user': user_schema.dump(user)
    }), 200

@auth_bp.route('/me', methods=['GET'])
@require_auth
def get_me():
    from flask import g
    user = g.current_user
    return jsonify(user_schema.dump(user)), 200


@auth_bp.route('/users', methods=['GET'])
@require_auth
@require_permission('all', 'can_read')
def list_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return jsonify(users_schema.dump(users)), 200


@auth_bp.route('/users/<uuid:user_id>/role', methods=['PATCH'])
@require_auth
@require_permission('all', 'can_write')
def update_user_role(user_id):
    data = request.get_json()
    errors = role_update_schema.validate(data)
    if errors:
        return jsonify(errors), 400

    if not data.get('role_id') and not data.get('role'):
        return jsonify({'message': 'role_id or role is required'}), 400

    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404

    if data.get('role_id'):
        role = db.session.get(Role, data['role_id'])
    else:
        role = Role.query.filter_by(name=data['role']).first()

    if not role:
        return jsonify({'message': 'Role not found'}), 404

    user.role_id = role.id
    db.session.commit()
    return jsonify(user_schema.dump(user)), 200


@auth_bp.route('/users/<uuid:user_id>/status', methods=['PATCH'])
@require_auth
@require_permission('all', 'can_write')
def update_user_status(user_id):
    data = request.get_json()
    errors = status_update_schema.validate(data)
    if errors:
        return jsonify(errors), 400

    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404

    user.is_active = data['is_active']
    db.session.commit()
    return jsonify(user_schema.dump(user)), 200
