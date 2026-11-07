"""
SWARIVA AI — Backend Automated Test Suite

Covers:
- System health and catalog info
- Multilingual text chat (English, Hindi, Telugu)
- Multi-turn session continuity and history clearing
- Voice interaction pipeline with mocked external Gnani APIs (zero credit consumption)
- Error handling for invalid inputs and audio formats
"""
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

# Add backend directory to sys.path
backend_path = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from main import app
from gnani_stt import STTResult
from gnani_tts import TTSResult

client = TestClient(app)


# ── 1. Health & System Info Tests ──
def test_health_check():
    """Verify GET /health confirms backend operational status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app"] == "SWARIVA AI"
    assert "models" in data
    assert data["models"]["stt"] == "prisma-v3.0"
    assert data["models"]["tts"] == "timbre-v2.5"


def test_app_info():
    """Verify GET /api/v1/info returns catalog metadata."""
    response = client.get("/api/v1/info")
    assert response.status_code == 200
    data = response.json()
    assert "supported_languages" in data
    assert "english" in data["supported_languages"]
    assert "hindi" in data["supported_languages"]
    assert "telugu" in data["supported_languages"]
    assert "voice_catalog" in data


def test_frontend_mount():
    """Verify GET /app/ serves the landing page HTML."""
    response = client.get("/app/")
    assert response.status_code == 200
    assert "SWARIVA AI" in response.text
    assert "<!DOCTYPE html>" in response.text


# ── 2. Multilingual Text Chat Tests ──
def test_text_chat_english():
    """Verify English text conversation."""
    payload = {
        "message": "Hello, who are you?",
        "language": "english",
    }
    response = client.post("/api/v1/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert len(data["response"]) > 0
    assert "Swariva" in data["response"]
    assert data["language"] == "english"
    assert "session_id" in data


def test_text_chat_hindi():
    """Verify Hindi text conversation."""
    payload = {
        "message": "नमस्ते, आप कौन हैं?",
        "language": "hindi",
    }
    response = client.post("/api/v1/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert data["language"] == "hindi"
    assert "स्वरिवा" in data["response"]


def test_text_chat_telugu():
    """Verify Telugu text conversation."""
    payload = {
        "message": "నమస్కారం, మీరు ఎవరు?",
        "language": "telugu",
    }
    response = client.post("/api/v1/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert data["language"] == "telugu"
    assert "స్వరివ" in data["response"]


# ── 3. Session Continuity & Context Tests ──
def test_session_continuity():
    """Verify that multi-turn conversation maintains context across turns."""
    # Turn 1
    t1_resp = client.post("/api/v1/chat", json={"message": "I need help with reminders"})
    assert t1_resp.status_code == 200
    t1_data = t1_resp.json()
    session_id = t1_data["session_id"]
    assert session_id is not None

    # Turn 2 using the same session_id
    t2_resp = client.post(
        "/api/v1/chat",
        json={"message": "Can you tell me more?", "session_id": session_id},
    )
    assert t2_resp.status_code == 200
    t2_data = t2_resp.json()
    assert t2_data["session_id"] == session_id
    assert t2_data["metadata"]["history_length"] == 4  # (U1, A1, U2, A2)

    # Verify session history endpoint
    hist_resp = client.get(f"/api/v1/chat/history/{session_id}")
    assert hist_resp.status_code == 200
    hist_data = hist_resp.json()
    assert hist_data["total_messages"] == 4
    assert hist_data["messages"][0]["content"] == "I need help with reminders"


def test_session_clear():
    """Verify clearing conversation history."""
    # Create session
    resp = client.post("/api/v1/chat", json={"message": "Test message"})
    session_id = resp.json()["session_id"]

    # Clear it
    clear_resp = client.post("/api/v1/chat/clear", json={"session_id": session_id})
    assert clear_resp.status_code == 200
    assert clear_resp.json()["cleared"] is True

    # History should now be empty
    hist_resp = client.get(f"/api/v1/chat/history/{session_id}")
    assert hist_resp.status_code == 200
    assert hist_resp.json()["total_messages"] == 0


# ── 4. Error Handling & Validation Tests ──
def test_empty_message_validation():
    """Verify that empty text triggers HTTP 422 Unprocessable Entity."""
    response = client.post("/api/v1/chat", json={"message": ""})
    assert response.status_code == 422


def test_invalid_session_history():
    """Verify 404 for non-existent session history."""
    response = client.get("/api/v1/chat/history/non_existent_session_12345")
    assert response.status_code == 404


def test_invalid_audio_format():
    """Verify rejection of unsupported audio extensions."""
    files = {"audio_file": ("test.txt", b"plain text is not audio", "text/plain")}
    response = client.post("/api/v1/voice/chat", files=files)
    assert response.status_code == 400
    assert "Unsupported audio format" in response.json()["detail"]


def test_empty_audio_file():
    """Verify rejection of 0-byte audio upload."""
    files = {"audio_file": ("empty.wav", b"", "audio/wav")}
    response = client.post("/api/v1/voice/chat", files=files)
    assert response.status_code == 400
    assert "empty" in response.json()["detail"]


# ── 5. Voice Interaction Pipeline (Mocked External Calls) ──
@pytest.mark.asyncio
async def test_voice_chat_pipeline_mocked():
    """
    Test the full voice pipeline:
    Audio In -> Prisma STT -> Agent Reasoning -> Timbre TTS -> Response with base64 audio.
    External Gnani APIs are mocked to prevent consuming real programme credits.
    """
    mock_stt_result = STTResult(
        success=True,
        transcript="Hello Swariva, how are you today?",
        detected_language="en-IN",
        model="prisma-v3.0",
        request_id="mock-req-001",
        processing_time=0.15,
        raw_response={"mock": True},
    )

    mock_tts_result = TTSResult(
        success=True,
        audio_bytes=b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x80>\x00\x00\x00}\x00\x00\x02\x00\x10\x00data\x00\x00\x00\x00",
        content_type="audio/wav",
        voice="Nalini",
        language="en-IN",
        model="timbre-v2.5",
        metadata={"audio_size_bytes": 44},
    )

    with patch("routes.voice.stt_client.transcribe_bytes", new=AsyncMock(return_value=mock_stt_result)), \
         patch("routes.voice.tts_client.synthesize", new=AsyncMock(return_value=mock_tts_result)):

        dummy_wav_bytes = b"RIFF....dummy wave data...."
        files = {"audio_file": ("speech.wav", dummy_wav_bytes, "audio/wav")}
        data = {"language": "english"}

        response = client.post("/api/v1/voice/chat", files=files, data=data)
        assert response.status_code == 200
        result = response.json()

        assert result["success"] is True
        assert result["transcript"] == "Hello Swariva, how are you today?"
        assert result["detected_language"] == "en-IN"
        assert len(result["response_text"]) > 0
        assert result["audio_base64"] is not None
        assert "metadata" in result
        assert result["metadata"]["stt_model"] == "prisma-v3.0"
        assert result["metadata"]["tts_model"] == "timbre-v2.5"

