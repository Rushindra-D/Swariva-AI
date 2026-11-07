"""
SWARIVA AI — Health & System Info Endpoints
"""
from fastapi import APIRouter
from config import (
    GNANI_STT_MODEL,
    GNANI_TTS_MODEL,
    SUPPORTED_LANGUAGES,
    TTS_VOICES,
    APP_ENV,
)

router = APIRouter(tags=["Health & System"])


@router.get("/health", summary="Health Check")
async def health_check():
    """
    Confirms that the SWARIVA AI backend is running properly.
    """
    return {
        "status": "healthy",
        "app": "SWARIVA AI",
        "tagline": "A voice that understands you.",
        "version": "1.0.0",
        "environment": APP_ENV,
        "models": {
            "stt": GNANI_STT_MODEL,
            "tts": GNANI_TTS_MODEL,
        },
    }


@router.get("/api/v1/info", summary="Application Information")
async def app_info():
    """
    Provides catalog metadata including supported languages, voice options,
    and configured speech models.
    """
    return {
        "app_name": "SWARIVA AI",
        "tagline": "A voice that understands you.",
        "description": "Multilingual, voice-first intelligent companion powered by Gnani AI.",
        "supported_languages": list(SUPPORTED_LANGUAGES.keys()),
        "language_codes": SUPPORTED_LANGUAGES,
        "active_models": {
            "stt_model": GNANI_STT_MODEL,
            "tts_model": GNANI_TTS_MODEL,
        },
        "voice_catalog": TTS_VOICES,
    }

