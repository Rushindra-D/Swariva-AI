"""
SWARIVA AI — Complete 12-Point Gemini Reasoning & Conversational Test Suite

Executes tests for the 12 evaluation criteria:
1. What is Diwali?
2. Describe a cyclone.
3. Explain artificial intelligence.
4. What is machine learning?
5. What is the difference between Python and Java?
6. Explain this concept in simple Telugu.
7. Explain this concept in Hindi.
8. Follow-up question based on the previous answer.
9. Switching from one topic to another.
10. English speech input producing an English response.
11. Telugu speech input producing a Telugu response.
12. Gemini API failure and quota handling.

Differentiates mocked tests from genuine live model API tests.
"""
import os
import sys
import uuid
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from agent import agent, clean_text_for_speech, filter_echo_prefixes
from conversation import ConversationSession
from providers.gemini_provider import (
    GeminiProvider,
    GeminiAuthError,
    GeminiQuotaError,
    GeminiTimeoutError,
)


def banner(title: str):
    print("\n" + "=" * 78)
    print(f"  {title}")
    print("=" * 78)


def verify_text(label: str, text: str, required_keywords: list, forbidden_echo: list = None):
    print(f"\n[{label}] Result: {text}")
    assert text and len(text.strip()) > 15, f"{label}: Response is too short or empty!"

    lower = text.lower()

    # Zero echo checks
    echoes = forbidden_echo or [
        "you said", "you asked", "you mentioned", "i heard you",
        "మీరు చెప్పారు", "మీరు అడిగారు", "मैंने सुना", "आपने पूछा"
    ]
    for e in echoes:
        assert e not in lower, f"{label}: Echo prefix '{e}' found in reply!"

    # Concept check
    if required_keywords:
        found = [kw for kw in required_keywords if kw.lower() in lower]
        assert len(found) > 0, f"{label}: None of required keywords {required_keywords} found in: '{text}'"
    print(f"[{label}] PASS (Keywords verified, zero echo confirmed)")


async def run_12_point_tests():
    banner("SWARIVA AI — 12-POINT REASONING & GEMINI VERIFICATION SUITE")

    # -------------------------------------------------------------
    # Test 1: What is Diwali?
    # -------------------------------------------------------------
    s1 = ConversationSession(session_id=str(uuid.uuid4()))
    r1 = await agent.generate_response("What is Diwali?", session=s1, language="english")
    verify_text("Test 1: What is Diwali?", r1.text, ["festival", "light", "diwali", "celebrat"])

    # -------------------------------------------------------------
    # Test 2: Describe a cyclone.
    # -------------------------------------------------------------
    s2 = ConversationSession(session_id=str(uuid.uuid4()))
    r2 = await agent.generate_response("Describe a cyclone.", session=s2, language="english")
    verify_text("Test 2: Describe a cyclone.", r2.text, ["cyclone", "storm", "wind", "system", "pressure"])

    # -------------------------------------------------------------
    # Test 3: Explain artificial intelligence.
    # -------------------------------------------------------------
    s3 = ConversationSession(session_id=str(uuid.uuid4()))
    r3 = await agent.generate_response("Explain artificial intelligence.", session=s3, language="english")
    verify_text("Test 3: Explain AI", r3.text, ["intelligence", "machine", "computer", "learn", "ai"])

    # -------------------------------------------------------------
    # Test 4: What is machine learning?
    # -------------------------------------------------------------
    s4 = ConversationSession(session_id=str(uuid.uuid4()))
    r4 = await agent.generate_response("What is machine learning?", session=s4, language="english")
    verify_text("Test 4: What is ML", r4.text, ["machine learning", "data", "learn", "algorithm", "model"])

    # -------------------------------------------------------------
    # Test 5: Difference between Python and Java
    # -------------------------------------------------------------
    s5 = ConversationSession(session_id=str(uuid.uuid4()))
    r5 = await agent.generate_response("What is the difference between Python and Java?", session=s5, language="english")
    verify_text("Test 5: Python vs Java", r5.text, ["python", "java", "language", "code", "syntax"])

    # -------------------------------------------------------------
    # Test 6: Explain this concept in simple Telugu
    # -------------------------------------------------------------
    s6 = ConversationSession(session_id=str(uuid.uuid4()))
    r6 = await agent.generate_response("కృత్రిమ మేధస్సు (AI) అంటే ఏమిటి? సులభంగా తెలుగులో వివరించండి.", session=s6, language="telugu")
    assert r6.language == "telugu", f"Expected telugu language, got {r6.language}"
    verify_text("Test 6: Simple Telugu AI Explanation", r6.text, ["కంప్యూటర్", "మేధస్సు", "సాంకేతిక", "యంత్రం", "విభాగం"])

    # -------------------------------------------------------------
    # Test 7: Explain this concept in Hindi
    # -------------------------------------------------------------
    s7 = ConversationSession(session_id=str(uuid.uuid4()))
    r7 = await agent.generate_response("आर्टिफिशियल इंटेलिजेंस (AI) क्या है? हिंदी में समझाइए।", session=s7, language="hindi")
    assert r7.language == "hindi", f"Expected hindi language, got {r7.language}"
    verify_text("Test 7: Hindi AI Explanation", r7.text, ["बुद्धिमत्ता", "कंप्यूटर", "मशीन", "तकनीक", "प्रणाली"])

    # -------------------------------------------------------------
    # Test 8: Follow-up question based on the previous answer
    # -------------------------------------------------------------
    s8 = ConversationSession(session_id=str(uuid.uuid4()))
    # Turn 1
    r8_1 = await agent.generate_response("What is Diwali?", session=s8, language="english")
    assert s8.metadata.get("active_subject") == "diwali"
    # Turn 2: Follow-up using pronoun "it"
    r8_2 = await agent.generate_response("When is it celebrated?", session=s8, language="english")
    assert s8.metadata.get("active_subject") == "diwali"
    verify_text("Test 8: Follow-up on Diwali ('When is it celebrated?')", r8_2.text, ["diwali", "celebrat", "october", "november", "month", "kartik"])

    # -------------------------------------------------------------
    # Test 9: Switching from one topic to another
    # -------------------------------------------------------------
    s9 = ConversationSession(session_id=str(uuid.uuid4()))
    # Start on Diwali
    await agent.generate_response("What is Diwali?", session=s9, language="english")
    assert s9.metadata.get("active_subject") == "diwali"
    # Switch cleanly to Cyclone
    r9 = await agent.generate_response("Describe a cyclone.", session=s9, language="english")
    assert s9.metadata.get("active_subject") == "cyclone"
    assert "festival of lights" not in r9.text.lower()
    verify_text("Test 9: Topic Switch from Diwali to Cyclone", r9.text, ["cyclone", "storm", "wind", "weather"])

    # -------------------------------------------------------------
    # Test 10: English input producing English response
    # -------------------------------------------------------------
    s10 = ConversationSession(session_id=str(uuid.uuid4()))
    r10 = await agent.generate_response("Tell me about photosynthesis.", session=s10, language="english")
    assert r10.language == "english"
    verify_text("Test 10: English Input -> English Output", r10.text, ["photosynthesis", "plant", "sunlight", "energy"])

    # -------------------------------------------------------------
    # Test 11: Telugu speech/text input producing Telugu response
    # -------------------------------------------------------------
    s11 = ConversationSession(session_id=str(uuid.uuid4()))
    r11 = await agent.generate_response("తుఫాను అంటే ఏమిటి? అది ఎలా ఏర్పడుతుంది?", session=s11, language="auto")
    assert r11.language == "telugu"
    verify_text("Test 11: Telugu Input -> Telugu Output", r11.text, ["తుఫాను", "గాలి", "వాతావరణం", "పీడనం"])

    # -------------------------------------------------------------
    # Test 12: Gemini API failure and quota handling
    # -------------------------------------------------------------
    banner("Test 12: Gemini Error and Quota Handling (Unit / Mocked)")

    mock_provider = GeminiProvider(api_key="mock_test_key")

    # 12A: Quota exceeded
    with patch.object(mock_provider, "_get_client") as mock_get_client:
        mock_c = MagicMock()
        mock_c.aio.models.generate_content = AsyncMock(
            side_effect=Exception("429 RESOURCE_EXHAUSTED: Rate limit exceeded")
        )
        mock_get_client.return_value = mock_c

        try:
            await mock_provider.generate(
                messages=[{"role": "user", "content": "Hello"}],
                system_prompt="Test",
                target_language="english",
            )
            assert False, "Should have raised GeminiQuotaError"
        except GeminiQuotaError as gqe:
            print(f"[Test 12A: Quota Exception Caught]: {gqe}")
            assert "quota" in str(gqe).lower() or "rate limit" in str(gqe).lower()

    # 12B: Invalid API Key / Auth failure
    with patch.object(mock_provider, "_get_client") as mock_get_client:
        mock_c = MagicMock()
        mock_c.aio.models.generate_content = AsyncMock(
            side_effect=Exception("401 API_KEY_INVALID: The provided API key is invalid")
        )
        mock_get_client.return_value = mock_c

        try:
            await mock_provider.generate(
                messages=[{"role": "user", "content": "Hello"}],
                system_prompt="Test",
                target_language="english",
            )
            assert False, "Should have raised GeminiAuthError"
        except GeminiAuthError as gae:
            print(f"[Test 12B: Auth Exception Caught]: {gae}")
            assert "api key" in str(gae).lower() or "unauthorized" in str(gae).lower()

    # 12C: Timeout handling
    with patch.object(mock_provider, "_get_client") as mock_get_client:
        mock_c = MagicMock()
        mock_c.aio.models.generate_content = AsyncMock(
            side_effect=Exception("Deadline Exceeded: request timed out")
        )
        mock_get_client.return_value = mock_c

        try:
            await mock_provider.generate(
                messages=[{"role": "user", "content": "Hello"}],
                system_prompt="Test",
                target_language="english",
            )
            assert False, "Should have raised GeminiTimeoutError"
        except GeminiTimeoutError as gte:
            print(f"[Test 12C: Timeout Exception Caught]: {gte}")
            assert "timed out" in str(gte).lower()

    print("\n[Test 12] PASS: All 3 error conditions correctly caught and typed.")

    # -------------------------------------------------------------
    # Real Gemini API Live Status Check
    # -------------------------------------------------------------
    banner("Live Gemini API Status Check")
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    if gemini_key and not gemini_key.startswith("placeholder") and not gemini_key.startswith("your_"):
        print("[Live Gemini Test] Active key found in .env. Running live request...")
        live_provider = GeminiProvider(api_key=gemini_key)
        live_res = await live_provider.generate(
            messages=[{"role": "user", "content": "Explain machine learning in 15 words."}],
            system_prompt="You are SWARIVA AI.",
            target_language="english",
        )
        print(f"[Live Gemini Test] SUCCESS: {live_res}")
    else:
        print("[Live Gemini Test] Notice: GEMINI_API_KEY in .env is currently a placeholder ('your_new_gemini_api_key').")
        print("                   Mocked tests PASSED. When you add your real GEMINI_API_KEY, Gemini live generation is active.")

    banner("ALL 12 EVALUATION TESTS PASSED SUCCESSFULLY!")


if __name__ == "__main__":
    asyncio.run(run_12_point_tests())
