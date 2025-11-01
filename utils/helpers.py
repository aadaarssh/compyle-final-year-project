"""Utility helper functions"""
import jwt
from datetime import datetime, timedelta
from config.config import get_config
from utils.errors import AuthenticationError

config = get_config()


def generate_jwt(user):
    """
    Generate JWT token with user payload

    Args:
        user: User document from MongoDB

    Returns:
        JWT token string
    """
    payload = {
        'user_id': str(user['_id']),
        'email': user['email'],
        'exp': datetime.utcnow() + timedelta(days=config.JWT_EXPIRATION_DAYS)
    }

    token = jwt.encode(payload, config.JWT_SECRET_KEY, algorithm='HS256')
    return token


def decode_jwt(token):
    """
    Decode and verify JWT token

    Args:
        token: JWT token string

    Returns:
        Decoded payload dictionary

    Raises:
        AuthenticationError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, config.JWT_SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token has expired")
    except jwt.InvalidTokenError:
        raise AuthenticationError("Invalid token")


def format_user_response(user_doc):
    """
    Format user document for API response (remove sensitive fields)

    Args:
        user_doc: User document from MongoDB

    Returns:
        Formatted user dictionary
    """
    if not user_doc:
        return None

    return {
        'id': str(user_doc['_id']),
        'email': user_doc['email'],
        'name': user_doc['name'],
        'created_at': format_datetime(user_doc.get('created_at'))
    }


def format_datetime(dt):
    """
    Convert datetime to ISO string

    Args:
        dt: datetime object

    Returns:
        ISO formatted string or None
    """
    if dt is None:
        return None

    if isinstance(dt, datetime):
        return dt.isoformat() + 'Z'

    return str(dt)


def handle_mongo_error(error):
    """
    Parse MongoDB errors into user-friendly messages

    Args:
        error: MongoDB exception

    Returns:
        User-friendly error message
    """
    error_message = str(error)

    # Duplicate key error
    if 'E11000' in error_message or 'duplicate key' in error_message:
        if 'email' in error_message:
            return "Email already exists"
        return "Duplicate entry found"

    # Connection errors
    if 'connection' in error_message.lower():
        return "Database connection error"

    # Default
    return "Database error occurred"


def calculate_pagination(total, page, limit):
    """
    Calculate pagination metadata

    Args:
        total: Total number of items
        page: Current page number
        limit: Items per page

    Returns:
        Dictionary with pagination metadata
    """
    total_pages = (total + limit - 1) // limit  # Ceiling division

    return {
        'page': page,
        'limit': limit,
        'total': total,
        'pages': total_pages
    }
