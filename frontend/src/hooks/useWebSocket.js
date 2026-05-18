import { useEffect, useRef, useState, useCallback } from 'react';

const RECONNECT_BASE_MS = 1000;
const RECONNECT_MAX_MS = 30000;

/**
 * Manages a WebSocket connection with automatic reconnection and binary+JSON protocol.
 *
 * Protocol:
 *  - Send:    raw audio bytes (ArrayBuffer)
 *  - Receive: JSON text (AgentResponse metadata), then optional binary audio bytes
 *
 * Fixes:
 *  - React StrictMode: intentionalClose flag prevents spurious 'closed' status
 *    when the effect cleanup tears down the first of the two double-invoked effects.
 *  - Auto-reconnect: exponential backoff (1s → 2s → 4s … capped at 30s) on
 *    unexpected disconnection.
 */
export function useWebSocket({ url, onMessage }) {
  const [status, setStatus] = useState('connecting');
  const wsRef = useRef(null);
  const pendingMetaRef = useRef(null);
  const intentionalCloseRef = useRef(false);
  const retryCountRef = useRef(0);
  const retryTimerRef = useRef(null);
  const reconnectRef = useRef(null);

  const connect = useCallback(() => {
    intentionalCloseRef.current = false;
    setStatus('connecting');

    const wsUrl = `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}${url}`;
    const ws = new WebSocket(wsUrl);
    ws.binaryType = 'arraybuffer';
    wsRef.current = ws;

    ws.onopen = () => {
      retryCountRef.current = 0;
      setStatus('open');
    };

    ws.onerror = () => {
      if (!intentionalCloseRef.current) setStatus('error');
    };

    ws.onclose = () => {
      if (intentionalCloseRef.current) return;
      const delay = Math.min(RECONNECT_BASE_MS * 2 ** retryCountRef.current, RECONNECT_MAX_MS);
      retryCountRef.current += 1;
      setStatus('reconnecting');
      retryTimerRef.current = setTimeout(() => reconnectRef.current?.(), delay);
    };

    ws.onmessage = (event) => {
      if (typeof event.data === 'string') {
        pendingMetaRef.current = JSON.parse(event.data);
        if (!pendingMetaRef.current.audio_available) {
          onMessage(pendingMetaRef.current, null);
          pendingMetaRef.current = null;
        }
      } else {
        if (pendingMetaRef.current) {
          onMessage(pendingMetaRef.current, event.data);
          pendingMetaRef.current = null;
        }
      }
    };
  }, [url, onMessage]);

  // Keep reconnectRef in sync so the closure inside onclose always calls the latest connect.
  reconnectRef.current = connect;

  useEffect(() => {
    connect();
    return () => {
      intentionalCloseRef.current = true;
      clearTimeout(retryTimerRef.current);
      wsRef.current?.close();
    };
  }, [connect]);

  const sendAudio = useCallback((audioBuffer) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(audioBuffer);
    }
  }, []);

  /** Manually trigger an immediate reconnection attempt. */
  const reconnect = useCallback(() => {
    clearTimeout(retryTimerRef.current);
    intentionalCloseRef.current = true;
    wsRef.current?.close();
    retryCountRef.current = 0;
    connect();
  }, [connect]);

  return { sendAudio, status, reconnect };
}
