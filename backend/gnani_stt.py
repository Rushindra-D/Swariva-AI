"""
SWARIVA AI — Gnani Prisma STT (Speech-to-Text) Module

Integrates with Gnani AI's Prisma API for speech recognition.
Supports Telugu, Hindi, English, and auto-detection.

API Reference: https://docs.gnani.ai/api/STT/speech-to-text
Endpoint: POST https://api.vachana.ai/stt/v3
Auth: X-API-Key-ID header
"""
import logging
from pathlib import Path
from dataclasses import dataclass

import httpx

from config import (
    GNANI_API_KEY,
    GNANI_STT_ENDPOINT,
    GNANI_STT_MODEL,
    SUPPORTED_LANGUAGES,
)

logger = logging.getLogger("swariva.stt")


@dataclass
class STTResult:
    """Structured result from a Prisma STT API call."""
    success: bool
    transcript: str
    detected_language: str
    model: str
    request_id: str
    processing_time: float
    raw_response: dict
    error: str | None = None


class GnaniSTT:
    """
    Client for Gnani AI's Prisma Speech-to-Text API.

    Usage:
        stt = GnaniSTT()
        result = await stt.transcribe("audio.wav", language="english")
        print(result.transcript)
    """

    # Max audio duration for the sync REST endpoint (Gnani limit)
    MAX_DURATION_SECONDS = 30

    # Supported audio formats (from Gnani docs)
    SUPPORTED_FORMATS = {".wav", ".mp3", ".ogg", ".flac", ".aac", ".m4a"}

    # Output format options
    FORMAT_OPTIONS = {"verbatim", "transcribe", "codemix", "transliterate"}

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or GNANI_API_KEY
        self.model = model or GNANI_STT_MODEL
        self._validate_setup()

    def _validate_setup(self) -> None:
        """Validate that the API key is configured."""
        if not self.api_key or self.api_key.startswith("placeholder"):
            raise ValueError(
                "Gnani API key is not configured. "
                "Set GNANI_API_KEY in your .env file."
            )

    def _get_headers(self) -> dict:
        """Build authentication headers for Gnani API."""
        return {"X-API-Key-ID": self.api_key}

    def _resolve_language(self, language: str) -> str:
        """
        Convert a friendly language name to a Gnani language code.
        Accepts: 'english', 'hindi', 'telugu', 'auto', or direct codes like 'en-IN'.
        """
        if language.lower() == "auto":
            return "indic-auto"
        # Check if it's already a locale code (e.g., "en-IN")
        if "-" in language:
            return language
        # Look up friendly name
        code = SUPPORTED_LANGUAGES.get(language.lower())
        if not code:
            supported = ", ".join(SUPPORTED_LANGUAGES.keys())
            raise ValueError(
                f"Unsupported language: '{language}'. "
                f"Choose from: {supported}, 'auto', or a locale code (e.g., 'en-IN')."
            )
        return code

    def _validate_audio_file(self, file_path: str | Path) -> Path:
        """Validate that the audio file exists and has a supported format."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Audio file not found: {path}")
        if path.suffix.lower() not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported audio format: '{path.suffix}'. "
                f"Supported: {', '.join(self.SUPPORTED_FORMATS)}"
            )
        return path

    async def transcribe(
        self,
        audio_source: str | Path | bytes,
        language: str = "auto",
        output_format: str = "transcribe",
        filename: str = "audio.wav",
    ) -> STTResult:
        """
        Transcribe an audio file or audio bytes using Gnani Prisma.

        Args:
            audio_source: Path to an audio file, or raw audio bytes.
            language: Language name ('english', 'hindi', 'telugu', 'auto')
                      or locale code ('en-IN', 'hi-IN', 'te-IN', 'indic-auto').
            output_format: One of 'verbatim', 'transcribe', 'codemix', 'transliterate'.
            filename: Filename hint when sending raw bytes.

        Returns:
            STTResult with transcript and metadata.
        """
        # Validate output format
        if output_format not in self.FORMAT_OPTIONS:
            raise ValueError(
                f"Invalid format: '{output_format}'. "
                f"Choose from: {', '.join(self.FORMAT_OPTIONS)}"
            )

        # Resolve language code
        lang_code = self._resolve_language(language)

        # Prepare the audio data and normalize to 16kHz mono PCM WAV
        if isinstance(audio_source, bytes):
            audio_data = audio_source
            audio_filename = filename
        else:
            path = self._validate_audio_file(audio_source)
            audio_data = path.read_bytes()
            audio_filename = path.name

        original_size = len(audio_data)
        try:
            from audio_utils import convert_to_pcm16_wav
            audio_data, detected_format = convert_to_pcm16_wav(audio_data)
            audio_filename = "speech.wav"
            logger.info(
                "Audio normalized for Prisma: format=%s, orig_size=%d, wav_size=%d",
                detected_format, original_size, len(audio_data),
            )
        except Exception as conv_err:
            logger.error("Audio normalization failed: %s", conv_err)
            return STTResult(
                success=False, transcript="", detected_language="",
                model=self.model, request_id="", processing_time=0.0,
                raw_response={},
                error=f"Audio format error: {str(conv_err)}",
            )

        # Build the multipart form data for Gnani Prisma STT
        files = {"audio_file": (audio_filename, audio_data, "audio/wav")}
        form_data = {
            "model": self.model,
            "language_code": lang_code,
            "format": output_format,
        }

        logger.info(
            "Prisma STT request — model=%s, language=%s, format=%s, file=%s, size=%d bytes",
            self.model, lang_code, output_format, audio_filename, len(audio_data),
        )

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    GNANI_STT_ENDPOINT,
                    headers=self._get_headers(),
                    data=form_data,
                    files=files,
                )

            # Handle HTTP errors with diagnostic detail
            if response.status_code == 400:
                try:
                    err_json = response.json()
                    err_msg = (
                        err_json.get("error", {}).get("message")
                        or err_json.get("message")
                        or response.text
                    )
                except Exception:
                    err_msg = response.text

                logger.error(
                    "Prisma STT HTTP 400 Bad Request — filename=%s, size=%d, model=%s, lang=%s, format=%s, detail=%s",
                    audio_filename, len(audio_data), self.model, lang_code, output_format, err_msg,
                )
                return STTResult(
                    success=False, transcript="", detected_language="",
                    model=self.model, request_id="", processing_time=0.0,
                    raw_response={"status": 400, "error": err_msg},
                    error=f"Speech recognition rejected audio: {err_msg}",
                )

            if response.status_code == 401:
                return STTResult(
                    success=False, transcript="", detected_language="",
                    model=self.model, request_id="", processing_time=0.0,
                    raw_response={},
                    error="Authentication failed. Check your GNANI_API_KEY.",
                )
            if response.status_code == 402:
                return STTResult(
                    success=False, transcript="", detected_language="",
                    model=self.model, request_id="", processing_time=0.0,
                    raw_response={},
                    error="Insufficient credits. Check your Gnani dashboard.",
                )
            if response.status_code == 429:
                return STTResult(
                    success=False, transcript="", detected_language="",
                    model=self.model, request_id="", processing_time=0.0,
                    raw_response={},
                    error="Rate limit exceeded. Wait and try again.",
                )
            if response.status_code >= 500:
                return STTResult(
                    success=False, transcript="", detected_language="",
                    model=self.model, request_id="", processing_time=0.0,
                    raw_response={},
                    error=f"Gnani server error (HTTP {response.status_code}). Try again later.",
                )

            response.raise_for_status()

            # Parse the successful response
            data = response.json()
            logger.info(
                "Prisma STT response — success=%s, language=%s, latency=%.2fs",
                data.get("success"), data.get("detected_language_code"),
                data.get("end_to_end_latency", 0),
            )

            return STTResult(
                success=data.get("success", True),
                transcript=data.get("transcript", ""),
                detected_language=data.get("detected_language_code", lang_code),
                model=data.get("model", self.model),
                request_id=data.get("request_id", ""),
                processing_time=data.get("end_to_end_latency", 0.0),
                raw_response=data,
            )

        except httpx.TimeoutException:
            logger.error("Prisma STT request timed out.")
            return STTResult(
                success=False, transcript="", detected_language="",
                model=self.model, request_id="", processing_time=0.0,
                raw_response={},
                error="Request timed out. Check your network connection.",
            )
        except httpx.HTTPError as e:
            logger.error("Prisma STT HTTP error: %s", e)
            return STTResult(
                success=False, transcript="", detected_language="",
                model=self.model, request_id="", processing_time=0.0,
                raw_response={},
                error=f"HTTP error: {e}",
            )
        except Exception as e:
            logger.error("Prisma STT unexpected error: %s", e)
            return STTResult(
                success=False, transcript="", detected_language="",
                model=self.model, request_id="", processing_time=0.0,
                raw_response={},
                error=f"Unexpected error: {e}",
            )

    async def transcribe_bytes(
        self,
        audio_bytes: bytes,
        language: str = "auto",
        output_format: str = "transcribe",
        filename: str = "recording.wav",
    ) -> STTResult:
        """
        Convenience method to transcribe raw audio bytes.
        Used when receiving audio from the frontend microphone.
        """
        return await self.transcribe(
            audio_source=audio_bytes,
            language=language,
            output_format=output_format,
            filename=filename,
        )

