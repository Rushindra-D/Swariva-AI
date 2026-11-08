"""
SWARIVA AI — Conversation Management Endpoints
Lists, inspects, and manages persistent user dialogues and message histories.
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status, Depends

from repositories.conversation_repo import ConversationRepository
from auth import get_current_user

router = APIRouter(prefix="/api/v1/conversations", tags=["Conversation History"])


@router.get("", summary="List conversation sessions")
async def list_conversations(current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """
    Returns list of previous conversation sessions.
    Scoped to user when authenticated.
    """
    user_id = current_user["id"] if current_user else None
    items = ConversationRepository.list_conversations(user_id=user_id)
    return {"conversations": items, "count": len(items)}


@router.get("/{conversation_id}", summary="Get conversation messages")
async def get_conversation_messages(
    conversation_id: str,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user),
):
    """
    Retrieves chronological messages for an active or previous conversation.
    Enforces user isolation.
    """
    user_id = current_user["id"] if current_user else None
    messages = ConversationRepository.get_messages(conversation_id, user_id=user_id)
    return {
        "conversation_id": conversation_id,
        "total_messages": len(messages),
        "messages": messages,
    }


@router.delete("/{conversation_id}", summary="Delete a conversation")
async def delete_conversation(
    conversation_id: str,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user),
):
    """
    Permanently deletes a conversation and all its dialogue turns.
    """
    user_id = current_user["id"] if current_user else None
    deleted = ConversationRepository.delete_conversation(conversation_id, user_id=user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' not found.",
        )
    return {"success": True, "message": "Conversation deleted."}

