"""
Chat management API endpoints.
"""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.database import User, ChatMode
from app.models.schemas import ChatCreate, ChatResponse, ChatListResponse
from app.api.deps import get_current_user
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chats", tags=["Chats"])
chat_service = ChatService()


@router.post("", response_model=ChatResponse, status_code=status.HTTP_201_CREATED)
async def create_chat(
    chat_data: ChatCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new chat session.
    
    - **mode**: Chat mode (hybrid or private)
    - **title**: Optional chat title (will be auto-generated from first message if not provided)
    """
    chat = await chat_service.create_chat(
        db=db,
        user_id=current_user.id,
        mode=chat_data.mode,
        title=chat_data.title
    )
    
    return chat


@router.get("", response_model=List[ChatResponse])
async def list_chats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=200)
):
    """
    Get all chats for the current user.
    
    - **limit**: Maximum number of chats to return (default: 50)
    """
    chats = await chat_service.get_user_chats(
        db=db,
        user_id=current_user.id,
        limit=limit
    )
    
    return chats


@router.get("/{chat_id}", response_model=ChatResponse)
async def get_chat(
    chat_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific chat by ID.
    """
    chat = await chat_service.get_chat(
        db=db,
        chat_id=chat_id,
        user_id=current_user.id
    )
    
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )
    
    return chat


@router.delete("/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat(
    chat_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a chat and all its messages.
    """
    deleted = await chat_service.delete_chat(
        db=db,
        chat_id=chat_id,
        user_id=current_user.id
    )
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )
    
    return None
