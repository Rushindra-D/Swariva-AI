/**
 * SWARIVA AI — Read Aloud Controller
 * Synthesizes user-entered text into expressive speech using Gnani Timbre.
 */

document.addEventListener('DOMContentLoaded', () => {
  const textInput = document.getElementById('read-text-input');
  const langSelect = document.getElementById('read-lang-select');
  const voiceSelect = document.getElementById('read-voice-select');
  const speedSlider = document.getElementById('read-speed-slider');
  const speedLabel = document.getElementById('read-speed-label');
  const speakBtn = document.getElementById('speak-aloud-btn');
  const stopBtn = document.getElementById('stop-aloud-btn');
  const downloadBtn = document.getElementById('download-audio-btn');
  const statusLabel = document.getElementById('read-status-label');

  let currentAudioBlobUrl = null;

  if (speedSlider && speedLabel) {
    speedSlider.addEventListener('input', (e) => {
      speedLabel.textContent = `${parseFloat(e.target.value).toFixed(1)}x`;
    });
  }

  // Pre-fill with sample text if empty
  if (textInput && !textInput.value) {
    textInput.value =
      'Welcome to SWARIVA AI Read Aloud. You can enter or paste any paragraph in English, Telugu, or Hindi, and our Gnani Timbre voice model will read it aloud for you clearly.';
  }

  async function handleSpeak() {
    const text = textInput.value.trim();
    if (!text) {
      showToast('Please enter text to read aloud.', 'error');
      return;
    }

    speakBtn.disabled = true;
    statusLabel.textContent = 'Synthesizing speech with Gnani Timbre...';

    try {
      const res = await SwarivaAPI.speakText({
        text,
        language: langSelect ? langSelect.value : 'auto',
        voice: voiceSelect ? voiceSelect.value : 'Nalini',
        speed: speedSlider ? parseFloat(speedSlider.value) : 1.0,
      });

      if (res.success && res.audio_base64) {
        statusLabel.textContent = `Speaking (${res.voice} • ${(res.size_bytes / 1024).toFixed(1)} KB)...`;

        // Create Blob URL for download
        const byteCharacters = atob(res.audio_base64);
        const byteNumbers = new Array(byteCharacters.length);
        for (let i = 0; i < byteCharacters.length; i++) {
          byteNumbers[i] = byteCharacters.charCodeAt(i);
        }
        const byteArray = new Uint8Array(byteNumbers);
        const blob = new Blob([byteArray], { type: 'audio/wav' });
        if (currentAudioBlobUrl) URL.revokeObjectURL(currentAudioBlobUrl);
        currentAudioBlobUrl = URL.createObjectURL(blob);

        if (downloadBtn) {
          downloadBtn.disabled = false;
          downloadBtn.onclick = () => {
            const a = document.createElement('a');
            a.href = currentAudioBlobUrl;
            a.download = `swariva_read_aloud_${Date.now()}.wav`;
            a.click();
          };
        }

        // Play the audio
        audioController.playBase64(
          res.audio_base64,
          () => {
            speakBtn.disabled = false;
            statusLabel.textContent = 'Playback completed.';
          },
          () => {
            speakBtn.disabled = false;
            statusLabel.textContent = 'Playback error.';
          }
        );
      } else {
        throw new Error(res.error || 'Failed to synthesize speech.');
      }
    } catch (err) {
      speakBtn.disabled = false;
      statusLabel.textContent = 'Error occurred.';
      showToast(err.message, 'error');
    }
  }

  if (speakBtn) speakBtn.addEventListener('click', handleSpeak);

  if (stopBtn) {
    stopBtn.addEventListener('click', () => {
      audioController.stop();
      speakBtn.disabled = false;
      statusLabel.textContent = 'Speech stopped.';
      showToast('Stopped reading aloud', 'info', 2000);
    });
  }
});
