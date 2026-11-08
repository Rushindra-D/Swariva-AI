/**
 * SWARIVA AI — Dedicated Voice Assistant Controller
 * Powers voice.html with prominent accessible voice controls,
 * animated waveform visualizer, and live voice interactions.
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
  const stopSpeechBtn = document.getElementById('stop-speech-btn');
  const repeatSpeechBtn = document.getElementById('repeat-speech-btn');

  let activeSessionId = getActiveSessionId();
  let lastAudioBase64 = null;

  if (langSelect) {
    langSelect.value = getStoredLanguage();
    langSelect.addEventListener('change', (e) => setStoredLanguage(e.target.value));
  }

  function setAgentState(state, customMessage = '') {
    giantMic.classList.remove('recording');

    switch (state) {
      case 'idle':
        micStatus.textContent = 'Tap Microphone to Speak';
        micTimer.textContent = 'Ready';
        break;
      case 'listening':
        giantMic.classList.add('recording');
        micStatus.textContent = 'Listening...';
        break;
      case 'processing_audio':
        micStatus.textContent = 'Processing audio...';
        micTimer.textContent = 'Normalizing audio format...';
        break;
      case 'recognizing':
        micStatus.textContent = 'Recognizing speech...';
        micTimer.textContent = 'Transcribing with Gnani Prisma...';
        break;
      case 'generating':
        micStatus.textContent = 'Generating response...';
        micTimer.textContent = 'Formulating companion response...';
        break;
      case 'speaking':
        micStatus.textContent = 'Playing response...';
        micTimer.textContent = 'Voice playback in progress (Gnani Timbre)';
        break;
      case 'error':
        micStatus.textContent = customMessage || 'Error occurred. Tap microphone to retry.';
        micTimer.textContent = 'Ready';
        break;
    }
  }

  async function handleMicToggle() {
    if (voiceRecorder.isRecording) {
      // User tapped to finish speaking
      voiceRecorder.stop();
      audioController.stopWaveform(waveCanvas);
      setAgentState('processing_audio');
    } else {
      // Stop any existing speech playback
      audioController.stop();

      try {
        const stream = await voiceRecorder.start({
          onTick: (sec) => {
            micTimer.textContent = `Recording: 00:${sec < 10 ? '0' : ''}${sec} / 00:30`;
          },
          onStop: async (audioBlob) => {
            setAgentState('recognizing');
            showToast('Recognizing speech with Gnani Prisma...', 'info', 1800);

            try {
              const res = await SwarivaAPI.sendVoiceChat({
                audioBlob,
                sessionId: activeSessionId,
                language: langSelect ? langSelect.value : 'auto',
                voice: voiceSelect ? voiceSelect.value : null,
              });

              if (res.success) {
                setAgentState('generating');
                // Update transcript card
                if (transcriptCard && userTranscriptText) {
                  transcriptCard.style.display = 'block';
                  userTranscriptText.textContent = `"${res.transcript}"`;
                }

                // Update response card
                if (responseCard && assistantResponseText) {
                  responseCard.style.display = 'block';
                  assistantResponseText.textContent = res.response_text;
                }

                lastAudioBase64 = res.audio_base64;
                if (repeatSpeechBtn) repeatSpeechBtn.disabled = !lastAudioBase64;

                // Playback synthesized audio
                if (res.audio_base64) {
                  setAgentState('speaking');
                  audioController.playBase64(
                    res.audio_base64,
                    () => setAgentState('idle'),
                    () => setAgentState('idle')
                  );
                } else {
                  setAgentState('idle');
                }
              } else {
                setAgentState('error', res.error || 'Could not recognize speech.');
                showToast(res.error || 'Speech not recognized. Please speak clearly.', 'error', 4000);
              }
            } catch (err) {
              setAgentState('error', err.message);
              showToast(err.message, 'error', 4000);
            }
          },
          onError: (err) => {
            audioController.stopWaveform(waveCanvas);
            setAgentState('error', 'Microphone access denied.');
            showToast('Microphone access denied. Please grant permission in browser.', 'error');
          },
        });

        setAgentState('listening');
        if (waveCanvas) audioController.startWaveform(waveCanvas, stream);
      } catch (err) {
        setAgentState('error', 'Could not open microphone.');
      }
    }
  }

  if (giantMic) giantMic.addEventListener('click', handleMicToggle);

  if (stopSpeechBtn) {
    stopSpeechBtn.addEventListener('click', () => {
      audioController.stop();
      setAgentState('idle');
      showToast('Speech stopped', 'info', 2000);
    });
  }

  if (repeatSpeechBtn) {
    repeatSpeechBtn.addEventListener('click', () => {
      if (lastAudioBase64) {
        setAgentState('speaking');
        audioController.playBase64(lastAudioBase64, () => setAgentState('idle'));
      }
    });
  }

  setAgentState('idle');
});

