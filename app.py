# app.py
from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.utils import secure_filename

import os
import uuid
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Immediate feedback for the user
print("\n🚀 Starting AI Research Paper Analyzer server...")
print("📝 Loading environment and configurations...")

load_dotenv()

from src.load_and_extract_text import extract_text_from_pdf, extract_pdf_sections
from src.detect_and_split_sections import split_sections_with_content
from src.get_summary import generate_detailed_summary
from src.create_vector_db import create_vector_db
from src.RAG_retrival_chain import get_qa_chain
from src.analysis_utils import get_keyword_frequency, extract_citations, get_topic_distribution

app = Flask(__name__)

# Security configurations
app.config['SECRET_KEY'] = os.getenv("FLASK_SECRET_KEY", os.urandom(24).hex())
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit

# Enable CORS with restrictions
CORS(app, origins=os.getenv("ALLOWED_ORIGINS", "*").split(","))

# Rate limiting to prevent API abuse
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per hour"],
    storage_uri="memory://"
)

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Validate required environment variables
groq_api_key = os.getenv("GROQ_API_KEY", "").strip()
if not groq_api_key:
    raise ValueError("GROQ_API_KEY environment variable is required")

llm_model = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile").strip()
cohere_api_key = os.getenv("COHERE_API_KEY", "").strip()

# Lazy-load LLM & Embeddings to ensure instant startup
_llm = None
_embedder = None

def get_llm():
    """Lazy-load the LLM only when a request arrives."""
    global _llm
    if _llm is None:
        logger.info("Initializing Groq LLM...")
        from langchain_groq import ChatGroq
        _llm = ChatGroq(groq_api_key=groq_api_key, model_name=llm_model)
    return _llm

def get_embedder():
    """Lazy-load embeddings to reduce memory at startup."""
    global _embedder
    if _embedder is None:
        if cohere_api_key:
            logger.info("Using Cohere cloud embeddings...")
            from langchain_cohere import CohereEmbeddings
            _embedder = CohereEmbeddings(
                cohere_api_key=cohere_api_key,
                model="embed-english-v3.0"
            )
            logger.info("Cohere cloud embeddings initialized successfully")
        else:
            logger.info("COHERE_API_KEY not set, using local HuggingFace embeddings...")
            from langchain_huggingface import HuggingFaceEmbeddings
            embedding_model = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
            _embedder = HuggingFaceEmbeddings(
                model_name=embedding_model,
                cache_folder="./model_cache",
                encode_kwargs={
                    "normalize_embeddings": True,
                    "batch_size": 8
                }
            )
            logger.info("HuggingFace embedding model loaded successfully")
    return _embedder

# In-memory user session storage
user_sessions = {}

# Upload progress tracking (session_id -> {step, total, message})
upload_progress = {}

def get_session_id():
    """Get or create a unique session ID for the current user."""
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    return session['session_id']

def get_user_data(session_id):
    """Get user data for a session, or create empty data structure."""
    if session_id not in user_sessions:
        user_sessions[session_id] = {
            'full_text': '',
            'topics': None,
            'vector_db': None
        }
    return user_sessions[session_id]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload-status')
def upload_status():
    """Return the current upload processing progress."""
    session_id = get_session_id()
    progress = upload_progress.get(session_id, {"step": 0, "total": 3, "message": "Waiting..."})
    return jsonify(progress)

@app.route('/upload', methods=['POST'])
@limiter.limit("10 per minute")
def upload_pdf():
    """Handle PDF upload and extract topics — fast path, no LLM."""
    try:
        session_id = get_session_id()
        user_data = get_user_data(session_id)
        file = request.files.get('file')

        if not file:
            return jsonify({"error": "No file uploaded"}), 400

        filename = secure_filename(file.filename)
        if not filename:
            return jsonify({"error": "Invalid filename"}), 400

        if not filename.lower().endswith('.pdf'):
            return jsonify({"error": "Only PDF files are allowed"}), 400

        safe_filename = f"{session_id}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
        file.save(filepath)

        logger.info(f"Processing PDF: {filename} for session: {session_id}")

        # --- Step 1: Extract text ---
        upload_progress[session_id] = {"step": 1, "total": 3, "message": "Extracting text from PDF..."}
        logger.info("[Step 1/3] Extracting text from PDF...")
        extracted_text = extract_text_from_pdf(filepath)
        if not extracted_text or not extracted_text.strip():
            os.remove(filepath)
            upload_progress.pop(session_id, None)
            return jsonify({"error": "Could not extract text from PDF."}), 400
        logger.info(f"[Step 1/3] Done. Extracted {len(extracted_text)} characters.")

        user_data['full_text'] = extracted_text

        # --- Step 2: Detect sections (fast regex, no LLM) ---
        upload_progress[session_id] = {"step": 2, "total": 3, "message": "Detecting sections..."}
        logger.info("[Step 2/3] Detecting sections...")
        extracted_sections = extract_pdf_sections(full_text=extracted_text)
        logger.info(f"[Step 2/3] Done. Found {len(extracted_sections)} sections.")

        # --- Step 3: Split content into topics ---
        upload_progress[session_id] = {"step": 3, "total": 3, "message": "Organizing topics..."}
        logger.info("[Step 3/3] Splitting section content...")
        section_with_content = split_sections_with_content(extracted_text, extracted_sections)
        logger.info(f"[Step 3/3] Done. Final topics: {list(section_with_content.keys())}")

        user_data['topics'] = section_with_content
        user_data['vector_db'] = None

        try:
            os.remove(filepath)
        except OSError:
            pass

        upload_progress.pop(session_id, None)
        return jsonify({"topics": list(section_with_content.keys())})
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        import traceback
        traceback.print_exc()
        upload_progress.pop(session_id, None)
        return jsonify({"error": f"Failed to process PDF: {str(e)}"}), 500

@app.route('/summary', methods=['POST'])
@limiter.limit("20 per minute")
def get_summary():
    """Generate summary for a specific topic."""
    try:
        session_id = get_session_id()
        user_data = get_user_data(session_id)
        
        if not user_data['topics']:
            return jsonify({"error": "No paper uploaded yet."}), 400
        
        data = request.get_json()
        if not data: return jsonify({"error": "No data provided"}), 400
            
        topic = data.get('topic')
        if not topic: return jsonify({"error": "Topic is required"}), 400
        
        topic_content = user_data['topics'].get(topic)
        if not topic_content: return jsonify({"error": f"Topic '{topic}' not found"}), 404
        
        summary = generate_detailed_summary(topic_content, get_llm())
        return jsonify({"summary": summary})
    except Exception as e:
        logger.error(f"Summary error: {str(e)}")
        return jsonify({"error": "Failed to generate summary."}), 500

@app.route('/chat', methods=['POST'])
@limiter.limit("30 per minute")
def chat():
    """Handle chat messages using RAG."""
    try:
        session_id = get_session_id()
        user_data = get_user_data(session_id)
        
        if not user_data['full_text']:
            return jsonify({"error": "No paper uploaded yet."}), 400
        
        data = request.get_json()
        if not data: return jsonify({"error": "No data provided"}), 400
            
        user_message = data.get('message')
        if not user_message or not user_message.strip():
            return jsonify({"error": "Message is required"}), 400
        
        logger.info(f"Chat query from session {session_id}: {user_message[:50]}...")
        
        if not user_data['vector_db']:
            db_path = f"vector_dbs/{session_id}"
            user_data['vector_db'] = create_vector_db(
                text=user_data['full_text'],
                embedder=get_embedder(),
                db_path=db_path
            )
        
        chain = get_qa_chain(vectordb=user_data['vector_db'], llm=get_llm())
        result = chain.invoke({"input": user_message})
        return jsonify({"response": result.get('answer', 'Unable to generate response.')})
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        return jsonify({"error": "Failed to process question."}), 500

@app.route('/stats', methods=['GET'])
@limiter.limit("10 per minute")
def get_stats():
    """Get analysis statistics for the current paper."""
    try:
        session_id = get_session_id()
        user_data = get_user_data(session_id)
        if not user_data['full_text']: return jsonify({"error": "No paper uploaded"}), 400
            
        full_text = user_data['full_text']
        sections = user_data['topics'] or {}
        
        keywords = get_keyword_frequency(full_text)
        citations = extract_citations(full_text)
        topics_dist = get_topic_distribution(sections)
        
        return jsonify({
            "keywords": keywords,
            "citations_count": len(citations),
            "citations": citations[:10],
            "topic_distribution": topics_dist
        })
    except Exception as e:
        logger.error(f"Stats error: {str(e)}")
        return jsonify({"error": "Failed to generate statistics."}), 500

@app.errorhandler(413)
def too_large(e):
    return jsonify({"error": "File is too large. Maximum size is 16 MB."}), 413

@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({"error": "Rate limit exceeded. Please slow down."}), 429

if __name__ == "__main__":
    print("✨ Server is ready! Waiting for requests on http://127.0.0.1:5000")
    debug_mode = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    app.run(debug=debug_mode)