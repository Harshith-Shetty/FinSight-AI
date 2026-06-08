"""
Admin-only endpoints for user management and system stats.
"""

from uuid import UUID
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.models.database import User, UserRole, TokenUsage, Document, Chat, PlanUpgradeRequest, UpgradeRequestStatus
from app.models.schemas import UserAdminResponse, UpdateUserRoleRequest, UserRoleEnum, PlanUpgradeRequestResponse
from app.core.permissions import require_role, _current_month
from app.services.email_service import send_plan_upgrade_approved_email

router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])


@router.get("/users", response_model=list[UserAdminResponse])
async def list_users(
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """List all users with their role and current-month token usage."""
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()

    month = _current_month()
    output = []
    for user in users:
        # Get token usage for current month
        usage_result = await db.execute(
            select(TokenUsage).where(
                TokenUsage.user_id == user.id,
                TokenUsage.month == month
            )
        )
        usage = usage_result.scalar_one_or_none()
        tokens = usage.tokens_used if usage else 0

        output.append(UserAdminResponse(
            id=user.id,
            email=user.email,
            role=UserRoleEnum(user.role.value),
            created_at=user.created_at,
            last_login=user.last_login,
            tokens_used_this_month=tokens,
        ))
    return output


@router.put("/users/{user_id}/role", response_model=UserAdminResponse)
async def update_user_role(
    user_id: UUID,
    body: UpdateUserRoleRequest,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Change a user's role. Admin only."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Map schema enum → DB enum
    user.role = str(body.role.value).upper()
    await db.commit()
    await db.refresh(user)

    month = _current_month()
    usage_result = await db.execute(
        select(TokenUsage).where(TokenUsage.user_id == user.id, TokenUsage.month == month)
    )
    usage = usage_result.scalar_one_or_none()
    tokens = usage.tokens_used if usage else 0

    return UserAdminResponse(
        id=user.id,
        email=user.email,
        role=UserRoleEnum(user.role.value),
        created_at=user.created_at,
        last_login=user.last_login,
        tokens_used_this_month=tokens,
    )


@router.get("/stats")
async def system_stats(
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """System-wide stats for the admin dashboard."""
    month = _current_month()

    total_users = (await db.execute(select(func.count()).select_from(User))).scalar()
    total_docs  = (await db.execute(select(func.count()).select_from(Document).where(Document.is_system_doc == False))).scalar()
    public_docs = (await db.execute(select(func.count()).select_from(Document).where(Document.is_system_doc == True))).scalar()
    total_chats = (await db.execute(select(func.count()).select_from(Chat))).scalar()
    total_tokens_this_month = (
        await db.execute(select(func.sum(TokenUsage.tokens_used)).where(TokenUsage.month == month))
    ).scalar() or 0

    # Users by role
    role_counts = {}
    for role in UserRole:
        count = (await db.execute(
            select(func.count()).select_from(User).where(User.role == role)
        )).scalar()
        role_counts[role.value] = count

    return {
        "total_users": total_users,
        "users_by_role": role_counts,
        "total_private_documents": total_docs,
        "total_public_documents": public_docs,
        "total_chats": total_chats,
        "total_tokens_this_month": total_tokens_this_month,
        "month": month.isoformat(),
    }


@router.get("/upgrade-requests", response_model=list[dict])
async def list_upgrade_requests(
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """List pending upgrade requests."""
    result = await db.execute(
        select(PlanUpgradeRequest, User.email)
        .join(User, PlanUpgradeRequest.user_id == User.id)
        .where(PlanUpgradeRequest.status == UpgradeRequestStatus.PENDING)
        .order_by(PlanUpgradeRequest.created_at.desc())
    )
    rows = result.all()
    
    output = []
    for req, email in rows:
        output.append({
            "id": req.id,
            "user_id": req.user_id,
            "email": email,
            "reason": req.reason,
            "status": req.status.value,
            "created_at": req.created_at,
        })
    return output


@router.post("/upgrade-requests/{request_id}/approve")
async def approve_upgrade_request(
    request_id: UUID,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
):
    """Approve a plan upgrade request."""
    # Find request
    result = await db.execute(
        select(PlanUpgradeRequest).where(PlanUpgradeRequest.id == request_id)
    )
    req = result.scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=404, detail="Request not found")
        
    if req.status != UpgradeRequestStatus.PENDING:
        raise HTTPException(status_code=400, detail="Request is not pending")
        
    # Update request status
    req.status = UpgradeRequestStatus.APPROVED
    
    # Find user and update role
    user_result = await db.execute(select(User).where(User.id == req.user_id))
    user = user_result.scalar_one_or_none()
    if user:
        user.role = UserRole.PREMIUM.value.upper()
    
    await db.commit()
    
    # Send approval email
    if user:
        await send_plan_upgrade_approved_email(
            user_email=user.email,
            admin_email=current_user.email,
            plan="Premium"
        )
        
    return {"message": "Upgrade request approved"}
