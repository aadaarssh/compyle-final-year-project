"""GridFS file operations wrapper"""
from bson import ObjectId
from gridfs import GridFS
from gridfs.errors import NoFile
from config.config import get_config
from utils.errors import FileStorageError, ValidationError

config = get_config()

# GridFS instance will be injected
fs = None


def init_gridfs(database):
    """Initialize GridFS instance"""
    global fs
    fs = GridFS(database)


def upload_file(file_stream, filename, content_type, metadata=None):
    """
    Save file to GridFS

    Args:
        file_stream: File-like object
        filename: Original filename
        content_type: MIME type
        metadata: Optional dictionary with additional file metadata

    Returns:
        GridFS file_id (ObjectId)

    Raises:
        FileStorageError: If upload fails
        ValidationError: If file exceeds size limit
    """
    try:
        # Check file size
        file_stream.seek(0, 2)
        file_size = file_stream.tell()
        file_stream.seek(0)

        max_size = config.MAX_FILE_SIZE_MB * 1024 * 1024
        if file_size > max_size:
            raise ValidationError(f"File size exceeds {config.MAX_FILE_SIZE_MB}MB limit")

        # Upload to GridFS
        file_id = fs.put(
            file_stream,
            filename=filename,
            content_type=content_type,
            metadata=metadata or {}
        )

        return file_id

    except ValidationError:
        raise
    except Exception as e:
        raise FileStorageError(f"Failed to upload file: {str(e)}")


def download_file(file_id):
    """
    Retrieve file from GridFS

    Args:
        file_id: GridFS file ObjectId or string

    Returns:
        GridFS file object (GridOut)

    Raises:
        FileStorageError: If file not found or download fails
    """
    try:
        if isinstance(file_id, str):
            file_id = ObjectId(file_id)

        grid_out = fs.get(file_id)
        return grid_out

    except NoFile:
        raise FileStorageError("File not found")
    except Exception as e:
        raise FileStorageError(f"Failed to download file: {str(e)}")


def delete_file(file_id):
    """
    Remove file from GridFS

    Args:
        file_id: GridFS file ObjectId or string

    Returns:
        True if deleted

    Raises:
        FileStorageError: If deletion fails
    """
    try:
        if isinstance(file_id, str):
            file_id = ObjectId(file_id)

        fs.delete(file_id)
        return True

    except NoFile:
        # File doesn't exist, consider it deleted
        return True
    except Exception as e:
        raise FileStorageError(f"Failed to delete file: {str(e)}")


def get_file_metadata(file_id):
    """
    Get file information without downloading content

    Args:
        file_id: GridFS file ObjectId or string

    Returns:
        Dictionary with file metadata

    Raises:
        FileStorageError: If file not found
    """
    try:
        if isinstance(file_id, str):
            file_id = ObjectId(file_id)

        grid_out = fs.get(file_id)

        return {
            'filename': grid_out.filename,
            'length': grid_out.length,
            'content_type': grid_out.content_type,
            'upload_date': grid_out.upload_date,
            'metadata': grid_out.metadata
        }

    except NoFile:
        raise FileStorageError("File not found")
    except Exception as e:
        raise FileStorageError(f"Failed to retrieve file metadata: {str(e)}")


def file_exists(file_id):
    """
    Check if file exists in GridFS

    Args:
        file_id: GridFS file ObjectId or string

    Returns:
        True if file exists, False otherwise
    """
    try:
        if isinstance(file_id, str):
            file_id = ObjectId(file_id)

        return fs.exists(file_id)
    except Exception:
        return False
