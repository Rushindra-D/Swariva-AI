"""
SWARIVA AI — Configuration Module
Loads environment variables and defines application-wide constants.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# ── Load .env file from project root ──
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# ── Gnani AI Configuration ──
GNANI_API_KEY: str = os.getenv("GNANI_API_KEY", "")
GNANI_BASE_URL: str = "https://api.vachana.ai"

# Gnani API Endpoints (verified from official docs)
GNANI_STT_ENDPOINT: str = f"{GNANI_BASE_URL}/stt/v3"
GNANI_TTS_ENDPOINT: str = f"{GNANI_BASE_URL}/api/v1/tts/inference"

# Default model versions
GNANI_STT_MODEL: str = "prisma-v3.0"
GNANI_TTS_MODEL: str = "timbre-v2.5"  # v2.5 has wider voice catalog; v3.0 for expressive tags

# ── Supported Languages ──
SUPPORTED_LANGUAGES = {
    "english": "en-IN",
    "hindi": "hi-IN",
    "telugu": "te-IN",
}

# ── Timbre Voice Catalog ──
# Voices are model-specific — don't mix v2.5 voices with v3.0 model or vice versa
TTS_VOICES = {
    "timbre-v2.5": {
        "default": "Nalini",
        "voices": ["Nalini", "Kaveri", "Deepak"],
    },
    "timbre-v3.0": {
        "default": "Shivani",
        "voices": ["Shivani", "Avinash"],
    },
}

# ── Supabase Configuration (Phase 5) ──
SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
SUPABASE_SECRET_KEY: str = os.getenv("SUPABASE_SECRET_KEY", "") or os.getenv("SUPABASE_KEY", "")
SUPABASE_PUBLISHABLE_KEY: str = os.getenv("SUPABASE_PUBLISHABLE_KEY", "")
SUPABASE_KEY: str = SUPABASE_SECRET_KEY

# ── LLM Reasoning Configuration (Phase 6 / Modular Provider) ──
LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")
LLM_MODEL: str = os.getenv("LLM_MODEL", "llama-3.1-8b-instant")

# ── Application Configuration ──
APP_ENV: str = os.getenv("APP_ENV", "development")
APP_PORT: int = int(os.getenv("APP_PORT", "8000"))
DEBUG: bool = APP_ENV == "development"

# ── Validation ──
def validate_config() -> list[str]:
    """Check for missing required configuration. Returns list of warnings."""
    warnings = []
    if not GNANI_API_KEY or GNANI_API_KEY.startswith("placeholder"):
        warnings.append("GNANI_API_KEY is not set. Gnani API calls will fail.")
    if not SUPABASE_URL or "your-project-id" in SUPABASE_URL or SUPABASE_URL.startswith("placeholder"):
        warnings.append("SUPABASE_URL is not set to a live project URL. Operating in fallback mode.")
    return warnings

