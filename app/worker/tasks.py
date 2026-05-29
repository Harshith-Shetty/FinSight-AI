"""
Celery worker tasks for background processing.
"""

from celery import Task
from sqlalchemy import select, update
from datetime import datetime
import asyncio

from app.worker.celery_app import celery_app
from app.models.database import AnalysisTask, TaskStatus, Document, ProcessingStatus
from app.core.database import AsyncSessionLocal
from app.services.rag_pipeline import RAGPipeline


class DatabaseTask(Task):
    """Base task with database session management."""
    
    def __init__(self):
        self._db = None
    
    @property
    def db(self):
        if self._db is None:
            self._db = AsyncSessionLocal()
        return self._db


@celery_app.task(bind=True, base=DatabaseTask, name="process_financial_analysis")
def process_financial_analysis(
    self,
    task_id: str,
    ticker: str,
    focus_area: str,
    filing_year: int
):
    """
    Background task for financial analysis using RAG.
    
    This task:
    1. Updates task status to PROCESSING
    2. Fetches SEC filing data
    3. Generates embeddings and stores in Qdrant
    4. Retrieves relevant context
    5. Generates LLM analysis
    6. Updates task with results or error
    
    Args:
        task_id: UUID of the analysis task
        ticker: Stock ticker symbol
        focus_area: Analysis focus area
        filing_year: SEC filing year
    """
    # Run async code in sync context
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(
        _process_analysis_async(task_id, ticker, focus_area, filing_year)
    )


async def _process_analysis_async(
    task_id: str,
    ticker: str,
    focus_area: str,
    filing_year: int
):
    """Async implementation of analysis task."""
    
    async with AsyncSessionLocal() as db:
        try:
            # Update status to PROCESSING
            await db.execute(
                update(AnalysisTask)
                .where(AnalysisTask.task_id == task_id)
                .values(status=TaskStatus.PROCESSING)
            )
            await db.commit()
            
            # Execute RAG pipeline
            pipeline = RAGPipeline()
            result = await pipeline.analyze(
                ticker=ticker,
                focus_area=focus_area,
                filing_year=filing_year
            )
            await pipeline.cleanup()
            
            # Update task with results
            await db.execute(
                update(AnalysisTask)
                .where(AnalysisTask.task_id == task_id)
                .values(
                    status=TaskStatus.COMPLETED,
                    result_json=result,
                    completed_at=datetime.utcnow()
                )
            )
            await db.commit()
            
            return {"status": "success", "task_id": task_id}
            
        except Exception as e:
            # Update task with error
            error_message = f"{type(e).__name__}: {str(e)}"
            
            await db.execute(
                update(AnalysisTask)
                .where(AnalysisTask.task_id == task_id)
                .values(
                    status=TaskStatus.FAILED,
                    error_log=error_message,
                    completed_at=datetime.utcnow()
                )
            )
            await db.commit()
            
            return {"status": "failed", "error": error_message}


@celery_app.task(bind=True, name="process_document")
def process_document_task(
    self,
    document_id: str,
    user_id: str,
    file_path: str,
    file_type: str,
    filename: str,
    is_public: bool = False,
):
    """
    Background task for processing uploaded documents.
    If is_public=True, stores vectors in system_knowledge_base collection.
    Otherwise stores in the per-user collection.
    """
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(
        _process_document_async(document_id, user_id, file_path, file_type, filename, is_public)
    )


async def _process_document_async(
    document_id: str,
    user_id: str,
    file_path: str,
    file_type: str,
    filename: str,
    is_public: bool = False,
):
    """Async implementation of document processing task."""
    
    async with AsyncSessionLocal() as db:
        try:
            # Update status to PROCESSING
            await db.execute(
                update(Document)
                .where(Document.id == document_id)
                .values(processing_status=ProcessingStatus.PROCESSING)
            )
            await db.commit()
            
            # Parse document
            from app.services.document_processor import DocumentProcessor
            processor = DocumentProcessor()
            text = processor.parse_document(file_path, file_type)
            
            # Chunk text
            chunks = processor.chunk_text(text)
            
            # Generate embeddings
            from app.services.embeddings import EmbeddingGenerator
            embedding_gen = EmbeddingGenerator()
            embeddings = await embedding_gen.generate_embeddings(chunks)
            
            # Store in Qdrant — route to system KB or per-user collection
            from app.services.vector_store import QdrantVectorStore
            vector_store = QdrantVectorStore()
            if is_public:
                await vector_store.upsert_system_kb_vectors(
                    document_id=document_id,
                    filename=filename,
                    chunks=chunks,
                    embeddings=embeddings
                )
            else:
                await vector_store.upsert_user_vectors(
                    user_id=user_id,
                    document_id=document_id,
                    filename=filename,
                    chunks=chunks,
                    embeddings=embeddings
                )
            
            # Update status to COMPLETED
            await db.execute(
                update(Document)
                .where(Document.id == document_id)
                .values(processing_status=ProcessingStatus.COMPLETED)
            )
            await db.commit()
            
            return {"status": "success", "document_id": document_id, "chunks": len(chunks)}
            
        except Exception as e:
            # Update status to FAILED
            error_message = f"{type(e).__name__}: {str(e)}"
            
            await db.execute(
                update(Document)
                .where(Document.id == document_id)
                .values(processing_status=ProcessingStatus.FAILED)
            )
            await db.commit()
            
            return {"status": "failed", "error": error_message}
