"""User model and database operations"""
import bcrypt
from datetime import datetime
from bson import ObjectId
from pymongo import errors


# Database instance will be injected
db = None


def init_db(database):
    """Initialize database instance"""
    global db
    db = database


def create_user(email, password, name):
    """
    Create new user with hashed password

    Args:
        email: User email
        password: Plain text password
        name: User full name

    Returns:
        Created user document

    Raises:
        Exception: If email already exists or database error
    """
    # Hash password with bcrypt (10 salt rounds)
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(10))

    user_doc = {
        'email': email,
        'password_hash': password_hash,
        'name': name,
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow()
    }

    try:
        result = db.users.insert_one(user_doc)
        user_doc['_id'] = result.inserted_id
        return user_doc
    except errors.DuplicateKeyError:
        raise Exception("Email already exists")


def find_by_email(email):
    """
    Find user by email

    Args:
        email: User email

    Returns:
        User document or None if not found
    """
    return db.users.find_one({'email': email})


def find_by_id(user_id):
    """
    Find user by ID

    Args:
        user_id: User ObjectId or string

    Returns:
        User document or None if not found
    """
    if isinstance(user_id, str):
        user_id = ObjectId(user_id)

    return db.users.find_one({'_id': user_id})


def verify_password(stored_hash, password):
    """
    Verify password against stored hash

    Args:
        stored_hash: Bcrypt hashed password from database
        password: Plain text password to verify

    Returns:
        True if password matches, False otherwise
    """
    return bcrypt.checkpw(password.encode('utf-8'), stored_hash)


def update_user(user_id, updates):
    """
    Update user fields

    Args:
        user_id: User ObjectId or string
        updates: Dictionary of fields to update

    Returns:
        Updated user document or None
    """
    if isinstance(user_id, str):
        user_id = ObjectId(user_id)

    updates['updated_at'] = datetime.utcnow()

    db.users.update_one(
        {'_id': user_id},
        {'$set': updates}
    )

    return find_by_id(user_id)


def delete_user(user_id):
    """
    Delete user from database

    Args:
        user_id: User ObjectId or string

    Returns:
        True if deleted, False if not found
    """
    if isinstance(user_id, str):
        user_id = ObjectId(user_id)

    result = db.users.delete_one({'_id': user_id})
<<<<<<< HEAD
    return result.deleted_count > 0
=======
    return result.deleted_count > 0
>>>>>>> 32989f47432449cbf85d306e8d421ab8734efed7
