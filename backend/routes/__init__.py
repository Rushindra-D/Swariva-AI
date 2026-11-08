"""
SWARIVA AI — Routes Package
"""
from .health import router as health_router
from .chat import router as chat_router
from .voice import router as voice_router
from .auth import router as auth_router
from .reminders import router as reminders_router
from .conversations import router as conversations_router

__all__ = [
    "health_router",
    "chat_router",
    "voice_router",
    "auth_router",
    "reminders_router",
    "conversations_router",
]
