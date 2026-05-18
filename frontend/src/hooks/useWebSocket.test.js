import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useWebSocket } from '../hooks/useWebSocket.js';

// --- WebSocket mock -------------------------------------------------------

class MockWebSocket {
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  constructor(url) {
    this.url = url;
    this.binaryType = 'arraybuffer';
    this.readyState = MockWebSocket.OPEN;
    this.sentMessages = [];
    MockWebSocket._instances.push(this);
  }

  send(data) { this.sentMessages.push(data); }

  close() {
    this.readyState = MockWebSocket.CLOSED;
    this.onclose?.({ code: 1000 });
  }

  triggerOpen() { this.onopen?.(); }
  triggerError() { this.onerror?.({}); }
  triggerClose() {
    this.readyState = MockWebSocket.CLOSED;
    this.onclose?.({ code: 1006 });
  }
  triggerJsonMessage(data) { this.onmessage?.({ data: JSON.stringify(data) }); }
  triggerBinaryMessage(data) { this.onmessage?.({ data }); }
}
MockWebSocket._instances = [];

function latestWs() {
  return MockWebSocket._instances[MockWebSocket._instances.length - 1];
}

// -------------------------------------------------------------------------

describe('useWebSocket', () => {
  let originalWebSocket;
  // Stable mock — using vi.fn() ensures the same function reference across renders,
  // preventing connect useCallback from recreating and re-triggering the effect.
  const stableOnMessage = vi.fn();

  beforeEach(() => {
    MockWebSocket._instances = [];
    stableOnMessage.mockReset();
    originalWebSocket = globalThis.WebSocket;
    globalThis.WebSocket = MockWebSocket;
  });

  afterEach(() => {
    globalThis.WebSocket = originalWebSocket;
  });

  it('starts with connecting status', () => {
    const { result } = renderHook(() =>
      useWebSocket({ url: '/ws', onMessage: stableOnMessage })
    );
    expect(result.current.status).toBe('connecting');
  });

  it('transitions to open when WebSocket connects', async () => {
    const { result } = renderHook(() =>
      useWebSocket({ url: '/ws', onMessage: stableOnMessage })
    );
    await act(async () => { latestWs().triggerOpen(); });
    expect(result.current.status).toBe('open');
  });

  it('transitions to reconnecting on unexpected close', async () => {
    const { result } = renderHook(() =>
      useWebSocket({ url: '/ws', onMessage: stableOnMessage })
    );
    await act(async () => { latestWs().triggerOpen(); });
    expect(result.current.status).toBe('open');

    await act(async () => { latestWs().triggerClose(); });
    expect(result.current.status).toBe('reconnecting');
  });

  it('transitions to error on onerror', async () => {
    const { result } = renderHook(() =>
      useWebSocket({ url: '/ws', onMessage: stableOnMessage })
    );
    await act(async () => { latestWs().triggerOpen(); });

    await act(async () => { latestWs().triggerError(); });
    expect(result.current.status).toBe('error');
  });

  it('sendAudio sends buffer when socket is OPEN', async () => {
    const { result } = renderHook(() =>
      useWebSocket({ url: '/ws', onMessage: stableOnMessage })
    );
    await act(async () => { latestWs().triggerOpen(); });

    const buf = new ArrayBuffer(8);
    act(() => { result.current.sendAudio(buf); });
    expect(latestWs().sentMessages).toContain(buf);
  });

  it('onMessage called with metadata when audio_available is false', async () => {
    renderHook(() => useWebSocket({ url: '/ws', onMessage: stableOnMessage }));
    await act(async () => { latestWs().triggerOpen(); });

    act(() => {
      latestWs().triggerJsonMessage({ transcript: 'hello', audio_available: false });
    });

    expect(stableOnMessage).toHaveBeenCalledWith(
      expect.objectContaining({ transcript: 'hello' }),
      null
    );
  });

  it('onMessage called with metadata + binary when audio follows JSON', async () => {
    renderHook(() => useWebSocket({ url: '/ws', onMessage: stableOnMessage }));
    await act(async () => { latestWs().triggerOpen(); });

    const audioBuf = new ArrayBuffer(16);
    act(() => {
      latestWs().triggerJsonMessage({ transcript: 'hi', audio_available: true });
      latestWs().triggerBinaryMessage(audioBuf);
    });

    expect(stableOnMessage).toHaveBeenCalledWith(
      expect.objectContaining({ transcript: 'hi' }),
      audioBuf
    );
  });

  it('reconnect() creates a new connection', async () => {
    const { result } = renderHook(() =>
      useWebSocket({ url: '/ws', onMessage: stableOnMessage })
    );
    await act(async () => { latestWs().triggerOpen(); });
    expect(result.current.status).toBe('open');

    const wsCountBefore = MockWebSocket._instances.length;
    await act(async () => { result.current.reconnect(); });

    expect(MockWebSocket._instances.length).toBeGreaterThan(wsCountBefore);
    expect(result.current.status).toBe('connecting');
  });
});
