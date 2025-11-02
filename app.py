"""Flask application entry point"""
import os
from flask import Flask, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from gridfs import GridFS
from config.config import get_config
from routes.auth import auth_bp
from routes.evaluation_schemes import evaluation_schemes_bp
from routes.answer_sheets import answer_sheets_bp
from routes.evaluation import evaluation_bp
from routes.files import files_bp
from services import gridfs_service, nlp_service
from models import user, evaluation_scheme, answer_sheet, evaluation_result

# Get configuration
config = get_config()

# Create Flask app
app = Flask(__name__)
app.config.from_object(config)

# Configure CORS
CORS(app, resources={
    r"/api/*": {
        "origins": [config.FRONTEND_URL],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "expose_headers": ["Content-Disposition"],
        "supports_credentials": True
    }
})

# Initialize MongoDB connection
mongo_client = MongoClient(config.MONGODB_URI)
db_name = config.MONGODB_URI.split('/')[-1].split('?')[0]
db = mongo_client[db_name]

# Initialize GridFS
gridfs_service.init_gridfs(db)

# Initialize models with database
user.init_db(db)
evaluation_scheme.init_db(db)
answer_sheet.init_db(db)
evaluation_result.init_db(db)

# Create indexes
print("Creating database indexes...")

# Users: unique index on email
db.users.create_index('email', unique=True)

# Evaluation schemes: index on teacher_id
db.evaluation_schemes.create_index('teacher_id')

# Answer sheets: indexes on evaluation_scheme_id, teacher_id, status
db.answer_sheets.create_index('evaluation_scheme_id')
db.answer_sheets.create_index('teacher_id')
db.answer_sheets.create_index('status')

# Evaluation results: unique index on answer_sheet_id, index on evaluation_scheme_id
db.evaluation_results.create_index('answer_sheet_id', unique=True)
db.evaluation_results.create_index('evaluation_scheme_id')

print("Database indexes created successfully")

# Initialize NLP models
print("Initializing NLP models...")
try:
    nlp_service.init_models()
    print("NLP models loaded successfully")
except Exception as e:
    print(f"Warning: Failed to initialize NLP models: {str(e)}")
    print("OCR and evaluation features will not work until models are loaded")

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(evaluation_schemes_bp, url_prefix='/api/evaluation-schemes')
app.register_blueprint(answer_sheets_bp, url_prefix='/api/answer-sheets')
app.register_blueprint(evaluation_bp, url_prefix='/api/evaluate')
app.register_blueprint(files_bp, url_prefix='/api/files')

# Root endpoint
@app.route('/')
def index():
    return jsonify({
        'message': 'Answer Sheet Evaluation System API',
        'version': '1.0',
        'status': 'running'
    })

# Health check endpoint
@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'database': 'connected',
        'nlp_models': 'loaded' if nlp_service.nlp_model else 'not loaded'
    })

# Error handlers
@app.errorhandler(400)
def bad_request(e):
    return jsonify({'error': 'Bad request'}), 400

@app.errorhandler(401)
def unauthorized(e):
    return jsonify({'error': 'Unauthorized'}), 401

@app.errorhandler(403)
def forbidden(e):
    return jsonify({'error': 'Access denied'}), 403

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(e):
    print(f"Internal server error: {str(e)}")
    return jsonify({'error': 'Internal server error'}), 500

# Run app
if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    host = os.getenv('HOST', '0.0.0.0')

    print(f"Starting Flask server on {host}:{port}")
    print(f"Frontend URL: {config.FRONTEND_URL}")
    print(f"MongoDB: {config.MONGODB_URI}")

  app.run(host=host, port=port, debug=config.DEBUG)
