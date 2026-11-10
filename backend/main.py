"""
SWARIVA AI — Core FastAPI Application

"A voice that understands you."
Multilingual, voice-first intelligent companion powered by Gnani AI.

API Documentation: http://127.0.0.1:8000/docs
"""
import sys
import logging
from contextlib import asynccontextmanager
from pathlib import Path

# Ensure backend directory is in sys.path for direct or root cloud invocations (Render, Railway, Docker)
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from config import (
    APP_ENV,
    DEBUG,
    GNANI_STT_MODEL,
    GNANI_TTS_MODEL,
    validate_config,
)
from routes import (
    health_router,
    chat_router,
    voice_router,
    auth_router,
    reminders_router,
    conversations_router,
)

# Configure centralized logging
logging.basicConfig(
    level=logging.INFO if not DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("swariva.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan event handling."""
    logger.info("==================================================")
    logger.info("   Starting SWARIVA AI Voice Assistant Backend   ")
    logger.info("   Tagline: 'A voice that understands you.'       ")
    logger.info("==================================================")
    logger.info("Environment: %s | Debug: %s", APP_ENV, DEBUG)
    logger.info("Speech-to-Text: Gnani %s", GNANI_STT_MODEL)
    logger.info("Text-to-Speech: Gnani %s", GNANI_TTS_MODEL)

    warnings = validate_config()
    for w in warnings:
        logger.warning("Config Notice: %s", w)

    yield

    logger.info("Shutting down SWARIVA AI backend.")


# Initialize FastAPI application with OpenAPI documentation metadata
app = FastAPI(
    title="SWARIVA AI API",
    description="""
### Multilingual Voice Assistant & Accessible Companion
Designed for visually impaired users, elderly individuals, and accessible voice interaction.

Powered by:
- **Gnani Prisma STT** (Speech-to-Text)
- **Gnani Timbre TTS** (Text-to-Speech)
- **Modular AI Reasoning Engine** (English, Hindi, Telugu)
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS Middleware ──
# Allows seamless communication from the HTML/JS frontend and local development servers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Centralized Exception Handler ──
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception at %s: %s", request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "An internal server error occurred.",
            "detail": str(exc) if str(exc) else "An unexpected error occurred during request processing.",
            "path": request.url.path,
        },
    )


# ── Register Routers ──
app.include_router(health_router)
app.include_router(chat_router)
app.include_router(voice_router)
app.include_router(auth_router)
app.include_router(reminders_router)
app.include_router(conversations_router)


# Root welcome endpoint
@app.get("/", tags=["Health & System"])
async def root():
    return {
        "message": "Welcome to SWARIVA AI — A voice that understands you.",
        "frontend_app": "/app/",
        "documentation": "/docs",
        "health_check": "/health",
        "api_endpoints": {
            "text_chat": "/api/v1/chat",
            "voice_chat": "/api/v1/voice/chat",
            "read_aloud": "/api/v1/voice/speak",
            "auth": "/api/v1/auth",
            "reminders": "/api/v1/reminders",
            "conversations": "/api/v1/conversations",
            "system_info": "/api/v1/info",
        },
    }


# ── Mount Frontend Static Web Application ──
frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/app", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
    logger.info("Mounted frontend web app at /app/")


