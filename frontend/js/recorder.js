/**
 * SWARIVA AI — Browser Microphone Audio Recorder
 * Uses the MediaRecorder API to record spoken audio clips (< 30s)
 * and formats them for the Gnani Prisma STT FastAPI endpoint.
 */

class VoiceRecorder {
  constructor() {
    this.mediaRecorder = null;
    this.audioChunks = [];
    this.stream = null;
    this.isRecording = false;
    this.startTime = null;
    this.timerInterval = null;
    this.maxDurationSeconds = 30; // Max allowed by Gnani REST STT
  }

  /**
   * Determine best supported audio MIME type
   */
  _getSupportedMimeType() {
    const types = [
      'audio/webm;codecs=opus',
      'audio/webm',
      'audio/ogg;codecs=opus',
      'audio/wav',
      'audio/mp4',
    ];
    for (const t of types) {
      if (MediaRecorder.isTypeSupported(t)) return t;
    }
    return '';
  }

  /**
   * Start recording microphone input
   */
  async start({ onTick = null, onStop = null, onError = null } = {}) {
    if (this.isRecording) return;

    try {
      this.stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: 16000,
          echoCancellation: true,
          noiseSuppression: true,
        },
      });

      const mimeType = this._getSupportedMimeType();
      const options = mimeType ? { mimeType } : {};

      this.mediaRecorder = new MediaRecorder(this.stream, options);
      this.audioChunks = [];

      this.mediaRecorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          this.audioChunks.push(event.data);
        }
      };

      this.mediaRecorder.onstop = () => {
        this._cleanupTimer();
        const blobType = this.mediaRecorder.mimeType || 'audio/webm';
        const audioBlob = new Blob(this.audioChunks, { type: blobType });

        // Release microphone hardware
        if (this.stream) {
          this.stream.getTracks().forEach((track) => track.stop());
          this.stream = null;
        }

        this.isRecording = false;
        if (onStop) onStop(audioBlob);
      };

      this.mediaRecorder.start(250); // Slice data every 250ms
      this.isRecording = true;
      this.startTime = Date.now();

      // Start elapsed seconds timer
      this.timerInterval = setInterval(() => {
        const elapsedSec = Math.floor((Date.now() - this.startTime) / 1000);
        if (onTick) onTick(elapsedSec);

        // Auto-stop at 30 seconds (Gnani REST limit)
        if (elapsedSec >= this.maxDurationSeconds) {
          this.stop();
        }
      }, 500);

      return this.stream;
    } catch (err) {
      this.isRecording = false;
      this._cleanupTimer();
      console.error('Microphone access failed:', err);
      if (onError) onError(err);
      throw err;
    }
  }

  /**
   * Stop active recording and trigger onStop callback with audio Blob
   */
  stop() {
    if (!this.isRecording || !this.mediaRecorder) return;
    if (this.mediaRecorder.state !== 'inactive') {
      this.mediaRecorder.stop();
    }
    this.isRecording = false;
  }

  _cleanupTimer() {
    if (this.timerInterval) {
      clearInterval(this.timerInterval);
      this.timerInterval = null;
    }
  }
}

// Global recorder instance
const voiceRecorder = new VoiceRecorder();
