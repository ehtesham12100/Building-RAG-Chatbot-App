from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field

# --- User Schemas ---
class UserBase(BaseModel):
    username: str
    email: Optional[str] = None

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# --- Document Schemas ---
class DocumentResponse(BaseModel):
    id: int
    title: str
    file_size: int
    page_count: int
    chunk_count: int
    status: str
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentDetailResponse(DocumentResponse):
    file_path: str


# --- Chat & RAG Schemas ---
class SourceCitation(BaseModel):
    document_id: int
    document_title: str
    page_number: int
    chunk_index: int
    snippet: str
    similarity_score: Optional[float] = None


class ChatMessageResponse(BaseModel):
    id: int
    role: str
    content: str
    model_used: Optional[str] = None
    sources: Optional[List[SourceCitation]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ChatSessionCreate(BaseModel):
    title: Optional[str] = "New Conversation"


class ChatSessionResponse(BaseModel):
    id: int
    session_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0

    class Config:
        from_attributes = True


class ChatQueryRequest(BaseModel):
    session_id: Optional[str] = None
    message: str = Field(..., min_length=1, description="Question or prompt from user")
    document_ids: Optional[List[int]] = Field(default=None, description="List of document IDs to query against. If None, queries all indexed docs.")
    top_k: Optional[int] = Field(default=4, description="Number of top chunks to retrieve")
    provider: Optional[str] = Field(default=None, description="Override LLM provider ('gemini' or 'groq')")
    api_key: Optional[str] = Field(default=None, description="Optional per-request API key")


class ChatQueryResponse(BaseModel):
    session_id: str
    answer: str
    model_used: str
    provider: str
    sources: List[SourceCitation]
