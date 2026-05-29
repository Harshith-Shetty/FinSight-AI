"""
Re-triggers Celery processing tasks for documents stuck in PENDING/FAILED state.
Run with: python retrigger_docs.py
"""
import asyncio
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.database import Document, ProcessingStatus
from app.worker.tasks import process_document_task


async def retrigger():
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Document).where(
                Document.processing_status.in_([
                    ProcessingStatus.PENDING,
                    ProcessingStatus.FAILED
                ])
            )
        )
        docs = result.scalars().all()

        if not docs:
            print("No stuck documents found.")
            return

        for doc in docs:
            print(f"Re-triggering: {doc.filename} (id={doc.id}, status={doc.processing_status})")
            # Reset to PENDING first
            doc.processing_status = ProcessingStatus.PENDING
            await db.commit()

            # Re-enqueue the Celery task
            process_document_task.delay(
                document_id=str(doc.id),
                user_id=str(doc.user_id),
                file_path=doc.file_path,
                file_type=doc.file_type,
                filename=doc.filename
            )
            print(f"  ✅ Task enqueued for {doc.filename}")

        print(f"\nDone. {len(docs)} document(s) re-queued.")

if __name__ == "__main__":
    asyncio.run(retrigger())
