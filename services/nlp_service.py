"""NLP evaluation logic using sentence transformers and spaCy"""
import spacy
from sentence_transformers import SentenceTransformer, util
from openai import OpenAI
from config.config import get_config
from utils.errors import NLPException

config = get_config()

# Initialize models (load once at startup)
sentence_model = None
nlp_model = None
openai_client = None


def init_models():
    """Initialize NLP models"""
    global sentence_model, nlp_model, openai_client

    try:
        # Load sentence transformer model
        sentence_model = SentenceTransformer(config.SENTENCE_TRANSFORMER_MODEL)

        # Load spaCy model
        nlp_model = spacy.load(config.SPACY_MODEL)

        # Initialize OpenAI client
        openai_client = OpenAI(api_key=config.OPENAI_API_KEY)

        print("NLP models initialized successfully")
    except Exception as e:
        print(f"Error initializing NLP models: {str(e)}")
        raise NLPException(f"Failed to initialize NLP models: {str(e)}")


def extract_keywords(text):
    """
    Extract keywords from text using spaCy

    Args:
        text: Input text

    Returns:
        List of keywords (lowercase)

    Raises:
        NLPException: If keyword extraction fails
    """
    if not nlp_model:
        raise NLPException("NLP model not initialized")

    try:
        # Process text with spaCy
        doc = nlp_model(text.lower())

        keywords = set()

        # Extract named entities
        for ent in doc.ents:
            keywords.add(ent.text.lower())

        # Extract noun chunks
        for chunk in doc.noun_chunks:
            # Get the root word of the chunk
            keywords.add(chunk.root.text.lower())

        # Extract important verbs and adjectives
        for token in doc:
            if token.pos_ in ['VERB', 'ADJ'] and not token.is_stop:
                keywords.add(token.lemma_.lower())

        # Return as sorted list
        return sorted(list(keywords))

    except Exception as e:
        raise NLPException(f"Keyword extraction failed: {str(e)}")


def calculate_semantic_similarity(text1, text2):
    """
    Calculate semantic similarity between two texts

    Args:
        text1: First text
        text2: Second text

    Returns:
        Similarity score (0-1)

    Raises:
        NLPException: If similarity calculation fails
    """
    if not sentence_model:
        raise NLPException("Sentence transformer model not initialized")

    try:
        # Encode both texts to embeddings
        embedding1 = sentence_model.encode(text1, convert_to_tensor=True)
        embedding2 = sentence_model.encode(text2, convert_to_tensor=True)

        # Calculate cosine similarity
        similarity = util.cos_sim(embedding1, embedding2)

        # Convert to float and return
        return float(similarity.item())

    except Exception as e:
        raise NLPException(f"Semantic similarity calculation failed: {str(e)}")


def calculate_keyword_match(model_keywords, student_text):
    """
    Calculate keyword match score

    Args:
        model_keywords: List of keywords from model answer
        student_text: Student answer text

    Returns:
        Match score (0-1)

    Raises:
        NLPException: If keyword matching fails
    """
    try:
        # Extract keywords from student text
        student_keywords = extract_keywords(student_text)

        if not model_keywords:
            return 0.0

        # Count matching keywords
        matching_count = 0
        for model_kw in model_keywords:
            if model_kw in student_keywords:
                matching_count += 1

        # Calculate percentage
        match_score = matching_count / len(model_keywords)

        return match_score

    except Exception as e:
        raise NLPException(f"Keyword matching failed: {str(e)}")


def generate_feedback(student_text, model_text, similarity_score, keyword_score):
    """
    Generate AI feedback using OpenAI GPT-4

    Args:
        student_text: Student answer text
        model_text: Model answer text
        similarity_score: Semantic similarity score (0-1)
        keyword_score: Keyword match score (0-1)

    Returns:
        Feedback text

    Raises:
        NLPException: If feedback generation fails
    """
    if not openai_client:
        raise NLPException("OpenAI client not initialized")

    try:
        prompt = f"""Compare the student answer with the model answer. Provide constructive feedback highlighting strengths and areas for improvement.

Model Answer:
{model_text[:1000]}

Student Answer:
{student_text[:1000]}

Metrics:
- Semantic Similarity: {similarity_score:.2%}
- Keyword Coverage: {keyword_score:.2%}

Provide feedback in 3-4 sentences focusing on:
1. What the student did well
2. What key concepts or keywords were missed
3. Specific areas for improvement"""

        response = openai_client.chat.completions.create(
            model=config.OPENAI_TEXT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are an educational assistant providing constructive feedback on student answers."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=500,
            temperature=0.7
        )

        feedback = response.choices[0].message.content

        return feedback

    except Exception as e:
        # If feedback generation fails, return a default message
        print(f"Feedback generation failed: {str(e)}")
        return f"Answer evaluated with {similarity_score:.1%} semantic similarity and {keyword_score:.1%} keyword coverage. Review your answer against the model answer for improvement areas."


def evaluate_answer(student_text, model_text, model_keywords, total_marks):
    """
    Complete evaluation of student answer

    Args:
        student_text: Student answer text
        model_text: Model answer text
        model_keywords: Keywords from model answer
        total_marks: Maximum possible marks

    Returns:
        Dictionary with scores and feedback

    Raises:
        NLPException: If evaluation fails
    """
    try:
        # Calculate semantic similarity
        semantic_similarity = calculate_semantic_similarity(student_text, model_text)

        # Calculate keyword match
        keyword_match = calculate_keyword_match(model_keywords, student_text)

        # Compute hybrid score using configured weights
        hybrid_score = (
            semantic_similarity * config.SEMANTIC_SIMILARITY_WEIGHT +
            keyword_match * config.KEYWORD_MATCH_WEIGHT
        )

        # Convert to marks
        total_score = round(hybrid_score * total_marks)

        # Calculate percentage
        percentage = round((total_score / total_marks) * 100, 2) if total_marks > 0 else 0

        # Generate feedback
        try:
            feedback = generate_feedback(student_text, model_text, semantic_similarity, keyword_match)
        except Exception as e:
            print(f"Feedback generation error: {str(e)}")
            feedback = f"Answer evaluated with {semantic_similarity:.1%} semantic similarity and {keyword_match:.1%} keyword coverage."

        return {
            'total_score': total_score,
            'max_score': total_marks,
            'percentage': percentage,
            'semantic_similarity_score': round(semantic_similarity, 4),
            'keyword_match_score': round(keyword_match, 4),
            'detailed_feedback': feedback
        }

    except NLPException:
        raise
    except Exception as e:
        raise NLPException(f"Answer evaluation failed: {str(e)}")
