import React from 'react';

const WS_LABELS = {
  connecting: '🟡 Connecting...',
  open: '🟢 Connected',
  reconnecting: '🟡 Reconnecting...',
  closed: '🔴 Disconnected',
  error: '🔴 Error',
};

const VAD_LABELS = {
  idle: '🎤 Idle',
  listening: '👂 Listening',
  recording: '🔴 Recording',
  processing: '⚙️ Processing',
  muted: '🔇 Agent speaking',
};

const SHOW_RETRY = new Set(['closed', 'error']);

/**
 * Displays WebSocket and VAD status indicators.
 * Shows a retry button when the connection is lost.
 */
export default function StatusBar({ wsStatus, vadStatus, onReconnect }) {
  return (
    <div className="status-bar">
      <span className="status-bar__item">{WS_LABELS[wsStatus] ?? wsStatus}</span>
      {SHOW_RETRY.has(wsStatus) && (
        <button className="status-bar__retry" onClick={onReconnect}>
          ↺ Retry
        </button>
      )}
      <span className="status-bar__item">{VAD_LABELS[vadStatus] ?? vadStatus}</span>
    </div>
  );
}
