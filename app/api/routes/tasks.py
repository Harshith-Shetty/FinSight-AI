"""
Tasks endpoint - GET /api/v1/tasks/{task_id}
Returns task status and results.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.models.schemas import TaskStatusResponse, TaskStatusEnum
from app.models.database import AnalysisTask, User
from app.core.database import get_db
from app.api.deps import get_current_user

router = APIRouter()


@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get the status and result of an analysis task.
    
    **Workflow:**
    1. Query database for task by ID
    2. Return current status
    3. If COMPLETED, include analysis results
    4. If FAILED, include error message
    
    **Status Values:**
    - `PENDING`: Task is queued, waiting for worker
    - `PROCESSING`: Worker is actively processing the task
    - `COMPLETED`: Analysis finished successfully
    - `FAILED`: Analysis failed (check error field)
    
    **Usage:**
    ```bash
    curl http://localhost:8000/api/v1/tasks/{task_id}
    ```
    """
    # Query task (scoped to the authenticated user to prevent IDOR)
    stmt = select(AnalysisTask).where(
        AnalysisTask.task_id == task_id,
        AnalysisTask.user_id == current_user.id
    )
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )
    
    # Map database status to API status
    status_map = {
        "PENDING": TaskStatusEnum.PENDING,
        "PROCESSING": TaskStatusEnum.PROCESSING,
        "COMPLETED": TaskStatusEnum.COMPLETED,
        "FAILED": TaskStatusEnum.FAILED,
    }
    
    return TaskStatusResponse(
        task_id=task.task_id,
        status=status_map[task.status.value],
        result=task.result_json if task.status.value == "COMPLETED" else None,
        error=task.error_log if task.status.value == "FAILED" else None,
        created_at=task.created_at,
        completed_at=task.completed_at
    )
