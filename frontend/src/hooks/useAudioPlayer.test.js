import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { useAudioPlayer } from '../hooks/useAudioPlayer.js';

// --- AudioContext mock ----------------------------------------------------

class MockAudioBufferSourceNode {
  constructor() {
    this.buffer = null;
    this.onended = null;
    this._connected = false;
    this._started = false;
    this._stopped = false;
  }
  connect() { this._connected = true; }
  start() {
    this._started = true;
    // Simulate audio ending shortly after start
    setTimeout(() => this.onended?.(), 50);
  }
  stop() { this._stopped = true; }
}

class MockAudioContext {
  constructor() {
    this.state = 'running';
    this.destination = {};
    this._decodeResult = null;
    MockAudioContext._instances.push(this);
  }

  async decodeAudioData(buffer) {
    if (this._decodeResult === 'error') throw new Error('decode failed');
    return { duration: 1.0, _buffer: buffer };
  }

  createBufferSource() {
    const node = new MockAudioBufferSourceNode();
    this._lastSource = node;
    return node;
  }
}
MockAudioContext._instances = [];

// -------------------------------------------------------------------------

describe('useAudioPlayer', () => {
  let originalAudioContext;

  beforeEach(() => {
    vi.useFakeTimers({ shouldAdvanceTime: false });
    MockAudioContext._instances = [];
    originalAudioContext = globalThis.AudioContext;
    globalThis.AudioContext = MockAudioContext;
  });

  afterEach(() => {
    vi.useRealTimers();
    globalThis.AudioContext = originalAudioContext;
  });

  it('isPlaying starts as false', () => {
    const { result } = renderHook(() => useAudioPlayer());
    expect(result.current.isPlaying).toBe(false);
  });

  it('playAudio sets isPlaying to true', async () => {
    const { result } = renderHook(() => useAudioPlayer());

    await act(async () => {
      result.current.playAudio(new ArrayBuffer(16));
    });

    expect(result.current.isPlaying).toBe(true);
  });

  it('stopAudio sets isPlaying to false', async () => {
    const { result } = renderHook(() => useAudioPlayer());

    await act(async () => {
      result.current.playAudio(new ArrayBuffer(16));
    });

    act(() => {
      result.current.stopAudio();
    });

    expect(result.current.isPlaying).toBe(false);
  });

  it('stopAudio is safe to call when nothing is playing', () => {
    const { result } = renderHook(() => useAudioPlayer());
    expect(() => {
      act(() => { result.current.stopAudio(); });
    }).not.toThrow();
    expect(result.current.isPlaying).toBe(false);
  });

  it('isPlaying returns to false after audio ends', async () => {
    const { result } = renderHook(() => useAudioPlayer());

    await act(async () => {
      result.current.playAudio(new ArrayBuffer(16));
    });

    expect(result.current.isPlaying).toBe(true);

    // Simulate audio ending
    const ctx = MockAudioContext._instances[MockAudioContext._instances.length - 1];
    await act(async () => {
      ctx._lastSource?.onended?.();
    });

    expect(result.current.isPlaying).toBe(false);
  });

  it('sets isPlaying to false when decodeAudioData throws', async () => {
    // Override decodeAudioData to throw on the already-created context
    MockAudioContext.prototype.decodeAudioData = async () => {
      throw new Error('decode failed');
    };

    const { result } = renderHook(() => useAudioPlayer());

    await act(async () => {
      result.current.playAudio(new ArrayBuffer(16));
    });

    expect(result.current.isPlaying).toBe(false);

    // Restore
    MockAudioContext.prototype.decodeAudioData = async (buffer) => ({ duration: 1.0, _buffer: buffer });
  });
});
