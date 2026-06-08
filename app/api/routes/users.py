from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.database import User, PlanUpgradeRequest, UpgradeRequestStatus, TokenUsage
from app.models.schemas import PlanUpgradeRequestCreate, PlanUpgradeRequestResponse, UserResponse
from app.core.permissions import require_role, get_current_user, _current_month
from app.services.email_service import send_plan_upgrade_request_email

router = APIRouter(prefix="/api/v1/users", tags=["Users"])


@router.get("/me", response_model=dict)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's profile including tokens and active plan upgrade request."""
    # Get tokens
    month = _current_month()
    usage_result = await db.execute(
        select(TokenUsage).where(
            TokenUsage.user_id == current_user.id,
            TokenUsage.month == month
        )
    )
    usage = usage_result.scalar_one_or_none()
    tokens = usage.tokens_used if usage else 0
    
    # Check for pending upgrade request
    request_result = await db.execute(
        select(PlanUpgradeRequest).where(
            PlanUpgradeRequest.user_id == current_user.id,
            PlanUpgradeRequest.status == UpgradeRequestStatus.PENDING
        )
    )
    pending_request = request_result.scalar_one_or_none()
    
    return {
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "role": current_user.role.value,
            "created_at": current_user.created_at,
        },
        "tokens_used_this_month": tokens,
        "has_pending_upgrade_request": pending_request is not None
    }


@router.post("/upgrade-request", response_model=PlanUpgradeRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_upgrade_request(
    body: PlanUpgradeRequestCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Submit a plan upgrade request."""
    # Check if user is already premium or admin
    if current_user.role.value.upper() in ["PREMIUM", "ADMIN"]:
        raise HTTPException(status_code=400, detail="You are already on a premium or admin plan.")
    
    # Check if there is already a pending request
    request_result = await db.execute(
        select(PlanUpgradeRequest).where(
            PlanUpgradeRequest.user_id == current_user.id,
            PlanUpgradeRequest.status == UpgradeRequestStatus.PENDING
        )
    )
    existing_request = request_result.scalar_one_or_none()
    if existing_request:
        raise HTTPException(status_code=400, detail="You already have a pending upgrade request.")
    
    # Create request
    upgrade_request = PlanUpgradeRequest(
        user_id=current_user.id,
        reason=body.reason,
        status=UpgradeRequestStatus.PENDING
    )
    db.add(upgrade_request)
    await db.commit()
    await db.refresh(upgrade_request)
    
    # Send email to admin in the background (we can await it since it runs in executor)
    await send_plan_upgrade_request_email(
        user_email=current_user.email,
        reason=body.reason,
        request_id=str(upgrade_request.id)
    )
    
    return upgrade_request
