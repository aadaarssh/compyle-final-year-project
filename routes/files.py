"""File download routes"""
from flask import Blueprint, send_file, jsonify
from middleware.auth_middleware import token_required
from services import gridfs_service
from utils.errors import FileStorageError
import io

files_bp = Blueprint('files', __name__)


@files_bp.route('/<file_id>', methods=['GET'])
@token_required
def download_file(current_user, file_id):
    """
    GET /api/files/:file_id
    Download PDF file from GridFS
    """
    try:
        # Get file metadata first
        metadata = gridfs_service.get_file_metadata(file_id)

        # Verify file belongs to current user
        uploader_id = metadata.get('metadata', {}).get('uploader_id')

        if not uploader_id or uploader_id != str(current_user['_id']):
            return jsonify({'error': 'Access denied'}), 403

        # Download file from GridFS
        grid_out = gridfs_service.download_file(file_id)

        # Read file content
        file_data = grid_out.read()

        # Create file-like object
        file_stream = io.BytesIO(file_data)

        # Return file with proper headers
        return send_file(
            file_stream,
            mimetype='application/pdf',
            as_attachment=False,
            download_name=metadata['filename']
        )

    except FileStorageError as e:
        return jsonify({'error': e.message}), 404
    except Exception as e:
        print(f"Error downloading file: {str(e)}")
<<<<<<< HEAD
        return jsonify({'error': 'Server error'}), 500
=======
        return jsonify({'error': 'Server error'}), 500
>>>>>>> 32989f47432449cbf85d306e8d421ab8734efed7
