import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import init_db
from app.routers import documents, chat, users

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite database schema
    init_db()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Production-grade RAG Chatbot over custom PDF documents using FastAPI, SQLite, ChromaDB, and Google Gemini / Groq.",
    lifespan=lifespan
)

# Enable CORS for local testing or custom frontend clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers
app.include_router(documents.router)
app.include_router(chat.router)
app.include_router(users.router)

# Mount Static Files (Frontend)
static_path = os.path.join(os.path.dirname(__file__), "app", "static")
if os.path.exists(static_path):
    app.mount("/static", StaticFiles(directory=static_path), name="static")

@app.get("/", include_in_schema=False)
def serve_home():
    index_file = os.path.join(static_path, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "DocuQuery RAG API is operational. Visit /docs for Swagger documentation."}

@app.get("/api/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "database": "SQLite (SQLAlchemy)",
        "vector_store": "ChromaDB",
        "llm_provider": settings.DEFAULT_LLM_PROVIDER
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
