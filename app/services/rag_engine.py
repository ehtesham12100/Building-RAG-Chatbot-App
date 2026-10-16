import json
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.services.vector_store import vector_store
from app.services.llm_service import llm_service
from app.models import ChatSession, ChatMessage
from app.schemas import SourceCitation, ChatQueryResponse
import uuid

class RAGEngine:
    def __init__(self):
        pass

    def get_or_create_session(self, db: Session, session_id: Optional[str] = None, user_id: Optional[int] = None) -> ChatSession:
        if session_id:
            session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
            if session:
                return session

        # Create new session
        new_session_id = session_id or str(uuid.uuid4())
        session = ChatSession(
            session_id=new_session_id,
            user_id=user_id,
            title="Document Q&A Session"
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    def query_rag(
        self,
        db: Session,
        query: str,
        session_id: Optional[str] = None,
        document_ids: Optional[List[int]] = None,
        top_k: int = 4,
        provider: Optional[str] = None,
        api_key: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> ChatQueryResponse:
        # 1. Get or create chat session
        session = self.get_or_create_session(db, session_id, user_id)

        # 2. Retrieve relevant chunks from ChromaDB
        retrieved_chunks = vector_store.query_similar(
            query_text=query,
            n_results=top_k,
            document_ids=document_ids
        )

        # 2b. If this is a high-level summary or overview query, also fetch introductory chunks
        summary_keywords = ["summary", "summarize", "overview", "main point", "about this", "core concept", "key point"]
        is_summary = any(k in query.lower() for k in summary_keywords)
        if is_summary:
            # Query introductory page chunks
            intro_chunks = vector_store.query_similar(
                query_text="Introduction overview topics concepts summary",
                n_results=2,
                document_ids=document_ids
            )
            existing_ids = {c.get("id") for c in retrieved_chunks}
            for ic in intro_chunks:
                if ic.get("id") not in existing_ids:
                    retrieved_chunks.insert(0, ic)
                    existing_ids.add(ic.get("id"))
            # Keep top_k + 2 max
            retrieved_chunks = retrieved_chunks[:top_k + 2]

        # 3. Format SourceCitations
        source_citations: List[SourceCitation] = []
        for chunk in retrieved_chunks:
            meta = chunk.get("metadata", {})
            snippet = chunk.get("text", "")
            if len(snippet) > 300:
                snippet = snippet[:300] + "..."

            source_citations.append(
                SourceCitation(
                    document_id=meta.get("document_id", 0),
                    document_title=meta.get("document_title", "Unknown"),
                    page_number=meta.get("page_number", 1),
                    chunk_index=meta.get("chunk_index", 0),
                    snippet=snippet,
                    similarity_score=chunk.get("similarity", 0.0)
                )
            )

        # 4. Fetch recent chat history from database
        history_msgs = (
            db.query(ChatMessage)
            .filter(ChatMessage.session_id == session.id)
            .order_by(ChatMessage.created_at.desc())
            .limit(6)
            .all()
        )
        # Reverse to chronological order
        history = [{"role": m.role, "content": m.content} for m in reversed(history_msgs)]

        # 5. Generate LLM response
        llm_result = llm_service.generate_rag_response(
            query=query,
            context_chunks=retrieved_chunks,
            chat_history=history,
            provider=provider,
            api_key=api_key
        )

        answer = llm_result["answer"]
        model_used = llm_result["model_used"]
        used_provider = llm_result["provider"]

        # 6. Save User message to SQLite
        user_msg = ChatMessage(
            session_id=session.id,
            role="user",
            content=query
        )
        db.add(user_msg)

        # 7. Save Assistant response with serialised sources to SQLite
        sources_json = json.dumps([s.model_dump() for s in source_citations])
        assistant_msg = ChatMessage(
            session_id=session.id,
            role="assistant",
            content=answer,
            model_used=model_used,
            sources=sources_json
        )
        db.add(assistant_msg)

        # Update session title if default
        if session.title == "Document Q&A Session" or session.title == "New Chat":
            clean_title = query.strip()
            if len(clean_title) > 40:
                clean_title = clean_title[:37] + "..."
            session.title = clean_title

        db.commit()

        return ChatQueryResponse(
            session_id=session.session_id,
            answer=answer,
            model_used=model_used,
            provider=used_provider,
            sources=source_citations
        )

rag_engine = RAGEngine()
