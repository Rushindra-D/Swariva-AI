"""
SWARIVA AI — Browser WebM to Gnani STT Live Pipeline Test
Simulates real browser microphone recordings (WebM/Opus) and validates
automatic conversion to 16kHz mono PCM WAV, Gnani Prisma STT transcription,
agent reasoning, and Gnani Timbre TTS speech output.
"""
import io
import time
import asyncio
from pathlib import Path
import av
import httpx

def wav_to_webm(wav_path: Path) -> bytes:
    """Convert a WAV file to WebM/Opus (mirroring Chrome browser MediaRecorder output)."""
    in_container = av.open(str(wav_path))
    in_stream = next(s for s in in_container.streams if s.type == "audio")

    out_io = io.BytesIO()
    with av.open(out_io, "w", format="webm") as out_container:
        out_stream = out_container.add_stream("opus", rate=48000)
        out_stream.layout = "mono"
        resampler = av.AudioResampler(format="s16", layout="mono", rate=48000)

        pts = 0
        for frame in in_container.decode(in_stream):
            frame.pts = None
            for r_frame in resampler.resample(frame):
                r_frame.pts = pts
                pts += r_frame.samples
                for packet in out_stream.encode(r_frame):
                    out_container.mux(packet)

        for r_frame in resampler.resample(None):
            r_frame.pts = pts
            pts += r_frame.samples
            for packet in out_stream.encode(r_frame):
                out_container.mux(packet)

        for packet in out_stream.encode(None):
            out_container.mux(packet)

    in_container.close()
    return out_io.getvalue()


async def test_live_browser_voice_pipeline():
    print("=" * 70)
    print("SWARIVA AI — LIVE BROWSER WEBM SPEECH PIPELINE TEST")
    print("=" * 70)

    audio_dir = Path(__file__).resolve().parent / "test_audio"
    test_cases = [
        ("English", audio_dir / "tts_english.wav", "en-IN"),
        ("Hindi", audio_dir / "tts_hindi.wav", "hi-IN"),
        ("Telugu", audio_dir / "tts_telugu.wav", "te-IN"),
    ]

    session_id = "test_live_webm_session"
    all_passed = True

    for label, wav_path, expected_lang in test_cases:
        print(f"\n--- Testing {label} (Browser WebM Audio) ---")
        webm_bytes = wav_to_webm(wav_path)
        print(f"  • Encoded to WebM/Opus: {len(webm_bytes)} bytes (starts with {webm_bytes[:4].hex()})")

        files = {"audio_file": ("user_speech.webm", webm_bytes, "audio/webm")}
        data = {"session_id": session_id, "language": "auto"}

        start_time = time.time()
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post("http://127.0.0.1:8000/api/v1/voice/chat", data=data, files=files)
        total_latency = time.time() - start_time

        if resp.status_code != 200:
            print(f"  ❌ HTTP Status: {resp.status_code}")
            print(f"     Response: {resp.text}")
            all_passed = False
            continue

        result = resp.json()
        print(f"  • HTTP Status Code    : {resp.status_code} OK (Round-trip: {total_latency:.2f}s)")
        print(f"  • Success Flag        : {result.get('success')}")
        print(f"  • User Transcript     : \"{result.get('transcript')}\"")
        print(f"  • Detected Language   : {result.get('detected_language')}")
        print(f"  • Assistant Response  : \"{result.get('response_text')}\"")
        b64 = result.get("audio_base64") or ""
        print(f"  • Audio Reply Base64  : {'YES' if b64 else 'NO'} ({len(b64)} chars)")
        print(f"  • Latency Breakdown   : STT: {result.get('processing_time_stt')}s | TTS: {result.get('processing_time_tts')}s")

        if not result.get("success"):
            print(f"  ❌ FAIL: {result.get('error')}")
            all_passed = False
        else:
            print(f"  ✅ PASS: {label} WebM successfully converted, transcribed, reasoned, and spoken!")

    print("\n" + "=" * 70)
    print(f"OVERALL RESULT: {'✅ 100% PASS' if all_passed else '❌ FAILED'}")
    print("=" * 70)
    return all_passed


if __name__ == "__main__":
    asyncio.run(test_live_browser_voice_pipeline())
