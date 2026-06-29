# 🔬 AI Research Paper Analyzer

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0-000000?style=for-the-badge&logo=flask&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-0.3-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white)
![Groq](https://img.shields.io/badge/Groq-LLM-F55036?style=for-the-badge&logo=groq&logoColor=white)

**Upload academic papers, extract key insights, and chat with your research using AI.**

[Features](#-features) • [Quick Start](#-quick-start) • [Deployment](#-deployment) • [API Reference](#-api-reference)

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
1. **Extract** all text, sections, and page numbers from your PDF
2. **Understand** the paper using FAISS vector embeddings
3. **Summarize** any section in simple terms
4. **Answer questions** about the paper accurately, citing the exact page numbers

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🎨 **Premium Mobile-First UI** | Sleek dark-mode interface with glassmorphism, dynamic Chart.js dashboards, and a seamless drag-and-drop experience. |
| 📄 **PDF Analysis & Metadata** | Extracts text and maps content to exact page numbers for accurate citations. |
| 🗂️ **Auto Section Detection** | Automatically detects Abstract, Introduction, Methods, Results, etc., with robust fallbacks. |
| 🧠 **AI Summarization** | Generate detailed, formatted markdown summaries for any section using Llama 3.3 70B. |
| 💬 **RAG-Powered Chat** | Ask questions using FAISS with **Maximal Marginal Relevance (MMR)** search for diverse and highly accurate answers. |
| 🎯 **Strict Grounding** | AI provides exact `[Source Page X]` citations and strictly refuses to hallucinate if the info is missing from the paper. |
| ⚡ **Production-Ready** | Lazy-loaded models, vector DB auto-cleanup (24h expiry), rate limiting, and robust error handling for scanned/encrypted PDFs. |
| 🐳 **Deployment Ready** | Supports standard Python hosting, native Render deployments, and comes with a `Dockerfile` for containerized setups. |

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

> **Note:** If `COHERE_API_KEY` is not set, the app will gracefully fall back to using local HuggingFace embeddings.

### Run Locally

```bash
python app.py
```

Visit **http://localhost:5000** in your browser.

---

## 🌐 Deployment

### Option A: Render.com (Recommended) ⭐

**Best for:** Easy deployment, auto-deploy directly from GitHub

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
4. Set environment variables (`GROQ_API_KEY`, `COHERE_API_KEY`, `FLASK_SECRET_KEY`)
5. Deploy! Every time you push to the `main` branch, Render will automatically adapt the new UI and backend changes.

### Option B: Docker

A `Dockerfile` and `docker-compose.yml` are included for effortless deployment on any VPS or local machine.

```bash
docker-compose up --build -d
```

---

## 📖 API Reference

### Upload PDF
```http
POST /upload
Content-Type: multipart/form-data

file: <PDF file, max 16 MB>
```

### Upload Progress (Polling)
Tracks real-time progress while building the FAISS vector database.
```http
GET /upload-status
```

**Response:**
```json
{"step": 2, "total": 4, "message": "Detecting sections..."}
```

### Get Paper Stats
```http
GET /stats
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

```text
AI-RESEARCH-PAPER-ANALYZER/
├── app.py                          # Flask app with lazy-loaded LLM & embeddings
├── src/
│   ├── load_and_extract_text.py    # PDF text extraction & page numbering
│   ├── detect_and_split_sections.py # Advanced section splitting logic
│   ├── get_summary.py              # LLM-powered summary generation
│   ├── create_vector_db.py         # FAISS vector DB creation & MMR integration
│   ├── RAG_retrival_chain.py       # RAG chain for strictly grounded Q&A
│   └── analysis_utils.py           # Keyword & topic distribution utilities
├── templates/index.html            # Premium mobile-first Frontend UI
├── Dockerfile                      # Containerized deployment config
├── docker-compose.yml              # Multi-container local orchestration
├── requirements.txt
├── render.yaml                     # Render deployment configuration
└── Procfile                        # Heroku/Render process definitions
```

---

## 🛡️ Security & Reliability

- ✅ **Strict Anti-Hallucination:** RAG prompt actively blocks the LLM from making up facts.
- ✅ **Graceful Error Handling:** Detects and safely rejects empty, scanned, or encrypted PDFs.
- ✅ **State Isolation:** FAISS vector DBs are strictly scoped per-user session.
- ✅ **Auto-Cleanup:** Old vector databases and temporary files are swept automatically after 24 hours.
- ✅ **XSS & Traversal Prevention:** Uses `secure_filename` and UI HTML escaping.
- ✅ **Rate Limiting:** Protects `/upload`, `/chat`, and `/summary` from abuse.

---

## 👤 Author

**Moiz Mansoori**

[![GitHub](https://img.shields.io/badge/GitHub-moiz--mansoori-181717?style=flat-square&logo=github)](https://github.com/moiz-mansoori)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-moiz--mansoori03-0A66C2?style=flat-square&logo=linkedin)](https://www.linkedin.com/in/moiz-mansoori03/)

---

<div align="center">

⭐ **Star this repo if you found it helpful!** ⭐

</div>
