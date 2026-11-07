/**
 * SWARIVA AI — Chat Interface Controller
 * Orchestrates text conversations, microphone recording, live audio playback,
 * session management, and language switching.
 */

document.addEventListener('DOMContentLoaded', () => {
  // Elements
  const conversationStream = document.getElementById('conversation-stream');
  const chatInput = document.getElementById('chat-input');
  const sendBtn = document.getElementById('send-btn');
  const micBtn = document.getElementById('mic-btn');
  const recordingBar = document.getElementById('recording-bar');
  const recordingTimer = document.getElementById('recording-timer');
  const stopAudioBtn = document.getElementById('stop-audio-btn');
  const newChatBtn = document.getElementById('new-chat-btn');
  const clearChatBtn = document.getElementById('clear-chat-btn');
  const langSelect = document.getElementById('language-select');
  const voiceSelect = document.getElementById('voice-select');
  const sessionDisplay = document.getElementById('session-display');
  const waveCanvas = document.getElementById('chat-waveform');

  let activeSessionId = getActiveSessionId();
  if (sessionDisplay) sessionDisplay.textContent = activeSessionId.substring(0, 16) + '...';

  // Sync initial language preference
  if (langSelect) {
    langSelect.value = getStoredLanguage();
    langSelect.addEventListener('change', (e) => {
      setStoredLanguage(e.target.value);
      showToast(`Language set to ${e.target.options[e.target.selectedIndex].text}`, 'info');
    });
  }

  // Sync initial voice preference
  if (voiceSelect) {
    const savedVoice = localStorage.getItem(CONFIG.STORAGE_KEYS.VOICE) || 'Nalini';
    voiceSelect.value = savedVoice;
    voiceSelect.addEventListener('change', (e) => {
      localStorage.setItem(CONFIG.STORAGE_KEYS.VOICE, e.target.value);
      showToast(`Voice set to ${e.target.value}`, 'info');
    });
  }

  /**
   * Append a message bubble to conversation stream
   */
  function appendMessage(role, text, audioB64 = null, metadata = {}) {
    const row = document.createElement('div');
    row.className = `message-row ${role}`;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = role === 'user' ? '👤' : '🎙️';

    const bubbleWrapper = document.createElement('div');

    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    bubble.textContent = text;
    bubbleWrapper.appendChild(bubble);

    // Audio Playback button for assistant messages if audio is available
    if (role === 'assistant' && audioB64) {
      const audioControl = document.createElement('div');
      audioControl.className = 'audio-inline-player';

      const playBtn = document.createElement('button');
      playBtn.className = 'play-audio-btn';
      playBtn.innerHTML = '▶';
      playBtn.setAttribute('aria-label', 'Play voice message');

      const tag = document.createElement('span');
      tag.className = 'audio-duration-tag';
      tag.textContent = '🔊 Spoken by Gnani Timbre';

      playBtn.addEventListener('click', () => {
        if (playBtn.textContent === '⏹') {
          audioController.stop();
          playBtn.textContent = '▶';
        } else {
          document.querySelectorAll('.play-audio-btn').forEach((b) => (b.textContent = '▶'));
          playBtn.textContent = '⏹';
          audioController.playBase64(
            audioB64,
            () => (playBtn.textContent = '▶'),
            () => (playBtn.textContent = '▶')
          );
        }
      });

      audioControl.appendChild(playBtn);
      audioControl.appendChild(tag);
      bubbleWrapper.appendChild(audioControl);

      // Auto-play if enabled in preferences
      const autoPlay = localStorage.getItem(CONFIG.STORAGE_KEYS.AUTO_PLAY) !== 'false';
      if (autoPlay) {
        audioController.playBase64(audioB64, () => (playBtn.textContent = '▶'));
        playBtn.textContent = '⏹';
      }
    }

    // Timestamp & Model meta
    const meta = document.createElement('div');
    meta.className = 'message-meta';
    const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    meta.textContent = `${now} ${metadata.detected_language ? `• ${metadata.detected_language}` : ''}`;
    bubbleWrapper.appendChild(meta);

    row.appendChild(avatar);
    row.appendChild(bubbleWrapper);
    conversationStream.appendChild(row);
    conversationStream.scrollTop = conversationStream.scrollHeight;
  }

  /**
   * Display or remove animated "thinking" indicator
   */
  function showThinking(show) {
    const existing = document.getElementById('thinking-bubble');
    if (show && !existing) {
      const row = document.createElement('div');
      row.className = 'message-row assistant';
      row.id = 'thinking-bubble';

      const avatar = document.createElement('div');
      avatar.className = 'message-avatar';
      avatar.textContent = '🎙️';

      const bubble = document.createElement('div');
      bubble.className = 'message-bubble thinking-bubble';
      bubble.innerHTML = '<div class="dot-pulse"></div><div class="dot-pulse"></div><div class="dot-pulse"></div>';

      row.appendChild(avatar);
      row.appendChild(bubble);
      conversationStream.appendChild(row);
      conversationStream.scrollTop = conversationStream.scrollHeight;
    } else if (!show && existing) {
      existing.remove();
    }
  }

  /**
   * Send Text Message
   */
  async function handleSendText() {
    const text = chatInput.value.trim();
    if (!text) return;

    chatInput.value = '';
    appendMessage('user', text);
    showThinking(true);

    try {
      const response = await SwarivaAPI.sendChatMessage({
        message: text,
        sessionId: activeSessionId,
        language: langSelect ? langSelect.value : 'auto',
        includeAudio: true, // Always request Gnani Timbre audio
        voice: voiceSelect ? voiceSelect.value : null,
      });

      showThinking(false);
      appendMessage('assistant', response.response, response.audio_base64, response.metadata);
    } catch (err) {
      showThinking(false);
      showToast(err.message, 'error');
      appendMessage('assistant', `⚠️ Sorry, I encountered an issue: ${err.message}`);
    }
  }

  // Send button & Enter key
  if (sendBtn) sendBtn.addEventListener('click', handleSendText);
  if (chatInput) {
    chatInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSendText();
      }
    });
  }

  /**
   * Microphone Recording & Voice-to-Voice Loop
   */
  async function toggleRecording() {
    if (voiceRecorder.isRecording) {
      // Stop recording and process
      voiceRecorder.stop();
      micBtn.classList.remove('recording');
      if (recordingBar) recordingBar.classList.remove('active');
      audioController.stopWaveform(waveCanvas);
      showThinking(true);
    } else {
      // Start recording
      try {
        const stream = await voiceRecorder.start({
          onTick: (sec) => {
            if (recordingTimer) recordingTimer.textContent = `00:${sec < 10 ? '0' : ''}${sec} / 00:30`;
          },
          onStop: async (audioBlob) => {
            try {
              showToast('Transcribing with Gnani Prisma...', 'info');
              const res = await SwarivaAPI.sendVoiceChat({
                audioBlob,
                sessionId: activeSessionId,
                language: langSelect ? langSelect.value : 'auto',
                voice: voiceSelect ? voiceSelect.value : null,
              });

              showThinking(false);

              if (res.success) {
                // Show user transcription
                appendMessage('user', res.transcript, null, { detected_language: res.detected_language });
                // Show assistant reply + play audio
                appendMessage('assistant', res.response_text, res.audio_base64, res.metadata);
              } else {
                showToast(res.error || 'Speech not recognized.', 'error');
                appendMessage('assistant', res.response_text || `⚠️ ${res.error}`);
              }
            } catch (err) {
              showThinking(false);
              showToast(err.message, 'error');
              appendMessage('assistant', `⚠️ Voice error: ${err.message}`);
            }
          },
          onError: (err) => {
            micBtn.classList.remove('recording');
            if (recordingBar) recordingBar.classList.remove('active');
            audioController.stopWaveform(waveCanvas);
            showToast('Microphone permission denied or unavailable.', 'error');
          },
        });

        micBtn.classList.add('recording');
        if (recordingBar) recordingBar.classList.add('active');
        if (waveCanvas) audioController.startWaveform(waveCanvas, stream);
      } catch (err) {
        showToast('Could not access microphone.', 'error');
      }
    }
  }

  if (micBtn) micBtn.addEventListener('click', toggleRecording);

  // Stop Audio Button
  if (stopAudioBtn) {
    stopAudioBtn.addEventListener('click', () => {
      audioController.stop();
      document.querySelectorAll('.play-audio-btn').forEach((b) => (b.textContent = '▶'));
      showToast('Speech stopped.', 'info', 2000);
    });
  }

  // New Chat Button
  if (newChatBtn) {
    newChatBtn.addEventListener('click', () => {
      activeSessionId = resetActiveSessionId();
      if (sessionDisplay) sessionDisplay.textContent = activeSessionId.substring(0, 16) + '...';
      conversationStream.innerHTML = '';
      audioController.stop();
      appendMessage(
        'assistant',
        'Hello! I have started a fresh conversation for you. How can I assist you right now?'
      );
      showToast('New conversation started', 'success');
    });
  }

  // Clear Chat Button
  if (clearChatBtn) {
    clearChatBtn.addEventListener('click', async () => {
      if (confirm('Are you sure you want to clear conversation history for this session?')) {
        try {
          await SwarivaAPI.clearSession(activeSessionId);
          conversationStream.innerHTML = '';
          audioController.stop();
          showToast('Session context cleared', 'success');
          appendMessage('assistant', 'Session context has been reset. What would you like to speak about?');
        } catch (err) {
          showToast(err.message, 'error');
        }
      }
    });
  }

  // Initial greeting
  appendMessage(
    'assistant',
    'Hello! I am Swariva, your intelligent voice assistant. You can speak to me or type your questions in English, Telugu, or Hindi.'
  );
});
