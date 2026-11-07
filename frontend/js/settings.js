/**
 * SWARIVA AI — Settings & Accessibility Controller
 * Manages accessibility settings, voice options, and backend connection test.
 */

document.addEventListener('DOMContentLoaded', () => {
  const langSelect = document.getElementById('setting-lang');
  const voiceSelect = document.getElementById('setting-voice');
  const autoPlayToggle = document.getElementById('setting-autoplay');
  const contrastToggle = document.getElementById('setting-contrast');
  const fontSizeSelect = document.getElementById('setting-fontsize');
  const apiUrlInput = document.getElementById('setting-api-url');
  const testConnBtn = document.getElementById('test-conn-btn');
  const saveBtn = document.getElementById('save-settings-btn');
  const resetBtn = document.getElementById('reset-data-btn');

  // Load current values
  if (langSelect) langSelect.value = getStoredLanguage();
  if (voiceSelect) voiceSelect.value = localStorage.getItem(CONFIG.STORAGE_KEYS.VOICE) || 'Nalini';
  if (autoPlayToggle) autoPlayToggle.checked = localStorage.getItem(CONFIG.STORAGE_KEYS.AUTO_PLAY) !== 'false';
  if (contrastToggle) contrastToggle.checked = localStorage.getItem(CONFIG.STORAGE_KEYS.HIGH_CONTRAST) === 'true';
  if (fontSizeSelect) fontSizeSelect.value = localStorage.getItem(CONFIG.STORAGE_KEYS.FONT_SIZE) || 'normal';
  if (apiUrlInput) apiUrlInput.value = CONFIG.API_BASE_URL;

  // Immediate live preview for contrast and font size
  if (contrastToggle) {
    contrastToggle.addEventListener('change', (e) => {
      localStorage.setItem(CONFIG.STORAGE_KEYS.HIGH_CONTRAST, e.target.checked);
      applyAccessibilityPreferences();
    });
  }

  if (fontSizeSelect) {
    fontSizeSelect.addEventListener('change', (e) => {
      localStorage.setItem(CONFIG.STORAGE_KEYS.FONT_SIZE, e.target.value);
      applyAccessibilityPreferences();
    });
  }

  // Test Backend Connection
  if (testConnBtn) {
    testConnBtn.addEventListener('click', async () => {
      testConnBtn.disabled = true;
      testConnBtn.textContent = 'Testing...';

      const customUrl = apiUrlInput ? apiUrlInput.value.trim() : CONFIG.API_BASE_URL;
      const oldUrl = CONFIG.API_BASE_URL;
      CONFIG.API_BASE_URL = customUrl;

      try {
        const health = await SwarivaAPI.checkHealth();
        if (health.status === 'healthy') {
          showToast(`Connected successfully! (STT: ${health.models.stt}, TTS: ${health.models.tts})`, 'success');
        } else {
          showToast(`Backend reachable, but reported: ${health.status}`, 'info');
        }
      } catch (err) {
        CONFIG.API_BASE_URL = oldUrl;
        showToast(`Connection failed: ${err.message}`, 'error');
      } finally {
        testConnBtn.disabled = false;
        testConnBtn.textContent = 'Test Connection';
      }
    });
  }

  // Save Settings
  if (saveBtn) {
    saveBtn.addEventListener('click', () => {
      if (langSelect) setStoredLanguage(langSelect.value);
      if (voiceSelect) localStorage.setItem(CONFIG.STORAGE_KEYS.VOICE, voiceSelect.value);
      if (autoPlayToggle) localStorage.setItem(CONFIG.STORAGE_KEYS.AUTO_PLAY, autoPlayToggle.checked);
      if (apiUrlInput) {
        const url = apiUrlInput.value.trim().replace(/\/+$/, '');
        localStorage.setItem('swariva_api_url', url);
        CONFIG.API_BASE_URL = url;
      }
      showToast('Settings saved successfully!', 'success');
    });
  }

  // Reset Data
  if (resetBtn) {
    resetBtn.addEventListener('click', () => {
      if (confirm('This will reset all local sessions, preferences, and reminders. Continue?')) {
        localStorage.clear();
        showToast('All local data cleared. Reloading...', 'info');
        setTimeout(() => window.location.reload(), 1000);
      }
    });
  }
});
