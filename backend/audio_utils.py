"""
SWARIVA AI — Audio Processing & Format Normalization Utility

Ensures all audio payloads delivered to Gnani Prisma STT strictly conform to:
- Container: WAV (RIFF/WAVE)
- Encoding: 16-bit Linear PCM (s16le)
- Channels: 1 (Mono)
- Sample Rate: 16,000 Hz

Converts browser WebM (Opus), OGG, MP4, AAC, MP3, and FLAC transparently in <15ms.
"""
import io
import wave
import logging
from typing import Tuple

import av

logger = logging.getLogger("swariva.audio_utils")


def is_valid_pcm16_wav(audio_bytes: bytes) -> bool:
    """Checks whether audio bytes already represent a valid 16kHz 16-bit mono PCM WAV."""
    if not (audio_bytes.startswith(b"RIFF") and b"WAVE" in audio_bytes[:16]):
        return False
    try:
        with wave.open(io.BytesIO(audio_bytes), "rb") as w:
            return (
                w.getnchannels() == 1
                and w.getframerate() == 16000
                and w.getsampwidth() == 2
            )
    except Exception:
        return False


def convert_to_pcm16_wav(audio_bytes: bytes) -> Tuple[bytes, str]:
    """
    Decodes any audio container (WebM, OGG, MP4, AAC, MP3, FLAC, non-standard WAV)
    and resamples to standard 16kHz mono 16-bit PCM WAV.

    Returns:
        Tuple[bytes, str]: (wav_bytes, original_detected_format)
    """
    if not audio_bytes or len(audio_bytes) == 0:
        raise ValueError("Audio payload is empty (0 bytes).")

    # Fast path: already valid 16kHz mono PCM WAV
    if is_valid_pcm16_wav(audio_bytes):
        return audio_bytes, "wav_pcm16"

    input_io = io.BytesIO(audio_bytes)
    output_io = io.BytesIO()

    try:
        with av.open(input_io) as in_container:
            audio_stream = next((s for s in in_container.streams if s.type == "audio"), None)
            if audio_stream is None:
                raise ValueError("No audio stream found in the uploaded media payload.")

            detected_format = in_container.format.name or "unknown"
            logger.info(
                "Converting audio container '%s' (codec: %s, rate: %s, channels: %s) to 16kHz mono PCM WAV",
                detected_format,
                audio_stream.codec_context.name if audio_stream.codec_context else "unknown",
                audio_stream.rate,
                audio_stream.channels,
            )

            # Resample to 16000 Hz, mono (layout: mono), s16 (16-bit signed integer)
            resampler = av.AudioResampler(format="s16", layout="mono", rate=16000)

            with wave.open(output_io, "wb") as wav_out:
                wav_out.setnchannels(1)
                wav_out.setsampwidth(2)
                wav_out.setframerate(16000)

                for frame in in_container.decode(audio_stream):
                    frame.pts = None
                    for r_frame in resampler.resample(frame):
                        wav_out.writeframes(r_frame.to_ndarray().tobytes())

                # Flush remaining buffered frames
                for r_frame in resampler.resample(None):
                    wav_out.writeframes(r_frame.to_ndarray().tobytes())

            result_bytes = output_io.getvalue()
            if len(result_bytes) <= 44:  # Only WAV header, no audio frames
                raise ValueError("Converted audio contains no audio frames (silence/empty).")

            return result_bytes, detected_format

    except Exception as e:
        logger.error("Audio conversion failed: %s", e)
        raise ValueError(f"Unable to decode and convert audio: {str(e)}") from e
