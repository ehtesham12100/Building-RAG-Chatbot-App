---
title: DocuQuery RAG Chatbot
emoji: 📚
colorFrom: indigo
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
---

# 📚 DocuQuery — RAG Chatbot Over Custom Documents

A production-grade **Retrieval-Augmented Generation (RAG)** chatbot built with **FastAPI**, **SQLite (SQLAlchemy)**, **ChromaDB**, and **Google Gemini / Groq**.

Upload your personal documents (college notes, company policies, legal agreements, research papers) and ask questions. Every answer is grounded directly in the text and cited with exact document names and page numbers.

---

## 🏛️ System Architecture

```
User Query / PDF Upload
       │
       ▼
┌────────────────────────────────────────────────────────┐
│                      FastAPI Server                     │
│  - REST Endpoints (/api/documents, /api/chat, /api/users)│
│  - Web UI (Single Page App with Citations & Filters)   │
└───────────────┬────────────────────────┬───────────────┘
                │                        │
       Metadata & History        Semantic Chunks & Vectors
                │                        │
                ▼                        ▼
┌───────────────────────────┐  ┌─────────────────────────┐
│     SQLite Database       │  │        ChromaDB         │
│  - Users                  │  │  - Vector Embeddings    │
│  - Documents Metadata     │  │  - Chunks & Metadata    │
│  - Chat Sessions & History│  │  - Cosine Search        │
└───────────────────────────┘  └─────────────┬───────────┘
                                             │ Top-K Chunks
                                             ▼
                               ┌─────────────────────────┐
                               │     LLM Generation      │
                               │  - Google Gemini 2.0    │
                               │  - Groq (Llama 3.3 70B) │
                               └─────────────────────────┘
```

---

## ✨ Features

- 📄 **Multi-PDF Ingestion**: Upload college notes, employee handbooks, legal contracts, or technical manuals.
- 📑 **Page-Aware Chunking**: Tracks exact page numbers and chunk offsets for full traceability.
- ⚡ **ChromaDB Vector Store**: Fast persistent local vector database with cosine similarity search.
- 🤖 **Multi-LLM Support**:
  - **Google Gemini** (Gemini 2.0 Flash / Gemini 1.5 Flash)
  - **Groq** (Llama 3.3 70B Versatile — ultra fast)
- 📌 **Grounding & Citations**: Answers include clickable source references displaying the excerpt and page number.
- 🎯 **Targeted Document Filtering**: Ask questions across *all* uploaded documents, or select specific files to filter retrieval.
- 💾 **SQLite Chat History**: Automatically saves conversation threads and citations.
- 🎨 **Modern Dark Web UI**: Complete single-page application with drag-and-drop uploader and live markdown rendering.

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.10+
- A Google Gemini API key ([Google AI Studio](https://aistudio.google.com/)) or Groq API key ([Groq Console](https://console.groq.com/))

### 2. Environment Setup
The virtual environment is already prepared in `venv`. To activate:
```powershell
.\venv\Scripts\Activate.ps1
```

Or install dependencies into any Python environment:
```bash
pip install -r requirements.txt
```

### 3. Configure API Keys
Edit the `.env` file in the project root:
```env
# Primary LLM provider: 'gemini' or 'groq'
DEFAULT_LLM_PROVIDER=gemini

# Google Gemini API key
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash

# (Optional) Groq API key
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
```

*(Note: You can also enter or switch your API key directly in the Web UI Settings modal at runtime).*

### 4. Run the Application
Start the FastAPI server:
```powershell
.\venv\Scripts\python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### 5. Access the Interface
- **Web UI**: Open your browser at [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive API Docs (Swagger UI)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 🧪 Testing with Sample Documents

Sample documents are included in `sample_docs/`:
1. `sample_docs/sample_college_notes.pdf`: Operating Systems lecture notes (Paging, Mutexes, Raft Consensus).
2. `sample_docs/sample_company_policy.pdf`: Employee Handbook (Hybrid work, PTO, Home office stipend).

Run the automated pipeline test anytime:
```powershell
.\venv\Scripts\python test_rag_pipeline.py
```

---

## 📡 API Endpoints Overview

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/documents/upload` | Upload PDF file, chunk, and index into ChromaDB |
| `GET` | `/api/documents` | List all uploaded documents with metadata |
| `DELETE` | `/api/documents/{id}` | Delete document and remove chunks from vector store |
| `POST` | `/api/chat/query` | Submit question to RAG engine and retrieve answer + citations |
| `GET` | `/api/chat/sessions` | List prior chat conversations |
| `GET` | `/api/chat/sessions/{id}` | Retrieve messages and citations for a specific chat |
| `DELETE` | `/api/chat/sessions/{id}` | Delete conversation |
| `GET` | `/api/chat/config` | Check currently configured provider and key status |
| `GET` | `/api/health` | Health check endpoint |
