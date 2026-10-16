import os
import shutil
from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Document, User
from app.schemas import DocumentResponse, DocumentDetailResponse
from app.config import settings
from app.services.pdf_processor import pdf_processor
from app.services.vector_store import vector_store

router = APIRouter(prefix="/api/documents", tags=["Documents"])

@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF documents are supported."
        )

    # 1. Clean filename & save file to disk
    original_filename = file.filename
    clean_filename = os.path.basename(original_filename).replace(" ", "_")
    target_path = os.path.join(settings.UPLOAD_PATH, clean_filename)

    # Handle duplicate filenames
    base_name, ext = os.path.splitext(clean_filename)
    counter = 1
    while os.path.exists(target_path):
        target_path = os.path.join(settings.UPLOAD_PATH, f"{base_name}_{counter}{ext}")
        counter += 1

    try:
        with open(target_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        file_size = os.path.getsize(target_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    # 2. Record document in SQLite database
    doc_record = Document(
        title=original_filename,
        file_path=target_path,
        file_size=file_size,
        status="processing"
    )
    db.add(doc_record)
    db.commit()
    db.refresh(doc_record)

    # 3. Process PDF and generate embeddings in ChromaDB
    try:
        chunks = pdf_processor.process_pdf(
            file_path=target_path,
            document_id=doc_record.id,
            document_title=original_filename
        )

        if not chunks:
            doc_record.status = "empty"
            doc_record.error_message = "No extractable text found in this PDF (might be image-only scan or empty)."
            db.commit()
            return doc_record

        # Determine page count from extracted pages
        pages = pdf_processor.extract_text_by_pages(target_path)
        doc_record.page_count = len(pages)
        doc_record.chunk_count = len(chunks)

        # Index into ChromaDB
        vector_store.add_chunks(chunks)

        doc_record.status = "indexed"
        db.commit()
        db.refresh(doc_record)
        return doc_record

    except Exception as e:
        doc_record.status = "error"
        doc_record.error_message = str(e)
        db.commit()
        db.refresh(doc_record)
        return doc_record


@router.get("", response_model=List[DocumentResponse])
def list_documents(db: Session = Depends(get_db)):
    """List all uploaded documents."""
    docs = db.query(Document).order_by(Document.created_at.desc()).all()
    return docs


@router.get("/{document_id}", response_model=DocumentDetailResponse)
def get_document(document_id: int, db: Session = Depends(get_db)):
    """Get single document details."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.delete("/{document_id}")
def delete_document(document_id: int, db: Session = Depends(get_db)):
    """Delete document from SQLite, disk, and vector store."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # 1. Delete chunks from ChromaDB
    vector_store.delete_document_chunks(document_id)

    # 2. Delete physical file
    if os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
        except Exception:
            pass

    # 3. Remove from SQLite
    db.delete(doc)
    db.commit()

    return {"message": f"Document '{doc.title}' deleted successfully."}
