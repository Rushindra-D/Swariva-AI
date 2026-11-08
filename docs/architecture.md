# 🏗️ SWARIVA AI — System Architecture Specification

## 1. Overview
**SWARIVA AI** is an intelligent, voice-first, accessible multilingual companion built for the **Great Indian AI Internship Challenge by Gnani AI**. It serves visually impaired users, senior citizens, and people with motor impairments across **Telugu**, **Hindi**, and **English**.

---

## 2. End-to-End Three-Model Voice Pipeline

```
  ┌─────────────────────────────────────────────────────────────────────────┐
  │                           BROWSER CLIENT (UI)                           │
  │  - Web Audio API Live Waveform Visualizer                               │
  │  - Real-Time Voice Activity Detection (VAD)                             │
  │  - Automatic 2-Second Silence Termination (No fixed 30s limit)          │
  └────────────────────────────────────┬────────────────────────────────────┘
                                       │ Raw Audio Bytes (WebM/WAV)
                                       ▼
  ┌─────────────────────────────────────────────────────────────────────────┐
  │                     FASTAPI BACKEND AUDIO PIPELINE                      │
  │  - PyAV Format Normalization (WebM/OGG -> 16kHz Mono PCM WAV)          │
  │  - Anti-Feedback Protection                                             │
  └────────────────────────────────────┬────────────────────────────────────┘
                                       │ 16kHz PCM WAV
                                       ▼
  ┌─────────────────────────────────────────────────────────────────────────┐
  │                 MODEL 1: GNANI PRISMA STT (v3.0)                       │
  │  - Multilingual Speech Recognition (Telugu, Hindi, English, Auto)       │
  │  - Endpoint: https://api.vachana.ai/stt/v3                              │
  │  - Auth: X-API-Key-ID (GNANI_PRISMA_API_KEY)                           │
  └────────────────────────────────────┬────────────────────────────────────┘
                                       │ Transcribed User Text
                                       ▼
  ┌─────────────────────────────────────────────────────────────────────────┐
  │                  SEMANTIC INTENT & RAG DISPATCHER                       │
  │  - Intent Classifier (14 semantic intents + greeting disentanglement)   │
  │  - Active Topic & Subject Context Tracking                              │
  │  - Real-Time Tool Calling:                                              │
  │    ├─ WeatherTool (Open-Meteo Live API)                                │
  │    ├─ GoldPriceTool (Hyderabad Bullion Feed: 22K/24K)                   │
  │    ├─ ReminderTool (Supabase Cloud / SQLite CRUD)                       │
  │    └─ SearchTool (Web Fact Retrieval)                                   │
  └────────────────────────────────────┬────────────────────────────────────┘
                                       │ User Query + RAG Grounding Context
                                       ▼
  ┌─────────────────────────────────────────────────────────────────────────┐
  │             MODEL 2: 3-TIER REASONING ENGINE / GNANI EVON               │
  │  - Tier 1: Gnani Evon v3.3 (30B-A3B) via OpenAI-compatible endpoint     │
  │  - Tier 2: High-Speed Indic Cloud LLM (Groq Llama 3.1 8B Instant)       │
  │  - Tier 3: Built-In Knowledge Companion Engine (100% offline fallback)  │
  │  - Conversational Rules:                                                │
  │    ├─ Strictly Zero Echoing ("You asked...", "You said...")             │
  │    ├─ Strictly Zero "How can I help you?" when answering questions      │
  │    └─ Direct, warm, spoken-friendly responses (2-4 sentences)           │
  └────────────────────────────────────┬────────────────────────────────────┘
                                       │ Reasoning Response Text
                                       ▼
  ┌─────────────────────────────────────────────────────────────────────────┐
  │                      SPEECH CLEANING PIPELINE                           │
  │  - Strips markdown formatting (*, #, __, URLs, emoji, stage cues)       │
  │  - Preserves authentic Telugu and Devanagari punctuation                │
  └────────────────────────────────────┬────────────────────────────────────┘
                                       │ Clean Spoken Text
                                       ▼
  ┌─────────────────────────────────────────────────────────────────────────┐
  │                 MODEL 3: GNANI TIMBRE TTS (v2.5)                       │
  │  - Expressive Indian Voice Synthesis (Nalini, Deepak, Kaveri, Shivani)  │
  │  - Endpoint: https://api.vachana.ai/api/v1/tts/inference               │
  │  - Auth: X-API-Key-ID (GNANI_TIMBRE_API_KEY)                           │
  └────────────────────────────────────┬────────────────────────────────────┘
                                       │ Synthesized Base64 WAV Audio
                                       ▼
  ┌─────────────────────────────────────────────────────────────────────────┐
  │                     BROWSER CLIENT PLAYBACK & LOOP                      │
  │  - Live Audio Playback via HTML5 AudioContext                           │
  │  - Seamless Continuous Conversation Loop (Re-arms mic after speech)     │
  └─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Persistence Layer Architecture

SWARIVA AI operates with a resilient **Dual-Engine Persistence Layer**:

```
                       ┌────────────────────────┐
                       │     Repository API     │
                       └───────────┬────────────┘
                                   │
                  ┌────────────────┴────────────────┐
                  ▼                                 ▼
       [ Cloud Authenticated ]             [ Guest / Offline ]
                  │                                 │
                  ▼                                 ▼
      ┌───────────────────────┐         ┌───────────────────────┐
      │ Supabase PostgreSQL   │         │ Local SQLite Fallback │
      │ - Row Level Security  │         │ - Zero Network Drop   │
      │ - 6 Relational Tables │         │ - Zero Breakage Guarantee│
      │ - Profiles & Auth     │         │ - database/swariva.db │
      └───────────────────────┘         └───────────────────────┘
```

### Relational Schema (6 Tables):
1. `public.profiles`: User identity, full name, preferred voice, preferred language, high-contrast settings.
2. `public.conversations`: Conversation sessions, titles, timestamps.
3. `public.messages`: Multi-turn dialogue entries (role, transcript, audio base64, latencies).
4. `public.reminders`: Daily routines, medicine schedules, status tracking.
5. `public.trusted_contacts`: Emergency contacts for accessibility features.
6. `public.user_settings`: User accessibility preferences and dark mode toggles.

