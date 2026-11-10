"""
SWARIVA AI — Supabase Database & Persistence Manager

Integrates with Supabase PostgreSQL using official Python SDK.
Provides:
- Admin / Service client for server-side management
- Per-user client adhering to Row Level Security (RLS)
- Seamless SQLite local fallback when offline or during test suites
"""
import logging
import sqlite3
from pathlib import Path
from typing import Optional, Any

from config import SUPABASE_URL, SUPABASE_SECRET_KEY, SUPABASE_PUBLISHABLE_KEY, PROJECT_ROOT

logger = logging.getLogger("swariva.database")

# Try importing supabase-py
try:
    from supabase import create_client, Client
    HAS_SUPABASE_LIB = True
except ImportError:
    HAS_SUPABASE_LIB = False
    Client = Any
    logger.warning("supabase-py library not installed. Database will use local fallback.")

_admin_client: Optional[Client] = None


def is_supabase_configured() -> bool:
    """Checks whether valid Supabase credentials are configured."""
    import os
    if os.getenv("SWARIVA_FORCE_SQLITE", "").lower() in ("1", "true", "yes"):
        return False

    return bool(
        HAS_SUPABASE_LIB
        and SUPABASE_URL
        and "your-project-id" not in SUPABASE_URL
        and not SUPABASE_URL.startswith("placeholder")
        and SUPABASE_SECRET_KEY
        and not SUPABASE_SECRET_KEY.startswith("placeholder")
    )


def get_supabase_admin_client() -> Optional[Client]:
    """
    Returns singleton admin/service client.
    Used for server-side tasks such as token verification and profile triggers.
    """
    global _admin_client
    if not is_supabase_configured():
        return None

    if _admin_client is None:
        try:
            _admin_client = create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)
            logger.info("Connected to Supabase at %s", SUPABASE_URL)
        except Exception as e:
            logger.error("Failed to initialize Supabase client: %s", e)
            return None

    return _admin_client


def get_supabase_user_client(access_token: str) -> Optional[Client]:
    """
    Creates a user-scoped client carrying the user's JWT.
    PostgreSQL Row Level Security (RLS) evaluates queries under auth.uid().
    """
    if not is_supabase_configured():
        return None

    try:
        # Create user-scoped client with bearer token
        # Prefer publishable (anon) key so PostgREST enforces RLS with role 'authenticated'
        auth_key = SUPABASE_PUBLISHABLE_KEY if SUPABASE_PUBLISHABLE_KEY else SUPABASE_SECRET_KEY
        client = create_client(SUPABASE_URL, auth_key)
        client.postgrest.auth(access_token)
        return client
    except Exception as e:
        logger.error("Failed to create user-scoped Supabase client: %s", e)
        return None


# ── LOCAL SQLITE FALLBACK STORAGE ──────────────────────────────────────────
# Uses writable /tmp in serverless environments (Vercel, AWS Lambda) or in-memory fallback.
import os
import tempfile

if os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME") or not os.access(str(PROJECT_ROOT), os.W_OK):
    SQLITE_DB_PATH = Path(tempfile.gettempdir()) / "swariva_local.db"
else:
    SQLITE_DB_PATH = PROJECT_ROOT / "database" / "swariva_local.db"

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS profiles (
    id TEXT PRIMARY KEY,
    full_name TEXT,
    email TEXT UNIQUE,
    preferred_language TEXT DEFAULT 'auto',
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    title TEXT NOT NULL,
    language TEXT DEFAULT 'auto',
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    audio_metadata TEXT DEFAULT '{}',
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS reminders (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    title TEXT NOT NULL,
    description TEXT,
    reminder_datetime TEXT NOT NULL,
    language TEXT DEFAULT 'auto',
    is_completed INTEGER DEFAULT 0,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS user_settings (
    id TEXT PRIMARY KEY,
    user_id TEXT UNIQUE,
    preferred_language TEXT DEFAULT 'auto',
    preferred_voice TEXT DEFAULT 'Nalini',
    autoplay_enabled INTEGER DEFAULT 1,
    font_size TEXT DEFAULT 'normal',
    high_contrast_enabled INTEGER DEFAULT 0,
    created_at TEXT,
    updated_at TEXT
);
"""


def init_local_sqlite():
    """Initializes local SQLite tables mirroring the Supabase schema safely."""
    try:
        SQLITE_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(SQLITE_DB_PATH))
        cursor = conn.cursor()
        cursor.executescript(SCHEMA_SQL)
        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning("Local SQLite table initialization warning: %s", e)


def get_local_db():
    """Returns a connection to the local SQLite database, falling back to memory if disk access fails."""
    try:
        conn = sqlite3.connect(str(SQLITE_DB_PATH))
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logger.warning("Failed to open SQLite at %s (%s). Using :memory: fallback.", SQLITE_DB_PATH, e)
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        try:
            conn.executescript(SCHEMA_SQL)
        except Exception:
            pass
        return conn


# Initialize SQLite tables on module import
init_local_sqlite()

