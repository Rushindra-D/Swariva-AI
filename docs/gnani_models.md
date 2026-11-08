# 🤖 Gnani AI Models Integration Specifications

SWARIVA AI implements a complete pipeline utilizing all three Gnani AI model families:

---

## 1. Gnani Prisma (Speech-to-Text)

- **Model Version:** `prisma-v3.0`
- **Official Documentation:** [https://docs.gnani.ai/api/STT/speech-to-text](https://docs.gnani.ai/api/STT/speech-to-text)
- **API Endpoint:** `POST https://api.vachana.ai/stt/v3`
- **Authentication:** `X-API-Key-ID: {GNANI_PRISMA_API_KEY}`
- **Request Format:** `multipart/form-data`
  - `audio_file`: 16kHz mono PCM WAV file (normalized automatically by `audio_utils.py`)
  - `model`: `prisma-v3.0`
  - `language_code`: `te-IN`, `hi-IN`, `en-IN`, or `indic-auto`
  - `format`: `transcribe`
- **Verified Latency:** ~1.2s to 1.8s end-to-end
- **Features in SWARIVA:**
  - Automatic silence termination (2.0s silence threshold)
  - PyAV WebM-to-WAV 16kHz PCM audio normalization to prevent HTTP 400 Bad Request
  - Multilingual code-mixing support (Tenglish, Hinglish)

---

## 2. Gnani Evon v3.3 (Reasoning & LLM)

- **Model Identifier:** `gnani/gnani-evon-v3.3-30B-A3B`
- **Hugging Face Model:** [https://huggingface.co/gnani/gnani-evon-v3.3-30B-A3B](https://huggingface.co/gnani/gnani-evon-v3.3-30B-A3B)
- **Architecture:** `nemotron_h_moe` (30 Billion total parameters, ~3.5 Billion active parameters per token)
- **Context Length:** 4,096 tokens
- **License:** Apache 2.0 (Open Weights)
- **Waitlist Access:** [https://www.gnani.ai/evon-waitlist](https://www.gnani.ai/evon-waitlist)
- **SWARIVA Provider Implementation (`backend/providers/evon_provider.py`):**
  - Connects to any standard OpenAI-compatible API host (vLLM, SGLang, llama.cpp server, or Gnani hosted endpoint).
  - Grounded RAG context injection for real-time live queries.
  - Strict spoken-response formatting guidelines.
- **Adaptive Fallback Tiers:**
  - **Tier 2 (Groq Cloud LLM):** Sub-second (~200ms) Llama 3.1 8B Instant inference.
  - **Tier 3 (Knowledge Companion Engine):** 100% offline, zero-latency, zero-cost Indic intelligence.

---

## 3. Gnani Timbre (Text-to-Speech)

- **Model Version:** `timbre-v2.5` / `timbre-v3.0`
- **Official Documentation:** [https://docs.gnani.ai/api/TTS/tts-inference](https://docs.gnani.ai/api/TTS/tts-inference)
- **API Endpoint:** `POST https://api.vachana.ai/api/v1/tts/inference`
- **Authentication:** `X-API-Key-ID: {GNANI_TIMBRE_API_KEY}`
- **Request Format:** `application/json`
  ```json
  {
    "text": "నమస్కారం! నేను స్వరివ.",
    "model": "timbre-v2.5",
    "voice": "Nalini",
    "language": "te-IN",
    "speed": 1.0,
    "audio_config": {
      "encoding": "linear_pcm",
      "container": "wav",
      "sample_rate": 24000,
      "num_channels": 1,
      "sample_width": 2
    }
  }
  ```
- **Voice Catalog:**
  - `timbre-v2.5`: `Nalini` (Default, warm & expressive), `Deepak` (Male), `Kaveri` (Female)
  - `timbre-v3.0`: `Shivani`, `Avinash`
- **Features in SWARIVA:**
  - Markdown stripping and punctuation optimization
  - Base64 WAV streaming to browser Web Audio API
