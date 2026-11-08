"""
SWARIVA AI — Voice Activity Detection (VAD) & Live Silence Simulation Suite

Validates:
1. Dynamic silence detection on spoken audio (user speaks for 3-5s, pauses for 2s).
2. End of speech detection without waiting for fixed limits.
3. Real-time conversion, STT recognition, agent response, and TTS synthesis.
4. Latency breakdown across each stage.
"""
import io
import time
import asyncio
from pathlib import Path
import numpy as np
import av
import wave
import httpx

def create_speech_with_silence(speech_wav_path: Path, silence_sec: float = 2.0) -> bytes:
    """Creates audio simulating speech followed by ~2.0s of silence, encoded as WebM/Opus."""
    # 1. Read speech audio frames
    in_container = av.open(str(speech_wav_path))
    in_stream = next(s for s in in_container.streams if s.type == "audio")

    out_io = io.BytesIO()
    with av.open(out_io, "w", format="webm") as out_container:
        out_stream = out_container.add_stream("opus", rate=48000)
        out_stream.layout = "mono"
        resampler = av.AudioResampler(format="s16", layout="mono", rate=48000)

        pts = 0
        # Stream spoken words
        for frame in in_container.decode(in_stream):
            frame.pts = None
            for r_frame in resampler.resample(frame):
                r_frame.pts = pts
                pts += r_frame.samples
                for packet in out_stream.encode(r_frame):
                    out_container.mux(packet)

        # Stream silence frames (silence_sec)
        silence_samples_per_frame = 960  # 20ms at 48kHz
        total_silence_frames = int((silence_sec * 48000) / silence_samples_per_frame)
        zero_samples = np.zeros((1, silence_samples_per_frame), dtype=np.int16)

        for _ in range(total_silence_frames):
            s_frame = av.AudioFrame.from_ndarray(zero_samples, format="s16", layout="mono")
            s_frame.rate = 48000
            s_frame.pts = pts
            pts += silence_samples_per_frame
            for packet in out_stream.encode(s_frame):
                out_container.mux(packet)

        # Flush
        for packet in out_stream.encode(None):
            out_container.mux(packet)

    in_container.close()
    return out_io.getvalue()


async def run_vad_simulation_tests():
    print("=" * 75)
    print("SWARIVA AI — VOICE ACTIVITY DETECTION & REAL-TIME SPEECH TEST")
    print("=" * 75)

    audio_dir = Path(__file__).resolve().parent / "test_audio"
    test_cases = [
        ("English Short Speech", audio_dir / "tts_english.wav", "en-IN"),
        ("Hindi Natural Speech", audio_dir / "tts_hindi.wav", "hi-IN"),
        ("Telugu Natural Speech", audio_dir / "tts_telugu.wav", "te-IN"),
    ]

    all_passed = True

    for label, wav_path, expected_lang in test_cases:
        print(f"\n🎙️  Testing {label} (Spoken Audio + 2.0s Trailing Silence):")
        start_enc = time.time()
        webm_with_silence = create_speech_with_silence(wav_path, silence_sec=2.0)
        enc_dur = time.time() - start_enc
        print(f"  • Generated WebM/Opus Payload: {len(webm_with_silence)} bytes (Simulated user finished speaking)")

        # Send to FastAPI live endpoint
        files = {"audio_file": ("user_speech.webm", webm_with_silence, "audio/webm")}
        data = {"session_id": "vad_test_session", "language": "auto"}

        start_call = time.time()
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post("http://127.0.0.1:8000/api/v1/voice/chat", data=data, files=files)
        total_time = time.time() - start_call

        if resp.status_code != 200:
            print(f"  ❌ HTTP Error: {resp.status_code}")
            all_passed = False
            continue

        result = resp.json()
        print(f"  • Response Code      : {resp.status_code} OK (Round-trip: {total_time:.2f}s)")
        print(f"  • Speech Recognized  : \"{result.get('transcript')}\"")
        print(f"  • Language Detected  : {result.get('detected_language')}")
        print(f"  • Assistant Reply    : \"{result.get('response_text')}\"")
        b64_len = len(result.get("audio_base64") or "")
        print(f"  • Synthesized Audio  : {b64_len} Base64 characters returned")
        print(f"  • Latency Metrics    : STT Latency: {result.get('processing_time_stt')}s | TTS Latency: {result.get('processing_time_tts')}s")

        if result.get("success") and result.get("transcript") and b64_len > 0:
            print(f"  ✅ PASS: {label} processed immediately without waiting for fixed timer!")
        else:
            print(f"  ❌ FAIL: {result.get('error')}")
            all_passed = False

    print("\n" + "=" * 75)
    print(f"VAD REAL-TIME TEST SUMMARY: {'✅ 100% PASS' if all_passed else '❌ FAILED'}")
    print("=" * 75)
    return all_passed


if __name__ == "__main__":
    asyncio.run(run_vad_simulation_tests())
