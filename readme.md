# 🔬 AI Research Paper Analyzer

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=for-the-badge&logo=flask&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-0.3-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white)
![Groq](https://img.shields.io/badge/Groq-LLM-F55036?style=for-the-badge&logo=groq&logoColor=white)

**Upload academic papers, extract key insights, and chat with your research using AI.**

[Features](#-features) • [Quick Start](#-quick-start) • [Deployment](#-free-deployment-option) • [API Reference](#-api-reference)

</div>

---

## 🤔 What is AI Research Paper Analyzer?

AI Research Paper Analyzer is an intelligent web application that helps researchers, students, and academics **understand complex research papers faster**. Instead of spending hours reading dense academic content, simply upload a PDF and let AI do the heavy lifting.

### The Problem It Solves

Reading research papers is time-consuming and challenging:
- 📚 Papers are often 50-100 pages long
- 🔬 Technical jargon makes understanding difficult
- ⏰ Finding specific information takes forever
- 🧠 Remembering key points across multiple papers is hard

### The Solution

This tool uses **Retrieval-Augmented Generation (RAG)** to:
1. **Extract** all text and sections from your PDF
2. **Understand** the paper using vector embeddings
3. **Summarize** any section in simple terms
4. **Answer questions** about the paper accurately

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📄 **PDF Upload & Analysis** | Drag & drop research papers (up to 16 MB), with real-time progress tracking |
| 🗂️ **Auto Section Detection** | Automatically finds Abstract, Introduction, Methods, Results, etc. using fast regex |
| 🧠 **AI Summarization** | Generate detailed summaries for any section using Llama 3.3 70B |
| 💬 **RAG-Powered Chat** | Ask questions about your paper with context-aware responses from FAISS vector search |
| 🧪 **Hybrid Knowledge** | If info isn't in the paper, AI provides general knowledge with clear distinction |
| ⚡ **Instant Startup** | Lazy-loaded LLM & embeddings — server starts in seconds |
| 🔒 **Production-Ready** | Rate limiting, input validation, CORS, XSS protection, and session isolation |

### Example Questions You Can Ask
- "What is the main contribution of this paper?"
- "Summarize the experimental results"
- "What datasets were used?"
- "Explain the proposed architecture in simple terms"
- "What are the limitations mentioned by the authors?"

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- [Groq API Key](https://console.groq.com/) (free tier available)
- [Cohere API Key](https://dashboard.cohere.com/api-keys) (recommended for cloud embeddings)

### Installation

```bash
# Clone the repository
git clone https://github.com/moiz-mansoori/AI-RESEARCH-PAPER-ANALYZER.git
cd AI-RESEARCH-PAPER-ANALYZER

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Copy the example environment file and fill in your keys:

```bash
cp .env.example .env
```

Edit `.env` with your API keys:

```env
GROQ_API_KEY=your_groq_api_key_here
COHERE_API_KEY=your_cohere_api_key_here
FLASK_SECRET_KEY=AI_researchpaper_analyzer
LLM_MODEL=llama-3.3-70b-versatile
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

> **Note:** If `COHERE_API_KEY` is not set, the app will use local HuggingFace embeddings (uses more RAM).

### Run Locally

```bash
python app.py
```

Visit **http://localhost:5000** in your browser.

---

## 🌐 Free Deployment Option

### Render.com ⭐

**Best for:** Easy deployment, auto-deploy from GitHub

| Feature | Details |
|---------|---------|
| **Free Tier** | 750 hours/month |
| **RAM** | 512 MB |
| **Sleep** | After 15 min inactivity |
| **Auto-deploy** | Yes, from GitHub |

**Steps:**
1. Push code to GitHub
2. Go to [render.com](https://render.com) → New → Web Service
3. Connect your GitHub repo
4. Set environment variables:
   - `GROQ_API_KEY` = your key
   - `COHERE_API_KEY` = your key (recommended)
   - `FLASK_SECRET_KEY` = `AI_researchpaper_analyzer`
5. Deploy!

> ⚠️ **Note:** Free tier sleeps after 15 min. First request takes ~30-60s to wake.

---

## 📖 API Reference

### Upload PDF
```http
POST /upload
Content-Type: multipart/form-data

file: <PDF file, max 16 MB>
```

**Response:**
```json
{"topics": ["Abstract", "Introduction", "Methodology", "Results"]}
```

### Upload Progress (Polling)
```http
GET /upload-status
```

**Response:**
```json
{"step": 2, "total": 3, "message": "Detecting sections..."}
```

### Get Summary
```http
POST /summary
Content-Type: application/json

{"topic": "Introduction"}
```

### Chat
```http
POST /chat
Content-Type: application/json

{"message": "What is the main contribution of this paper?"}
```

---

## 🏗️ Project Structure

```
AI-RESEARCH-PAPER-ANALYZER/
├── app.py                          # Flask app with lazy-loaded LLM & embeddings
├── src/
│   ├── load_and_extract_text.py    # PDF text extraction & section parsing
│   ├── detect_and_split_sections.py # Section splitting logic
│   ├── get_summary.py              # LLM-powered summary generation
│   ├── create_vector_db.py         # FAISS vector database creation
│   ├── RAG_retrival_chain.py       # RAG chain for Q&A chat
│   └── analysis_utils.py           # Keyword, citation & topic utilities
├── templates/index.html            # Frontend UI
├── data_samples/                   # Sample extracted JSON data
├── .env.example                    # Environment variable template
├── requirements.txt
├── Procfile                        # For Render/Heroku
├── render.yaml                     # Render deployment config
└── runtime.txt
```

---

## 🔧 Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GROQ_API_KEY` | ✅ Yes | - | Your Groq API key |
| `COHERE_API_KEY` | ⭐ Recommended | - | Cohere API for cloud embeddings |
| `FLASK_SECRET_KEY` | No | `AI_researchpaper_analyzer` | Flask session secret key |
| `LLM_MODEL` | No | `llama-3.3-70b-versatile` | Groq LLM model name |
| `EMBEDDING_MODEL` | No | `all-MiniLM-L6-v2` | HuggingFace model (fallback) |
| `ALLOWED_ORIGINS` | No | `*` | CORS allowed origins |
| `FLASK_DEBUG` | No | `False` | Enable Flask debug mode |

---

## 🛡️ Security

- ✅ Path traversal protection (`secure_filename`)
- ✅ XSS prevention (`escapeHtml` on user input)
- ✅ Rate limiting (200 req/hour, 10 uploads/min, 30 chats/min)
- ✅ File size limits (16 MB)
- ✅ PDF-only file validation
- ✅ Session isolation per user
- ✅ CORS configured
- ✅ Auto-cleanup of uploaded files

---

## 👤 Author

**Moiz Mansoori**

[![GitHub](https://img.shields.io/badge/GitHub-moiz--mansoori-181717?style=flat-square&logo=github)](https://github.com/moiz-mansoori)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-moiz--mansoori03-0A66C2?style=flat-square&logo=linkedin)](https://www.linkedin.com/in/moiz-mansoori03/)

---

<div align="center">

⭐ **Star this repo if you found it helpful!** ⭐

</div>
