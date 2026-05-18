import { useEffect, useRef, useState } from 'react';
import { encodeWAV } from '../services/audioUtils.js';

const SAMPLE_RATE = 16000;
const ENERGY_THRESHOLD = 0.01;
const SILENCE_DURATION_MS = 1500;
const MIN_SPEECH_DURATION_MS = 300;

/**
 * Voice Activity Detection using Web Audio API.
 *
 * @param {function} onSpeechEnd - Called with WAV ArrayBuffer when speech finishes.
 * @param {boolean}  enabled     - When false, audio chunks are ignored and any
 *                                 in-progress recording is cancelled (e.g. while agent speaks).
 * @param {boolean}  active      - Controls mic acquisition. When false the microphone is
 *                                 released entirely. Toggling this starts/stops the session.
 */
export function useVAD({ onSpeechEnd, enabled = true, active = true }) {
  const [vadStatus, setVadStatus] = useState('idle');

  // Refs keep latest prop values accessible inside effect closures without
  // adding them to the dependency array (which would cause mic restarts).
  const enabledRef = useRef(enabled);
  enabledRef.current = enabled;
  const onSpeechEndRef = useRef(onSpeechEnd);
  onSpeechEndRef.current = onSpeechEnd;

  const recordingRef = useRef(false);
  const samplesRef = useRef([]);
  const silenceTimerRef = useRef(null);
  const speechStartRef = useRef(null);

  // Cancel any in-progress recording when muted mid-speech.
  useEffect(() => {
    if (!enabled && recordingRef.current) {
      clearTimeout(silenceTimerRef.current);
      recordingRef.current = false;
      samplesRef.current = [];
      setVadStatus('listening');
    }
  }, [enabled]);

  // Acquire / release the microphone based on the active prop.
  useEffect(() => {
    if (!active) {
      setVadStatus('idle');
      return;
    }

    let cancelled = false;
    let stream = null;
    let audioCtx = null;

    async function start() {
      try {
        stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
        if (cancelled) { stream.getTracks().forEach(t => t.stop()); return; }

        audioCtx = new AudioContext({ sampleRate: SAMPLE_RATE });
        const source = audioCtx.createMediaStreamSource(stream);
        await audioCtx.audioWorklet.addModule(createWorkletBlob());
        const processor = new AudioWorkletNode(audioCtx, 'vad-processor');

        processor.port.onmessage = (e) => {
          if (!enabledRef.current) return;
          handleAudioChunk(e.data.rms, e.data.samples);
        };

        source.connect(processor);
        processor.connect(audioCtx.destination);
        setVadStatus('listening');
      } catch (err) {
        console.error('VAD init error:', err);
        setVadStatus('idle');
      }
    }

    function handleAudioChunk(rms, samples) {
      if (rms > ENERGY_THRESHOLD) {
        if (!recordingRef.current) {
          recordingRef.current = true;
          samplesRef.current = [];
          speechStartRef.current = Date.now();
          setVadStatus('recording');
        }
        clearTimeout(silenceTimerRef.current);
        samplesRef.current.push(...samples);

        silenceTimerRef.current = setTimeout(() => {
          if (recordingRef.current) {
            const duration = Date.now() - (speechStartRef.current ?? 0);
            recordingRef.current = false;
            if (duration >= MIN_SPEECH_DURATION_MS && samplesRef.current.length > 0) {
              const wav = encodeWAV(new Float32Array(samplesRef.current), SAMPLE_RATE);
              onSpeechEndRef.current(wav);
            }
            samplesRef.current = [];
            setVadStatus('listening');
          }
        }, SILENCE_DURATION_MS);
      } else if (recordingRef.current) {
        samplesRef.current.push(...samples);
      }
    }

    start();

    return () => {
      cancelled = true;
      clearTimeout(silenceTimerRef.current);

      // If mid-speech when paused, send what was captured rather than discarding it.
      if (recordingRef.current && samplesRef.current.length > 0) {
        const duration = Date.now() - (speechStartRef.current ?? 0);
        if (duration >= MIN_SPEECH_DURATION_MS) {
          const wav = encodeWAV(new Float32Array(samplesRef.current), SAMPLE_RATE);
          onSpeechEndRef.current(wav);
        }
      }

      recordingRef.current = false;
      samplesRef.current = [];
      stream?.getTracks().forEach(t => t.stop());
      audioCtx?.close();
    };
  }, [active]);

  return { vadStatus };
}

/** Creates an AudioWorklet blob URL that sends RMS + samples to the main thread. */
function createWorkletBlob() {
  const code = `
    class VadProcessor extends AudioWorkletProcessor {
      process(inputs) {
        const input = inputs[0]?.[0];
        if (!input) return true;
        let sum = 0;
        for (let i = 0; i < input.length; i++) sum += input[i] * input[i];
        const rms = Math.sqrt(sum / input.length);
        this.port.postMessage({ rms, samples: Array.from(input) });
        return true;
      }
    }
    registerProcessor('vad-processor', VadProcessor);
  `;
  const blob = new Blob([code], { type: 'application/javascript' });
  return URL.createObjectURL(blob);
}
