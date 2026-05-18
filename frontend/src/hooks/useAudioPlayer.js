import { useRef, useState, useCallback } from 'react';

/**
 * Decodes and plays WAV audio received as an ArrayBuffer.
 *
 * Guarantees only one clip plays at a time: any currently playing audio is
 * stopped before the new clip starts. Exposes `isPlaying` so other hooks
 * (e.g. useVAD) can pause while the agent is speaking.
 */
export function useAudioPlayer() {
  const audioCtxRef = useRef(null);
  const currentSourceRef = useRef(null);
  const [isPlaying, setIsPlaying] = useState(false);

  const getAudioContext = () => {
    if (!audioCtxRef.current || audioCtxRef.current.state === 'closed') {
      audioCtxRef.current = new AudioContext();
    }
    return audioCtxRef.current;
  };

  const playAudio = useCallback(async (arrayBuffer) => {
    try {
      // Stop any currently playing audio before starting the new clip.
      if (currentSourceRef.current) {
        try { currentSourceRef.current.stop(); } catch (_) { /* already ended */ }
        currentSourceRef.current = null;
      }

      const ctx = getAudioContext();
      const audioBuffer = await ctx.decodeAudioData(arrayBuffer.slice(0));
      const source = ctx.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(ctx.destination);

      source.onended = () => {
        currentSourceRef.current = null;
        setIsPlaying(false);
      };

      currentSourceRef.current = source;
      setIsPlaying(true);
      source.start();
    } catch (err) {
      console.error('Audio playback error:', err);
      setIsPlaying(false);
    }
  }, []);

  const stopAudio = useCallback(() => {
    if (currentSourceRef.current) {
      try { currentSourceRef.current.stop(); } catch (_) { /* already ended */ }
      currentSourceRef.current = null;
    }
    setIsPlaying(false);
  }, []);

  return { playAudio, stopAudio, isPlaying };
}
