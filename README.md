# 🎙️ SWARIVA AI — A Voice That Understands You

> **A multilingual, voice-first intelligent companion for visually impaired, elderly, and mobility-limited users.**  
> Built for the **Great Indian AI Internship Challenge by Gnani AI**.

---

## 🌟 Overview

**SWARIVA AI** is an accessible, voice-driven AI companion designed to bridge the accessibility gap for users who cannot easily interact with screens, keyboards, or small text. It provides natural voice conversations, daily routine and medicine reminders, and a supportive presence in **English**, **Hindi**, and **Telugu**.

### Core Voice Technology & Gnani Three-Model Integration
- **Model 1 — Speech-to-Text (STT):** [Gnani AI Prisma v3.0](https://docs.gnani.ai/api/STT/speech-to-text) — High-accuracy multilingual Indic speech recognition with VAD and 2-second silence auto-termination.
- **Model 2 — Reasoning & LLM:** [Gnani AI Evon v3.3](https://huggingface.co/gnani/gnani-evon-v3.3-30B-A3B) — 30B MoE model with 3-tier adaptive architecture (Evon Cloud, High-Speed Groq Cloud, Built-in Offline Indic Knowledge Companion).
- **Model 3 — Text-to-Speech (TTS):** [Gnani AI Timbre v2.5 / v3.0](https://docs.gnani.ai/api/TTS/tts-inference) — Expressive Indian voice synthesis with dynamic speech sanitization.
- **Real-Time Tools & RAG:** Grounded real-time live tools for Open-Meteo weather, Hyderabad bullion gold prices, voice reminders, and web search.
- **Database & Auth (Phase 5):** Supabase PostgreSQL with Row Level Security (RLS), persistent dialogue turns, and automatic local SQLite fallback.
- **Frontend (Phase 4):** Premium accessible dark-themed web app with Web Audio waveforms, live mic streaming, dynamic font sizing, and high-contrast modes.

---

## 🏗️ Architecture

```
                                  [ User Microphone / Web UI ]
                                               │
                                               ▼ (Audio Stream / Text)
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SWARIVA AI FASTAPI BACKEND                          │
│                                                                             │
│   POST /api/v1/voice/chat ──► [ Gnani Prisma STT (v3.0) ]                   │
│                                              │ (Transcribed Text)           │
│                                              ▼                              │
│   POST /api/v1/chat       ──► [ Conversation Manager (Sliding Context) ]    │
│                                              │                              │
│                                              ▼                              │
│                                 [ SWARIVA Reasoning Engine ]                │
│                                 (English / Hindi / Telugu)                  │
│                                              │                              │
│                                              ▼ (Speech-Cleaned Text)         │
│                                 [ Gnani Timbre TTS (v2.5) ]                 │
│                                              │                              │
│   PERSISTENCE LAYER ─────────────────────────┼───────────────────────────   │
│   ├── Supabase PostgreSQL (Cloud)            ▼ (Base64 WAV Audio + Text)    │
│   └── Local SQLite Fallback (Zero-Breakage)                                │
└──────────────────────────────────────────────┼──────────────────────────────┘
                                               ▼
                                    [ User Audio Playback ]
```

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.11+
- Git

### 2. Clone and Setup Environment

```powershell
# Navigate to the project directory
cd "c:\Users\dobil\OneDrive\Desktop\swariva ai"

# Install dependencies
pip install -r backend/requirements.txt
```

### 3. Configure Credentials

Ensure `.env` at the project root contains your Gnani API key and Supabase credentials:

```env
# Gnani AI Credentials
GNANI_API_KEY=your_gnani_api_key_here

# Supabase Cloud PostgreSQL & Auth (Optional: local SQLite fallback active by default)
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_SECRET_KEY=your_supabase_secret_key_here
SUPABASE_PUBLISHABLE_KEY=your_supabase_publishable_key_here

# Application Settings
APP_ENV=development
APP_PORT=8000
```

> **Security Note:** `.env` and `*.db` are automatically ignored by Git and will never be tracked or committed.

### 4. Setting Up Supabase Database

If you have a Supabase project:
1. Open the **SQL Editor** in your [Supabase Dashboard](https://supabase.com/dashboard).
2. Copy and paste the contents of [`database/schema.sql`](file:///c:/Users/dobil/OneDrive/Desktop/swariva%20ai/database/schema.sql).
3. Click **Run** to provision the 6 tables, Row Level Security policies, indexes, and user creation triggers.
4. Set `SUPABASE_URL` in `.env` to your project's URL.

*Note: If `SUPABASE_URL` is omitted or set to placeholder, SWARIVA automatically persists data to the built-in local SQLite fallback (`database/swariva_local.db`), ensuring zero breakage.*

---

## 🏃 Running the Application

Start the FastAPI ASGI server with auto-reload:

```powershell
cd backend
uvicorn main:app --reload --port 8000
```

Once running, access the interfaces:
- **Web App Dashboard:** [http://127.0.0.1:8000/app/index.html](http://127.0.0.1:8000/app/index.html)
- **Voice Assistant:** [http://127.0.0.1:8000/app/voice.html](http://127.0.0.1:8000/app/voice.html)
- **AI Text Chat:** [http://127.0.0.1:8000/app/chat.html](http://127.0.0.1:8000/app/chat.html)
- **Daily Reminders:** [http://127.0.0.1:8000/app/reminders.html](http://127.0.0.1:8000/app/reminders.html)
- **Read Aloud:** [http://127.0.0.1:8000/app/read_aloud.html](http://127.0.0.1:8000/app/read_aloud.html)
- **History & Transcripts:** [http://127.0.0.1:8000/app/history.html](http://127.0.0.1:8000/app/history.html)
- **Sign In / Registration:** [http://127.0.0.1:8000/app/auth.html](http://127.0.0.1:8000/app/auth.html)
- **Swagger UI (Interactive API Docs):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 📡 API Endpoints Reference

### 1. Health & Info
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Server operational status and speech model confirmation |
| `GET` | `/api/v1/info` | Supported languages, model versions, and voice catalog |

### 2. Authentication & Profiles
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/auth/signup` | Register new user account and provision profile |
| `POST` | `/api/v1/auth/login` | Authenticate credentials and receive Bearer JWT |
| `GET` | `/api/v1/auth/me` | Fetch authenticated profile details (requires Bearer token) |
| `POST` | `/api/v1/auth/logout` | Terminate session |

### 3. Voice-to-Voice Loop (`POST /api/v1/voice/chat`)
Upload a speech audio recording (WAV, MP3, OGG < 30s) and receive the transcription, reasoning response, and synthesized audio in a single payload.

### 4. Text Chat (`POST /api/v1/chat`)
Send a text message and receive an intelligent companion response with conversation context and optional synthesized audio.

### 5. Daily Reminders (`/api/v1/reminders`)
- `GET /api/v1/reminders`: List scheduled reminders (scoped to user if authenticated).
- `POST /api/v1/reminders`: Create a new reminder.
- `PUT /api/v1/reminders/{id}`: Update completion status or reminder properties.
- `DELETE /api/v1/reminders/{id}`: Delete reminder record.

### 6. Conversation Persistence (`/api/v1/conversations`)
- `GET /api/v1/conversations`: List past conversation sessions.
- `GET /api/v1/conversations/{id}`: Retrieve message history for a session.
- `DELETE /api/v1/conversations/{id}`: Delete conversation and all dialogue turns.

---

## 🧪 Testing

Run the full automated verification suites:

```powershell
# 1. Core API & Database Integration Suite (20 tests)
python -m pytest tests/ -v

# 2. Conversational Intelligence & Echo Filter Suite (12 tests)
python backend/test_ai_intelligence.py

# 3. Phase 6 Gnani Three-Model & Real-Time RAG Tools Suite
python backend/test_phase6_three_models.py

# 4. Live Supabase Cloud PostgreSQL & RLS Verification
python backend/test_supabase_cloud.py
```

All suites achieve **100% green pass** status across all languages and scenarios.

---

## 📋 Challenge Phase Roadmap

- [x] **Phase 1:** Environment Setup, Directory Structure & Dependencies
- [x] **Phase 2:** Gnani AI Prisma & Timbre Live Integration & Audio Verification
- [x] **Phase 3:** FastAPI Backend & Voice-to-Voice AI Agent
- [x] **Phase 4:** Frontend Development (Accessible Web UI, Waveforms & Mic)
- [x] **Phase 5:** Supabase Database (User Profiles, History & Reminders)
- [x] **Phase 6:** Advanced AI Agent & Intent Recognition (Gnani Three-Model Integration & Real-Time RAG)
- [ ] **Phase 7:** End-to-End System Integration & UI Badges
- [ ] **Phase 8:** Testing & Cloud Deployment (Render/Railway/Vercel)
- [ ] **Phase 9:** Challenge Submission & Demonstration Video
