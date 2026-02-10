"""
Document management API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import os
import uuid as uuid_lib
from pathlib import Path

from app.models.schemas import DocumentUploadResponse, DocumentListResponse
from app.models.database import Document, User, ProcessingStatus
from app.api.routes.auth import get_current_user
from app.core.database import get_db
from app.worker.tasks import process_document_task

router = APIRouter(prefix="/api/v1/documents", tags=["Documents"])

# Upload directory
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Allowed file types
ALLOWED_EXTENSIONS = {".pdf", ".txt", ".docx"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a document for processing.
    
    - **file**: PDF, TXT, or DOCX file (max 10MB)
    
    Returns document ID and processing status.
    """
    # Validate file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not supported. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Read file content
    content = await file.read()
    file_size = len(content)
    
    # Validate file size
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE / 1024 / 1024}MB"
        )
    
    # Create user directory
    user_dir = UPLOAD_DIR / str(current_user.id)
    user_dir.mkdir(exist_ok=True)
    
    # Generate document ID and save file
    doc_id = uuid_lib.uuid4()
    safe_filename = f"{doc_id}_{file.filename}"
    file_path = user_dir / safe_filename
    
    # Save file to disk
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Create database record
    document = Document(
        id=doc_id,
        user_id=current_user.id,
        filename=file.filename,
        file_path=str(file_path),
        file_size=file_size,
        file_type=file_ext,
        processing_status=ProcessingStatus.PENDING
    )
    
    db.add(document)
    await db.commit()
    await db.refresh(document)
    
    # Enqueue Celery task for processing
    process_document_task.delay(
        document_id=str(doc_id),
        user_id=str(current_user.id),
        file_path=str(file_path),
        file_type=file_ext,
        filename=file.filename
    )
    
    return document


@router.get("", response_model=List[DocumentListResponse])
async def list_documents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all documents for the current user.
    """
    result = await db.execute(
        select(Document)
        .where(Document.user_id == current_user.id)
        .order_by(Document.upload_date.desc())
    )
    documents = result.scalars().all()
    
    return documents


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a document and its vectors from Qdrant.
    """
    # Get document
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.user_id == current_user.id
        )
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Delete file from disk
    try:
        if os.path.exists(document.file_path):
            os.remove(document.file_path)
    except Exception as e:
        print(f"Failed to delete file: {e}")
    
    # Delete vectors from Qdrant
    from app.services.vector_store import QdrantVectorStore
    vector_store = QdrantVectorStore()
    try:
        await vector_store.delete_user_document(
            user_id=str(current_user.id),
            document_id=str(document_id)
        )
    except Exception as e:
        print(f"Failed to delete vectors: {e}")
    
    # Delete database record
    await db.delete(document)
    await db.commit()
    
    return None


@router.get("/{document_id}/status", response_model=DocumentListResponse)
async def get_document_status(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get processing status of a document.
    """
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.user_id == current_user.id
        )
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return document
