"""
SWARIVA AI — Voice Endpoints
Full Voice-to-Voice Loop (Microphone Audio -> Prisma STT -> Agent Reasoning -> Timbre TTS -> Audio Out)
and Standalone Read-Aloud (Text-to-Speech).
"""
import base64
import time
from typing import Optional, Dict, Any
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status, Depends

from schemas.voice import (
    VoiceChatResponse,
    TextToSpeechRequest,
    TextToSpeechResponse,
)
from conversation import conversation_manager
from agent import agent
from gnani_stt import GnaniSTT
from gnani_tts import GnaniTTS
from auth import get_current_user

router = APIRouter(prefix="/api/v1/voice", tags=["Voice Assistant"])

# Instantiate the verified Phase 2 clients
stt_client = GnaniSTT()
tts_client = GnaniTTS()

ALLOWED_EXTENSIONS = {".wav", ".mp3", ".ogg", ".flac", ".aac", ".m4a", ".webm"}
MAX_AUDIO_BYTES = 10 * 1024 * 1024  # 10 MB limit


@router.post("/chat", response_model=VoiceChatResponse, summary="End-to-End Voice Interaction")
async def voice_chat_endpoint(
    audio_file: UploadFile = File(..., description="User recorded audio clip (WAV, MP3, OGG, etc. < 30s)"),
    session_id: Optional[str] = Form(None, description="Active session ID for conversation continuity"),
    language: Optional[str] = Form("auto", description="Spoken language ('english', 'hindi', 'telugu', or 'auto')"),
    voice: Optional[str] = Form(None, description="Voice name for synthesized reply"),
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user),
):
    """
    End-to-End Voice Interaction:
    1. Receives speech audio from the browser / microphone.
    2. Transcribes speech using Gnani Prisma STT (v3.0).
    3. Feeds transcript into the SWARIVA AI reasoning agent with session context.
    4. Synthesizes the response into human voice using Gnani Timbre TTS (v2.5).
    5. Returns transcript, text response, and base64 audio in a single cohesive payload.
    """
    user_id = current_user["id"] if current_user else None
    # 1. Validate audio file
    filename = audio_file.filename or "recording.wav"
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS and "audio" not in (audio_file.content_type or ""):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported audio format '{suffix}'. Supported formats: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    audio_bytes = await audio_file.read()
    if not audio_bytes or len(audio_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded audio file is empty.",
        )

    if len(audio_bytes) > MAX_AUDIO_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Audio file exceeds the maximum 10MB limit.",
        )

    # 2. Transcribe speech using Gnani Prisma STT
    stt_result = await stt_client.transcribe_bytes(
        audio_bytes=audio_bytes,
        language=language or "auto",
        output_format="transcribe",
        filename=filename,
    )

    if not stt_result.success:
        return VoiceChatResponse(
            success=False,
            transcript="",
            detected_language="",
            response_text="",
            session_id=session_id or "",
            audio_base64=None,
            processing_time_stt=stt_result.processing_time,
            processing_time_tts=0.0,
            error=f"Speech recognition failed: {stt_result.error}",
        )

    user_transcript = stt_result.transcript.strip()
    if not user_transcript:
        return VoiceChatResponse(
            success=False,
            transcript="",
            detected_language=stt_result.detected_language,
            response_text="I could not hear any speech clearly. Could you please repeat that?",
            session_id=session_id or "",
            audio_base64=None,
            processing_time_stt=stt_result.processing_time,
            processing_time_tts=0.0,
            error="No speech detected in audio.",
        )

    # 3. Process transcription with AI reasoning agent
    session = conversation_manager.get_or_create(
        session_id=session_id,
        preferred_language=stt_result.detected_language,
        user_id=user_id,
    )

    reply = await agent.generate_response(
        user_message=user_transcript,
        session=session,
        language=stt_result.detected_language,
    )

    # 4. Synthesize reply with Gnani Timbre TTS
    start_tts = time.time()
    tts_result = await tts_client.synthesize(
        text=reply.speech_text,
        language=reply.language,
        voice=voice,
    )
    tts_latency = time.time() - start_tts

    audio_b64 = None
    if tts_result.success and tts_result.audio_bytes:
        audio_b64 = base64.b64encode(tts_result.audio_bytes).decode("utf-8")

    return VoiceChatResponse(
        success=True,
        transcript=user_transcript,
        detected_language=stt_result.detected_language,
        response_text=reply.text,
        session_id=session.session_id,
        audio_base64=audio_b64,
        processing_time_stt=stt_result.processing_time,
        processing_time_tts=round(tts_latency, 2),
        metadata={
            "stt_model": stt_result.model,
            "tts_model": tts_result.model,
            "tts_voice": tts_result.voice,
            "audio_size_bytes": len(tts_result.audio_bytes) if tts_result.audio_bytes else 0,
            "agent_provider": reply.provider,
        },
    )


@router.post("/speak", response_model=TextToSpeechResponse, summary="Read Aloud / Text-to-Speech")
async def read_aloud_endpoint(req: TextToSpeechRequest):
    """
    Standalone Text-to-Speech endpoint (for Module 6: Read Aloud feature).
    Converts any pasted text into expressive Indian voice audio.
    """
    tts_result = await tts_client.synthesize(
        text=req.text,
        language=req.language or "auto",
        voice=req.voice,
        speed=req.speed,
    )

    if not tts_result.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Text-to-speech synthesis failed: {tts_result.error}",
        )

    audio_b64 = base64.b64encode(tts_result.audio_bytes).decode("utf-8")

    return TextToSpeechResponse(
        success=True,
        audio_base64=audio_b64,
        voice=tts_result.voice,
        language=tts_result.language,
        size_bytes=len(tts_result.audio_bytes),
    )

