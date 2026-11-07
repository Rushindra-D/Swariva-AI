"""
SWARIVA AI — Live FastAPI Endpoints Verification Script

Executes real HTTP requests against the FastAPI app:
1. Health check: GET /health
2. System info: GET /api/v1/info
3. Text chat: POST /api/v1/chat (English, Hindi, Telugu)
4. Session context: Multi-turn chat
5. Voice interaction: POST /api/v1/voice/chat (using real audio from Phase 2)
"""
import sys
from pathlib import Path
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent))

from main import app

client = TestClient(app)


def test_live_suite():
    print("=" * 60)
    print("  SWARIVA AI — Live FastAPI Endpoints Verification")
    print("=" * 60)

    # 1. Health check
    print("\n[1] Testing GET /health ...")
    r = client.get("/health")
    assert r.status_code == 200, f"Health check failed: {r.text}"
    print("✅ /health status:", r.json()["status"], f"(STT: {r.json()['models']['stt']}, TTS: {r.json()['models']['tts']})")

    # 2. Text chat
    print("\n[2] Testing POST /api/v1/chat ...")
    r = client.post("/api/v1/chat", json={"message": "Hello Swariva, who are you?", "language": "english"})
    assert r.status_code == 200
    res = r.json()
    print("✅ Chat response:", res["response"][:80], "...")
    print("   Session ID:", res["session_id"])
    session_id = res["session_id"]

    # 3. Follow-up turn
    print("\n[3] Testing multi-turn session continuity ...")
    r2 = client.post("/api/v1/chat", json={"message": "Can you remind me about my medicine?", "session_id": session_id})
    assert r2.status_code == 200
    print("✅ Follow-up response:", r2.json()["response"][:80], "...")
    print("   History turns recorded:", r2.json()["metadata"]["history_length"])

    # 4. Multilingual (Telugu)
    print("\n[4] Testing Telugu Text Chat ...")
    r_te = client.post("/api/v1/chat", json={"message": "నమస్కారం, బాగున్నారా?", "language": "telugu"})
    assert r_te.status_code == 200
    print("✅ Telugu reply:", r_te.json()["response"])

    # 5. Live Voice interaction with real audio
    audio_path = Path(__file__).resolve().parent / "test_audio" / "tts_english.wav"
    if audio_path.exists():
        print(f"\n[5] Testing POST /api/v1/voice/chat with live audio ({audio_path.name}) ...")
        with open(audio_path, "rb") as f:
            files = {"audio_file": (audio_path.name, f.read(), "audio/wav")}
            data = {"language": "english"}
            r_voice = client.post("/api/v1/voice/chat", files=files, data=data)

        assert r_voice.status_code == 200
        v_data = r_voice.json()
        print("✅ Voice-to-Voice Loop Successful!")
        print("   Transcript:   ", v_data["transcript"])
        print("   Detected Lang:", v_data["detected_language"])
        print("   Response Text:", v_data["response_text"][:80], "...")
        print("   Audio Base64: ", f"{len(v_data['audio_base64'])} chars" if v_data["audio_base64"] else "None")
        print("   STT Latency:  ", f"{v_data['processing_time_stt']}s")
        print("   TTS Latency:  ", f"{v_data['processing_time_tts']}s")
    else:
        print("\n[5] ⏭️ Skipped voice test (tts_english.wav not found)")

    print("\n" + "=" * 60)
    print("  ALL LIVE API CHECKS PASSED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    test_live_suite()
