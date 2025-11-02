"""JWT authentication middleware"""
from functools import wraps
from flask import request, jsonify
from utils.helpers import decode_jwt
from utils.errors import AuthenticationError
from models import user


def token_required(f):
    """
    Decorator for routes that require authentication

    Usage:
        @token_required
        def protected_route(current_user):
            # current_user is the authenticated user document
            pass
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # Check if Authorization header is present
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']

            # Extract token from "Bearer <token>"
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]

        if not token:
            return jsonify({'error': 'Unauthorized'}), 401

        try:
            # Decode JWT token
            payload = decode_jwt(token)

            # Extract user_id from payload
            user_id = payload.get('user_id')

            if not user_id:
                return jsonify({'error': 'Unauthorized'}), 401

            # Fetch user from database
            current_user = user.find_by_id(user_id)

            if not current_user:
                return jsonify({'error': 'Unauthorized'}), 401

            # Pass current_user to the route function
            return f(current_user, *args, **kwargs)

        except AuthenticationError as e:
            return jsonify({'error': str(e.message)}), 401
        except Exception as e:
            return jsonify({'error': 'Unauthorized'}), 401

<<<<<<< HEAD
    return decorated
=======
    return decorated
>>>>>>> 32989f47432449cbf85d306e8d421ab8734efed7
