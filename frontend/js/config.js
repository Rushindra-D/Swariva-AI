/**
 * SWARIVA AI — Frontend Configuration & State Management
 * Centralized settings, endpoints, and local storage state.
 */

const CONFIG = {
  // Configurable Backend API URL (defaults to local FastAPI backend)
  API_BASE_URL: localStorage.getItem('swariva_api_url') || 'http://127.0.0.1:8000',

  ENDPOINTS: {
    HEALTH: '/health',
    INFO: '/api/v1/info',
    CHAT: '/api/v1/chat',
    CHAT_CLEAR: '/api/v1/chat/clear',
    CHAT_HISTORY: (sessionId) => `/api/v1/chat/history/${encodeURIComponent(sessionId)}`,
    VOICE_CHAT: '/api/v1/voice/chat',
    VOICE_SPEAK: '/api/v1/voice/speak',
    AUTH_SIGNUP: '/api/v1/auth/signup',
    AUTH_LOGIN: '/api/v1/auth/login',
    AUTH_ME: '/api/v1/auth/me',
    AUTH_LOGOUT: '/api/v1/auth/logout',
    REMINDERS: '/api/v1/reminders',
    CONVERSATIONS: '/api/v1/conversations',
  },

  STORAGE_KEYS: {
    AUTH_TOKEN: 'swariva_auth_token',
    USER_PROFILE: 'swariva_user_profile',
    SESSION_ID: 'swariva_session_id',
    LANGUAGE: 'swariva_preferred_language',
    VOICE: 'swariva_preferred_voice',
    HIGH_CONTRAST: 'swariva_high_contrast',
    FONT_SIZE: 'swariva_font_size',
    AUTO_PLAY: 'swariva_auto_play_voice',
    REMINDERS: 'swariva_local_reminders',
    RECENT_SESSIONS: 'swariva_recent_sessions',
  },

  DEFAULTS: {
    LANGUAGE: 'auto',
    VOICE: 'Nalini',
    AUTO_PLAY: true,
  },
};

function generateUUID() {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0, v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

/**
 * Retrieve or generate active Session ID
 */
function getActiveSessionId() {
  let sid = localStorage.getItem(CONFIG.STORAGE_KEYS.SESSION_ID);
  const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
  if (!sid || !uuidRegex.test(sid)) {
    sid = generateUUID();
    localStorage.setItem(CONFIG.STORAGE_KEYS.SESSION_ID, sid);
  }
  return sid;
}

function setActiveSessionId(newId) {
  if (newId) {
    localStorage.setItem(CONFIG.STORAGE_KEYS.SESSION_ID, newId);
  }
}

function resetActiveSessionId() {
  const newId = generateUUID();
  localStorage.setItem(CONFIG.STORAGE_KEYS.SESSION_ID, newId);
  return newId;
}

function getStoredLanguage() {
  return localStorage.getItem(CONFIG.STORAGE_KEYS.LANGUAGE) || CONFIG.DEFAULTS.LANGUAGE;
}

function setStoredLanguage(lang) {
  localStorage.setItem(CONFIG.STORAGE_KEYS.LANGUAGE, lang);
}

function getAuthToken() {
  return localStorage.getItem(CONFIG.STORAGE_KEYS.AUTH_TOKEN);
}

function setAuthToken(token) {
  if (token) {
    localStorage.setItem(CONFIG.STORAGE_KEYS.AUTH_TOKEN, token);
  } else {
    localStorage.removeItem(CONFIG.STORAGE_KEYS.AUTH_TOKEN);
  }
}

function getUserProfile() {
  try {
    const raw = localStorage.getItem(CONFIG.STORAGE_KEYS.USER_PROFILE);
    return raw ? JSON.parse(raw) : null;
  } catch (e) {
    return null;
  }
}

function setUserProfile(profile) {
  if (profile) {
    localStorage.setItem(CONFIG.STORAGE_KEYS.USER_PROFILE, JSON.stringify(profile));
  } else {
    localStorage.removeItem(CONFIG.STORAGE_KEYS.USER_PROFILE);
  }
}

function clearAuth() {
  localStorage.removeItem(CONFIG.STORAGE_KEYS.AUTH_TOKEN);
  localStorage.removeItem(CONFIG.STORAGE_KEYS.USER_PROFILE);
}

/**
 * Global accessible Toast notification
 */
function showToast(message, type = 'info', durationMs = 3500) {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.setAttribute('role', 'status');
  toast.setAttribute('aria-live', 'polite');

  const icon = type === 'error' ? '⚠️' : type === 'success' ? '✅' : 'ℹ️';
  toast.innerHTML = `<span>${icon}</span><span>${message}</span>`;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    setTimeout(() => toast.remove(), 300);
  }, durationMs);
}

/**
 * Apply saved Accessibility settings to DOM
 */
function applyAccessibilityPreferences() {
  const isHighContrast = localStorage.getItem(CONFIG.STORAGE_KEYS.HIGH_CONTRAST) === 'true';
  const fontSize = localStorage.getItem(CONFIG.STORAGE_KEYS.FONT_SIZE) || 'normal';

  if (isHighContrast) {
    document.body.classList.add('high-contrast');
  } else {
    document.body.classList.remove('high-contrast');
  }

  document.body.classList.remove('font-large', 'font-xlarge');
  if (fontSize === 'large') document.body.classList.add('font-large');
  if (fontSize === 'xlarge') document.body.classList.add('font-xlarge');
}

// Auto-run on DOM ready
document.addEventListener('DOMContentLoaded', applyAccessibilityPreferences);

