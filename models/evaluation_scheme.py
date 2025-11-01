"""Evaluation scheme model and database operations"""
from datetime import datetime
from bson import ObjectId


# Database instance will be injected
db = None


def init_db(database):
    """Initialize database instance"""
    global db
    db = database


def create_scheme(teacher_id, title, subject, total_marks, file_id):
    """
    Create new evaluation scheme

    Args:
        teacher_id: Teacher's ObjectId or string
        title: Scheme title
        subject: Subject name (optional)
        total_marks: Maximum possible score
        file_id: GridFS file ID for model answer PDF

    Returns:
        Created scheme document
    """
    if isinstance(teacher_id, str):
        teacher_id = ObjectId(teacher_id)

    if isinstance(file_id, str):
        file_id = ObjectId(file_id)

    scheme_doc = {
        'teacher_id': teacher_id,
        'title': title,
        'subject': subject,
        'total_marks': total_marks,
        'model_answer_file_id': file_id,
        'extracted_text': None,
        'keywords': [],
        'status': 'processing',
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow()
    }

    result = db.evaluation_schemes.insert_one(scheme_doc)
    scheme_doc['_id'] = result.inserted_id
    return scheme_doc


def find_by_teacher(teacher_id, page=1, limit=20):
    """
    Get paginated list of schemes for a teacher

    Args:
        teacher_id: Teacher's ObjectId or string
        page: Page number (1-indexed)
        limit: Number of items per page

    Returns:
        List of scheme documents
    """
    if isinstance(teacher_id, str):
        teacher_id = ObjectId(teacher_id)

    skip = (page - 1) * limit

    schemes = list(db.evaluation_schemes.find(
        {'teacher_id': teacher_id}
    ).sort('created_at', -1).skip(skip).limit(limit))

    return schemes


def count_by_teacher(teacher_id):
    """
    Count total schemes for a teacher

    Args:
        teacher_id: Teacher's ObjectId or string

    Returns:
        Total count
    """
    if isinstance(teacher_id, str):
        teacher_id = ObjectId(teacher_id)

    return db.evaluation_schemes.count_documents({'teacher_id': teacher_id})


def find_by_id(scheme_id):
    """
    Find scheme by ID

    Args:
        scheme_id: Scheme ObjectId or string

    Returns:
        Scheme document or None
    """
    if isinstance(scheme_id, str):
        scheme_id = ObjectId(scheme_id)

    return db.evaluation_schemes.find_one({'_id': scheme_id})


def update_scheme(scheme_id, updates):
    """
    Update scheme fields

    Args:
        scheme_id: Scheme ObjectId or string
        updates: Dictionary of fields to update

    Returns:
        Updated scheme document or None
    """
    if isinstance(scheme_id, str):
        scheme_id = ObjectId(scheme_id)

    updates['updated_at'] = datetime.utcnow()

    db.evaluation_schemes.update_one(
        {'_id': scheme_id},
        {'$set': updates}
    )

    return find_by_id(scheme_id)


def delete_scheme(scheme_id):
    """
    Delete scheme

    Args:
        scheme_id: Scheme ObjectId or string

    Returns:
        True if deleted, False if not found
    """
    if isinstance(scheme_id, str):
        scheme_id = ObjectId(scheme_id)

    result = db.evaluation_schemes.delete_one({'_id': scheme_id})
    return result.deleted_count > 0


def count_answer_sheets(scheme_id):
    """
    Count answer sheets associated with a scheme

    Args:
        scheme_id: Scheme ObjectId or string

    Returns:
        Count of answer sheets
    """
    if isinstance(scheme_id, str):
        scheme_id = ObjectId(scheme_id)

    return db.answer_sheets.count_documents({'evaluation_scheme_id': scheme_id})


def get_statistics(scheme_id):
    """
    Calculate statistics for scheme results

    Args:
        scheme_id: Scheme ObjectId or string

    Returns:
        Dictionary with statistics
    """
    if isinstance(scheme_id, str):
        scheme_id = ObjectId(scheme_id)

    # Aggregate results for this scheme
    pipeline = [
        {'$match': {'evaluation_scheme_id': scheme_id}},
        {'$group': {
            '_id': None,
            'total_evaluated': {'$sum': 1},
            'average_score': {'$avg': '$total_score'},
            'highest_score': {'$max': '$total_score'},
            'lowest_score': {'$min': '$total_score'},
            'average_percentage': {'$avg': '$percentage'}
        }}
    ]

    result = list(db.evaluation_results.aggregate(pipeline))

    if not result:
        return {
            'total_evaluated': 0,
            'average_score': 0,
            'highest_score': 0,
            'lowest_score': 0,
            'pass_rate': 0
        }

    stats = result[0]

    # Calculate pass rate (assuming 50% is passing)
    pass_count = db.evaluation_results.count_documents({
        'evaluation_scheme_id': scheme_id,
        'percentage': {'$gte': 50}
    })

    pass_rate = (pass_count / stats['total_evaluated'] * 100) if stats['total_evaluated'] > 0 else 0

    return {
        'total_evaluated': stats['total_evaluated'],
        'average_score': round(stats['average_score'], 2) if stats['average_score'] else 0,
        'highest_score': stats['highest_score'] or 0,
        'lowest_score': stats['lowest_score'] or 0,
        'pass_rate': round(pass_rate, 2)
    }
