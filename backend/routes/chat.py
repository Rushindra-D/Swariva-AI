"""
SWARIVA AI — Text Chat Routes
Handles text queries, multi-turn session continuity, and history management.
"""
import base64
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status

from schemas.chat import (
    ChatRequest,
    ChatResponse,
    SessionClearResponse,
    ChatHistoryResponse,
)
from conversation import conversation_manager
from agent import agent
from gnani_tts import GnaniTTS

router = APIRouter(prefix="/api/v1/chat", tags=["Text Chat"])

# Reusable TTS instance for optional audio response
tts_client = GnaniTTS()


@router.post("", response_model=ChatResponse, summary="Send a text message")
async def send_chat_message(req: ChatRequest):
    """
    Main text chat endpoint:
    - Maintains conversation context across multiple turns using session_id
    - Supports multilingual reasoning (English, Telugu, Hindi)
    - Optionally generates Timbre TTS audio for the response if include_audio=True
    """
    try:
        # Retrieve or initialize session
        session = conversation_manager.get_or_create(
            session_id=req.session_id,
            preferred_language=req.language or "auto",
        )

        # Generate intelligent response
        reply = await agent.generate_response(
            user_message=req.message,
            session=session,
            language=req.language or "auto",
        )

        audio_b64 = None
        # Optional TTS generation for read-along experience
        if req.include_audio and reply.speech_text:
            tts_res = await tts_client.synthesize(
                text=reply.speech_text,
                language=reply.language,
                voice=req.voice,
            )
            if tts_res.success and tts_res.audio_bytes:
                audio_b64 = base64.b64encode(tts_res.audio_bytes).decode("utf-8")

        return ChatResponse(
            response=reply.text,
            session_id=session.session_id,
            language=reply.language,
            audio_base64=audio_b64,
            timestamp=datetime.now(timezone.utc).isoformat(),
            metadata={
                **reply.metadata,
                "provider": reply.provider,
                "audio_included": bool(audio_b64),
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat processing failed: {str(e)}",
        )


@router.get("/history/{session_id}", response_model=ChatHistoryResponse, summary="Get session history")
async def get_session_history(session_id: str):
    """
    Fetches chronological message history for an active session.
    """
    session = conversation_manager.get(session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found.",
        )

    messages = session.get_all_messages()
    return ChatHistoryResponse(
        session_id=session.session_id,
        total_messages=len(messages),
        messages=messages,
    )


@router.post("/clear", response_model=SessionClearResponse, summary="Clear session context")
async def clear_session_context(payload: dict):
    """
    Clears all messages from a session to reset conversational context.
    """
    session_id = payload.get("session_id")
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="session_id is required.",
        )

    cleared = conversation_manager.clear(session_id)
    if not cleared:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found.",
        )

    return SessionClearResponse(
        session_id=session_id,
        message="Session history cleared successfully.",
        cleared=True,
    )
