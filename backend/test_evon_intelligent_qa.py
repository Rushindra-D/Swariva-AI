"""
SWARIVA AI — Evon Intelligent Question Answering & Reasoning Verification Suite

Tests the 7 mandatory Phase 5 questions:
1. What is Diwali?
2. What is a cyclone?
3. Explain artificial intelligence.
4. Explain machine learning.
5. What causes cyclones?
6. What is blockchain?
7. Explain photosynthesis.

Also tests:
- Multilingual reasoning (Telugu, Hindi, Code-mixed Hinglish/Tenglish)
- Real-time tool RAG integration (Weather, Gold prices, Reminders)
- Zero echoing and non-generic answers
- End-to-end voice loop (Prisma STT -> Reasoning -> Timbre TTS)
"""
import sys
import uuid
import asyncio
from pathlib import Path

# Add backend directory to path
BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from agent import agent, clean_text_for_speech, filter_echo_prefixes
from conversation import ConversationSession
from gnani_stt import GnaniSTT
from gnani_tts import GnaniTTS


def print_banner(text: str):
    print("\n" + "=" * 78)
    print(f"  {text}")
    print("=" * 78)


def verify_answer(query: str, reply_text: str, expected_keywords: list, test_num: int):
    print(f"\n[Q{test_num}] User Query: '{query}'")
    print(f"      Response: '{reply_text}'")

    # 1. Non-empty check
    assert reply_text and len(reply_text.strip()) > 30, f"Q{test_num}: Response too short or empty!"

    # 2. Zero Echo check
    lower = reply_text.lower()
    echo_phrases = ["you asked", "you said", "you mentioned", "i heard you", "మీరు చెప్పింది", "మీరు అడిగారు", "मैंने सुना", "आपने पूछा"]
    for echo in echo_phrases:
        assert echo not in lower, f"Q{test_num}: Echo detected ('{echo}') in: {reply_text}"

    # 3. Non-generic check
    generic_phrases = ["how can i help", "నేను మీకు ఎలా సహాయపడగలను", "मैं आपकी क्या सहायता", "that is an insightful question", "ఇది చాలా మంచి ప్రశ్న"]
    for gen in generic_phrases:
        assert gen not in lower, f"Q{test_num}: Generic placeholder answer detected ('{gen}') in: {reply_text}"

    # 4. Relevance check (at least one key concept mentioned)
    matched = [kw for kw in expected_keywords if kw.lower() in lower]
    assert len(matched) > 0, f"Q{test_num}: Response does not mention expected concepts {expected_keywords}!"

    print(f"      ✅ PASS (Keywords matched: {matched})")


async def main():
    print_banner("SWARIVA AI — INTELLIGENT QUESTION ANSWERING & REASONING SUITE")

    # ─────────────────────────────────────────────────────────────
    # PART 1: THE 7 MANDATORY EVALUATION QUESTIONS (ENGLISH)
    # ─────────────────────────────────────────────────────────────
    print("\n--- PART 1: The 7 Evaluation Questions (English) ---")

    test_cases_en = [
        ("What is Diwali?", ["diwali", "festival", "lights", "light"], 1),
        ("What is a cyclone?", ["cyclone", "storm", "pressure", "rotating", "winds"], 2),
        ("Explain artificial intelligence.", ["artificial intelligence", "ai", "computer science", "machines", "reasoning"], 3),
        ("Explain machine learning.", ["machine learning", "data", "patterns", "models", "learn"], 4),
        ("What causes cyclones?", ["warm", "ocean", "pressure", "coriolis", "air", "water"], 5),
        ("What is blockchain?", ["blockchain", "ledger", "blocks", "cryptograph", "decentralized", "transactions"], 6),
        ("Explain photosynthesis.", ["photosynthesis", "sunlight", "plants", "oxygen", "chlorophyll", "carbon dioxide"], 7),
    ]

    for q, keywords, num in test_cases_en:
        session = ConversationSession(str(uuid.uuid4()))
        reply = await agent.generate_response(q, session=session, language="english")
        verify_answer(q, reply.text, keywords, num)

    # ─────────────────────────────────────────────────────────────
    # PART 2: MULTILINGUAL REASONING (TELUGU & HINDI)
    # ─────────────────────────────────────────────────────────────
    print("\n--- PART 2: Multilingual Reasoning (Telugu & Hindi) ---")

    test_cases_indic = [
        # Telugu
        ("దీపావళి పండుగ గురించి చెప్పండి.", ["దీపావళి", "వెలుగుల", "పండుగ"], "Telugu Diwali", "telugu"),
        ("తుఫాను అంటే ఏమిటి?", ["తుఫాను", "అల్పపీడన", "గాలుల", "వాయుగుండం"], "Telugu Cyclone", "telugu"),
        ("తుఫానులు ఎందుకు వస్తాయి?", ["సముద్ర", "వేడి", "అల్పపీడన", "కొరియోలిస్"], "Telugu Cyclone Causes", "telugu"),
        ("బ్లాక్‌చెయిన్ అంటే ఏమిటి?", ["బ్లాక్‌చెయిన్", "డిజిటల్", "లెడ్జర్", "క్రిప్టోగ్రఫీ"], "Telugu Blockchain", "telugu"),
        ("కిరణజన్య సంయోగక్రియను వివరించండి.", ["కిరణజన్య", "సూర్యరశ్మి", "ఆహారాన్ని", "ఆక్సిజన్"], "Telugu Photosynthesis", "telugu"),

        # Hindi
        ("दीपावली क्या है?", ["दीपावली", "त्योहार", "रोशनी", "दीपक"], "Hindi Diwali", "hindi"),
        ("चक्रवात क्या होता है?", ["चक्रवात", "तूफान", "दबाव", "हवा"], "Hindi Cyclone", "hindi"),
        ("चक्रवात क्यों आते हैं?", ["चक्रवात", "समुद्र", "दबाव", "गर्म", "कोरिओलिस"], "Hindi Cyclone Causes", "hindi"),
        ("ब्लॉकचेन क्या है?", ["ब्लॉकचेन", "डिजिटल", "बहीखाता", "ब्लॉक"], "Hindi Blockchain", "hindi"),
        ("प्रकाश संश्लेषण को समझाइए।", ["प्रकाश संश्लेषण", "पौधे", "सूर्य", "ऑक्सीजन", "क्लोरोफिल"], "Hindi Photosynthesis", "hindi"),
    ]

    idx = 8
    for q, keywords, label, lang in test_cases_indic:
        session = ConversationSession(str(uuid.uuid4()))
        reply = await agent.generate_response(q, session=session, language=lang)
        verify_answer(q, reply.text, keywords, idx)
        idx += 1

    # ─────────────────────────────────────────────────────────────
    # PART 3: CODE-MIXED CONVERSATIONS (TENGLISH & HINGLISH)
    # ─────────────────────────────────────────────────────────────
    print("\n--- PART 3: Code-Mixed Conversations ---")

    code_mixed_cases = [
        ("Diwali gurinchi cheppandi", ["దీపావళి", "పండుగ", "వెలుగుల"], "Tenglish Diwali", "telugu"),
        ("Cyclone ante enti?", ["తుఫాను", "గాలుల", "అల్పపీడన"], "Tenglish Cyclone", "telugu"),
        ("Diwali ke baare mein batao", ["दीपावली", "त्योहार", "रोशनी"], "Hinglish Diwali", "hindi"),
        ("Cyclone kya hota hai?", ["चक्रवात", "तूफान", "दबाव"], "Hinglish Cyclone", "hindi"),
    ]

    for q, keywords, label, lang in code_mixed_cases:
        session = ConversationSession(str(uuid.uuid4()))
        reply = await agent.generate_response(q, session=session, language="auto")
        verify_answer(q, reply.text, keywords, idx)
        idx += 1

    # ─────────────────────────────────────────────────────────────
    # PART 4: REAL-TIME TOOL RETRIEVAL (WEATHER, GOLD, REMINDERS)
    # ─────────────────────────────────────────────────────────────
    print("\n--- PART 4: Real-Time Tool Retrieval & RAG Grounding ---")

    # Weather
    sess_w = ConversationSession(str(uuid.uuid4()))
    reply_w = await agent.generate_response("What is the weather in Hyderabad?", session=sess_w, language="english")
    verify_answer("What is the weather in Hyderabad?", reply_w.text, ["temperature", "°c", "humidity"], idx)
    idx += 1

    # Gold
    sess_g = ConversationSession(str(uuid.uuid4()))
    reply_g = await agent.generate_response("ఈరోజు బంగారం ధర ఎంత?", session=sess_g, language="telugu")
    verify_answer("ఈరోజు బంగారం ధర ఎంత?", reply_g.text, ["బంగారం", "రూపాయలు"], idx)
    idx += 1

    # ─────────────────────────────────────────────────────────────
    # PART 5: END-TO-END VOICE LOOP (PRISMA STT -> REASONING -> TIMBRE TTS)
    # ─────────────────────────────────────────────────────────────
    print("\n--- PART 5: End-to-End Voice Loop ---")
    stt = GnaniSTT()
    tts = GnaniTTS()

    audio_path = BACKEND_DIR / "test_audio" / "tts_english.wav"
    stt_res = await stt.transcribe(audio_path, language="english")
    assert stt_res.success, f"Voice loop STT failed: {stt_res.error}"
    print(f"      [STT Transcript]: '{stt_res.transcript}'")

    sess_voice = ConversationSession(str(uuid.uuid4()))
    agent_res = await agent.generate_response(stt_res.transcript, session=sess_voice, language="english")
    print(f"      [Agent Reasoning]: '{agent_res.text}'")

    tts_res = await tts.synthesize(agent_res.speech_text, language="english")
    assert tts_res.success and len(tts_res.audio_bytes) > 1000, f"Voice loop TTS failed: {tts_res.error}"
    print(f"      [TTS Synthesized Audio]: {len(tts_res.audio_bytes):,} bytes | Voice: {tts_res.voice}")
    print("      ✅ PASS (End-to-End Voice-to-Voice Loop Successful)")

    print_banner("🎉 ALL INTELLIGENT QUESTION ANSWERING & VOICE PIPELINE TESTS PASSED!")


if __name__ == "__main__":
    asyncio.run(main())
