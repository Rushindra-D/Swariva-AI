/**
 * SWARIVA AI — Real-Time Voice Activity Detection & Audio Recorder
 *
 * Provides intelligent, automatic silence-based recording termination:
 * 1. Analyzes microphone audio in real-time via Web Audio API AnalyserNode.
 * 2. Continuously measures RMS audio energy with adaptive background noise calibration.
 * 3. Ignores initial ambient silence before the user speaks.
 * 4. Detects when the user begins speaking (minimum 300ms speech duration).
 * 5. Monitors natural speech and brief pauses between words.
 * 6. Automatically stops recording when ~2 seconds of silence are detected after speech.
 * 7. Enforces a 120-second safety cutoff (to prevent accidental indefinite recording).
 * 8. Supports cancellation and clean audio cleanup without feedback loops.
 */

class VoiceRecorder {
  constructor() {
    this.mediaRecorder = null;
    this.audioChunks = [];
    this.stream = null;
    this.audioContext = null;
    this.analyser = null;

    this.isRecording = false;
    this.speechDetected = false;
    this.speechStartTime = null;
    this.silenceStartTime = null;
    this.noiseFloor = 0.008; // Baseline ambient noise floor
    this.speechThreshold = 0.022; // Adaptive threshold to trigger speech

    this.startTime = null;
    this.timerInterval = null;
    this.vadInterval = null;
    this.isCancelled = false;

    // Configurable VAD timing parameters
    this.silenceThresholdMs = 2000;       // 2.0s silence terminates recording
    this.minSpeechDurationMs = 300;       // Ignore clicks/pops shorter than 300ms
    this.maxRecordingDurationMs = 120000; // 120s safety ceiling
  }

  setSilenceThreshold(ms) {
    if (ms && ms >= 500 && ms <= 10000) {
      this.silenceThresholdMs = ms;
    }
  }

  _getSupportedMimeType() {
    const types = [
      'audio/webm;codecs=opus',
      'audio/webm',
      'audio/ogg;codecs=opus',
      'audio/mp4',
      'audio/wav',
    ];
    for (const t of types) {
      if (typeof MediaRecorder !== 'undefined' && MediaRecorder.isTypeSupported(t)) {
        return t;
      }
    }
    return '';
  }

  /**
   * Start microphone capture with real-time VAD
   */
  async start({
    onTick = null,
    onSpeechStart = null,
    onSilenceDetected = null,
    onStop = null,
    onError = null,
    silenceThresholdMs = null,
  } = {}) {
    if (this.isRecording) return;
    this.isCancelled = false;

    if (silenceThresholdMs) {
      this.setSilenceThreshold(silenceThresholdMs);
    }

    try {
      this.stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: 16000,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });

      // ── 1. Setup Web Audio API Analyser for Voice Activity Detection ──
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      this.audioContext = new AudioCtx();
      const source = this.audioContext.createMediaStreamSource(this.stream);
      this.analyser = this.audioContext.createAnalyser();
      this.analyser.fftSize = 1024;
      this.analyser.smoothingTimeConstant = 0.3;
      source.connect(this.analyser);

      // ── 2. Setup MediaRecorder for audio payload capture ──
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
        this._cleanupVAD();
        this._cleanupTimer();

        if (this.isCancelled) {
          this._releaseStream();
          this.isRecording = false;
          return;
        }

        const blobType = this.mediaRecorder.mimeType || 'audio/webm';
        const audioBlob = new Blob(this.audioChunks, { type: blobType });

        this._releaseStream();
        this.isRecording = false;

        if (onStop) {
          onStop(audioBlob, {
            speechDetected: this.speechDetected,
            durationMs: Date.now() - (this.startTime || Date.now()),
          });
        }
      };

      // Slice audio in small chunks (150ms) for responsiveness
      this.mediaRecorder.start(150);
      this.isRecording = true;
      this.speechDetected = false;
      this.speechStartTime = null;
      this.silenceStartTime = null;
      this.startTime = Date.now();

      // ── 3. Start Elapsed Timer (Up to 120s safety limit) ──
      this.timerInterval = setInterval(() => {
        const elapsedSec = Math.floor((Date.now() - this.startTime) / 1000);
        if (onTick) onTick(elapsedSec, this.speechDetected);

        // Safety limit: 120 seconds
        if (elapsedSec * 1000 >= this.maxRecordingDurationMs) {
          console.warn('Reached maximum safety recording limit (120s). Auto-stopping.');
          this.stop();
        }
      }, 500);

      // ── 4. Start Voice Activity Detection Loop ──
      this._startVADLoop({ onSpeechStart, onSilenceDetected });

      return this.stream;
    } catch (err) {
      this.isRecording = false;
      this._cleanupVAD();
      this._cleanupTimer();
      this._releaseStream();
      console.error('Microphone initialization failed:', err);
      if (onError) onError(err);
      throw err;
    }
  }

  /**
   * Real-time Voice Activity Detection logic
   */
  _startVADLoop({ onSpeechStart, onSilenceDetected }) {
    const dataArray = new Float32Array(this.analyser.fftSize);
    let calibrationFrames = 0;
    let calibrationSum = 0;

    const checkIntervalMs = 60; // Run check ~16 times per second

    this.vadInterval = setInterval(() => {
      if (!this.isRecording || !this.analyser) return;

      this.analyser.getFloatTimeDomainData(dataArray);

      // Calculate Root Mean Square (RMS) audio energy
      let sumSquares = 0;
      for (let i = 0; i < dataArray.length; i++) {
        sumSquares += dataArray[i] * dataArray[i];
      }
      const rms = Math.sqrt(sumSquares / dataArray.length);

      const now = Date.now();
      const elapsedSinceStart = now - this.startTime;

      // Initial Calibration (First 400ms): measure ambient noise floor
      if (elapsedSinceStart < 400) {
        calibrationSum += rms;
        calibrationFrames++;
        this.noiseFloor = Math.max(0.005, calibrationSum / calibrationFrames);
        this.speechThreshold = Math.max(0.018, this.noiseFloor * 2.3);
        return;
      }

      const isVoiceActive = rms >= this.speechThreshold;

      // ── STATE 1: Waiting for Speech to Begin ──
      if (!this.speechDetected) {
        if (isVoiceActive) {
          if (!this.speechStartTime) {
            this.speechStartTime = now;
          } else if (now - this.speechStartTime >= this.minSpeechDurationMs) {
            // Speech confirmed!
            this.speechDetected = true;
            this.silenceStartTime = null;
            if (onSpeechStart) onSpeechStart();
          }
        } else {
          // Reset speech start timestamp if voice dipped before minimum duration
          this.speechStartTime = null;
        }
        return;
      }

      // ── STATE 2: Speech Active — Tracking End of Speech Silence ──
      if (isVoiceActive) {
        // User is still speaking or resumed speaking after a brief pause
        this.silenceStartTime = null;
      } else {
        // Silence detected
        if (this.silenceStartTime === null) {
          this.silenceStartTime = now;
        } else {
          const silenceDuration = now - this.silenceStartTime;
          if (silenceDuration >= this.silenceThresholdMs) {
            // User finished speaking!
            console.log(`VAD: Silence detected (${silenceDuration}ms >= ${this.silenceThresholdMs}ms). Auto-terminating recording.`);
            if (onSilenceDetected) onSilenceDetected(silenceDuration);
            this.stop();
          }
        }
      }
    }, checkIntervalMs);
  }

  /**
   * Stop recording normally and finalize payload
   */
  stop() {
    if (!this.isRecording || !this.mediaRecorder) return;
    this._cleanupVAD();
    if (this.mediaRecorder.state !== 'inactive') {
      try {
        this.mediaRecorder.stop();
      } catch (e) {
        // Safe guard
      }
    }
  }

  /**
   * Cancel recording without submitting audio
   */
  cancel() {
    this.isCancelled = true;
    this.stop();
  }

  _cleanupVAD() {
    if (this.vadInterval) {
      clearInterval(this.vadInterval);
      this.vadInterval = null;
    }
    if (this.audioContext && this.audioContext.state !== 'closed') {
      try {
        this.audioContext.close();
      } catch (e) {}
      this.audioContext = null;
    }
    this.analyser = null;
  }

  _cleanupTimer() {
    if (this.timerInterval) {
      clearInterval(this.timerInterval);
      this.timerInterval = null;
    }
  }

  _releaseStream() {
    if (this.stream) {
      try {
        this.stream.getTracks().forEach((track) => track.stop());
      } catch (e) {}
      this.stream = null;
    }
  }
}

// Global recorder instance
const voiceRecorder = new VoiceRecorder();
