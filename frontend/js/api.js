/**
 * SWARIVA AI — API Communication Client
 * Handles real communication with the FastAPI backend,
 * including Gnani Voice APIs, Supabase Auth, Reminders, and Conversations.
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
   * Constructs request headers, automatically appending Authorization Bearer token if logged in.
   */
  _headers(extra = {}) {
    const headers = { ...extra };
    const token = getAuthToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    return headers;
  },

  /**
   * Check backend server health
   */
  async checkHealth() {
    try {
      const resp = await fetch(this._url(CONFIG.ENDPOINTS.HEALTH), {
        method: 'GET',
        headers: this._headers({ 'Accept': 'application/json' }),
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
      const resp = await fetch(this._url(CONFIG.ENDPOINTS.INFO), {
        headers: this._headers(),
      });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      return await resp.json();
    } catch (err) {
      console.error('Failed to fetch app info:', err);
      return null;
    }
  },

  /**
   * ── AUTHENTICATION ───────────────────────────────────────────────
   */
  auth: {
    async signup({ email, password, fullName, preferredLanguage }) {
      const resp = await fetch(SwarivaAPI._url(CONFIG.ENDPOINTS.AUTH_SIGNUP), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: email.trim(),
          password,
          full_name: fullName ? fullName.trim() : 'Swariva User',
          preferred_language: preferredLanguage || getStoredLanguage(),
        }),
      });

      const data = await resp.json();
      if (!resp.ok) {
        throw new Error(data.detail || `Registration failed: HTTP ${resp.status}`);
      }

      if (data.access_token) {
        setAuthToken(data.access_token);
        setUserProfile({
          id: data.user_id,
          email: data.email,
          full_name: data.full_name,
          preferred_language: data.preferred_language,
        });
      }
      return data;
    },

    async login({ email, password }) {
      const resp = await fetch(SwarivaAPI._url(CONFIG.ENDPOINTS.AUTH_LOGIN), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: email.trim(),
          password,
        }),
      });

      const data = await resp.json();
      if (!resp.ok) {
        throw new Error(data.detail || `Sign in failed: HTTP ${resp.status}`);
      }

      if (data.access_token) {
        setAuthToken(data.access_token);
        setUserProfile({
          id: data.user_id,
          email: data.email,
          full_name: data.full_name,
          preferred_language: data.preferred_language,
        });
      }
      return data;
    },

    async me() {
      const token = getAuthToken();
      if (!token) return null;

      const resp = await fetch(SwarivaAPI._url(CONFIG.ENDPOINTS.AUTH_ME), {
        method: 'GET',
        headers: SwarivaAPI._headers({ 'Accept': 'application/json' }),
      });

      if (!resp.ok) {
        if (resp.status === 401) {
          clearAuth();
          return null;
        }
        throw new Error(`Profile check failed: HTTP ${resp.status}`);
      }

      const data = await resp.json();
      setUserProfile(data);
      return data;
    },

    async logout() {
      try {
        await fetch(SwarivaAPI._url(CONFIG.ENDPOINTS.AUTH_LOGOUT), {
          method: 'POST',
          headers: SwarivaAPI._headers(),
        });
      } catch (e) {
        // Silent
      }
      clearAuth();
    },
  },

  /**
   * ── TEXT CHAT ────────────────────────────────────────────────────
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
      headers: this._headers({
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      }),
      body: JSON.stringify(payload),
    });

    if (!resp.ok) {
      const errorData = await resp.json().catch(() => ({}));
      throw new Error(errorData.detail || `Server error: HTTP ${resp.status}`);
    }

    return await resp.json();
  },

  /**
   * ── VOICE INTERACTION (Gnani Prisma STT -> Agent -> Timbre TTS) ──
   */
  async sendVoiceChat({ audioBlob, sessionId, language, voice = null }) {
    const formData = new FormData();
    const filename = (audioBlob && audioBlob.type && audioBlob.type.includes('webm')) ? 'user_speech.webm' : 'user_speech.wav';
    formData.append('audio_file', audioBlob, filename);
    formData.append('session_id', sessionId || getActiveSessionId());
    formData.append('language', language || getStoredLanguage());
    if (voice) {
      formData.append('voice', voice);
    }

    const resp = await fetch(this._url(CONFIG.ENDPOINTS.VOICE_CHAT), {
      method: 'POST',
      headers: this._headers(),
      body: formData,
    });

    if (!resp.ok) {
      const errorData = await resp.json().catch(() => ({}));
      throw new Error(errorData.detail || `Voice processing failed: HTTP ${resp.status}`);
    }

    return await resp.json();
  },

  /**
   * ── READ ALOUD (Gnani Timbre TTS) ────────────────────────────────
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
      headers: this._headers({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(payload),
    });

    if (!resp.ok) {
      const errData = await resp.json().catch(() => ({}));
      throw new Error(errData.detail || `Speech synthesis failed: HTTP ${resp.status}`);
    }

    return await resp.json();
  },

  /**
   * ── REMINDERS ────────────────────────────────────────────────────
   */
  reminders: {
    async list() {
      const resp = await fetch(SwarivaAPI._url(CONFIG.ENDPOINTS.REMINDERS), {
        headers: SwarivaAPI._headers(),
      });
      if (!resp.ok) throw new Error(`Failed to load reminders: HTTP ${resp.status}`);
      return await resp.json();
    },

    async create({ title, reminder_datetime, description, language }) {
      const resp = await fetch(SwarivaAPI._url(CONFIG.ENDPOINTS.REMINDERS), {
        method: 'POST',
        headers: SwarivaAPI._headers({ 'Content-Type': 'application/json' }),
        body: JSON.stringify({
          title: title.trim(),
          reminder_datetime,
          description: description || '',
          language: language || getStoredLanguage(),
        }),
      });
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        throw new Error(err.detail || `Failed to create reminder: HTTP ${resp.status}`);
      }
      return await resp.json();
    },

    async update(id, updates) {
      const resp = await fetch(SwarivaAPI._url(`${CONFIG.ENDPOINTS.REMINDERS}/${encodeURIComponent(id)}`), {
        method: 'PUT',
        headers: SwarivaAPI._headers({ 'Content-Type': 'application/json' }),
        body: JSON.stringify(updates),
      });
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        throw new Error(err.detail || `Failed to update reminder: HTTP ${resp.status}`);
      }
      return await resp.json();
    },

    async delete(id) {
      const resp = await fetch(SwarivaAPI._url(`${CONFIG.ENDPOINTS.REMINDERS}/${encodeURIComponent(id)}`), {
        method: 'DELETE',
        headers: SwarivaAPI._headers(),
      });
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        throw new Error(err.detail || `Failed to delete reminder: HTTP ${resp.status}`);
      }
      return await resp.json();
    },
  },

  /**
   * ── CONVERSATIONS ────────────────────────────────────────────────
   */
  conversations: {
    async list() {
      const resp = await fetch(SwarivaAPI._url(CONFIG.ENDPOINTS.CONVERSATIONS), {
        headers: SwarivaAPI._headers(),
      });
      if (!resp.ok) throw new Error(`Failed to list conversations: HTTP ${resp.status}`);
      const data = await resp.json();
      return data.conversations || [];
    },

    async getMessages(conversationId) {
      const resp = await fetch(SwarivaAPI._url(`${CONFIG.ENDPOINTS.CONVERSATIONS}/${encodeURIComponent(conversationId)}`), {
        headers: SwarivaAPI._headers(),
      });
      if (!resp.ok) throw new Error(`Failed to get conversation messages: HTTP ${resp.status}`);
      const data = await resp.json();
      return data.messages || [];
    },

    async delete(conversationId) {
      const resp = await fetch(SwarivaAPI._url(`${CONFIG.ENDPOINTS.CONVERSATIONS}/${encodeURIComponent(conversationId)}`), {
        method: 'DELETE',
        headers: SwarivaAPI._headers(),
      });
      if (!resp.ok) throw new Error(`Failed to delete conversation: HTTP ${resp.status}`);
      return await resp.json();
    },
  },

  /**
   * Fetch conversation history
   */
  async getHistory(sessionId) {
    const resp = await fetch(this._url(CONFIG.ENDPOINTS.CHAT_HISTORY(sessionId)), {
      headers: this._headers(),
    });
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
      headers: this._headers({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({ session_id: sessionId }),
    });
    if (!resp.ok) throw new Error(`Clear session failed: HTTP ${resp.status}`);
    return await resp.json();
  },
};
