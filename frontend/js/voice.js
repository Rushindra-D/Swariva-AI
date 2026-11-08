/**
 * SWARIVA AI — Dedicated Voice Assistant Controller
 *
 * Real-Time Voice Activity Detection (VAD) & Conversation Controller:
 * 1. Automatically detects when the user finishes speaking (~2s silence) and terminates recording immediately.
 * 2. Removes the fixed 30-second waiting limit.
 * 3. Supports Push-to-Talk Mode and Continuous Conversation Mode.
 * 4. Mutes/suspends microphone capture during TTS playback to eliminate acoustic feedback.
 * 5. In continuous mode, resumes listening automatically after assistant speech finishes.
 * 6. Dynamic visual state machine for accessible, transparent interaction.
 */

document.addEventListener('DOMContentLoaded', () => {
  const giantMic = document.getElementById('giant-mic-btn');
  const micStatus = document.getElementById('mic-status-label');
  const micTimer = document.getElementById('mic-timer');
  const waveCanvas = document.getElementById('voice-waveform');
  const transcriptCard = document.getElementById('transcript-display-card');
  const userTranscriptText = document.getElementById('user-transcript-text');
  const responseCard = document.getElementById('response-display-card');
  const assistantResponseText = document.getElementById('assistant-response-text');
  const langSelect = document.getElementById('voice-page-lang');
  const voiceSelect = document.getElementById('voice-page-voice');
  const silenceSelect = document.getElementById('silence-timeout-select');
  const continuousToggle = document.getElementById('continuous-mode-toggle');
  const stopSpeechBtn = document.getElementById('stop-speech-btn');
  const cancelRecBtn = document.getElementById('cancel-recording-btn');
  const repeatSpeechBtn = document.getElementById('repeat-speech-btn');

  let activeSessionId = getActiveSessionId();
  let lastAudioBase64 = null;
  let isContinuousConversationActive = false;
  let isAssistantSpeaking = false;

  // ── Restore Stored Preferences ──
  if (langSelect) {
    langSelect.value = getStoredLanguage();
    langSelect.addEventListener('change', (e) => setStoredLanguage(e.target.value));
  }

  if (silenceSelect) {
    const savedSilence = localStorage.getItem('swariva_silence_timeout') || '2000';
    silenceSelect.value = savedSilence;
    voiceRecorder.setSilenceThreshold(parseInt(savedSilence, 10));

    silenceSelect.addEventListener('change', (e) => {
      const ms = parseInt(e.target.value, 10);
      localStorage.setItem('swariva_silence_timeout', e.target.value);
      voiceRecorder.setSilenceThreshold(ms);
      showToast(`Silence pause set to ${(ms / 1000).toFixed(1)}s`, 'info', 1800);
    });
  }

  if (continuousToggle) {
    const savedContinuous = localStorage.getItem('swariva_continuous_mode') === 'true';
    continuousToggle.checked = savedContinuous;
    continuousToggle.addEventListener('change', (e) => {
      localStorage.setItem('swariva_continuous_mode', e.target.checked);
      if (!e.target.checked && isContinuousConversationActive) {
        isContinuousConversationActive = false;
        showToast('Continuous conversation mode disabled.', 'info', 2000);
      } else if (e.target.checked) {
        showToast('Continuous conversation mode enabled. Swariva will auto-listen after each response.', 'info', 2500);
      }
    });
  }

  /**
   * Visual State Machine
   */
  function setAgentState(state, customMessage = '') {
    giantMic.classList.remove('recording');
    if (cancelRecBtn) cancelRecBtn.style.display = 'none';

    switch (state) {
      case 'idle':
        micStatus.textContent = 'Tap Microphone to Speak';
        micTimer.textContent = 'Speak naturally • Swariva responds automatically when you finish';
        break;

      case 'listening':
        giantMic.classList.add('recording');
        if (cancelRecBtn) cancelRecBtn.style.display = 'inline-flex';
        micStatus.textContent = isContinuousConversationActive ? 'Listening (Continuous Mode)...' : 'Listening... Speak naturally';
        micTimer.textContent = 'Waiting for your voice... (Auto-stops after ~2s silence)';
        break;

      case 'speech_detected':
        giantMic.classList.add('recording');
        if (cancelRecBtn) cancelRecBtn.style.display = 'inline-flex';
        micStatus.textContent = 'Speaking detected...';
        micTimer.textContent = 'Listening to your words... (Will process when you finish)';
        break;

      case 'silence_detected':
        micStatus.textContent = 'Silence detected, finalizing audio...';
        micTimer.textContent = 'Submitting to Gnani Prisma STT...';
        break;

      case 'processing_audio':
        micStatus.textContent = 'Processing audio format...';
        micTimer.textContent = 'Normalizing to 16kHz PCM WAV...';
        break;

      case 'recognizing':
        micStatus.textContent = 'Recognizing speech (Gnani Prisma)...';
        micTimer.textContent = 'Transcribing your words...';
        break;

      case 'generating':
        micStatus.textContent = 'Generating intelligent response...';
        micTimer.textContent = 'Formulating companion reply...';
        break;

      case 'speaking':
        micStatus.textContent = 'Playing response (Gnani Timbre)...';
        micTimer.textContent = 'Voice playback in progress...';
        break;

      case 'error':
        micStatus.textContent = customMessage || 'Error occurred. Tap microphone to retry.';
        micTimer.textContent = 'Ready';
        break;
    }
  }

  /**
   * Start a real-time listening session with VAD
   */
  async function startListeningSession() {
    if (voiceRecorder.isRecording || isAssistantSpeaking) return;

    // Stop any existing speech playback to prevent self-transcription
    audioController.stop();

    try {
      const silenceMs = silenceSelect ? parseInt(silenceSelect.value, 10) : 2000;

      const stream = await voiceRecorder.start({
        silenceThresholdMs: silenceMs,

        onTick: (sec, speechDetected) => {
          if (speechDetected) {
            micTimer.textContent = `Speaking: 00:${sec < 10 ? '0' : ''}${sec} (Auto-terminates after silence)`;
          } else {
            micTimer.textContent = `Listening: 00:${sec < 10 ? '0' : ''}${sec} (Speak whenever ready)`;
          }
        },

        onSpeechStart: () => {
          setAgentState('speech_detected');
        },

        onSilenceDetected: (silenceDuration) => {
          setAgentState('silence_detected');
        },

        onStop: async (audioBlob, { speechDetected, durationMs }) => {
          audioController.stopWaveform(waveCanvas);

          // If recording stopped without speech detected
          if (!speechDetected && durationMs < 1200) {
            console.log('VAD: No speech detected before stopping.');
            setAgentState('idle');
            showToast('No speech detected. Please speak clearly into your microphone.', 'info', 2500);
            return;
          }

          setAgentState('recognizing');

          try {
            const res = await SwarivaAPI.sendVoiceChat({
              audioBlob,
              sessionId: activeSessionId,
              language: langSelect ? langSelect.value : 'auto',
              voice: voiceSelect ? voiceSelect.value : null,
            });

            if (res.success) {
              setAgentState('generating');

              // Update user transcript card
              if (transcriptCard && userTranscriptText) {
                transcriptCard.style.display = 'block';
                userTranscriptText.textContent = `"${res.transcript}"`;
              }

              // Update assistant response card
              if (responseCard && assistantResponseText) {
                responseCard.style.display = 'block';
                assistantResponseText.textContent = res.response_text;
              }

              lastAudioBase64 = res.audio_base64;
              if (repeatSpeechBtn) repeatSpeechBtn.disabled = !lastAudioBase64;

              // Play synthesized speech audio
              if (res.audio_base64) {
                isAssistantSpeaking = true;
                setAgentState('speaking');

                audioController.playBase64(
                  res.audio_base64,
                  // onEnded callback
                  () => {
                    isAssistantSpeaking = false;
                    // Check continuous conversation mode
                    if (continuousToggle && continuousToggle.checked && isContinuousConversationActive) {
                      // Small anti-feedback pause (400ms) before opening microphone
                      setTimeout(() => {
                        if (isContinuousConversationActive && !voiceRecorder.isRecording) {
                          startListeningSession();
                        }
                      }, 400);
                    } else {
                      setAgentState('idle');
                    }
                  },
                  // onError callback
                  () => {
                    isAssistantSpeaking = false;
                    setAgentState('idle');
                  }
                );
              } else {
                setAgentState('idle');
                if (continuousToggle && continuousToggle.checked && isContinuousConversationActive) {
                  setTimeout(startListeningSession, 500);
                }
              }
            } else {
              setAgentState('error', res.error || 'Could not recognize speech.');
              showToast(res.error || 'Speech not recognized. Please speak clearly.', 'error', 4000);
              if (isContinuousConversationActive) {
                isContinuousConversationActive = false;
              }
            }
          } catch (err) {
            setAgentState('error', err.message);
            showToast(err.message, 'error', 4000);
            if (isContinuousConversationActive) {
              isContinuousConversationActive = false;
            }
          }
        },

        onError: (err) => {
          audioController.stopWaveform(waveCanvas);
          setAgentState('error', 'Microphone access denied.');
          showToast('Microphone access denied. Please allow microphone permissions.', 'error');
          isContinuousConversationActive = false;
        },
      });

      setAgentState('listening');
      if (waveCanvas) audioController.startWaveform(waveCanvas, stream);
    } catch (err) {
      setAgentState('error', 'Could not open microphone.');
      isContinuousConversationActive = false;
    }
  }

  /**
   * Main Microphone Button Action
   */
  async function handleMicToggle() {
    if (voiceRecorder.isRecording) {
      // User manually clicked to stop speaking early
      voiceRecorder.stop();
      audioController.stopWaveform(waveCanvas);
      setAgentState('silence_detected');
    } else {
      // If continuous mode is enabled, mark conversation active
      if (continuousToggle && continuousToggle.checked) {
        isContinuousConversationActive = true;
      }
      await startListeningSession();
    }
  }

  if (giantMic) giantMic.addEventListener('click', handleMicToggle);

  // Cancel Recording Button
  if (cancelRecBtn) {
    cancelRecBtn.addEventListener('click', () => {
      voiceRecorder.cancel();
      audioController.stopWaveform(waveCanvas);
      isContinuousConversationActive = false;
      setAgentState('idle');
      showToast('Recording cancelled.', 'info', 1800);
    });
  }

  // Stop / Pause Speech Button
  if (stopSpeechBtn) {
    stopSpeechBtn.addEventListener('click', () => {
      isAssistantSpeaking = false;
      isContinuousConversationActive = false;
      audioController.stop();
      if (voiceRecorder.isRecording) {
        voiceRecorder.cancel();
        audioController.stopWaveform(waveCanvas);
      }
      setAgentState('idle');
      showToast('Conversation paused.', 'info', 1800);
    });
  }

  // Repeat Speech Button
  if (repeatSpeechBtn) {
    repeatSpeechBtn.addEventListener('click', () => {
      if (lastAudioBase64) {
        isAssistantSpeaking = true;
        setAgentState('speaking');
        audioController.playBase64(lastAudioBase64, () => {
          isAssistantSpeaking = false;
          setAgentState('idle');
        });
      }
    });
  }

  setAgentState('idle');
});
