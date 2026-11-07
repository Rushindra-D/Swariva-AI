/**
 * SWARIVA AI — API Communication Client
 * Handles real communication with the FastAPI backend.
 */

const SwarivaAPI = {
  /**
   * Helper to construct full URLs
   */
  _url(path) {
    const base = CONFIG.API_BASE_URL.replace(/\/+$/, '');
    return `${base}${path}`;
  },

  /**
   * Check backend server health
   */
  async checkHealth() {
    try {
      const resp = await fetch(this._url(CONFIG.ENDPOINTS.HEALTH), {
        method: 'GET',
        headers: { 'Accept': 'application/json' },
      });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      return await resp.json();
    } catch (err) {
      console.warn('Health check failed:', err);
      return { status: 'offline', error: err.message };
    }
  },

  /**
   * Fetch application metadata and voice catalog
   */
  async getInfo() {
    try {
      const resp = await fetch(this._url(CONFIG.ENDPOINTS.INFO));
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      return await resp.json();
    } catch (err) {
      console.error('Failed to fetch app info:', err);
      return null;
    }
  },

  /**
   * Send text message to /api/v1/chat
   */
  async sendChatMessage({ message, sessionId, language, includeAudio = false, voice = null }) {
    const payload = {
      message: message.trim(),
      session_id: sessionId || getActiveSessionId(),
      language: language || getStoredLanguage(),
      include_audio: includeAudio,
      voice: voice || localStorage.getItem(CONFIG.STORAGE_KEYS.VOICE) || null,
    };

    const resp = await fetch(this._url(CONFIG.ENDPOINTS.CHAT), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (!resp.ok) {
      const errorData = await resp.json().catch(() => ({}));
      throw new Error(errorData.detail || `Server error: HTTP ${resp.status}`);
    }

    return await resp.json();
  },

  /**
   * Upload user audio to /api/v1/voice/chat (Full Voice-to-Voice Loop)
   */
  async sendVoiceChat({ audioBlob, sessionId, language, voice = null }) {
    const formData = new FormData();
    formData.append('audio_file', audioBlob, 'user_speech.wav');
    formData.append('session_id', sessionId || getActiveSessionId());
    formData.append('language', language || getStoredLanguage());
    if (voice) {
      formData.append('voice', voice);
    }

    const resp = await fetch(this._url(CONFIG.ENDPOINTS.VOICE_CHAT), {
      method: 'POST',
      body: formData,
    });

    if (!resp.ok) {
      const errorData = await resp.json().catch(() => ({}));
      throw new Error(errorData.detail || `Voice processing failed: HTTP ${resp.status}`);
    }

    return await resp.json();
  },

  /**
   * Standalone Read Aloud via Gnani Timbre (/api/v1/voice/speak)
   */
  async speakText({ text, language, voice = null, speed = 1.0 }) {
    const payload = {
      text: text.trim(),
      language: language || getStoredLanguage(),
      voice: voice || localStorage.getItem(CONFIG.STORAGE_KEYS.VOICE) || null,
      speed: parseFloat(speed) || 1.0,
    };

    const resp = await fetch(this._url(CONFIG.ENDPOINTS.VOICE_SPEAK), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!resp.ok) {
      const errData = await resp.json().catch(() => ({}));
      throw new Error(errData.detail || `Speech synthesis failed: HTTP ${resp.status}`);
    }

    return await resp.json();
  },

  /**
   * Fetch conversation history
   */
  async getHistory(sessionId) {
    const resp = await fetch(this._url(CONFIG.ENDPOINTS.CHAT_HISTORY(sessionId)));
    if (!resp.ok) {
      if (resp.status === 404) return { messages: [] };
      throw new Error(`Failed to load history: HTTP ${resp.status}`);
    }
    return await resp.json();
  },

  /**
   * Clear session history
   */
  async clearSession(sessionId) {
    const resp = await fetch(this._url(CONFIG.ENDPOINTS.CHAT_CLEAR), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId }),
    });
    if (!resp.ok) throw new Error(`Clear session failed: HTTP ${resp.status}`);
    return await resp.json();
  },
};
