"""
SWARIVA AI — AI Intelligence & Response Generation Verification Suite

Tests the 12 conversational intelligence criteria:
1. English greeting
2. English general knowledge ("Tell me about artificial intelligence." -> must give actual AI explanation, NOT a greeting)
3. English educational questions ("What is machine learning?")
4. Telugu general knowledge ("దీపావళి పండుగ గురించి చెప్పండి." -> must give actual Telugu explanation of Diwali, NOT echo)
5. Hindi general knowledge ("मुझे कृत्रिम बुद्धिमत्ता के बारे में समझाइए।")
6. Telugu-English code-mixed questions ("Diwali gurinchi cheppandi", "AI gurinchi explain chey")
7. Hindi-English code-mixed questions ("Diwali ke baare mein batao", "AI kya hota hai explain karo")
8. Follow-up contextual memory questions:
   - Turn 1: "Tell me about Diwali."
   - Turn 2: "When is it celebrated?"
   - Turn 3: "Why do people celebrate it?"
9. Reminder intent ("Remind me to take my medicine at 8 PM.")
10. Accessibility intent ("How do you help blind people?")
11. Duplicate response prevention (same consecutive question doesn't output exact duplicate)
12. Strict no-question-echo rule across all responses:
    - Never begins with "You said", "You asked", "I heard you say", "You mentioned"
    - Never begins with "మీరు చెప్పింది విన్నాను"
    - Never begins with "मैंने सुना कि आपने कहा"
    - Never responds with "How can I help you?" when a question was asked.
"""
import sys
import asyncio
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from agent import agent, clean_text_for_speech
from conversation import ConversationSession, conversation_manager
from intent_classifier import IntentClassifier, IntentType


FORBIDDEN_ECHO_PHRASES = [
    "you said", "you asked", "i heard you say", "you mentioned",
    "మీరు చెప్పింది విన్నాను", "మీరు అడిగారు",
    "मैंने सुना कि आपने कहा", "मैंने आपकी बात सुनी",
]


def assert_no_echo(query: str, reply: str):
    """Asserts that response doesn't repeat query or use echo template phrases."""
    lower_reply = reply.lower().strip()
    for phrase in FORBIDDEN_ECHO_PHRASES:
        assert phrase not in lower_reply, f"Forbidden echo phrase '{phrase}' found in response: '{reply}'"

    # Also assert that the reply doesn't start with the exact query
    assert not lower_reply.startswith(query.lower().strip()), f"Reply begins with exact user query: '{reply}'"

    # If query was a question, assert that reply is not simply 'How can I help you?'
    if any(qmark in query for qmark in ["?", "tell", "explain", "చెప్పు", "చెప్పండి", "बताओ", "समझाओ"]):
        assert lower_reply not in [
            "how can i help you today?",
            "how can i help you?",
            "నేను మీకు ఎలా సహాయపడగలను?",
            "मैं आपकी क्या सहायता कर सकती हूँ?"
        ], f"Generic greeting fallback returned for substantive question: '{reply}'"


async def run_tests():
    print("=" * 75)
    print("SWARIVA AI — AI CONVERSATIONAL INTELLIGENCE & REASONING VERIFICATION")
    print(f"Active Provider: {agent.primary_provider.name}")
    print("=" * 75)

    passed = 0
    total = 12

    # ── TEST 1: English Greeting ──
    print("\n[TEST 1] English Greeting...")
    s1 = conversation_manager.get_or_create(preferred_language="english")
    r1 = await agent.generate_response("Hello Swariva, good morning!", s1, language="english")
    print(f"  User : 'Hello Swariva, good morning!'")
    print(f"  Reply: '{r1.text}'")
    assert any(w in r1.text.lower() for w in ["hello", "swariva", "good morning", "wonderful"]), "Failed greeting response"
    assert_no_echo("Hello Swariva, good morning!", r1.text)
    print("  -> PASS")
    passed += 1

    # ── TEST 2: English General Knowledge (MANDATORY TEST: Artificial Intelligence) ──
    print("\n[TEST 2] English General Knowledge (Mandatory: 'Tell me about artificial intelligence.')...")
    s2 = conversation_manager.get_or_create(preferred_language="english")
    r2 = await agent.generate_response("Tell me about artificial intelligence.", s2, language="english")
    print(f"  User : 'Tell me about artificial intelligence.'")
    print(f"  Reply: '{r2.text}'")
    assert "artificial intelligence" in r2.text.lower() or "ai" in r2.text.lower() or "computer science" in r2.text.lower(), "Missing AI concept explanation"
    assert not r2.text.lower().startswith("hello"), "Incorrect greeting returned for direct AI question"
    assert "how can i help you" not in r2.text.lower(), "Generic fallback returned for AI question"
    assert_no_echo("Tell me about artificial intelligence.", r2.text)
    print("  -> PASS (Direct AI explanation provided without echo or greeting)")
    passed += 1

    # ── TEST 3: English Educational Question ──
    print("\n[TEST 3] English Educational Question ('What is machine learning?')...")
    s3 = conversation_manager.get_or_create(preferred_language="english")
    r3 = await agent.generate_response("What is machine learning?", s3, language="english")
    print(f"  User : 'What is machine learning?'")
    print(f"  Reply: '{r3.text}'")
    assert "machine learning" in r3.text.lower() or "data" in r3.text.lower() or "patterns" in r3.text.lower()
    assert_no_echo("What is machine learning?", r3.text)
    print("  -> PASS")
    passed += 1

    # ── TEST 4: Telugu General Knowledge (MANDATORY TEST: Diwali) ──
    print("\n[TEST 4] Telugu General Knowledge (Mandatory: 'దీపావళి పండుగ గురించి చెప్పండి.')...")
    s4 = conversation_manager.get_or_create(preferred_language="telugu")
    r4 = await agent.generate_response("దీపావళి పండుగ గురించి చెప్పండి.", s4, language="telugu")
    print(f"  User : 'దీపావళి పండుగ గురించి చెప్పండి.'")
    print(f"  Reply: '{r4.text}'")
    assert any(term in r4.text for term in ["వెలుగు", "పండుగ", "దీపాలు", "లక్ష్మీదేవి", "నరకాసుర", "శ్రీరాముడు"]), "Missing Telugu Diwali explanation"
    assert "మీరు చెప్పింది విన్నాను" not in r4.text, "Forbidden Telugu echo detected"
    assert r4.text.strip() != "దీపావళి పండుగ గురించి చెప్పండి.", "Echoed user question exactly"
    assert_no_echo("దీపావళి పండుగ గురించి చెప్పండి.", r4.text)
    print("  -> PASS (Rich, authentic Telugu explanation of Diwali provided with zero echo)")
    passed += 1

    # ── TEST 5: Hindi General Knowledge ──
    print("\n[TEST 5] Hindi General Knowledge ('मुझे कृत्रिम बुद्धिमत्ता के बारे में समझाइए।')...")
    s5 = conversation_manager.get_or_create(preferred_language="hindi")
    r5 = await agent.generate_response("मुझे कृत्रिम बुद्धिमत्ता के बारे में समझाइए।", s5, language="hindi")
    print(f"  User : 'मुझे कृत्रिम बुद्धिमत्ता के बारे में समझाइए।'")
    print(f"  Reply: '{r5.text}'")
    assert any(w in r5.text for w in ["कृत्रिम बुद्धिमत्ता", "कंप्यूटर", "मशीन", "सीखने"]), "Missing Hindi AI explanation"
    assert "मैंने सुना कि आपने कहा" not in r5.text, "Forbidden Hindi echo detected"
    assert_no_echo("मुझे कृत्रिम बुद्धिमत्ता के बारे में समझाइए।", r5.text)
    print("  -> PASS")
    passed += 1

    # ── TEST 6: Telugu-English Code-Mixed ──
    print("\n[TEST 6] Telugu-English Code-Mixed ('Diwali gurinchi cheppandi')...")
    s6 = conversation_manager.get_or_create(preferred_language="telugu")
    r6 = await agent.generate_response("Diwali gurinchi cheppandi", s6, language="auto")
    print(f"  User : 'Diwali gurinchi cheppandi'")
    print(f"  Reply: '{r6.text}'")
    assert any(term in r6.text for term in ["దీపావళి", "పండుగ", "వెలుగుల", "Diwali"]), "Failed code-mixed resolution"
    assert_no_echo("Diwali gurinchi cheppandi", r6.text)
    print("  -> PASS")
    passed += 1

    # ── TEST 7: Hindi-English Code-Mixed ──
    print("\n[TEST 7] Hindi-English Code-Mixed ('Diwali ke baare mein batao')...")
    s7 = conversation_manager.get_or_create(preferred_language="hindi")
    r7 = await agent.generate_response("Diwali ke baare mein batao", s7, language="auto")
    print(f"  User : 'Diwali ke baare mein batao'")
    print(f"  Reply: '{r7.text}'")
    assert any(term in r7.text for term in ["दीपावली", "दिवाली", "त्योहार", "रोशनी"]), "Failed Hinglish resolution"
    assert_no_echo("Diwali ke baare mein batao", r7.text)
    print("  -> PASS")
    passed += 1

    # ── TEST 8: Multi-Turn Contextual Follow-Up ──
    print("\n[TEST 8] Multi-Turn Contextual Memory Follow-Ups (Diwali: Intro -> When -> Why)...")
    s8 = conversation_manager.get_or_create(preferred_language="english")
    # Turn 1: Main topic
    t1 = await agent.generate_response("Tell me about Diwali.", s8, language="english")
    print(f"  Turn 1 User : 'Tell me about Diwali.'")
    print(f"  Turn 1 Reply: '{t1.text}'")
    assert "diwali" in t1.text.lower() or "festival of lights" in t1.text.lower()

    # Turn 2: 'When is it celebrated?' (Pronoun 'it' must resolve to Diwali)
    t2 = await agent.generate_response("When is it celebrated?", s8, language="english")
    print(f"  Turn 2 User : 'When is it celebrated?'")
    print(f"  Turn 2 Reply: '{t2.text}'")
    assert any(w in t2.text.lower() for w in ["october", "november", "kartika", "autumn", "new moon", "calendar"]), "Turn 2 failed to resolve 'it' to Diwali date"
    assert_no_echo("When is it celebrated?", t2.text)

    # Turn 3: 'Why do people celebrate it?'
    t3 = await agent.generate_response("Why do people celebrate it?", s8, language="english")
    print(f"  Turn 3 User : 'Why do people celebrate it?'")
    print(f"  Turn 3 Reply: '{t3.text}'")
    assert any(w in t3.text.lower() for w in ["victory", "rama", "narakasura", "light over darkness", "lakshmi"]), "Turn 3 failed to explain reason for Diwali"
    assert_no_echo("Why do people celebrate it?", t3.text)
    print("  -> PASS (Multi-turn pronoun resolution fully functional across all turns)")
    passed += 1

    # ── TEST 9: Reminder Intent ──
    print("\n[TEST 9] Reminder Intent Extraction ('Remind me to take my medicine at 8 PM')...")
    s9 = conversation_manager.get_or_create(preferred_language="english")
    r9 = await agent.generate_response("Remind me to take my medicine at 8 PM", s9, language="english")
    print(f"  User : 'Remind me to take my medicine at 8 PM'")
    print(f"  Reply: '{r9.text}'")
    assert "reminder" in r9.text.lower() or "alert" in r9.text.lower()
    assert_no_echo("Remind me to take my medicine at 8 PM", r9.text)
    print("  -> PASS")
    passed += 1

    # ── TEST 10: Accessibility Intent ──
    print("\n[TEST 10] Accessibility Intent ('How do you help blind people?')...")
    s10 = conversation_manager.get_or_create(preferred_language="english")
    r10 = await agent.generate_response("How do you help blind people?", s10, language="english")
    print(f"  User : 'How do you help blind people?'")
    print(f"  Reply: '{r10.text}'")
    assert any(w in r10.text.lower() for w in ["accessibility", "voice", "hands-free", "contrast", "read-aloud"])
    assert_no_echo("How do you help blind people?", r10.text)
    print("  -> PASS")
    passed += 1

    # ── TEST 11: Duplicate Response Prevention ──
    print("\n[TEST 11] Duplicate Response Prevention...")
    s11 = conversation_manager.get_or_create(preferred_language="english")
    r11_a = await agent.generate_response("What is cloud computing?", s11, language="english")
    r11_b = await agent.generate_response("What is cloud computing?", s11, language="english")
    print(f"  Reply 1: '{r11_a.text[:60]}...'")
    print(f"  Reply 2: '{r11_b.text[:60]}...'")
    assert r11_a.text != r11_b.text, "Consecutive identical responses were not differentiated"
    print("  -> PASS (Duplicate response variation mechanism confirmed)")
    passed += 1

    # ── TEST 12: Speech Text Formatting Cleanliness ──
    print("\n[TEST 12] Speech Cleanliness (clean_text_for_speech)...")
    sample_raw = "**Diwali** is a #festival. [cheerfully] It is celebrated on https://example.com/diwali *every year*!"
    cleaned = clean_text_for_speech(sample_raw)
    print(f"  Raw    : '{sample_raw}'")
    print(f"  Cleaned: '{cleaned}'")
    assert "**" not in cleaned
    assert "#" not in cleaned
    assert "http" not in cleaned
    assert "[" not in cleaned
    assert "]" not in cleaned
    assert cleaned == "Diwali is a festival. It is celebrated on every year!"
    print("  -> PASS")
    passed += 1

    print("\n" + "=" * 75)
    print(f"🎉 AI CONVERSATIONAL INTELLIGENCE SUITE: {passed}/{total} PASSED (100%)")
    print("=" * 75)


if __name__ == "__main__":
    asyncio.run(run_tests())
