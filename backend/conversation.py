"""
SWARIVA AI — Conversation Management Module

Maintains conversation sessions and context across turns.
Designed with in-memory storage for development, structured for
seamless database (Supabase) integration in Phase 5.
"""
import time
import uuid
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field

from repositories.conversation_repo import ConversationRepository


@dataclass
class Message:
    """A single dialogue turn."""
    role: str               # "user" or "assistant"
    content: str
    timestamp: float = field(default_factory=time.time)
    language: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
            "language": self.language,
        }


class ConversationSession:
    """
    Tracks state and history for a single user interaction session.
    Implements a sliding window so context stays relevant without token bloat.
    """

    def __init__(self, session_id: str, preferred_language: str = "auto", user_id: Optional[str] = None):
        self.session_id = session_id
        self.preferred_language = preferred_language
        self.user_id = user_id
        self.messages: List[Message] = []
        self.created_at = time.time()
        self.updated_at = time.time()
        self.metadata: Dict[str, Any] = {}

    def add_user_message(self, content: str, language: Optional[str] = None) -> Message:
        msg = Message(role="user", content=content, language=language)
        self.messages.append(msg)
        self.updated_at = time.time()
        if language and language != "auto":
            self.preferred_language = language

        # Persist to database (Supabase / SQLite fallback)
        try:
            ConversationRepository.get_or_create_conversation(
                conversation_id=self.session_id,
                user_id=self.user_id,
                title=content[:30] + ("..." if len(content) > 30 else ""),
                language=language or self.preferred_language,
            )
            ConversationRepository.save_message(
                conversation_id=self.session_id,
                role="user",
                content=content,
            )
        except Exception:
            pass

        return msg

    def add_assistant_message(self, content: str, language: Optional[str] = None, audio_metadata: Optional[Dict] = None) -> Message:
        msg = Message(role="assistant", content=content, language=language)
        self.messages.append(msg)
        self.updated_at = time.time()

        # Persist to database (Supabase / SQLite fallback)
        try:
            ConversationRepository.save_message(
                conversation_id=self.session_id,
                role="assistant",
                content=content,
                audio_metadata=audio_metadata or {},
            )
        except Exception:
            pass

        return msg

    def get_history_for_llm(self, max_turns: int = 6) -> List[Dict[str, str]]:
        """
        Returns recent messages formatted as standard [{"role": "...", "content": "..."}].
        Uses a sliding window (default: last 6 turns) to prevent token overload.
        """
        recent = self.messages[-max_turns:] if len(self.messages) > max_turns else self.messages
        return [{"role": m.role, "content": m.content} for m in recent]

    def clear(self) -> None:
        """Clear conversation history while retaining session identifier."""
        self.messages.clear()
        self.updated_at = time.time()
        try:
            ConversationRepository.delete_conversation(self.session_id)
        except Exception:
            pass

    def get_all_messages(self) -> List[Dict[str, Any]]:
        return [m.to_dict() for m in self.messages]


class ConversationManager:
    """
    Manages active user sessions in memory with persistent database backing.
    """

    def __init__(self, session_ttl_seconds: int = 86400):
        self._sessions: Dict[str, ConversationSession] = {}
        self.session_ttl = session_ttl_seconds

    def get_or_create(
        self,
        session_id: Optional[str] = None,
        preferred_language: str = "auto",
        user_id: Optional[str] = None,
    ) -> ConversationSession:
        """
        Retrieve an existing session or generate a new UUID-based session.
        Hydrates from database if session is not yet in cache.
        """
        if not session_id or session_id.strip() == "":
            session_id = str(uuid.uuid4())

        if session_id not in self._sessions:
            session = ConversationSession(
                session_id=session_id,
                preferred_language=preferred_language,
                user_id=user_id,
            )
            # Hydrate previous messages from database if they exist
            try:
                db_msgs = ConversationRepository.get_messages(session_id)
                for db_m in db_msgs:
                    session.messages.append(
                        Message(
                            role=db_m["role"],
                            content=db_m["content"],
                            timestamp=time.time(),
                        )
                    )
            except Exception:
                pass

            self._sessions[session_id] = session

        session = self._sessions[session_id]
        if user_id and not session.user_id:
            session.user_id = user_id
        if preferred_language and preferred_language != "auto":
            session.preferred_language = preferred_language

        return session

    def get(self, session_id: str) -> Optional[ConversationSession]:
        return self._sessions.get(session_id)

    def clear(self, session_id: str) -> bool:
        session = self._sessions.get(session_id)
        if session:
            session.clear()
            return True
        return False

    def list_active_session_ids(self) -> List[str]:
        return list(self._sessions.keys())


# Global singleton instance for application use
conversation_manager = ConversationManager()

