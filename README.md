# 🎙️ SWARIVA AI — A Voice That Understands You

> **A multilingual, voice-first intelligent companion for visually impaired, elderly, and mobility-limited users.**  
> Built for the **Great Indian AI Internship Challenge by Gnani AI**.

---

## 🌟 Overview

**SWARIVA AI** is an accessible, voice-driven AI companion designed to bridge the accessibility gap for users who cannot easily interact with screens, keyboards, or small text. It provides natural voice conversations, daily routine and medicine reminders, and a supportive presence in **English**, **Hindi**, and **Telugu**.

### Core Voice Technology
- **Speech-to-Text (STT):** [Gnani AI Prisma v3.0](https://docs.gnani.ai/api/STT/speech-to-text) — High-accuracy multilingual Indic speech recognition.
- **Text-to-Speech (TTS):** [Gnani AI Timbre v2.5 / v3.0](https://docs.gnani.ai/api/TTS/tts-inference) — Expressive, natural voice synthesis in Indian accents.
- **AI Reasoning Engine:** Modular companion agent with multi-turn context retention, safety disclaimers, and configurable external LLM hook.

---

## 🏗️ Architecture

```
                                  [ User Microphone ]
                                           │
                                           ▼ (Audio Stream)
┌────────────────────────────────────────────────────────────────────────┐
│                        SWARIVA AI FASTAPI BACKEND                       │
│                                                                        │
│   POST /api/v1/voice/chat ──► [ Gnani Prisma STT (v3.0) ]               │
│                                           │ (Transcribed Text)         │
│                                           ▼                            │
│   POST /api/v1/chat       ──► [ Conversation Manager (Context Window) ] │
│                                           │                            │
│                                           ▼                            │
│                               [ SWARIVA AI Reasoning Agent ]           │
│                               (English / Hindi / Telugu)               │
│                                           │                            │
│                                           ▼ (Speech-Cleaned Text)      │
│                               [ Gnani Timbre TTS (v2.5) ]              │
│                                           │                            │
└───────────────────────────────────────────┼────────────────────────────┘
                                            ▼ (Base64 WAV Audio + Text)
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

Ensure `.env` at the project root contains your Gnani API key:

```env
# Gnani AI Credentials
GNANI_API_KEY=your_gnani_api_key_here

# Application Settings
APP_ENV=development
APP_PORT=8000
```

> **Security Note:** `.env` is automatically ignored by Git and will never be tracked or committed.

---

## 🏃 Running the Backend Server

Start the FastAPI ASGI server with auto-reload:

```powershell
cd backend
uvicorn main:app --reload --port 8000
```

Once running, access the interactive API docs at:
- **Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **Health Check:** [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

## 📡 API Endpoints Reference

### 1. Health & Info
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Server operational status and speech model confirmation |
| `GET` | `/api/v1/info` | Supported languages, model versions, and voice catalog |

#### Example:
```powershell
curl http://127.0.0.1:8000/health
```

### 2. Text Chat (`POST /api/v1/chat`)
Send a text message and receive an intelligent companion response with conversation context.

**Request Body (JSON):**
```json
{
  "message": "Hello Swariva, can you help me with my medicine reminders?",
  "language": "english",
  "include_audio": false
}
```

**Response (JSON):**
```json
{
  "response": "I would be glad to help you keep track of your reminders!...",
  "session_id": "13a4564b-6675-4bea-87bb-8bb548570ca6",
  "language": "english",
  "audio_base64": null,
  "timestamp": "2026-11-07T16:46:26.036000+00:00",
  "metadata": {
    "history_length": 2,
    "provider": "rule_based"
  }
}
```

### 3. Voice-to-Voice Loop (`POST /api/v1/voice/chat`)
Upload a speech audio recording (WAV, MP3, OGG < 30s) and receive the transcription, reasoning response, and synthesized audio in a single payload.

**Request (Multipart Form Data):**
- `audio_file`: binary audio file
- `session_id`: (optional) active session ID
- `language`: `auto`, `english`, `hindi`, or `telugu`

**Response (JSON):**
```json
{
  "success": true,
  "transcript": "Hello, I am Swariva, your intelligent voice assistant...",
  "detected_language": "en-IN",
  "response_text": "Hello! I'm Swariva, your voice companion...",
  "session_id": "13a4564b-6675-4bea-87bb-8bb548570ca6",
  "audio_base64": "UklGRk... (Base64 WAV string)",
  "processing_time_stt": 0.22,
  "processing_time_tts": 1.37,
  "metadata": {
    "stt_model": "prisma-v3.0",
    "tts_model": "timbre-v2.5",
    "tts_voice": "Nalini"
  }
}
```

### 4. Read Aloud / TTS (`POST /api/v1/voice/speak`)
Converts any text into expressive speech using Gnani Timbre.

```json
{
  "text": "నమస్కారం! నేను స్వరివ.",
  "language": "telugu",
  "voice": "Nalini",
  "speed": 1.0
}
```

---

## 🧪 Testing

### Automated Unit Tests (Zero External Credits)
Runs 12 comprehensive unit tests mocking external APIs to verify routing, schemas, validation, and session memory:

```powershell
python -m pytest tests/test_backend.py -v
```

### Live Endpoints Integration Verification
Tests real requests across all endpoints using live Gnani AI connections:

```powershell
python backend/test_api_endpoints.py
```

---

## 📋 Challenge Phase Roadmap

- [x] **Phase 1:** Environment Setup, Directory Structure & Dependencies
- [x] **Phase 2:** Gnani AI Prisma & Timbre Live Integration & Audio Verification
- [x] **Phase 3:** FastAPI Backend & Voice-to-Voice AI Agent
- [ ] **Phase 4:** Frontend Development (Accessible Web UI, Waveforms & Mic)
- [ ] **Phase 5:** Supabase Database (User Profiles, History & Reminders)
- [ ] **Phase 6:** Advanced AI Agent & Intent Recognition
- [ ] **Phase 7:** End-to-End System Integration
- [ ] **Phase 8:** Testing & Cloud Deployment (Render/Railway/Vercel)
- [ ] **Phase 9:** Challenge Submission & Demonstration Video
