"""
SWARIVA AI — Chat Schemas
Request and response models for text chat and conversation management.
"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Incoming user text query."""
    message: str = Field(..., min_length=1, max_length=2000, description="The user's input message.")
    session_id: Optional[str] = Field(None, description="Active session ID. If omitted, a new session is created.")
    language: Optional[str] = Field("auto", description="Preferred response language ('english', 'hindi', 'telugu', or 'auto').")
    include_audio: bool = Field(False, description="Whether to also synthesize and return Timbre TTS audio for the response.")
    voice: Optional[str] = Field(None, description="Optional custom Timbre voice name (e.g. 'Nalini', 'Deepak').")


class ChatResponse(BaseModel):
    """Outgoing assistant response for text chat."""
    response: str = Field(..., description="The AI assistant's generated response.")
    session_id: str = Field(..., description="The session identifier maintaining conversation context.")
    language: str = Field(..., description="The language of the response.")
    audio_base64: Optional[str] = Field(None, description="Base64-encoded WAV audio (if include_audio was true).")
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Execution and routing metadata.")


class SessionClearResponse(BaseModel):
    """Confirmation of session history clearing."""
    session_id: str
    message: str
    cleared: bool


class MessageItem(BaseModel):
    """Single message entry in conversation history."""
    role: str
    content: str
    timestamp: float
    language: Optional[str] = None


class ChatHistoryResponse(BaseModel):
    """History of messages in a session."""
    session_id: str
    total_messages: int
    messages: List[MessageItem]

