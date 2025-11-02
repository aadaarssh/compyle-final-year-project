"""Custom exception classes for the application"""


class ValidationError(Exception):
    """Raised when input validation fails"""
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class AuthenticationError(Exception):
    """Raised when login or token authentication fails"""
    def __init__(self, message, status_code=401):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class AuthorizationError(Exception):
    """Raised when access is denied"""
    def __init__(self, message, status_code=403):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class OCRException(Exception):
    """Raised when OpenAI Vision API operations fail"""
    def __init__(self, message, status_code=500):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class NLPException(Exception):
    """Raised when NLP processing fails"""
    def __init__(self, message, status_code=500):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class FileStorageError(Exception):
    """Raised when GridFS operations fail"""
    def __init__(self, message, status_code=500):
        super().__init__(message)
        self.message = message
<<<<<<< HEAD
        self.status_code = status_code
=======
        self.status_code = status_code
>>>>>>> 32989f47432449cbf85d306e8d421ab8734efed7
