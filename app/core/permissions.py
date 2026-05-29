"""
Permission helpers and token quota management for RBAC.
"""

from datetime import date
from uuid import UUID
from typing import Optional

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.models.database import User, UserRole, TokenUsage, ROLE_TOKEN_LIMITS
from app.api.deps import get_current_user


def _role_str(role) -> str:
    """Normalize role to uppercase string for comparison."""
    if isinstance(role, UserRole):
        return role.value.upper()
    return str(role).upper()


def _get_user_role(user: User) -> UserRole:
    """Safely get UserRole enum from user.role (which may be a string)."""
    raw = str(user.role).upper()
    for r in UserRole:
        if r.value.upper() == raw:
            return r
    return UserRole.NORMAL


# ─────────────────────────────────────────────
# Role guard dependency
# ─────────────────────────────────────────────

def require_role(*roles: UserRole):
    """FastAPI dependency — raises 403 if user's role is not in allowed list."""
    allowed = {_role_str(r) for r in roles}
    async def _check(current_user: User = Depends(get_current_user)):
        if _role_str(current_user.role) not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This action requires one of: {[r.value for r in roles]}"
            )
        return current_user
    return _check


# ─────────────────────────────────────────────
# Token quota helpers
# ─────────────────────────────────────────────

def _current_month() -> date:
    today = date.today()
    return today.replace(day=1)


async def get_token_usage(user_id: UUID, db: AsyncSession) -> TokenUsage:
    """Get or create the TokenUsage row for this user for the current month."""
    month = _current_month()
    result = await db.execute(
        select(TokenUsage).where(
            TokenUsage.user_id == user_id,
            TokenUsage.month == month
        )
    )
    usage = result.scalar_one_or_none()
    if not usage:
        usage = TokenUsage(user_id=user_id, month=month, tokens_used=0)
        db.add(usage)
        await db.commit()
        await db.refresh(usage)
    return usage


async def get_token_quota_status(user: User, db: AsyncSession) -> dict:
    """Returns quota info for the current month."""
    usage = await get_token_usage(user.id, db)
    user_role = _get_user_role(user)
    limit = ROLE_TOKEN_LIMITS.get(user_role)
    remaining = None if limit is None else max(0, limit - usage.tokens_used)
    return {
        "tokens_used": usage.tokens_used,
        "limit": limit,
        "remaining": remaining,
        "month": usage.month.isoformat(),
        "is_over_limit": False if limit is None else usage.tokens_used >= limit,
    }


async def check_token_quota(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Hard-limit dependency — blocks request if token quota is reached.
    Returns the user so it can be chained with other dependencies.
    """
    # Admin always passes
    if _role_str(current_user.role) == "ADMIN":
        return current_user

    quota = await get_token_quota_status(current_user, db)
    if quota["is_over_limit"]:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Monthly token limit reached. Please upgrade your plan to continue."
        )
    return current_user


async def record_token_usage(user_id: UUID, tokens: int, db: AsyncSession) -> int:
    """
    Add `tokens` to this user's current-month usage.
    Returns the new total.
    """
    usage = await get_token_usage(user_id, db)
    usage.tokens_used += tokens
    await db.commit()
    await db.refresh(usage)
    return usage.tokens_used
