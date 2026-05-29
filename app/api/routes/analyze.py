"""
Analysis endpoint - POST /api/v1/analyze
Accepts financial analysis requests and returns task ID.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from app.models.schemas import AnalysisRequest, TaskResponse, TaskStatusEnum
from app.models.database import AnalysisTask, TaskStatus
from app.core.database import get_db

from app.core.permissions import check_token_quota
from app.models.database import User

router = APIRouter()


@router.post("/analyze", response_model=TaskResponse, status_code=status.HTTP_202_ACCEPTED)
async def submit_analysis(
    request: AnalysisRequest,
    current_user: User = Depends(check_token_quota),
    db: AsyncSession = Depends(get_db)
):
    """
    Submit a financial analysis request.
    
    This endpoint immediately returns with a task_id. The actual analysis
    runs asynchronously in the background via Celery workers.
    
    **Flow:**
    1. Validate request
    2. Create task record in database (status=PENDING)
    3. Enqueue task to Celery
    4. Return 202 Accepted with task_id
    
    **Usage:**
    ```bash
    curl -X POST http://localhost:8000/api/v1/analyze \\
      -H "Content-Type: application/json" \\
      -d '{
        "ticker": "AAPL",
        "focus_area": "risk_factors",
        "filing_year": 2024
      }'
    ```
    """
    # Create task record
    
    task = AnalysisTask(
        task_id=uuid4(),
        user_id=current_user.id,
        ticker_symbol=request.ticker,
        status=TaskStatus.PENDING,
        focus_area=request.focus_area,
        filing_year=request.filing_year
    )
    
    db.add(task)
    await db.commit()
    await db.refresh(task)
    
    # Enqueue Celery task for background processing
    from app.worker.tasks import process_financial_analysis
    
    process_financial_analysis.delay(
        task_id=str(task.task_id),
        ticker=request.ticker,
        focus_area=request.focus_area,
        filing_year=request.filing_year
    )
    
    return TaskResponse(
        task_id=task.task_id,
        status=TaskStatusEnum.PENDING,
        message="Analysis queued successfully. Use GET /api/v1/tasks/{task_id} to check status."
    )
