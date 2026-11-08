"""
SWARIVA AI — Gnani Timbre TTS (Text-to-Speech) Module

Integrates with Gnani AI's Timbre API for voice synthesis.
Supports Telugu, Hindi, English with multiple voice options.

API Reference: https://docs.gnani.ai/api/TTS/tts-inference
Endpoint: POST https://api.vachana.ai/api/v1/tts/inference
Auth: X-API-Key-ID header
"""
import logging
from pathlib import Path
from dataclasses import dataclass, field

import httpx

from config import (
    GNANI_API_KEY,
    GNANI_TIMBRE_API_KEY,
    GNANI_TTS_ENDPOINT,
    GNANI_TTS_MODEL,
    SUPPORTED_LANGUAGES,
    TTS_VOICES,
)

logger = logging.getLogger("swariva.tts")


@dataclass
class TTSResult:
    """Structured result from a Timbre TTS API call."""
    success: bool
    audio_bytes: bytes
    content_type: str
    voice: str
    language: str
    model: str
    error: str | None = None
    metadata: dict = field(default_factory=dict)


class GnaniTTS:
    """
    Client for Gnani AI's Timbre Text-to-Speech API.

    Usage:
        tts = GnaniTTS()
        result = await tts.synthesize("Hello, how are you?", language="english")
        if result.success:
            with open("output.wav", "wb") as f:
                f.write(result.audio_bytes)
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        default_voice: str | None = None,
    ):
        self.api_key = api_key or GNANI_TIMBRE_API_KEY or GNANI_API_KEY
        self.model = model or GNANI_TTS_MODEL
        self.default_voice = default_voice or self._get_default_voice()
        self._validate_setup()

    def _validate_setup(self) -> None:
        """Validate that the API key is configured."""
        if not self.api_key or self.api_key.startswith("placeholder"):
            raise ValueError(
                "Gnani API key is not configured. "
                "Set GNANI_API_KEY in your .env file."
            )

    def _get_default_voice(self) -> str:
        """Get the default voice for the configured model."""
        model_voices = TTS_VOICES.get(self.model)
        if model_voices:
            return model_voices["default"]
        return "Nalini"  # Safe fallback

    def _get_headers(self) -> dict:
        """Build authentication headers for Gnani API."""
        return {
            "X-API-Key-ID": self.api_key,
            "Content-Type": "application/json",
        }

    def _resolve_language(self, language: str) -> str:
        """
        Convert a friendly language name to a Gnani language code.
        Accepts: 'english', 'hindi', 'telugu', 'auto', or direct codes like 'en-IN'.
        """
        if language.lower() == "auto":
            return "auto"
        if "-" in language:
            return language
        code = SUPPORTED_LANGUAGES.get(language.lower())
        if not code:
            supported = ", ".join(SUPPORTED_LANGUAGES.keys())
            raise ValueError(
                f"Unsupported language: '{language}'. "
                f"Choose from: {supported}, 'auto', or a locale code (e.g., 'en-IN')."
            )
        return code

    def _validate_voice(self, voice: str) -> str:
        """Validate that the voice is compatible with the selected model."""
        model_voices = TTS_VOICES.get(self.model)
        if model_voices and voice not in model_voices["voices"]:
            available = ", ".join(model_voices["voices"])
            logger.warning(
                "Voice '%s' may not be compatible with model '%s'. "
                "Available voices: %s. Proceeding anyway.",
                voice, self.model, available,
            )
        return voice

    async def synthesize(
        self,
        text: str,
        language: str = "english",
        voice: str | None = None,
        speed: float = 1.0,
        sample_rate: int = 24000,
    ) -> TTSResult:
        """
        Convert text to speech using Gnani Timbre.

        Args:
            text: The text to convert to speech.
            language: Language name ('english', 'hindi', 'telugu', 'auto')
                      or locale code ('en-IN', 'hi-IN', 'te-IN').
            voice: Voice name (e.g., 'Nalini', 'Kaveri', 'Deepak' for v2.5;
                   'Shivani', 'Avinash' for v3.0). Defaults to model's default voice.
            speed: Speech speed multiplier (1.0 = normal).
            sample_rate: Audio sample rate in Hz.

        Returns:
            TTSResult with audio bytes and metadata.
        """
        if not text or not text.strip():
            return TTSResult(
                success=False, audio_bytes=b"", content_type="",
                voice="", language="", model=self.model,
                error="Text cannot be empty.",
            )

        # Resolve parameters
        lang_code = self._resolve_language(language)
        selected_voice = self._validate_voice(voice or self.default_voice)

        # Build the JSON request body (verified from Gnani docs)
        payload = {
            "text": text,
            "model": self.model,
            "voice": selected_voice,
            "language": lang_code,
            "speed": speed,
            "audio_config": {
                "encoding": "linear_pcm",
                "container": "wav",
                "sample_rate": sample_rate,
                "num_channels": 1,
                "sample_width": 2,
            },
        }

        logger.info(
            "Timbre TTS request — model=%s, voice=%s, language=%s, "
            "text_length=%d, speed=%.1f",
            self.model, selected_voice, lang_code, len(text), speed,
        )

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    GNANI_TTS_ENDPOINT,
                    headers=self._get_headers(),
                    json=payload,
                )

            # Handle HTTP errors
            if response.status_code == 401:
                return TTSResult(
                    success=False, audio_bytes=b"", content_type="",
                    voice=selected_voice, language=lang_code, model=self.model,
                    error="Authentication failed. Check your GNANI_API_KEY.",
                )
            if response.status_code == 402:
                return TTSResult(
                    success=False, audio_bytes=b"", content_type="",
                    voice=selected_voice, language=lang_code, model=self.model,
                    error="Insufficient credits. Check your Gnani dashboard.",
                )
            if response.status_code == 429:
                return TTSResult(
                    success=False, audio_bytes=b"", content_type="",
                    voice=selected_voice, language=lang_code, model=self.model,
                    error="Rate limit exceeded. Wait and try again.",
                )
            if response.status_code >= 500:
                return TTSResult(
                    success=False, audio_bytes=b"", content_type="",
                    voice=selected_voice, language=lang_code, model=self.model,
                    error=f"Gnani server error (HTTP {response.status_code}). Try again later.",
                )

            response.raise_for_status()

            # Determine response type
            content_type = response.headers.get("content-type", "")

            # If the response is binary audio (expected from REST inference)
            if "audio" in content_type or "octet-stream" in content_type:
                audio_data = response.content
            elif "application/json" in content_type:
                # Some API versions return JSON with base64 audio
                data = response.json()
                if "audio" in data:
                    import base64
                    audio_data = base64.b64decode(data["audio"])
                else:
                    return TTSResult(
                        success=False, audio_bytes=b"", content_type=content_type,
                        voice=selected_voice, language=lang_code, model=self.model,
                        error=f"Unexpected JSON response: {data}",
                    )
            else:
                # Treat as binary audio data
                audio_data = response.content

            if not audio_data:
                return TTSResult(
                    success=False, audio_bytes=b"", content_type=content_type,
                    voice=selected_voice, language=lang_code, model=self.model,
                    error="Empty audio response from Gnani API.",
                )

            logger.info(
                "Timbre TTS response — content_type=%s, audio_size=%d bytes",
                content_type, len(audio_data),
            )

            return TTSResult(
                success=True,
                audio_bytes=audio_data,
                content_type=content_type,
                voice=selected_voice,
                language=lang_code,
                model=self.model,
                metadata={
                    "text_length": len(text),
                    "audio_size_bytes": len(audio_data),
                    "sample_rate": sample_rate,
                    "speed": speed,
                },
            )

        except httpx.TimeoutException:
            logger.error("Timbre TTS request timed out.")
            return TTSResult(
                success=False, audio_bytes=b"", content_type="",
                voice=selected_voice, language=lang_code, model=self.model,
                error="Request timed out. Check your network connection.",
            )
        except httpx.HTTPError as e:
            logger.error("Timbre TTS HTTP error: %s", e)
            return TTSResult(
                success=False, audio_bytes=b"", content_type="",
                voice=selected_voice, language=lang_code, model=self.model,
                error=f"HTTP error: {e}",
            )
        except Exception as e:
            logger.error("Timbre TTS unexpected error: %s", e)
            return TTSResult(
                success=False, audio_bytes=b"", content_type="",
                voice=selected_voice, language=lang_code, model=self.model,
                error=f"Unexpected error: {e}",
            )

    async def save_audio(
        self,
        text: str,
        output_path: str | Path,
        language: str = "english",
        voice: str | None = None,
        speed: float = 1.0,
    ) -> TTSResult:
        """
        Synthesize speech and save directly to a file.

        Args:
            text: Text to convert to speech.
            output_path: File path to save the audio (e.g., "output.wav").
            language: Language name or code.
            voice: Voice name.
            speed: Speech speed multiplier.

        Returns:
            TTSResult (audio_bytes will also be populated).
        """
        result = await self.synthesize(
            text=text, language=language, voice=voice, speed=speed,
        )
        if result.success:
            out = Path(output_path)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(result.audio_bytes)
            logger.info("Audio saved to %s (%d bytes)", out, len(result.audio_bytes))
        return result

    def get_available_voices(self) -> list[str]:
        """Return the list of voices available for the current model."""
        model_voices = TTS_VOICES.get(self.model)
        if model_voices:
            return model_voices["voices"]
        return []

