import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration class"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dev-jwt-secret')
    MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/answer_evaluation_system')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')

    # File upload limits
    MAX_FILE_SIZE_MB = int(os.getenv('MAX_FILE_SIZE_MB', 10))
    MAX_BULK_UPLOAD = int(os.getenv('MAX_BULK_UPLOAD', 50))

    # JWT configuration
    JWT_EXPIRATION_DAYS = int(os.getenv('JWT_EXPIRATION_DAYS', 7))

    # NLP model configuration
    SENTENCE_TRANSFORMER_MODEL = os.getenv('SENTENCE_TRANSFORMER_MODEL', 'all-MiniLM-L6-v2')
    SPACY_MODEL = os.getenv('SPACY_MODEL', 'en_core_web_sm')

    # Scoring weights
    SEMANTIC_SIMILARITY_WEIGHT = float(os.getenv('SEMANTIC_SIMILARITY_WEIGHT', 0.6))
    KEYWORD_MATCH_WEIGHT = float(os.getenv('KEYWORD_MATCH_WEIGHT', 0.4))

    # OpenAI API configuration
    OPENAI_VISION_MODEL = os.getenv('OPENAI_VISION_MODEL', 'gpt-4-vision-preview')
    OPENAI_TEXT_MODEL = os.getenv('OPENAI_TEXT_MODEL', 'gpt-4')
    OPENAI_MAX_RETRIES = int(os.getenv('OPENAI_MAX_RETRIES', 3))
    OPENAI_RETRY_DELAY_SECONDS = int(os.getenv('OPENAI_RETRY_DELAY_SECONDS', 2))


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}


def get_config():
    """Get configuration based on FLASK_ENV"""
    env = os.getenv('FLASK_ENV', 'development')
    return config.get(env, config['default'])