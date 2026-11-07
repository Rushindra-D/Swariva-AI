/**
 * SWARIVA AI — Audio Player & Waveform Visualizer
 * Decodes and plays Base64 WAV audio returned from Gnani Timbre TTS
 * and renders live audio waveforms using the Web Audio API.
 */

class AudioController {
  constructor() {
    this.currentAudio = null;
    this.audioContext = null;
    this.analyser = null;
    this.animationFrameId = null;
    this.isPlaying = false;
  }

  /**
   * Stop any actively playing speech
   */
  stop() {
    if (this.currentAudio) {
      this.currentAudio.pause();
      this.currentAudio.currentTime = 0;
      this.currentAudio = null;
    }
    this.isPlaying = false;
    this._dispatchStateChange('stopped');
  }

  /**
   * Plays Base64-encoded WAV audio returned by Gnani Timbre
   */
  async playBase64(base64Audio, onEnded = null, onError = null) {
    this.stop();

    if (!base64Audio || base64Audio.length === 0) {
      if (onError) onError(new Error('Audio data is empty.'));
      return;
    }

    try {
      // Decode Base64 string to Uint8Array binary
      const byteCharacters = atob(base64Audio);
      const byteNumbers = new Array(byteCharacters.length);
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
      }
      const byteArray = new Uint8Array(byteNumbers);
      const blob = new Blob([byteArray], { type: 'audio/wav' });
      const audioUrl = URL.createObjectURL(blob);

      this.currentAudio = new Audio(audioUrl);
      this.isPlaying = true;
      this._dispatchStateChange('playing');

      this.currentAudio.onended = () => {
        this.isPlaying = false;
        URL.revokeObjectURL(audioUrl);
        this._dispatchStateChange('ended');
        if (onEnded) onEnded();
      };

      this.currentAudio.onerror = (e) => {
        this.isPlaying = false;
        this._dispatchStateChange('error');
        console.error('Audio playback error:', e);
        if (onError) onError(e);
      };

      await this.currentAudio.play();
    } catch (err) {
      this.isPlaying = false;
      this._dispatchStateChange('error');
      console.error('Failed to initialize audio playback:', err);
      if (onError) onError(err);
    }
  }

  _dispatchStateChange(state) {
    window.dispatchEvent(new CustomEvent('swariva:audio_state', { detail: { state } }));
  }

  /**
   * Connects live microphone or audio stream to an HTML5 Canvas for real-time visualization
   */
  startWaveform(canvas, stream) {
    if (!canvas || !stream) return;

    try {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      this.audioContext = new AudioCtx();
      const source = this.audioContext.createMediaStreamSource(stream);
      this.analyser = this.audioContext.createAnalyser();
      this.analyser.fftSize = 256;
      source.connect(this.analyser);

      const bufferLength = this.analyser.frequencyBinCount;
      const dataArray = new Uint8Array(bufferLength);
      const ctx = canvas.getContext('2d');

      const draw = () => {
        this.animationFrameId = requestAnimationFrame(draw);
        this.analyser.getByteFrequencyData(dataArray);

        ctx.clearRect(0, 0, canvas.width, canvas.height);

        const barWidth = (canvas.width / bufferLength) * 2.2;
        let x = 0;

        for (let i = 0; i < bufferLength; i++) {
          const barHeight = (dataArray[i] / 255) * canvas.height * 0.9;

          // Glowing purple to cyan gradient
          const gradient = ctx.createLinearGradient(0, canvas.height - barHeight, 0, canvas.height);
          gradient.addColorStop(0, '#38bdf8');
          gradient.addColorStop(0.5, '#8b5cf6');
          gradient.addColorStop(1, '#6366f1');

          ctx.fillStyle = gradient;
          ctx.beginPath();
          ctx.roundRect(x, canvas.height - barHeight, barWidth - 2, barHeight, [4, 4, 0, 0]);
          ctx.fill();

          x += barWidth;
        }
      };

      draw();
    } catch (err) {
      console.warn('Web Audio visualizer could not start:', err);
    }
  }

  stopWaveform(canvas) {
    if (this.animationFrameId) {
      cancelAnimationFrame(this.animationFrameId);
      this.animationFrameId = null;
    }
    if (this.audioContext) {
      this.audioContext.close().catch(() => {});
      this.audioContext = null;
    }
    if (canvas) {
      const ctx = canvas.getContext('2d');
      ctx.clearRect(0, 0, canvas.width, canvas.height);
    }
  }
}

// Global instance
const audioController = new AudioController();
