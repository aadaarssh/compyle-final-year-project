"""Answer sheet model and database operations"""
from datetime import datetime
from bson import ObjectId


# Database instance will be injected
db = None


def init_db(database):
    """Initialize database instance"""
    global db
    db = database


def create_answer_sheet(teacher_id, scheme_id, file_id, student_name=None, student_roll=None):
    """
    Create new answer sheet

    Args:
        teacher_id: Teacher's ObjectId or string
        scheme_id: Evaluation scheme ObjectId or string
        file_id: GridFS file ID for student answer PDF
        student_name: Student name (optional)
        student_roll: Student roll number (optional)

    Returns:
        Created answer sheet document
    """
    if isinstance(teacher_id, str):
        teacher_id = ObjectId(teacher_id)

    if isinstance(scheme_id, str):
        scheme_id = ObjectId(scheme_id)

    if isinstance(file_id, str):
        file_id = ObjectId(file_id)

    sheet_doc = {
        'evaluation_scheme_id': scheme_id,
        'teacher_id': teacher_id,
        'student_name': student_name,
        'student_roll_number': student_roll,
        'answer_file_id': file_id,
        'extracted_text': None,
        'status': 'pending',
        'uploaded_at': datetime.utcnow(),
        'processed_at': None,
        'error_message': None
    }

    result = db.answer_sheets.insert_one(sheet_doc)
    sheet_doc['_id'] = result.inserted_id
    return sheet_doc


def create_bulk(teacher_id, scheme_id, file_data_list):
    """
    Create multiple answer sheets

    Args:
        teacher_id: Teacher's ObjectId or string
        scheme_id: Evaluation scheme ObjectId or string
        file_data_list: List of dicts with {file_id, student_name, student_roll}

    Returns:
        List of created answer sheet documents
    """
    if isinstance(teacher_id, str):
        teacher_id = ObjectId(teacher_id)

    if isinstance(scheme_id, str):
        scheme_id = ObjectId(scheme_id)

    sheets = []
    for file_data in file_data_list:
        file_id = file_data['file_id']
        if isinstance(file_id, str):
            file_id = ObjectId(file_id)

        sheet_doc = {
            'evaluation_scheme_id': scheme_id,
            'teacher_id': teacher_id,
            'student_name': file_data.get('student_name'),
            'student_roll_number': file_data.get('student_roll'),
            'answer_file_id': file_id,
            'extracted_text': None,
            'status': 'pending',
            'uploaded_at': datetime.utcnow(),
            'processed_at': None,
            'error_message': None
        }
        sheets.append(sheet_doc)

    if sheets:
        result = db.answer_sheets.insert_many(sheets)
        for i, inserted_id in enumerate(result.inserted_ids):
            sheets[i]['_id'] = inserted_id

    return sheets


def find_by_teacher(teacher_id, filters=None, page=1, limit=50):
    """
    Get paginated list of answer sheets for a teacher

    Args:
        teacher_id: Teacher's ObjectId or string
        filters: Optional dict with filter criteria (evaluation_scheme_id, status)
        page: Page number (1-indexed)
        limit: Number of items per page

    Returns:
        List of answer sheet documents
    """
    if isinstance(teacher_id, str):
        teacher_id = ObjectId(teacher_id)

    query = {'teacher_id': teacher_id}

    if filters:
        if 'evaluation_scheme_id' in filters:
            scheme_id = filters['evaluation_scheme_id']
            if isinstance(scheme_id, str):
                scheme_id = ObjectId(scheme_id)
            query['evaluation_scheme_id'] = scheme_id

        if 'status' in filters:
            query['status'] = filters['status']

    skip = (page - 1) * limit

    sheets = list(db.answer_sheets.find(query).sort('uploaded_at', -1).skip(skip).limit(limit))

    return sheets


def count_by_teacher(teacher_id, filters=None):
    """
    Count total answer sheets for a teacher

    Args:
        teacher_id: Teacher's ObjectId or string
        filters: Optional dict with filter criteria

    Returns:
        Total count
    """
    if isinstance(teacher_id, str):
        teacher_id = ObjectId(teacher_id)

    query = {'teacher_id': teacher_id}

    if filters:
        if 'evaluation_scheme_id' in filters:
            scheme_id = filters['evaluation_scheme_id']
            if isinstance(scheme_id, str):
                scheme_id = ObjectId(scheme_id)
            query['evaluation_scheme_id'] = scheme_id

        if 'status' in filters:
            query['status'] = filters['status']

    return db.answer_sheets.count_documents(query)


def find_by_id(sheet_id):
    """
    Find answer sheet by ID

    Args:
        sheet_id: Answer sheet ObjectId or string

    Returns:
        Answer sheet document or None
    """
    if isinstance(sheet_id, str):
        sheet_id = ObjectId(sheet_id)

    return db.answer_sheets.find_one({'_id': sheet_id})


def update_status(sheet_id, status):
    """
    Update answer sheet status

    Args:
        sheet_id: Answer sheet ObjectId or string
        status: New status ('pending', 'processing', 'completed', 'failed')

    Returns:
        Updated answer sheet document or None
    """
    if isinstance(sheet_id, str):
        sheet_id = ObjectId(sheet_id)

    updates = {'status': status}

    if status == 'completed':
        updates['processed_at'] = datetime.utcnow()

    db.answer_sheets.update_one(
        {'_id': sheet_id},
        {'$set': updates}
    )

    return find_by_id(sheet_id)


def update_extracted_text(sheet_id, text):
    """
    Store OCR extracted text

    Args:
        sheet_id: Answer sheet ObjectId or string
        text: Extracted text from OCR

    Returns:
        Updated answer sheet document or None
    """
    if isinstance(sheet_id, str):
        sheet_id = ObjectId(sheet_id)

    db.answer_sheets.update_one(
        {'_id': sheet_id},
        {'$set': {'extracted_text': text}}
    )

    return find_by_id(sheet_id)


def set_error(sheet_id, error_message):
    """
    Set error message and failed status

    Args:
        sheet_id: Answer sheet ObjectId or string
        error_message: Error description

    Returns:
        Updated answer sheet document or None
    """
    if isinstance(sheet_id, str):
        sheet_id = ObjectId(sheet_id)

    db.answer_sheets.update_one(
        {'_id': sheet_id},
        {'$set': {
            'status': 'failed',
            'error_message': error_message,
            'processed_at': datetime.utcnow()
        }}
    )

    return find_by_id(sheet_id)


def delete_sheet(sheet_id):
    """
    Delete answer sheet

    Args:
        sheet_id: Answer sheet ObjectId or string

    Returns:
        True if deleted, False if not found
    """
    if isinstance(sheet_id, str):
        sheet_id = ObjectId(sheet_id)

    result = db.answer_sheets.delete_one({'_id': sheet_id})
    return result.deleted_count > 0
