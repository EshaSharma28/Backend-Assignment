from flask import Blueprint, request, jsonify
from datetime import datetime, timezone
from app.extensions import db
from app.models.auth import User, Role
from app.auth.schemas import LoginSchema, RegisterSchema, UserSchema
from app.auth.utils import hash_password, check_password, generate_jwt
from app.auth.decorators import require_auth

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

login_schema = LoginSchema()
register_schema = RegisterSchema()
user_schema = UserSchema()

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    errors = register_schema.validate(data)
    if errors:
        return jsonify(errors), 400

    email = data['email']
    password = data['password']
    # Security: Do not allow role_id from request. Default to 'Sales' role (ID 3)
    # Only an Admin should be able to promote a user role via a separate endpoint.
    sales_role_id = 3 

    # Check if user exists
    if User.query.filter_by(email=email).first():
        return jsonify({'message': 'User with this email already exists'}), 409

    hashed_password = hash_password(password)
    new_user = User(
        email=email,
        password_hash=hashed_password,
        role_id=sales_role_id
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
