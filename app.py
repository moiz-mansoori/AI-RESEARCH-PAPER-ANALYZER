# app.py
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.utils import secure_filename

from src.load_and_extract_text import extract_text_from_pdf, extract_pdf_sections
from src.detect_and_split_sections import refine_sections, split_sections_with_content
from src.get_summary import generate_detailed_summary
from src.create_vector_db import create_vector_db
from src.RAG_retrival_chain import get_qa_chain

from dotenv import load_dotenv
import os
import uuid
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

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
groq_api_key = os.getenv("GROQ_API_KEY")
if not groq_api_key:
    raise ValueError("GROQ_API_KEY environment variable is required")

llm_model = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
# Using L3 model (faster) instead of L6 - 2x speedup with minimal quality loss
embedding_model = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L3-v2")

# Initialize LLM
llm = ChatGroq(groq_api_key=groq_api_key, model_name=llm_model)

# Initialize embeddings with multi-threading for faster CPU inference
embedder = HuggingFaceEmbeddings(
    model_name=embedding_model,
    cache_folder="./model_cache",
    encode_kwargs={
        "normalize_embeddings": True,
        "batch_size": 32  # Process 32 chunks at once for speed
    }
)

# In-memory user session storage (use Redis in production for multi-worker support)
user_sessions = {}


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


@app.route('/upload', methods=['POST'])
@limiter.limit("10 per minute")
def upload_pdf():
    """Handle PDF upload and extract topics."""
    try:
        session_id = get_session_id()
        user_data = get_user_data(session_id)
        
        file = request.files.get('file')
        
        if not file:
            return jsonify({"error": "No file uploaded"}), 400
        
        # Secure the filename to prevent path traversal attacks
        filename = secure_filename(file.filename)
        if not filename:
            return jsonify({"error": "Invalid filename"}), 400
        
        if not filename.lower().endswith('.pdf'):
            return jsonify({"error": "Only PDF files are allowed"}), 400
        
        # Use session ID in filename to avoid conflicts
        safe_filename = f"{session_id}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
        file.save(filepath)
        
        logger.info(f"Processing PDF: {filename} for session: {session_id}")
        
        # Extract text from PDF
        extracted_text = extract_text_from_pdf(filepath)
        if not extracted_text or not extracted_text.strip():
            os.remove(filepath)  # Clean up
            return jsonify({"error": "Could not extract text from PDF. The file may be scanned or corrupted."}), 400
        
        user_data['full_text'] = extracted_text
        
        # Extract and refine sections
        extracted_sections = extract_pdf_sections(full_text=extracted_text)
        refined_sections = refine_sections(extracted_sections, llm)
        section_with_content = split_sections_with_content(extracted_text, refined_sections)
        
        user_data['topics'] = section_with_content
        user_data['vector_db'] = None  # Reset vector DB for new upload
        
        # Clean up uploaded file after processing
        try:
            os.remove(filepath)
        except OSError:
            pass
        
        return jsonify({"topics": list(section_with_content.keys())})
        
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return jsonify({"error": "Failed to process PDF. Please try again."}), 500


@app.route('/summary', methods=['POST'])
@limiter.limit("20 per minute")
def get_summary():
    """Generate summary for a specific topic."""
    try:
        session_id = get_session_id()
        user_data = get_user_data(session_id)
        
        if not user_data['topics']:
            return jsonify({"error": "No paper uploaded yet. Please upload a PDF first."}), 400
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        topic = data.get('topic')
        if not topic:
            return jsonify({"error": "Topic is required"}), 400
        
        topic_content = user_data['topics'].get(topic)
        if not topic_content:
            return jsonify({"error": f"Topic '{topic}' not found"}), 404
        
        summary = generate_detailed_summary(topic_content, llm)
        
        return jsonify({"summary": summary})
        
    except Exception as e:
        logger.error(f"Summary error: {str(e)}")
        return jsonify({"error": "Failed to generate summary. Please try again."}), 500


@app.route('/chat', methods=['POST'])
@limiter.limit("30 per minute")
def chat():
    """Handle chat messages using RAG."""
    try:
        session_id = get_session_id()
        user_data = get_user_data(session_id)
        
        if not user_data['full_text']:
            return jsonify({"error": "No paper uploaded yet. Please upload a PDF first."}), 400
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        user_message = data.get('message')
        if not user_message or not user_message.strip():
            return jsonify({"error": "Message is required"}), 400
        
        logger.info(f"Chat query from session {session_id}: {user_message[:50]}...")
        
        # Create or retrieve vector database
        if not user_data['vector_db']:
            db_path = f"vector_dbs/{session_id}"
            user_data['vector_db'] = create_vector_db(
                text=user_data['full_text'],
                embedder=embedder,
                db_path=db_path
            )
        
        chain = get_qa_chain(vectordb=user_data['vector_db'], llm=llm)
        
        result = chain.invoke(user_message)
        ai_response = result.get('result', 'Unable to generate response.')
        
        return jsonify({"response": ai_response})
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        return jsonify({"error": "Failed to process your question. Please try again."}), 500


@app.errorhandler(413)
def too_large(e):
    """Handle file too large error."""
    return jsonify({"error": "File is too large. Maximum size is 16 MB."}), 413


@app.errorhandler(429)
def ratelimit_handler(e):
    """Handle rate limit exceeded error."""
    return jsonify({"error": "Rate limit exceeded. Please slow down."}), 429


if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    app.run(debug=debug_mode)