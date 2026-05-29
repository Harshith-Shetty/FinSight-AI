"""
Public Knowledge Base document endpoints.
Admin-only upload, all authenticated users can list/view.
"""

from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.database import User, Document, ProcessingStatus, UserRole
from app.models.schemas import DocumentUploadResponse, DocumentListResponse
from app.api.deps import get_current_user
from app.core.permissions import require_role
from app.worker.tasks import process_document_task

router = APIRouter(prefix="/api/v1/public-documents", tags=["Public Knowledge Base"])

UPLOAD_DIR = Path("uploads/public")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
ALLOWED_EXTENSIONS = {".pdf", ".txt", ".docx", ".md"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_public_document(
    file: UploadFile = File(...),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Upload a document to the Public Knowledge Base. Admin only."""
    # Validate extension
    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {suffix}")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 10 MB)")

    # Save to disk
    file_path = UPLOAD_DIR / f"{file.filename}"
    file_path.write_bytes(content)

    # Create DB record with is_system_doc=True
    doc = Document(
        user_id=current_user.id,
        filename=file.filename,
        file_path=str(file_path),
        file_size=len(content),
        file_type=suffix.lstrip("."),
        is_system_doc=True,
        processing_status=ProcessingStatus.PENDING,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    # Enqueue Celery task — stores in system_knowledge_base collection
    process_document_task.delay(
        document_id=str(doc.id),
        user_id=str(current_user.id),
        file_path=str(file_path),
        file_type=suffix.lstrip("."),
        filename=file.filename,
        is_public=True,
    )

    return doc


@router.get("", response_model=list[DocumentListResponse])
async def list_public_documents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all Public Knowledge Base documents. All authenticated users."""
    result = await db.execute(
        select(Document)
        .where(Document.is_system_doc == True)
        .order_by(Document.upload_date.desc())
    )
    return result.scalars().all()


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_public_document(
    doc_id: UUID,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Delete a Public Knowledge Base document. Admin only."""
    result = await db.execute(
        select(Document).where(Document.id == doc_id, Document.is_system_doc == True)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Public document not found")

    await db.delete(doc)
    await db.commit()
    return None
