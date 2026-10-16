import json
import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import ChatSession, ChatMessage
from app.schemas import (
    ChatQueryRequest,
    ChatQueryResponse,
    ChatSessionResponse,
    ChatMessageResponse,
    SourceCitation
)
from app.services.rag_engine import rag_engine
from app.config import settings

router = APIRouter(prefix="/api/chat", tags=["Chat & RAG"])

@router.post("/query", response_model=ChatQueryResponse)
def ask_question(
    request: ChatQueryRequest,
    db: Session = Depends(get_db)
):
    """
    Submit a question to the RAG engine.
    Retrieves most relevant chunks from ChromaDB and generates an answer using Gemini or Groq.
    """
    try:
        response = rag_engine.query_rag(
            db=db,
            query=request.message,
            session_id=request.session_id,
            document_ids=request.document_ids,
            top_k=request.top_k or 4,
            provider=request.provider,
            api_key=request.api_key
        )
        return response
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"RAG Error: {str(e)}")


@router.get("/sessions", response_model=List[ChatSessionResponse])
def list_sessions(db: Session = Depends(get_db)):
    """List all previous conversation sessions."""
    sessions = db.query(ChatSession).order_by(ChatSession.updated_at.desc()).all()
    results = []
    for s in sessions:
        results.append(ChatSessionResponse(
            id=s.id,
            session_id=s.session_id,
            title=s.title,
            created_at=s.created_at,
            updated_at=s.updated_at,
            message_count=len(s.messages)
        ))
    return results


@router.get("/sessions/{session_id}", response_model=List[ChatMessageResponse])
def get_session_messages(session_id: str, db: Session = Depends(get_db)):
    """Get all messages and citations for a specific conversation session."""
    session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )

    response_messages = []
    for m in messages:
        sources_list = None
        if m.sources:
            try:
                raw_sources = json.loads(m.sources)
                sources_list = [SourceCitation(**src) for src in raw_sources]
            except Exception:
                sources_list = None

        response_messages.append(ChatMessageResponse(
            id=m.id,
            role=m.role,
            content=m.content,
            model_used=m.model_used,
            sources=sources_list,
            created_at=m.created_at
        ))

    return response_messages


@router.delete("/sessions/{session_id}")
def delete_session(session_id: str, db: Session = Depends(get_db)):
    """Delete a conversation and all its messages."""
    session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    db.delete(session)
    db.commit()
    return {"message": "Chat session deleted successfully."}


@router.get("/config")
def get_system_config():
    """Check active LLM provider and available keys."""
    gemini_key_set = bool(os.getenv("GEMINI_API_KEY") or settings.GEMINI_API_KEY)
    groq_key_set = bool(os.getenv("GROQ_API_KEY") or settings.GROQ_API_KEY)

    return {
        "default_provider": settings.DEFAULT_LLM_PROVIDER,
        "gemini_model": settings.GEMINI_MODEL,
        "groq_model": settings.GROQ_MODEL,
        "gemini_configured": gemini_key_set,
        "groq_configured": groq_key_set
    }
