"""Celery task definitions for async processing"""
import time
from celery import Celery, group
from pymongo import MongoClient
from gridfs import GridFS
from config.config import get_config
from services import ocr_service, nlp_service, gridfs_service
from models import evaluation_scheme, answer_sheet, evaluation_result

config = get_config()

# Initialize Celery
celery_app = Celery(
    'answer_evaluation',
    broker=config.REDIS_URL,
    backend=config.REDIS_URL
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

# MongoDB connection for background tasks
mongo_client = None
db = None


def init_celery_db():
    """Initialize MongoDB connection for Celery tasks"""
    global mongo_client, db
    mongo_client = MongoClient(config.MONGODB_URI)
    db_name = config.MONGODB_URI.split('/')[-1].split('?')[0]
    db = mongo_client[db_name]

    # Initialize GridFS
    gridfs_service.init_gridfs(db)

    # Initialize model DB references
    evaluation_scheme.init_db(db)
    answer_sheet.init_db(db)
    evaluation_result.init_db(db)

    # Initialize NLP models
    nlp_service.init_models()


@celery_app.task(bind=True, max_retries=3)
def process_model_answer(self, scheme_id):
    """
    Background task to process model answer PDF

    Args:
        scheme_id: Evaluation scheme ID (string)

    Returns:
        Success message or raises exception
    """
    # Initialize DB if not already done
    if db is None:
        init_celery_db()

    try:
        # Fetch evaluation scheme
        scheme = evaluation_scheme.find_by_id(scheme_id)
        if not scheme:
            raise Exception(f"Evaluation scheme {scheme_id} not found")

        # Extract text from model answer PDF
        print(f"Extracting text from model answer for scheme {scheme_id}...")
        extracted_text = ocr_service.extract_text_from_pdf(scheme['model_answer_file_id'])

        # Extract keywords from text
        print(f"Extracting keywords for scheme {scheme_id}...")
        keywords = nlp_service.extract_keywords(extracted_text)

        # Update scheme with extracted data
        evaluation_scheme.update_scheme(scheme_id, {
            'extracted_text': extracted_text,
            'keywords': keywords,
            'status': 'ready'
        })

        print(f"Model answer processing complete for scheme {scheme_id}")
        return f"Model answer processed successfully for scheme {scheme_id}"

    except Exception as e:
        error_message = f"Failed to process model answer: {str(e)}"
        print(error_message)

        # Update scheme status to failed
        try:
            evaluation_scheme.update_scheme(scheme_id, {
                'status': 'failed',
                'error_message': error_message
            })
        except:
            pass

        # Retry if not exceeded max retries
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60)

        raise Exception(error_message)


@celery_app.task(bind=True, max_retries=3)
def process_evaluation(self, answer_sheet_id):
    """
    Background task to evaluate a single answer sheet

    Args:
        answer_sheet_id: Answer sheet ID (string)

    Returns:
        Success message or raises exception
    """
    # Initialize DB if not already done
    if db is None:
        init_celery_db()

    start_time = time.time()

    try:
        # Fetch answer sheet
        sheet = answer_sheet.find_by_id(answer_sheet_id)
        if not sheet:
            raise Exception(f"Answer sheet {answer_sheet_id} not found")

        # Fetch evaluation scheme
        scheme = evaluation_scheme.find_by_id(sheet['evaluation_scheme_id'])
        if not scheme:
            raise Exception(f"Evaluation scheme not found")

        # Verify scheme is ready
        if scheme['status'] != 'ready':
            raise Exception("Model answer is not ready. Please wait for processing to complete.")

        # Update status to processing
        answer_sheet.update_status(answer_sheet_id, 'processing')

        # Extract text from student answer PDF
        print(f"Extracting text from answer sheet {answer_sheet_id}...")
        extracted_text = ocr_service.extract_text_from_pdf(sheet['answer_file_id'])

        # Update answer sheet with extracted text
        answer_sheet.update_extracted_text(answer_sheet_id, extracted_text)

        # Evaluate answer
        print(f"Evaluating answer sheet {answer_sheet_id}...")
        evaluation_result_data = nlp_service.evaluate_answer(
            student_text=extracted_text,
            model_text=scheme['extracted_text'],
            model_keywords=scheme['keywords'],
            total_marks=scheme['total_marks']
        )

        # Calculate evaluation time
        evaluation_time = time.time() - start_time
        evaluation_result_data['evaluation_time'] = round(evaluation_time, 2)

        # Create evaluation result
        evaluation_result.create_result(
            answer_sheet_id=answer_sheet_id,
            scheme_id=scheme['_id'],
            scores=evaluation_result_data,
            feedback=evaluation_result_data['detailed_feedback']
        )

        # Update answer sheet status to completed
        answer_sheet.update_status(answer_sheet_id, 'completed')

        print(f"Evaluation complete for answer sheet {answer_sheet_id}")
        return f"Answer sheet {answer_sheet_id} evaluated successfully"

    except Exception as e:
        error_message = f"Evaluation failed: {str(e)}"
        print(error_message)

        # Set error status
        try:
            answer_sheet.set_error(answer_sheet_id, error_message)
        except:
            pass

        # Retry if not exceeded max retries
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60)

        raise Exception(error_message)


@celery_app.task
def process_bulk_evaluation(answer_sheet_ids):
    """
    Background task to evaluate multiple answer sheets

    Args:
        answer_sheet_ids: List of answer sheet IDs (strings)

    Returns:
        Summary of processing
    """
    # Initialize DB if not already done
    if db is None:
        init_celery_db()

    try:
        # Create a group of evaluation tasks (limit to 5 concurrent)
        # Split into batches of 5
        batch_size = 5
        results = []

        for i in range(0, len(answer_sheet_ids), batch_size):
            batch = answer_sheet_ids[i:i + batch_size]

            # Create group for this batch
            job = group(process_evaluation.s(sheet_id) for sheet_id in batch)

            # Execute batch
            result = job.apply_async()

            # Wait for batch to complete before starting next
            result.get()

            results.extend(result.results)

        return {
            'total': len(answer_sheet_ids),
            'message': 'Bulk evaluation completed'
        }

    except Exception as e:
        error_message = f"Bulk evaluation failed: {str(e)}"
        print(error_message)
        return {
            'total': len(answer_sheet_ids),
            'error': error_message
        }
