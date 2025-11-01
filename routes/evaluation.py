"""Evaluation routes"""
from flask import Blueprint, request, jsonify
from middleware.auth_middleware import token_required
from utils.validators import validate_pagination
from utils.helpers import format_datetime, calculate_pagination
from models import answer_sheet, evaluation_scheme, evaluation_result
from services.background_tasks import process_evaluation, process_bulk_evaluation

evaluation_bp = Blueprint('evaluation', __name__)


@evaluation_bp.route('/<answer_sheet_id>', methods=['POST'])
@token_required
def trigger_evaluation(current_user, answer_sheet_id):
    """
    POST /api/evaluate/:answer_sheet_id
    Trigger AI evaluation for specific answer sheet
    """
    try:
        # Fetch answer sheet
        sheet = answer_sheet.find_by_id(answer_sheet_id)

        if not sheet:
            return jsonify({'error': 'Answer sheet not found'}), 404

        # Verify ownership
        if str(sheet['teacher_id']) != str(current_user['_id']):
            return jsonify({'error': 'Access denied'}), 403

        # Check if already evaluated
        existing_result = evaluation_result.find_by_answer_sheet(sheet['_id'])
        if existing_result:
            return jsonify({'error': 'Answer sheet already evaluated'}), 400

        # Check if evaluation scheme is ready
        scheme = evaluation_scheme.find_by_id(sheet['evaluation_scheme_id'])

        if not scheme:
            return jsonify({'error': 'Evaluation scheme not found'}), 404

        if scheme['status'] != 'ready':
            return jsonify({'error': 'Model answer still processing. Please wait.'}), 400

        # Trigger background evaluation task
        process_evaluation.delay(answer_sheet_id)

        return jsonify({
            'message': 'Evaluation started',
            'answer_sheet_id': answer_sheet_id,
            'status': 'processing'
        }), 202

    except Exception as e:
        print(f"Error triggering evaluation: {str(e)}")
        return jsonify({'error': 'Server error'}), 500


@evaluation_bp.route('/bulk', methods=['POST'])
@token_required
def trigger_bulk_evaluation(current_user):
    """
    POST /api/evaluate/bulk
    Trigger evaluation for multiple answer sheets
    """
    try:
        data = request.get_json()

        if not data or 'answer_sheet_ids' not in data:
            return jsonify({'error': 'answer_sheet_ids required'}), 400

        sheet_ids = data['answer_sheet_ids']

        if not isinstance(sheet_ids, list) or len(sheet_ids) == 0:
            return jsonify({'error': 'answer_sheet_ids must be a non-empty array'}), 400

        # Validate all IDs exist and belong to user
        valid_ids = []
        for sheet_id in sheet_ids:
            sheet = answer_sheet.find_by_id(sheet_id)

            if not sheet:
                continue

            if str(sheet['teacher_id']) != str(current_user['_id']):
                continue

            # Check if already evaluated
            existing_result = evaluation_result.find_by_answer_sheet(sheet['_id'])
            if existing_result:
                continue

            valid_ids.append(sheet_id)

        if not valid_ids:
            return jsonify({'error': 'No valid answer sheets to evaluate'}), 400

        # Trigger bulk evaluation
        process_bulk_evaluation.delay(valid_ids)

        return jsonify({
            'message': 'Bulk evaluation started',
            'processing': len(valid_ids),
            'failed': len(sheet_ids) - len(valid_ids)
        }), 202

    except Exception as e:
        print(f"Error triggering bulk evaluation: {str(e)}")
        return jsonify({'error': 'Server error'}), 500


@evaluation_bp.route('/results/<answer_sheet_id>', methods=['GET'])
@token_required
def get_result(current_user, answer_sheet_id):
    """
    GET /api/results/:answer_sheet_id
    Get evaluation result for specific answer sheet
    """
    try:
        # Fetch answer sheet
        sheet = answer_sheet.find_by_id(answer_sheet_id)

        if not sheet:
            return jsonify({'error': 'Answer sheet not found'}), 404

        # Verify ownership
        if str(sheet['teacher_id']) != str(current_user['_id']):
            return jsonify({'error': 'Access denied'}), 403

        # Fetch evaluation result
        result = evaluation_result.find_by_answer_sheet(sheet['_id'])

        if not result:
            return jsonify({'error': 'Evaluation not yet completed'}), 404

        # Get scheme info
        scheme = evaluation_scheme.find_by_id(sheet['evaluation_scheme_id'])

        # Format response
        response_data = {
            'id': str(result['_id']),
            'answer_sheet': {
                'id': str(sheet['_id']),
                'student_name': sheet.get('student_name'),
                'student_roll_number': sheet.get('student_roll_number')
            },
            'evaluation_scheme': {
                'id': str(scheme['_id']),
                'title': scheme['title']
            } if scheme else None,
            'total_score': result['total_score'],
            'max_score': result['max_score'],
            'percentage': result['percentage'],
            'semantic_similarity_score': result['semantic_similarity_score'],
            'keyword_match_score': result['keyword_match_score'],
            'detailed_feedback': result['detailed_feedback'],
            'evaluated_at': format_datetime(result['evaluated_at']),
            'evaluation_time_seconds': result['evaluation_time_seconds']
        }

        return jsonify({'result': response_data}), 200

    except Exception as e:
        print(f"Error getting result: {str(e)}")
        return jsonify({'error': 'Server error'}), 500


@evaluation_bp.route('/results/scheme/<scheme_id>', methods=['GET'])
@token_required
def get_scheme_results(current_user, scheme_id):
    """
    GET /api/results/scheme/:scheme_id
    Get all evaluation results for an evaluation scheme
    """
    try:
        # Fetch scheme
        scheme = evaluation_scheme.find_by_id(scheme_id)

        if not scheme:
            return jsonify({'error': 'Evaluation scheme not found'}), 404

        # Verify ownership
        if str(scheme['teacher_id']) != str(current_user['_id']):
            return jsonify({'error': 'Access denied'}), 403

        # Get pagination and sort parameters
        page = request.args.get('page', 1)
        limit = request.args.get('limit', 50)
        sort_by = request.args.get('sort_by', 'date_desc')

        page, limit = validate_pagination(page, limit)

        # Get results
        results = evaluation_result.find_by_scheme(scheme_id, page, limit, sort_by)
        total = evaluation_result.count_by_scheme(scheme_id)

        # Calculate statistics
        statistics = evaluation_result.calculate_statistics(scheme_id)

        # Format results with student info
        results_data = []
        for result in results:
            # Get answer sheet for student info
            sheet = answer_sheet.find_by_id(result['answer_sheet_id'])

            results_data.append({
                'id': str(result['_id']),
                'student_name': sheet.get('student_name') if sheet else None,
                'student_roll_number': sheet.get('student_roll_number') if sheet else None,
                'total_score': result['total_score'],
                'percentage': result['percentage'],
                'evaluated_at': format_datetime(result['evaluated_at'])
            })

        # Calculate pagination
        pagination = calculate_pagination(total, page, limit)

        return jsonify({
            'results': results_data,
            'statistics': statistics,
            'pagination': pagination
        }), 200

    except Exception as e:
        print(f"Error getting scheme results: {str(e)}")
        return jsonify({'error': 'Server error'}), 500
