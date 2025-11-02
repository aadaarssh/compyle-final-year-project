"""Evaluation routes"""
from flask import Blueprint, request, jsonify
from middleware.auth_middleware import token_required
from utils.validators import validate_pagination
from utils.helpers import format_datetime, calculate_pagination
from models import answer_sheet, evaluation_scheme, evaluation_result

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

        # For now, return a success message (background processing would be added later)
        return jsonify({
            'message': 'Evaluation started',
            'answer_sheet_id': answer_sheet_id,
            'status': 'processing'
        }), 202

    except Exception as e:
        print(f"Error triggering evaluation: {str(e)}")
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