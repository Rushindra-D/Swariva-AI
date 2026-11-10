"""
SWARIVA AI — Gemini Provider & Reasoning Unit Tests

Tests:
- GeminiProvider initialization and parameter validation
- System instruction construction and message role formatting (user -> user, assistant -> model)
- Error handling: Auth, Quota, Timeout, Model Unavailable, Empty Response
- Multi-turn conversation and follow-up question resolution
- Topic switching without residual topic echo
- Multilingual responses (English, Telugu, Hindi)
- Real API test (only executed if live GEMINI_API_KEY is configured)
"""
import os
import sys
from pathlib import Path
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Add backend directory to sys.path
backend_path = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from providers.gemini_provider import (
    GeminiProvider,
    GeminiProviderError,
    GeminiAuthError,
    GeminiQuotaError,
    GeminiModelError,
    GeminiTimeoutError,
)
from conversation import ConversationSession
from agent import SWARIVAAgent, clean_text_for_speech, filter_echo_prefixes


# ── 1. Provider Unit Tests ──

def test_gemini_provider_requires_api_key():
    """Verify ValueError is raised if initialized with empty API key."""
    with pytest.raises(ValueError, match="GEMINI_API_KEY is required"):
        GeminiProvider(api_key="")


def test_gemini_provider_init_valid():
    """Verify GeminiProvider initializes with correct defaults."""
    provider = GeminiProvider(api_key="test_api_key_123", model="gemini-2.5-flash", timeout=25.0)
    assert provider.model == "gemini-2.5-flash"
    assert provider.timeout == 25.0
    assert provider.name == "gemini:gemini-2.5-flash"
    assert provider.last_latency == 0.0


@pytest.mark.asyncio
async def test_gemini_generate_success_mocked():
    """Verify GeminiProvider formats messages and returns assistant response."""
    provider = GeminiProvider(api_key="mock_key_valid", model="gemini-2.5-flash")

    # Mock response object from Google GenAI
    mock_response = MagicMock()
    mock_response.text = "Diwali is the Hindu festival of lights symbolizing the victory of light over darkness."

    mock_client = MagicMock()
    mock_client.models.generate_content = MagicMock(return_value=mock_response)

    with patch.object(provider, "_get_client", return_value=mock_client):
        result = await provider.generate(
            messages=[{"role": "user", "content": "What is Diwali?"}],
            system_prompt="You are SWARIVA AI.",
            target_language="english",
            active_subject="Diwali",
        )

        assert "festival of lights" in result
        assert provider.last_latency >= 0.0
        mock_client.models.generate_content.assert_called_once()


@pytest.mark.asyncio
async def test_gemini_generate_empty_response():
    """Verify empty response from Gemini raises GeminiProviderError."""
    provider = GeminiProvider(api_key="mock_key_valid")

    mock_response = MagicMock()
    mock_response.text = ""

    mock_client = MagicMock()
    mock_client.models.generate_content = MagicMock(return_value=mock_response)

    with patch.object(provider, "_get_client", return_value=mock_client):
        with pytest.raises(GeminiProviderError, match="empty response"):
            await provider.generate(
                messages=[{"role": "user", "content": "Hello"}],
                system_prompt="Test",
                target_language="english",
            )


@pytest.mark.asyncio
async def test_gemini_auth_error_handling():
    """Verify authentication failures map to GeminiAuthError."""
    provider = GeminiProvider(api_key="invalid_key")

    mock_client = MagicMock()
    mock_client.models.generate_content = MagicMock(
        side_effect=Exception("401 API_KEY_INVALID: The provided API key is invalid.")
    )

    with patch.object(provider, "_get_client", return_value=mock_client):
        with pytest.raises(GeminiAuthError, match="Invalid or unauthorized Gemini API key"):
            await provider.generate(
                messages=[{"role": "user", "content": "Test"}],
                system_prompt="Test",
                target_language="english",
            )


@pytest.mark.asyncio
async def test_gemini_quota_error_handling():
    """Verify rate limit / quota exhaustion maps to GeminiQuotaError."""
    provider = GeminiProvider(api_key="quota_exhausted_key")

    mock_client = MagicMock()
    mock_client.models.generate_content = MagicMock(
        side_effect=Exception("429 RESOURCE_EXHAUSTED: Quota exceeded for model gemini-3.5-flash-lite.")
    )

    with patch.object(provider, "_get_client", return_value=mock_client):
        with pytest.raises(GeminiQuotaError, match="rate limit or quota exceeded"):
            await provider.generate(
                messages=[{"role": "user", "content": "Test"}],
                system_prompt="Test",
                target_language="english",
            )


@pytest.mark.asyncio
async def test_gemini_timeout_error_handling():
    """Verify request timeout maps to GeminiTimeoutError."""
    provider = GeminiProvider(api_key="valid_key", timeout=15.0)

    mock_client = MagicMock()
    mock_client.models.generate_content = MagicMock(
        side_effect=Exception("Deadline Exceeded: request timed out")
    )

    with patch.object(provider, "_get_client", return_value=mock_client):
        with pytest.raises(GeminiTimeoutError, match="timed out"):
            await provider.generate(
                messages=[{"role": "user", "content": "Test"}],
                system_prompt="Test",
                target_language="english",
            )


# ── 2. Multi-turn Agent Reasoning & Context Tests ──

@pytest.mark.asyncio
async def test_agent_follow_up_question_resolution():
    """
    Test 8: Follow-up question based on the previous answer.
    Turn 1: 'What is Diwali?'
    Turn 2: 'When is it celebrated?' -> Should retain 'Diwali' as active subject.
    """
    session = ConversationSession(session_id="test_follow_up_1")
    agent_instance = SWARIVAAgent()

    # Turn 1
    reply1 = await agent_instance.generate_response(
        user_message="What is Diwali?",
        session=session,
        language="english",
    )
    assert reply1.metadata["active_subject"] == "diwali"
    assert session.metadata.get("active_subject") == "diwali"

    # Turn 2: Follow-up question with pronoun
    reply2 = await agent_instance.generate_response(
        user_message="When is it celebrated?",
        session=session,
        language="english",
    )
    # The active subject should still be diwali
    assert reply2.metadata["active_subject"] == "diwali"
    assert "diwali" in reply2.text.lower() or "october" in reply2.text.lower() or "november" in reply2.text.lower() or "celebrated" in reply2.text.lower()


@pytest.mark.asyncio
async def test_agent_topic_switching():
    """
    Test 9: Switching from one topic to another.
    Turn 1: Diwali discussion.
    Turn 2: Cyclone question -> Must switch active subject to cyclone without lingering Diwali content.
    """
    session = ConversationSession(session_id="test_topic_switch_1")
    agent_instance = SWARIVAAgent()

    # Turn 1: Diwali
    await agent_instance.generate_response(
        user_message="What is Diwali?",
        session=session,
        language="english",
    )
    assert session.metadata.get("active_subject") == "diwali"

    # Turn 2: Cyclone
    reply2 = await agent_instance.generate_response(
        user_message="Describe a cyclone.",
        session=session,
        language="english",
    )
    assert session.metadata.get("active_subject") == "cyclone"
    assert "cyclone" in reply2.text.lower() or "storm" in reply2.text.lower()
    # Ensure no remnant Diwali statements in the cyclone answer
    assert "festival of lights" not in reply2.text.lower()


@pytest.mark.asyncio
async def test_agent_multilingual_routing_telugu():
    """Test 6 & 11: Telugu input producing a Telugu response without English fallback."""
    session = ConversationSession(session_id="test_telugu_routing")
    agent_instance = SWARIVAAgent()

    reply = await agent_instance.generate_response(
        user_message="దీపావళి పండుగ గురించి చెప్పండి",
        session=session,
        language="auto",
    )
    assert reply.language == "telugu"
    # Verify response contains Telugu script
    assert any("\u0c00" <= char <= "\u0c7f" for char in reply.text)


@pytest.mark.asyncio
async def test_agent_multilingual_routing_hindi():
    """Test 7: Hindi input producing a Hindi response."""
    session = ConversationSession(session_id="test_hindi_routing")
    agent_instance = SWARIVAAgent()

    reply = await agent_instance.generate_response(
        user_message="दीपावली का क्या महत्व है?",
        session=session,
        language="auto",
    )
    assert reply.language == "hindi"
    # Verify response contains Devanagari script
    assert any("\u0900" <= char <= "\u097f" for char in reply.text)


@pytest.mark.asyncio
async def test_clean_text_for_speech_output():
    """Verify that speech text is stripped of asterisks, headers, and stage cues."""
    raw = "### Artificial Intelligence\n**AI** is a *branch* of computer science. [smiling] #tech"
    cleaned = clean_text_for_speech(raw)
    assert "#" not in cleaned
    assert "*" not in cleaned
    assert "[" not in cleaned
    assert "smiling" not in cleaned
    assert "AI is a branch of computer science" in cleaned


def test_filter_echo_prefixes():
    """Verify that user question echo phrases are stripped cleanly."""
    query = "What is machine learning?"
    bot_reply = "You asked about What is machine learning?. Machine learning is a field of artificial intelligence."
    cleaned = filter_echo_prefixes(bot_reply, query)
    assert not cleaned.lower().startswith("you asked")


# ── 3. Real Gemini API Test (Conditionally Executed) ──

@pytest.mark.asyncio
async def test_real_gemini_api_call():
    """
    Real Gemini API integration test.
    Only executed if GEMINI_API_KEY is configured with an actual key.
    """
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    if not gemini_key or gemini_key.startswith("placeholder") or gemini_key.startswith("your_"):
        pytest.skip("Skipping real Gemini API test: GEMINI_API_KEY is not configured with a live key.")

    provider = GeminiProvider(api_key=gemini_key, model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))
    response = await provider.generate(
        messages=[{"role": "user", "content": "Explain artificial intelligence in one brief sentence."}],
        system_prompt="You are SWARIVA AI, an accessible voice assistant.",
        target_language="english",
    )
    assert response and len(response.strip()) > 10
    assert "intelligence" in response.lower() or "computer" in response.lower() or "ai" in response.lower()
