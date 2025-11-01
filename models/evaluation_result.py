"""Evaluation result model and database operations"""
from datetime import datetime
from bson import ObjectId


# Database instance will be injected
db = None


def init_db(database):
    """Initialize database instance"""
    global db
    db = database


def create_result(answer_sheet_id, scheme_id, scores, feedback):
    """
    Create evaluation result

    Args:
        answer_sheet_id: Answer sheet ObjectId or string
        scheme_id: Evaluation scheme ObjectId or string
        scores: Dictionary with scoring data
        feedback: AI-generated feedback text

    Returns:
        Created evaluation result document
    """
    if isinstance(answer_sheet_id, str):
        answer_sheet_id = ObjectId(answer_sheet_id)

    if isinstance(scheme_id, str):
        scheme_id = ObjectId(scheme_id)

    result_doc = {
        'answer_sheet_id': answer_sheet_id,
        'evaluation_scheme_id': scheme_id,
        'total_score': scores['total_score'],
        'max_score': scores['max_score'],
        'percentage': scores['percentage'],
        'semantic_similarity_score': scores['semantic_similarity_score'],
        'keyword_match_score': scores['keyword_match_score'],
        'detailed_feedback': feedback,
        'evaluated_at': datetime.utcnow(),
        'evaluation_time_seconds': scores.get('evaluation_time', 0)
    }

    result = db.evaluation_results.insert_one(result_doc)
    result_doc['_id'] = result.inserted_id
    return result_doc


def find_by_answer_sheet(sheet_id):
    """
    Get evaluation result for specific answer sheet

    Args:
        sheet_id: Answer sheet ObjectId or string

    Returns:
        Evaluation result document or None
    """
    if isinstance(sheet_id, str):
        sheet_id = ObjectId(sheet_id)

    return db.evaluation_results.find_one({'answer_sheet_id': sheet_id})


def find_by_scheme(scheme_id, page=1, limit=50, sort_by='date_desc'):
    """
    Get paginated list of results for an evaluation scheme

    Args:
        scheme_id: Evaluation scheme ObjectId or string
        page: Page number (1-indexed)
        limit: Number of items per page
        sort_by: Sorting option ('score_desc', 'score_asc', 'date_desc', 'date_asc')

    Returns:
        List of evaluation result documents
    """
    if isinstance(scheme_id, str):
        scheme_id = ObjectId(scheme_id)

    # Determine sort field and order
    sort_mapping = {
        'score_desc': ('total_score', -1),
        'score_asc': ('total_score', 1),
        'date_desc': ('evaluated_at', -1),
        'date_asc': ('evaluated_at', 1)
    }

    sort_field, sort_order = sort_mapping.get(sort_by, ('evaluated_at', -1))

    skip = (page - 1) * limit

    results = list(db.evaluation_results.find(
        {'evaluation_scheme_id': scheme_id}
    ).sort(sort_field, sort_order).skip(skip).limit(limit))

    return results


def count_by_scheme(scheme_id):
    """
    Count total results for an evaluation scheme

    Args:
        scheme_id: Evaluation scheme ObjectId or string

    Returns:
        Total count
    """
    if isinstance(scheme_id, str):
        scheme_id = ObjectId(scheme_id)

    return db.evaluation_results.count_documents({'evaluation_scheme_id': scheme_id})


def calculate_statistics(scheme_id):
    """
    Calculate aggregate statistics for scheme results

    Args:
        scheme_id: Evaluation scheme ObjectId or string

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


def update_result(result_id, updates):
    """
    Update result fields

    Args:
        result_id: Result ObjectId or string
        updates: Dictionary of fields to update

    Returns:
        Updated result document or None
    """
    if isinstance(result_id, str):
        result_id = ObjectId(result_id)

    db.evaluation_results.update_one(
        {'_id': result_id},
        {'$set': updates}
    )

    return db.evaluation_results.find_one({'_id': result_id})


def delete_result(result_id):
    """
    Delete evaluation result

    Args:
        result_id: Result ObjectId or string

    Returns:
        True if deleted, False if not found
    """
    if isinstance(result_id, str):
        result_id = ObjectId(result_id)

    result = db.evaluation_results.delete_one({'_id': result_id})
    return result.deleted_count > 0


def delete_by_answer_sheet(sheet_id):
    """
    Delete evaluation result by answer sheet ID

    Args:
        sheet_id: Answer sheet ObjectId or string

    Returns:
        True if deleted, False if not found
    """
    if isinstance(sheet_id, str):
        sheet_id = ObjectId(sheet_id)

    result = db.evaluation_results.delete_one({'answer_sheet_id': sheet_id})
    return result.deleted_count > 0
