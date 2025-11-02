"""Evaluation scheme routes"""
from flask import Blueprint, request, jsonify
from middleware.auth_middleware import token_required
<<<<<<< HEAD
from utils.validators import validate_pagination, validate_pdf, validate_file_size
from utils.helpers import format_datetime, calculate_pagination
from utils.errors import ValidationError
from models import evaluation_scheme
from services import gridfs_service
=======
from utils.validators import validate_pagination, validate_pdf, validate_file_size, validate_required_fields
from utils.helpers import format_datetime, calculate_pagination
from utils.errors import ValidationError, AuthorizationError
from models import evaluation_scheme
from services import gridfs_service
from services.background_tasks import process_model_answer
>>>>>>> 32989f47432449cbf85d306e8d421ab8734efed7
from config.config import get_config

config = get_config()

evaluation_schemes_bp = Blueprint('evaluation_schemes', __name__)


@evaluation_schemes_bp.route('', methods=['POST'])
@token_required
def create_scheme(current_user):
    """
    POST /api/evaluation-schemes
    Create new evaluation scheme with model answer PDF
    """
    try:
        # Validate multipart form data
        if 'model_answer' not in request.files:
            return jsonify({'error': 'PDF file is required'}), 400

        model_answer_file = request.files['model_answer']

        if model_answer_file.filename == '':
            return jsonify({'error': 'PDF file is required'}), 400

        # Get form data
        title = request.form.get('title', '').strip()
        subject = request.form.get('subject', '').strip()
        total_marks = request.form.get('total_marks', '')

        # Validate required fields
        if not title:
            return jsonify({'error': 'Title is required'}), 400

        if not total_marks:
            return jsonify({'error': 'Total marks is required'}), 400

        try:
            total_marks = int(total_marks)
            if total_marks <= 0:
                return jsonify({'error': 'Total marks must be positive'}), 400
        except ValueError:
            return jsonify({'error': 'Total marks must be a valid number'}), 400

        # Validate PDF file
        validate_pdf(model_answer_file)
        validate_file_size(model_answer_file, config.MAX_FILE_SIZE_MB)

        # Upload PDF to GridFS
        file_id = gridfs_service.upload_file(
            file_stream=model_answer_file.stream,
            filename=model_answer_file.filename,
            content_type='application/pdf',
            metadata={
                'uploader_id': str(current_user['_id']),
                'file_type': 'model_answer'
            }
        )

        # Create evaluation scheme
        scheme = evaluation_scheme.create_scheme(
            teacher_id=current_user['_id'],
            title=title,
            subject=subject if subject else None,
            total_marks=total_marks,
            file_id=file_id
        )

<<<<<<< HEAD
=======
        # Trigger background task to process model answer
        process_model_answer.delay(str(scheme['_id']))

>>>>>>> 32989f47432449cbf85d306e8d421ab8734efed7
        # Format response
        return jsonify({
            'message': 'Evaluation scheme created successfully',
            'scheme': {
                'id': str(scheme['_id']),
                'title': scheme['title'],
                'subject': scheme.get('subject'),
                'total_marks': scheme['total_marks'],
<<<<<<< HEAD
                'status': scheme.get('status', 'processing'),
=======
                'status': scheme['status'],
>>>>>>> 32989f47432449cbf85d306e8d421ab8734efed7
                'created_at': format_datetime(scheme['created_at'])
            }
        }), 201

    except ValidationError as e:
        return jsonify({'error': e.message}), 400
    except Exception as e:
        print(f"Error creating scheme: {str(e)}")
        return jsonify({'error': 'Server error'}), 500


@evaluation_schemes_bp.route('', methods=['GET'])
@token_required
def list_schemes(current_user):
    """
    GET /api/evaluation-schemes
    List all evaluation schemes for authenticated teacher
    """
    try:
        # Get pagination parameters
        page = request.args.get('page', 1)
        limit = request.args.get('limit', 20)

        page, limit = validate_pagination(page, limit)

        # Get schemes
        schemes = evaluation_scheme.find_by_teacher(current_user['_id'], page, limit)
        total = evaluation_scheme.count_by_teacher(current_user['_id'])

        # Format response with answer sheet counts
        schemes_data = []
        for scheme in schemes:
            answer_sheets_count = evaluation_scheme.count_answer_sheets(scheme['_id'])

            schemes_data.append({
                'id': str(scheme['_id']),
                'title': scheme['title'],
                'subject': scheme.get('subject'),
                'total_marks': scheme['total_marks'],
                'status': scheme.get('status', 'processing'),
                'answer_sheets_count': answer_sheets_count,
                'created_at': format_datetime(scheme['created_at'])
            })

        # Calculate pagination metadata
        pagination = calculate_pagination(total, page, limit)

        return jsonify({
            'schemes': schemes_data,
            'pagination': pagination
        }), 200

    except Exception as e:
        print(f"Error listing schemes: {str(e)}")
        return jsonify({'error': 'Server error'}), 500


@evaluation_schemes_bp.route('/<scheme_id>', methods=['GET'])
@token_required
def get_scheme(current_user, scheme_id):
    """
    GET /api/evaluation-schemes/:id
    Get specific evaluation scheme details
    """
    try:
        # Fetch scheme
        scheme = evaluation_scheme.find_by_id(scheme_id)

        if not scheme:
            return jsonify({'error': 'Evaluation scheme not found'}), 404

        # Verify ownership
        if str(scheme['teacher_id']) != str(current_user['_id']):
            return jsonify({'error': 'Access denied'}), 403

        # Get answer sheets count
        answer_sheets_count = evaluation_scheme.count_answer_sheets(scheme['_id'])

        # Format response
        response_data = {
            'id': str(scheme['_id']),
            'title': scheme['title'],
            'subject': scheme.get('subject'),
            'total_marks': scheme['total_marks'],
            'status': scheme.get('status', 'processing'),
            'extracted_text': scheme.get('extracted_text'),
            'keywords': scheme.get('keywords', []),
            'model_answer_url': f"/api/files/{scheme['model_answer_file_id']}",
            'answer_sheets_count': answer_sheets_count,
            'created_at': format_datetime(scheme['created_at'])
        }

        return jsonify({'scheme': response_data}), 200

    except Exception as e:
        print(f"Error getting scheme: {str(e)}")
        return jsonify({'error': 'Server error'}), 500


@evaluation_schemes_bp.route('/<scheme_id>', methods=['DELETE'])
@token_required
def delete_scheme(current_user, scheme_id):
    """
    DELETE /api/evaluation-schemes/:id
    Delete evaluation scheme and associated data
    """
    try:
        # Fetch scheme
        scheme = evaluation_scheme.find_by_id(scheme_id)

        if not scheme:
            return jsonify({'error': 'Evaluation scheme not found'}), 404

        # Verify ownership
        if str(scheme['teacher_id']) != str(current_user['_id']):
            return jsonify({'error': 'Access denied'}), 403

        # Check for associated answer sheets
        answer_sheets_count = evaluation_scheme.count_answer_sheets(scheme['_id'])

        if answer_sheets_count > 0:
            return jsonify({
                'error': 'Cannot delete scheme with existing answer sheets. Delete answer sheets first.'
            }), 400

        # Delete model answer PDF from GridFS
        gridfs_service.delete_file(scheme['model_answer_file_id'])

        # Delete scheme document
        evaluation_scheme.delete_scheme(scheme_id)

        return jsonify({'message': 'Evaluation scheme deleted successfully'}), 200

    except Exception as e:
        print(f"Error deleting scheme: {str(e)}")
<<<<<<< HEAD
        return jsonify({'error': 'Server error'}), 500
=======
        return jsonify({'error': 'Server error'}), 500
>>>>>>> 32989f47432449cbf85d306e8d421ab8734efed7
