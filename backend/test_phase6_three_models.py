"""
SWARIVA AI — Phase 6 Gnani Three-Model & Real-Time Tools Verification Suite

Validates:
1. Gnani Prisma STT (Speech-to-Text) configuration & multi-key setup
2. Gnani Evon v3.3 (Reasoning & LLM) 3-tier provider architecture
3. Gnani Timbre TTS (Text-to-Speech) configuration & multi-key setup
4. Real-time Tool Calling & RAG (Weather, Gold Prices, Reminders)
5. Zero-Echo and Non-Generic Conversational Guarantees across English, Telugu, and Hindi
"""
import os
import sys
import asyncio
from pathlib import Path

# Add backend directory to path
BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from config import (
    GNANI_API_KEY,
    GNANI_PRISMA_API_KEY,
    GNANI_TIMBRE_API_KEY,
    GNANI_EVON_API_KEY,
    EVON_BASE_URL,
    EVON_MODEL,
    LLM_MODEL,
)
from gnani_stt import GnaniSTT
from gnani_tts import GnaniTTS
from providers import (
    BaseLLMProvider,
    KnowledgeCompanionProvider,
    EvonLLMProvider,
    GroqLLMProvider,
    get_llm_provider,
)
from tools import (
    WeatherTool,
    GoldPriceTool,
    ReminderTool,
    tool_registry,
)
from conversation import ConversationSession
from agent import agent, clean_text_for_speech, filter_echo_prefixes


def print_header(title: str):
    print("\n" + "=" * 75)
    print(f" {title}")
    print("=" * 75)


def assert_pass(condition: bool, test_name: str, detail: str = ""):
    if condition:
        print(f"  ✅ PASS: {test_name}")
        if detail:
            print(f"     └─ {detail}")
    else:
        print(f"  ❌ FAIL: {test_name}")
        if detail:
            print(f"     └─ {detail}")
        raise AssertionError(f"Test failed: {test_name} — {detail}")


async def test_suite():
    print_header("SWARIVA AI — PHASE 6 THREE-MODEL & TOOL INTEGRATION VERIFICATION")

    # ─────────────────────────────────────────────────────────────
    # 1. GNANI MULTI-KEY CONFIGURATION AUDIT
    # ─────────────────────────────────────────────────────────────
    print("\n[SECTION 1] Gnani Multi-Key Architecture Verification:")
    assert_pass(bool(GNANI_API_KEY), "GNANI_API_KEY is configured in environment")
    assert_pass(bool(GNANI_PRISMA_API_KEY), "GNANI_PRISMA_API_KEY resolves cleanly (with fallback)")
    assert_pass(bool(GNANI_TIMBRE_API_KEY), "GNANI_TIMBRE_API_KEY resolves cleanly (with fallback)")

    stt_client = GnaniSTT()
    tts_client = GnaniTTS()
    assert_pass(stt_client.api_key == GNANI_PRISMA_API_KEY, "GnaniSTT initialized with Prisma key")
    assert_pass(tts_client.api_key == GNANI_TIMBRE_API_KEY, "GnaniTTS initialized with Timbre key")

    # ─────────────────────────────────────────────────────────────
    # 2. GNANI TIMBRE TTS MULTILINGUAL SYNTHESIS
    # ─────────────────────────────────────────────────────────────
    print("\n[SECTION 2] Gnani Timbre TTS Live Voice Synthesis:")
    test_phrases = [
        ("english", "Hello, I am Swariva AI, your voice companion."),
        ("telugu", "నమస్కారం, నేను స్వరివ. మీకు ఎలా సహాయపడగలను?"),
        ("hindi", "नमस्ते, मैं स्वरिवा हूँ। आपकी क्या सहायता करूँ?"),
    ]
    for lang, phrase in test_phrases:
        res = await tts_client.synthesize(phrase, language=lang)
        assert_pass(
            res.success and len(res.audio_bytes) > 500,
            f"Timbre TTS Synthesis ({lang})",
            f"Audio size: {len(res.audio_bytes):,} bytes | Voice: {res.voice} | Content-Type: {res.content_type}",
        )

    # ─────────────────────────────────────────────────────────────
    # 3. 3-TIER REASONING PROVIDER ARCHITECTURE
    # ─────────────────────────────────────────────────────────────
    print("\n[SECTION 3] 3-Tier LLM Provider Architecture Verification:")
    primary, fallback = get_llm_provider()
    assert_pass(isinstance(primary, BaseLLMProvider), f"Primary provider configured: {primary.name}")
    assert_pass(isinstance(fallback, KnowledgeCompanionProvider), f"Fallback provider configured: {fallback.name}")

    # Evon Provider payload check
    evon_provider = EvonLLMProvider(base_url=EVON_BASE_URL, model=EVON_MODEL)
    assert_pass(evon_provider.model == EVON_MODEL, f"Evon Provider configured for: {EVON_MODEL}")
    assert_pass(evon_provider.base_url == EVON_BASE_URL.rstrip("/"), f"Evon Endpoint: {EVON_BASE_URL}")

    # ─────────────────────────────────────────────────────────────
    # 4. REAL-TIME TOOL CALLING & RAG (WEATHER, GOLD, REMINDERS)
    # ─────────────────────────────────────────────────────────────
    print("\n[SECTION 4] Real-Time Tool Calling & RAG Pipeline:")

    # 4.1 Weather Tool (Open-Meteo)
    weather_tool = WeatherTool()
    assert_pass(weather_tool.can_handle("What is the weather in Hyderabad?"), "WeatherTool detects English query")
    assert_pass(weather_tool.can_handle("హైదరాబాద్‌లో వాతావరణం ఎలా ఉంది?"), "WeatherTool detects Telugu query")
    assert_pass(weather_tool.can_handle("हैदराबाद में मौसम कैसा है?"), "WeatherTool detects Hindi query")

    weather_res = await weather_tool.execute("What is the weather in Hyderabad?")
    assert_pass(
        weather_res.success and "temperature_c" in weather_res.data,
        "WeatherTool live execution (Open-Meteo)",
        f"Hyderabad Temp: {weather_res.data.get('temperature_c')}°C | Source: {weather_res.source}",
    )
    assert_pass(
        "డిగ్రీల సెల్సియస్" in weather_res.get_spoken_text("telugu"),
        "WeatherTool Telugu spoken formatting",
        weather_res.get_spoken_text("telugu"),
    )

    # 4.2 Gold Price Tool
    gold_tool = GoldPriceTool()
    assert_pass(gold_tool.can_handle("What is today's gold price in Hyderabad?"), "GoldPriceTool detects English query")
    assert_pass(gold_tool.can_handle("ఈరోజు బంగారం ధర ఎంత?"), "GoldPriceTool detects Telugu query")
    assert_pass(gold_tool.can_handle("आज सोने का भाव क्या है?"), "GoldPriceTool detects Hindi query")

    gold_res = await gold_tool.execute("What is the gold rate today?")
    assert_pass(
        gold_res.success and "gold_24k_per_gram" in gold_res.data,
        "GoldPriceTool execution (Bullion rates)",
        f"24K Gold: ₹{gold_res.data.get('gold_24k_per_gram'):,}/g | 22K: ₹{gold_res.data.get('gold_22k_per_gram'):,}/g",
    )
    assert_pass(
        "బంగారం" in gold_res.get_spoken_text("telugu"),
        "GoldPriceTool Telugu spoken formatting",
        gold_res.get_spoken_text("telugu")[:80] + "...",
    )

    # 4.3 Reminder Tool
    reminder_tool = ReminderTool()
    assert_pass(reminder_tool.can_handle("Remind me to take my blood pressure pills"), "ReminderTool detects English voice intent")
    assert_pass(reminder_tool.can_handle("మందులు వేసుకోవాలని గుర్తు చేయి"), "ReminderTool detects Telugu voice intent")

    rem_res = await reminder_tool.execute("Remind me to take my morning medicine")
    assert_pass(
        rem_res.success,
        "ReminderTool creation",
        f"Spoken reply: {rem_res.get_spoken_text('english')}",
    )

    # 4.4 Tool Registry Routing
    routed_weather = tool_registry.find_tool("How is the climate in Bengaluru today?")
    assert_pass(isinstance(routed_weather, WeatherTool), "ToolRegistry accurately routes weather queries")

    routed_gold = tool_registry.find_tool("హైదరాబాద్‌లో 22 క్యారెట్ల బంగారం ధర చెప్పండి")
    assert_pass(isinstance(routed_gold, GoldPriceTool), "ToolRegistry accurately routes Telugu gold queries")

    # ─────────────────────────────────────────────────────────────
    # 5. END-TO-END AGENT ORCHESTRATION WITH REAL-TIME RAG
    # ─────────────────────────────────────────────────────────────
    print("\n[SECTION 5] End-to-End Agent Reasoning & Grounded RAG:")

    import uuid
    # 5.1 Weather Query through Agent
    sess1 = ConversationSession(str(uuid.uuid4()))
    reply_weather = await agent.generate_response("What is the weather in Hyderabad?", session=sess1, language="english")
    assert_pass(
        "temperature is" in reply_weather.text.lower() or "°c" in reply_weather.text.lower(),
        "Agent successfully grounds weather with live Open-Meteo RAG",
        f"Reply: '{reply_weather.text}'",
    )
    assert_pass(
        not reply_weather.text.startswith("You asked") and not reply_weather.text.startswith("I heard"),
        "Zero echo verification on weather query",
    )

    # 5.2 Gold Rate Query in Telugu through Agent
    sess2 = ConversationSession(str(uuid.uuid4()))
    reply_gold = await agent.generate_response("ఈరోజు బంగారం ధర ఎంత?", session=sess2, language="telugu")
    assert_pass(
        "బంగారం" in reply_gold.text and "రూపాయలు" in reply_gold.text,
        "Agent grounds Telugu gold rate query with live bullion RAG",
        f"Reply: '{reply_gold.text}'",
    )
    assert_pass(
        "మీరు చెప్పింది" not in reply_gold.text,
        "Zero echo verification on Telugu gold query",
    )

    # 5.3 Cultural Knowledge (Mandatory: Telugu Diwali)
    sess3 = ConversationSession(str(uuid.uuid4()))
    reply_diwali = await agent.generate_response("దీపావళి పండుగ గురించి చెప్పండి.", session=sess3, language="telugu")
    assert_pass(
        "దీపావళి" in reply_diwali.text and "వెలుగుల పండుగ" in reply_diwali.text,
        "Mandatory Telugu Diwali festival response provided with cultural richness",
        f"Reply: '{reply_diwali.text[:90]}...'",
    )
    assert_pass(
        "మీరు చెప్పింది విన్నాను" not in reply_diwali.text and "ఎలా సహాయపడగలను" not in reply_diwali.text,
        "Zero echo and zero generic fallback on Telugu Diwali",
    )

    # 5.4 Technology Knowledge (Mandatory: English AI)
    sess4 = ConversationSession(str(uuid.uuid4()))
    reply_ai = await agent.generate_response("Tell me about artificial intelligence.", session=sess4, language="english")
    assert_pass(
        "artificial intelligence" in reply_ai.text.lower() and "computer science" in reply_ai.text.lower(),
        "Mandatory English AI explanation provided directly and informatively",
        f"Reply: '{reply_ai.text[:90]}...'",
    )
    assert_pass(
        "you asked" not in reply_ai.text.lower() and "how can i help" not in reply_ai.text.lower(),
        "Zero echo and zero generic greeting on English AI query",
    )

    # 5.5 Multi-Turn Conversation Memory Follow-Up
    sess5 = ConversationSession(str(uuid.uuid4()))
    turn1 = await agent.generate_response("Tell me about Diwali.", session=sess5, language="english")
    turn2 = await agent.generate_response("When is it celebrated?", session=sess5, language="english")
    assert_pass(
        "october" in turn2.text.lower() or "november" in turn2.text.lower() or "kartika" in turn2.text.lower(),
        "Multi-turn pronoun follow-up ('When is it celebrated?') resolved to Diwali context",
        f"Follow-up Reply: '{turn2.text}'",
    )

    # 5.6 Spoken Text Cleanliness
    assert_pass(
        reply_diwali.speech_text == clean_text_for_speech(reply_diwali.text),
        "Spoken text formatted and cleaned for Gnani Timbre TTS delivery",
    )

    print_header("🎉 PHASE 6 GNANI THREE-MODEL & TOOL SUITE: ALL TESTS PASSED!")


if __name__ == "__main__":
    asyncio.run(test_suite())
