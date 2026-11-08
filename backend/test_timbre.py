"""
SWARIVA AI — Timbre TTS Test Script

Tests the Gnani Timbre Text-to-Speech integration.
Run from the backend/ directory with the virtual environment activated:

    cd backend
    python test_timbre.py

This script will:
1. Verify API key configuration.
2. Test English TTS with the default voice.
3. Test Hindi TTS.
4. Test Telugu TTS.
5. Save generated audio files to backend/test_audio/.
6. Show you how to play the generated files.
"""
import asyncio
import sys
import json
import logging
from pathlib import Path

# ── Setup logging ──
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("test_timbre")

# ── Ensure we can import from backend/ ──
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import GNANI_API_KEY, TTS_VOICES, GNANI_TTS_MODEL
from gnani_tts import GnaniTTS


async def test_api_connection():
    """Test 1: Verify API key and TTS client setup."""
    print("\n" + "=" * 60)
    print("TEST 1: API Key & TTS Client Check")
    print("=" * 60)

    if not GNANI_API_KEY or GNANI_API_KEY.startswith("placeholder"):
        print("❌ FAIL: GNANI_API_KEY is not set in .env")
        return False

    print("✅ API key loaded: [CONFIGURED SECURELY]")

    try:
        tts = GnaniTTS()
        print(f"✅ GnaniTTS client created")
        print(f"   Model:         {tts.model}")
        print(f"   Default voice:  {tts.default_voice}")
        print(f"   Available:      {tts.get_available_voices()}")
        return True
    except ValueError as e:
        print(f"❌ FAIL: {e}")
        return False


async def test_english_tts():
    """Test 2: Generate English speech."""
    print("\n" + "=" * 60)
    print("TEST 2: English TTS")
    print("=" * 60)

    tts = GnaniTTS()
    output_dir = Path(__file__).resolve().parent / "test_audio"
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / "tts_english.wav"

    text = "Hello! I am Swariva, your intelligent voice assistant. How can I help you today?"
    print(f"📝 Text: \"{text}\"")
    print(f"🎤 Voice: {tts.default_voice}")
    print(f"🌐 Language: English (en-IN)")

    result = await tts.save_audio(
        text=text,
        output_path=output_file,
        language="english",
    )

    if result.success:
        print(f"\n✅ PASS: Audio generated successfully!")
        print(f"   📁 Saved to: {output_file}")
        print(f"   📊 Size: {result.metadata.get('audio_size_bytes', 0):,} bytes")
        return True
    else:
        print(f"\n❌ FAIL: {result.error}")
        return False


async def test_hindi_tts():
    """Test 3: Generate Hindi speech."""
    print("\n" + "=" * 60)
    print("TEST 3: Hindi TTS")
    print("=" * 60)

    tts = GnaniTTS()
    output_dir = Path(__file__).resolve().parent / "test_audio"
    output_file = output_dir / "tts_hindi.wav"

    text = "नमस्ते! मैं स्वरिवा हूँ, आपकी बुद्धिमान आवाज सहायक। आज मैं आपकी कैसे मदद कर सकती हूँ?"
    print(f"📝 Text: \"{text}\"")
    print(f"🌐 Language: Hindi (hi-IN)")

    result = await tts.save_audio(
        text=text,
        output_path=output_file,
        language="hindi",
    )

    if result.success:
        print(f"\n✅ PASS: Hindi audio generated!")
        print(f"   📁 Saved to: {output_file}")
        print(f"   📊 Size: {result.metadata.get('audio_size_bytes', 0):,} bytes")
        return True
    else:
        print(f"\n❌ FAIL: {result.error}")
        return False


async def test_telugu_tts():
    """Test 4: Generate Telugu speech."""
    print("\n" + "=" * 60)
    print("TEST 4: Telugu TTS")
    print("=" * 60)

    tts = GnaniTTS()
    output_dir = Path(__file__).resolve().parent / "test_audio"
    output_file = output_dir / "tts_telugu.wav"

    text = "నమస్కారం! నేను స్వరివ, మీ తెలివైన వాయిస్ అసిస్టెంట్. ఈరోజు మీకు ఎలా సహాయం చేయగలను?"
    print(f"📝 Text: \"{text}\"")
    print(f"🌐 Language: Telugu (te-IN)")

    result = await tts.save_audio(
        text=text,
        output_path=output_file,
        language="telugu",
    )

    if result.success:
        print(f"\n✅ PASS: Telugu audio generated!")
        print(f"   📁 Saved to: {output_file}")
        print(f"   📊 Size: {result.metadata.get('audio_size_bytes', 0):,} bytes")
        return True
    else:
        print(f"\n❌ FAIL: {result.error}")
        return False


async def test_voice_catalog():
    """Test 5: Verify voice catalog configuration."""
    print("\n" + "=" * 60)
    print("TEST 5: Voice Catalog")
    print("=" * 60)

    for model_name, voice_info in TTS_VOICES.items():
        print(f"\n  Model: {model_name}")
        print(f"  Default voice: {voice_info['default']}")
        print(f"  Available voices: {', '.join(voice_info['voices'])}")

    current_model = GNANI_TTS_MODEL
    current_voices = TTS_VOICES.get(current_model, {})
    print(f"\n  ➤ Active model: {current_model}")
    print(f"  ➤ Active voices: {current_voices.get('voices', [])}")
    print("\n✅ PASS: Voice catalog loaded.")
    return True


async def main():
    """Run all Timbre TTS tests sequentially."""
    print("=" * 60)
    print("  SWARIVA AI — Gnani Timbre TTS Test Suite")
    print("=" * 60)

    results = {}

    # Test 1: API key check
    results["api_key"] = await test_api_connection()
    if not results["api_key"]:
        print("\n🛑 Cannot proceed without a valid API key. Fix .env and retry.")
        return

    # Test 2: English
    results["english_tts"] = await test_english_tts()

    # Test 3: Hindi
    results["hindi_tts"] = await test_hindi_tts()

    # Test 4: Telugu
    results["telugu_tts"] = await test_telugu_tts()

    # Test 5: Voice catalog
    results["voice_catalog"] = await test_voice_catalog()

    # Summary
    print("\n" + "=" * 60)
    print("  TEST SUMMARY")
    print("=" * 60)
    for name, passed in results.items():
        icon = "✅" if passed else "❌"
        label = "PASS" if passed else "FAIL"
        print(f"  {icon} {name}: {label}")

    # Show how to play the files
    audio_dir = Path(__file__).resolve().parent / "test_audio"
    wav_files = list(audio_dir.glob("tts_*.wav"))
    if wav_files:
        print("\n" + "=" * 60)
        print("  🔊 HOW TO PLAY THE GENERATED AUDIO FILES")
        print("=" * 60)
        print("\n  Option 1 — Windows File Explorer:")
        print(f"    Open this folder and double-click any .wav file:")
        print(f"    {audio_dir}")
        print("\n  Option 2 — PowerShell command:")
        for f in wav_files:
            print(f"    Start-Process \"{f}\"")
        print("\n  Option 3 — Python (in the venv):")
        print("    import os")
        for f in wav_files:
            print(f"    os.startfile(r\"{f}\")")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

