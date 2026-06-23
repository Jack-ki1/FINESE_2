"""
FINESE2 - Authentication Routes
JWT-based authentication with registration, login, and token management.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    get_jwt
)
from app.models.user import User
from app.extensions import db
from datetime import datetime, timedelta

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register a new user account.
    
    Expected JSON body:
    {
        "username": "string",
        "email": "string",
        "password": "string"
    }
    
    Returns:
        201: User created successfully
        400: Missing required fields
        409: Username or email already exists
    """
    data = request.get_json()
    
    # Validate input
    if not data:
        return jsonify({'error': 'No input data provided'}), 400
    
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    
    if not username or not email or not password:
        return jsonify({'error': 'Missing required fields: username, email, and password are required'}), 400
    
    # Validate username length
    if len(username) < 3 or len(username) > 80:
        return jsonify({'error': 'Username must be between 3 and 80 characters'}), 400
    
    # Validate email format (basic check)
    if '@' not in email or '.' not in email:
        return jsonify({'error': 'Invalid email format'}), 400
    
    # Validate password strength
    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters long'}), 400
    
    # Check if username already exists
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 409
    
    # Check if email already exists
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already registered'}), 409
    
    # Create new user
    try:
        user = User(
            username=username,
            email=email.lower(),  # Normalize email to lowercase
            role='user'  # Default role
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'message': 'User created successfully',
            'user': user.to_dict(include_email=True)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create user', 'details': str(e)}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Authenticate user and return JWT tokens.
    
    Expected JSON body:
    {
        "username": "string",
        "password": "string"
    }
    
    Returns:
        200: Login successful with access and refresh tokens
        400: Missing credentials
        401: Invalid credentials
        403: Account deactivated
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No input data provided'}), 400
    
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    if not username or not password:
        return jsonify({'error': 'Missing credentials: username and password are required'}), 400
    
    # Find user by username
    user = User.query.filter_by(username=username).first()
    
    # Verify credentials
    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid username or password'}), 401
    
    # Check if account is active
    if not user.is_active:
        return jsonify({'error': 'Account is deactivated. Please contact support.'}), 403
    
    # Update last login timestamp
    user.last_login = datetime.utcnow()
    db.session.commit()
    
    # Create JWT tokens
    additional_claims = {'role': user.role}
    access_token = create_access_token(
        identity=user.id,
        additional_claims=additional_claims,
        expires_delta=timedelta(hours=1)
    )
    refresh_token = create_refresh_token(
        identity=user.id,
        additional_claims=additional_claims
    )
    
    return jsonify({
        'message': 'Login successful',
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': user.to_dict(include_email=True)
    }), 200


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """
    Refresh an expired access token using a valid refresh token.
    
    Returns:
        200: New access token
        401: Invalid or expired refresh token
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user or not user.is_active:
        return jsonify({'error': 'User not found or inactive'}), 401
    
    # Create new access token
    additional_claims = {'role': user.role}
    access_token = create_access_token(
        identity=current_user_id,
        additional_claims=additional_claims,
        expires_delta=timedelta(hours=1)
    )
    
    return jsonify({
        'access_token': access_token
    }), 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """
    Get current authenticated user information.
    
    Returns:
        200: User information
        401: Not authenticated
        404: User not found
    """
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    if not user.is_active:
        return jsonify({'error': 'Account is deactivated'}), 403
    
    return jsonify({
        'user': user.to_dict(include_email=True)
    }), 200


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    Logout current user (client should discard tokens).
    
    Note: In production, you might want to implement token blacklisting.
    
    Returns:
        200: Logout successful
    """
    # For now, just acknowledge logout
    # In production, add token to blacklist using JWT extended's blacklist feature
    return jsonify({'message': 'Logged out successfully'}), 200


@auth_bp.route('/users/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    """
    Get user information by ID (requires authentication).
    
    Args:
        user_id: User ID to retrieve
        
    Returns:
        200: User information
        404: User not found
    """
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({
        'user': user.to_dict(include_email=False)
    }), 200


# Admin-only routes
@auth_bp.route('/admin/users', methods=['GET'])
@jwt_required()
def list_users():
    """
    List all users (admin only).
    
    Returns:
        200: List of users
        403: Not authorized
    """
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    if not current_user or not current_user.is_admin():
        return jsonify({'error': 'Admin access required'}), 403
    
    users = User.query.all()
    return jsonify({
        'users': [user.to_dict(include_email=True) for user in users],
        'total': len(users)
    }), 200


@auth_bp.route('/admin/users/<int:user_id>/deactivate', methods=['POST'])
@jwt_required()
def deactivate_user(user_id):
    """
    Deactivate a user account (admin only).
    
    Args:
        user_id: User ID to deactivate
        
    Returns:
        200: User deactivated
        403: Not authorized
        404: User not found
    """
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    
    if not current_user or not current_user.is_admin():
        return jsonify({'error': 'Admin access required'}), 403
    
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Prevent deactivating yourself
    if user.id == current_user_id:
        return jsonify({'error': 'Cannot deactivate your own account'}), 400
    
    user.is_active = False
    db.session.commit()
    
    return jsonify({'message': f'User {user.username} has been deactivated'}), 200
