"""Authentication routes"""
from flask import Blueprint, request, jsonify
from utils.validators import validate_email, validate_password, validate_name
from utils.helpers import generate_jwt, format_user_response
from utils.errors import ValidationError
from models import user
from middleware.auth_middleware import token_required

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    POST /api/auth/register
    Create new teacher account
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'Request body is required'}), 400

        # Extract fields
        email = data.get('email', '').strip()
        password = data.get('password', '')
        name = data.get('name', '').strip()

        # Validate input
        validate_email(email)
        validate_password(password)
        validate_name(name)

        # Check if email already exists
        existing_user = user.find_by_email(email)
        if existing_user:
            return jsonify({'error': 'Email already exists'}), 400

        # Create user
        new_user = user.create_user(email, password, name)

        # Generate JWT token
        token = generate_jwt(new_user)

        # Format response
        return jsonify({
            'message': 'Account created successfully',
            'user': format_user_response(new_user),
            'token': token
        }), 201

    except ValidationError as e:
        return jsonify({'error': e.message}), 400
    except Exception as e:
        error_message = str(e)
        if 'Email already exists' in error_message:
            return jsonify({'error': 'Email already exists'}), 400
        return jsonify({'error': 'Server error'}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    POST /api/auth/login
    Authenticate teacher and return JWT token
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'Request body is required'}), 400

        # Extract fields
        email = data.get('email', '').strip()
        password = data.get('password', '')

        # Validate presence
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400

        # Find user by email
        found_user = user.find_by_email(email)

        if not found_user:
            return jsonify({'error': 'Invalid email or password'}), 401

        # Verify password
        if not user.verify_password(found_user['password_hash'], password):
            return jsonify({'error': 'Invalid email or password'}), 401

        # Generate JWT token
        token = generate_jwt(found_user)

        # Format response
        return jsonify({
            'message': 'Login successful',
            'user': format_user_response(found_user),
            'token': token
        }), 200

    except Exception as e:
        return jsonify({'error': 'Server error'}), 500


@auth_bp.route('/me', methods=['GET'])
@token_required
def get_current_user(current_user):
    """
    GET /api/auth/me
    Get current authenticated user details
    """
    try:
        return jsonify({
            'user': format_user_response(current_user)
        }), 200

    except Exception as e:
<<<<<<< HEAD
        return jsonify({'error': 'Server error'}), 500
=======
        return jsonify({'error': 'Server error'}), 500
>>>>>>> 32989f47432449cbf85d306e8d421ab8734efed7
