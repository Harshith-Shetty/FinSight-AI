"""
Message API endpoints with streaming support.
"""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import json

from app.core.database import get_db
from app.models.database import User, Message, MessageRole
from app.models.schemas import MessageCreate, MessageResponse, ChatHistoryResponse
from app.api.routes.auth import get_current_user
from app.services.chat_service import ChatService
from app.services.rag_service import RAGService

router = APIRouter(prefix="/chats", tags=["Messages"])
chat_service = ChatService()
rag_service = RAGService()


@router.post("/{chat_id}/messages", response_model=ChatHistoryResponse)
async def send_message(
    chat_id: UUID,
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Send a message and get AI response (synchronous).
    
    - **content**: Message content
    
    Returns both the user message and AI response.
    """
    # Verify chat exists and belongs to user
    chat = await chat_service.get_chat(db, chat_id, current_user.id)
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )
    
    # Save user message
    user_message = Message(
        chat_id=chat_id,
        role=MessageRole.USER,
        content=message_data.content
    )
    db.add(user_message)
    await db.commit()
    await db.refresh(user_message)
    
    # Generate AI response using RAG
    response = await rag_service.generate_response(
        user_id=current_user.id,
        query=message_data.content,
        mode=chat.mode
    )
    
    # Save AI message
    ai_message = Message(
        chat_id=chat_id,
        role=MessageRole.ASSISTANT,
        content=response["text"],
        message_metadata={
            "sources": response["sources"],
            "mode": response["mode"]
        }
    )
    db.add(ai_message)
    await db.commit()
    await db.refresh(ai_message)
    
    # Auto-generate chat title from first message
    if chat.title == "New Chat":
        title = await chat_service.generate_chat_title(message_data.content)
        await chat_service.update_chat_title(db, chat_id, title)
    
    return {
        "user_message": user_message,
        "assistant_message": ai_message
    }


@router.post("/{chat_id}/messages/stream")
async def send_message_stream(
    chat_id: UUID,
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Send a message and stream AI response (Server-Sent Events).
    
    - **content**: Message content
    
    Returns a stream of response chunks.
    """
    # Verify chat exists and belongs to user
    chat = await chat_service.get_chat(db, chat_id, current_user.id)
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )
    
    # Save user message
    user_message = Message(
        chat_id=chat_id,
        role=MessageRole.USER,
        content=message_data.content
    )
    db.add(user_message)
    await db.commit()
    await db.refresh(user_message)
    
    async def event_generator():
        """Generate Server-Sent Events."""
        # Send user message ID
        yield f"data: {json.dumps({'type': 'user_message', 'message_id': str(user_message.id)})}\n\n"
        
        # Collect full response for saving
        full_response = ""
        sources = []
        
        # Stream AI response
        async for chunk in rag_service.generate_response_stream(
            user_id=current_user.id,
            query=message_data.content,
            mode=chat.mode
        ):
            if chunk["type"] == "chunk":
                full_response += chunk["content"]
                yield f"data: {json.dumps(chunk)}\n\n"
            elif chunk["type"] == "sources":
                sources = chunk["sources"]
                yield f"data: {json.dumps(chunk)}\n\n"
            elif chunk["type"] == "done":
                # Save AI message to database
                ai_message = Message(
                    chat_id=chat_id,
                    role=MessageRole.ASSISTANT,
                    content=full_response,
                    message_metadata={
                        "sources": sources,
                        "mode": chat.mode.value
                    }
                )
                db.add(ai_message)
                await db.commit()
                await db.refresh(ai_message)
                
                # Auto-generate chat title from first message
                if chat.title == "New Chat":
                    title = await chat_service.generate_chat_title(message_data.content)
                    await chat_service.update_chat_title(db, chat_id, title)
                
                # Send final message with AI message ID
                yield f"data: {json.dumps({'type': 'done', 'message_id': str(ai_message.id)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.get("/{chat_id}/messages", response_model=List[MessageResponse])
async def get_chat_history(
    chat_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 100
):
    """
    Get chat message history.
    
    - **limit**: Maximum number of messages to return (default: 100)
    """
    messages = await chat_service.get_chat_messages(
        db=db,
        chat_id=chat_id,
        user_id=current_user.id,
        limit=limit
    )
    
    return messages
