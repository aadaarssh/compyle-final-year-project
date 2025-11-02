"""Answer sheet routes"""
from flask import Blueprint, request, jsonify
from middleware.auth_middleware import token_required
from utils.validators import validate_pagination, validate_pdf, validate_file_size
from utils.helpers import format_datetime, calculate_pagination
from utils.errors import ValidationError
from models import answer_sheet, evaluation_scheme, evaluation_result
from services import gridfs_service
from config.config import get_config

config = get_config()

answer_sheets_bp = Blueprint('answer_sheets', __name__)


@answer_sheets_bp.route('/bulk', methods=['POST'])
@token_required
def bulk_upload(current_user):
    """
    POST /api/answer-sheets/bulk
    Upload multiple student answer sheets for evaluation
    """
    try:
        # Get evaluation_scheme_id from form
        scheme_id = request.form.get('evaluation_scheme_id', '').strip()

        if not scheme_id:
            return jsonify({'error': 'Evaluation scheme ID required'}), 400

        # Verify scheme exists and belongs to user
        scheme = evaluation_scheme.find_by_id(scheme_id)

        if not scheme:
            return jsonify({'error': 'Evaluation scheme not found'}), 404

        if str(scheme['teacher_id']) != str(current_user['_id']):
            return jsonify({'error': 'Access denied'}), 403

        # Get uploaded files
        if 'answer_sheets' not in request.files:
            return jsonify({'error': 'No files uploaded'}), 400

        files = request.files.getlist('answer_sheets')

        if not files or len(files) == 0:
            return jsonify({'error': 'No files uploaded'}), 400

        if len(files) > config.MAX_BULK_UPLOAD:
            return jsonify({'error': f'Maximum {config.MAX_BULK_UPLOAD} files allowed'}), 400

        # Get optional student names and roll numbers
        student_names = request.form.getlist('student_names')
        student_rolls = request.form.getlist('student_roll_numbers')

        # Process each file
        uploaded_sheets = []
        failed_files = []

        for i, file in enumerate(files):
            try:
                if file.filename == '':
                    continue

                # Validate PDF
                validate_pdf(file)
                validate_file_size(file, config.MAX_FILE_SIZE_MB)

                # Upload to GridFS
                file_id = gridfs_service.upload_file(
                    file_stream=file.stream,
                    filename=file.filename,
                    content_type='application/pdf',
                    metadata={
                        'uploader_id': str(current_user['_id']),
                        'file_type': 'student_answer',
                        'evaluation_scheme_id': str(scheme_id)
                    }
                )

                # Get student info if provided
                student_name = student_names[i] if i < len(student_names) else None
                student_roll = student_rolls[i] if i < len(student_rolls) else None

                # Create answer sheet document
                sheet = answer_sheet.create_answer_sheet(
                    teacher_id=current_user['_id'],
                    scheme_id=scheme_id,
                    file_id=file_id,
                    student_name=student_name,
                    student_roll=student_roll
                )

                uploaded_sheets.append({
                    'id': str(sheet['_id']),
                    'filename': file.filename,
                    'student_name': sheet.get('student_name'),
                    'status': sheet['status']
                })

            except ValidationError as e:
                failed_files.append({
                    'filename': file.filename,
                    'error': e.message
                })
            except Exception as e:
                failed_files.append({
                    'filename': file.filename,
                    'error': str(e)
                })

        return jsonify({
            'message': 'Answer sheets uploaded successfully',
            'uploaded': len(uploaded_sheets),
            'failed': len(failed_files),
            'answer_sheets': uploaded_sheets,
            'errors': failed_files if failed_files else None
        }), 201

    except ValidationError as e:
        return jsonify({'error': e.message}), 400
    except Exception as e:
        print(f"Error uploading answer sheets: {str(e)}")
        return jsonify({'error': 'Server error'}), 500


@answer_sheets_bp.route('', methods=['GET'])
@token_required
def list_answer_sheets(current_user):
    """
    GET /api/answer-sheets
    List all answer sheets for authenticated teacher
    """
    try:
        # Get query parameters
        page = request.args.get('page', 1)
        limit = request.args.get('limit', 50)
        scheme_id = request.args.get('evaluation_scheme_id')
        status = request.args.get('status')

        page, limit = validate_pagination(page, limit)

        # Build filters
        filters = {}
        if scheme_id:
            filters['evaluation_scheme_id'] = scheme_id
        if status:
            filters['status'] = status

        # Get answer sheets
        sheets = answer_sheet.find_by_teacher(current_user['_id'], filters, page, limit)
        total = answer_sheet.count_by_teacher(current_user['_id'], filters)

        # Format response
        sheets_data = []
        for sheet in sheets:
            # Get evaluation scheme info
            scheme = evaluation_scheme.find_by_id(sheet['evaluation_scheme_id'])

            sheet_data = {
                'id': str(sheet['_id']),
                'evaluation_scheme': {
                    'id': str(scheme['_id']),
                    'title': scheme['title']
                } if scheme else None,
                'student_name': sheet.get('student_name'),
                'student_roll_number': sheet.get('student_roll_number'),
                'status': sheet['status'],
                'uploaded_at': format_datetime(sheet['uploaded_at']),
                'processed_at': format_datetime(sheet.get('processed_at'))
            }

            # If completed, include score
            if sheet['status'] == 'completed':
                result = evaluation_result.find_by_answer_sheet(sheet['_id'])
                if result:
                    sheet_data['score'] = result['total_score']
                    sheet_data['max_score'] = result['max_score']
                    sheet_data['percentage'] = result['percentage']

            sheets_data.append(sheet_data)

        # Calculate pagination
        pagination = calculate_pagination(total, page, limit)

        return jsonify({
            'answer_sheets': sheets_data,
            'pagination': pagination
        }), 200

    except Exception as e:
        print(f"Error listing answer sheets: {str(e)}")
<<<<<<< HEAD
        return jsonify({'error': 'Server error'}), 500
=======
        return jsonify({'error': 'Server error'}), 500


@answer_sheets_bp.route('/<sheet_id>', methods=['GET'])
@token_required
def get_answer_sheet(current_user, sheet_id):
    """
    GET /api/answer-sheets/:id
    Get specific answer sheet details
    """
    try:
        # Fetch answer sheet
        sheet = answer_sheet.find_by_id(sheet_id)

        if not sheet:
            return jsonify({'error': 'Answer sheet not found'}), 404

        # Verify ownership
        if str(sheet['teacher_id']) != str(current_user['_id']):
            return jsonify({'error': 'Access denied'}), 403

        # Get evaluation scheme
        scheme = evaluation_scheme.find_by_id(sheet['evaluation_scheme_id'])

        # Format response
        response_data = {
            'id': str(sheet['_id']),
            'evaluation_scheme': {
                'id': str(scheme['_id']),
                'title': scheme['title'],
                'total_marks': scheme['total_marks']
            } if scheme else None,
            'student_name': sheet.get('student_name'),
            'student_roll_number': sheet.get('student_roll_number'),
            'answer_file_url': f"/api/files/{sheet['answer_file_id']}",
            'extracted_text': sheet.get('extracted_text'),
            'status': sheet['status'],
            'uploaded_at': format_datetime(sheet['uploaded_at']),
            'processed_at': format_datetime(sheet.get('processed_at'))
        }

        # If completed, include evaluation result
        if sheet['status'] == 'completed':
            result = evaluation_result.find_by_answer_sheet(sheet['_id'])
            if result:
                response_data['evaluation_result'] = {
                    'total_score': result['total_score'],
                    'max_score': result['max_score'],
                    'percentage': result['percentage'],
                    'semantic_similarity_score': result['semantic_similarity_score'],
                    'keyword_match_score': result['keyword_match_score'],
                    'detailed_feedback': result['detailed_feedback'],
                    'evaluated_at': format_datetime(result['evaluated_at']),
                    'evaluation_time_seconds': result['evaluation_time_seconds']
                }

        return jsonify({'answer_sheet': response_data}), 200

    except Exception as e:
        print(f"Error getting answer sheet: {str(e)}")
        return jsonify({'error': 'Server error'}), 500


@answer_sheets_bp.route('/<sheet_id>', methods=['DELETE'])
@token_required
def delete_answer_sheet(current_user, sheet_id):
    """
    DELETE /api/answer-sheets/:id
    Delete answer sheet and associated evaluation result
    """
    try:
        # Fetch answer sheet
        sheet = answer_sheet.find_by_id(sheet_id)

        if not sheet:
            return jsonify({'error': 'Answer sheet not found'}), 404

        # Verify ownership
        if str(sheet['teacher_id']) != str(current_user['_id']):
            return jsonify({'error': 'Access denied'}), 403

        # Delete answer PDF from GridFS
        gridfs_service.delete_file(sheet['answer_file_id'])

        # Delete evaluation result if exists
        evaluation_result.delete_by_answer_sheet(sheet['_id'])

        # Delete answer sheet document
        answer_sheet.delete_sheet(sheet_id)

        return jsonify({'message': 'Answer sheet deleted successfully'}), 200

    except Exception as e:
        print(f"Error deleting answer sheet: {str(e)}")
        return jsonify({'error': 'Server error'}), 500
>>>>>>> 32989f47432449cbf85d306e8d421ab8734efed7
