"""Input validation functions"""
import re
from bson import ObjectId
from email_validator import validate_email as validate_email_lib, EmailNotValidError
from utils.errors import ValidationError


def validate_email(email):
    """Validate email format"""
    if not email:
        raise ValidationError("Email is required")

    try:
        validate_email_lib(email)
        return True
    except EmailNotValidError:
        raise ValidationError("Invalid email format")


def validate_password(password):
    """
    Validate password meets requirements:
    - Minimum 8 characters
    - At least 1 uppercase letter
    - At least 1 lowercase letter
    - At least 1 number
    """
    if not password:
        raise ValidationError("Password is required")

    if len(password) < 8:
        raise ValidationError("Password must be at least 8 characters")

    if not re.search(r'[A-Z]', password):
        raise ValidationError("Password must contain at least 1 uppercase letter")

    if not re.search(r'[a-z]', password):
        raise ValidationError("Password must contain at least 1 lowercase letter")

    if not re.search(r'\d', password):
        raise ValidationError("Password must contain at least 1 number")

    return True


def validate_name(name):
    """Validate name field"""
    if not name:
        raise ValidationError("Name is required")

    if len(name) < 2:
        raise ValidationError("Name must be at least 2 characters")

    if len(name) > 100:
        raise ValidationError("Name must not exceed 100 characters")

    return True


def validate_file_size(file, max_mb):
    """Check if file size is within limit"""
    # Get file size by seeking to end
    file.seek(0, 2)
    file_size = file.tell()
    file.seek(0)  # Reset to beginning

    max_bytes = max_mb * 1024 * 1024

    if file_size > max_bytes:
        raise ValidationError(f"File size exceeds {max_mb}MB limit")

    return True


def validate_pdf(file):
    """
    Validate that file is a PDF
    Checks both content type and magic bytes
    """
    # Check content type
    if file.content_type != 'application/pdf':
        raise ValidationError("Only PDF files are allowed")

    # Check magic bytes (PDF files start with %PDF)
    file.seek(0)
    header = file.read(4)
    file.seek(0)  # Reset to beginning

    if header != b'%PDF':
        raise ValidationError("Invalid PDF file")

    return True


def validate_object_id(id_string):
    """Validate MongoDB ObjectId format"""
    if not id_string:
        raise ValidationError("ID is required")

    if not ObjectId.is_valid(id_string):
        raise ValidationError("Invalid ID format")

    return True


def validate_pagination(page, limit, max_limit=100):
    """
    Validate and sanitize pagination parameters
    Returns tuple of (page, limit)
    """
    try:
        page = int(page) if page else 1
        limit = int(limit) if limit else 20
    except (ValueError, TypeError):
        raise ValidationError("Invalid pagination parameters")

    if page < 1:
        page = 1

    if limit < 1:
        limit = 20

    if limit > max_limit:
        limit = max_limit

    return page, limit


def validate_required_fields(data, required_fields):
    """
    Validate that all required fields are present in data

    Args:
        data: Dictionary to validate
        required_fields: List of required field names
    """
    missing_fields = [field for field in required_fields if field not in data or not data[field]]

    if missing_fields:
        raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")

    return True
