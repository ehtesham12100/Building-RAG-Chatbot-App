import os
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent
STORAGE_DIR = BASE_DIR / "storage"
UPLOAD_DIR = STORAGE_DIR / "uploads"
CHROMA_DIR = STORAGE_DIR / "chroma_db"

# Ensure storage directories exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

class Settings(BaseSettings):
    PROJECT_NAME: str = "DocuQuery - Document RAG Chatbot"
    VERSION: str = "1.0.0"
    
    # Storage & DB
    DATABASE_URL: str = f"sqlite:///{STORAGE_DIR / 'rag_app.db'}"
    UPLOAD_PATH: str = str(UPLOAD_DIR)
    CHROMA_PATH: str = str(CHROMA_DIR)
    
    # LLM Settings
    DEFAULT_LLM_PROVIDER: str = "gemini"  # "gemini" or "groq"
    
    # Google Gemini Settings
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.8-flash"
    GEMINI_EMBEDDING_MODEL: str = "models/text-embedding-004"
    
    # Groq Settings
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    
    # RAG Chunker & Retrieval Settings
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 150
    TOP_K_CHUNKS: int = 4
    SIMILARITY_THRESHOLD: float = 0.25  # minimum relevance score
    
    class Config:
        env_file = str(BASE_DIR / ".env")
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()
