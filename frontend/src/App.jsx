import React, { useState, useCallback } from 'react';
import ChatWindow from './components/ChatWindow.jsx';
import StatusBar from './components/StatusBar.jsx';
import ModelSelector from './components/ModelSelector.jsx';
import { useWebSocket } from './hooks/useWebSocket.js';
import { useVAD } from './hooks/useVAD.js';
import { useAudioPlayer } from './hooks/useAudioPlayer.js';

/**
 * Root application component.
 * Wires together WebSocket, VAD, audio playback, and model selection hooks.
 */
export default function App() {
  const [messages, setMessages] = useState([]);
  const [isStarted, setIsStarted] = useState(false);
  const [selectedModel, setSelectedModel] = useState({ provider: 'ollama', model: 'llama3' });

  const addMessage = useCallback((role, text) => {
    setMessages(prev => [...prev, { id: Date.now() + Math.random(), role, text }]);
  }, []);

  const { playAudio, stopAudio, isPlaying } = useAudioPlayer();

  // Build WebSocket URL with selected provider + model as query params.
  const wsUrl = `/ws?provider=${selectedModel.provider}&model=${encodeURIComponent(selectedModel.model)}`;

  const { sendAudio, status: wsStatus, reconnect } = useWebSocket({
    url: wsUrl,
    onMessage: useCallback((meta, audioBytes) => {
      if (meta.transcript) addMessage('user', meta.transcript);
      if (meta.response) addMessage('assistant', meta.response);
      if (meta.error) addMessage('error', `Error: ${meta.error}`);
      if (audioBytes && audioBytes.byteLength > 0) playAudio(audioBytes);
    }, [addMessage, playAudio]),
  });

  const { vadStatus } = useVAD({
    onSpeechEnd: sendAudio,
    enabled: !isPlaying,
    active: isStarted,
  });

  const handleToggle = useCallback(() => {
    if (isStarted) {
      stopAudio();
      setIsStarted(false);
    } else {
      setIsStarted(true);
    }
  }, [isStarted, stopAudio]);

  const derivedVadStatus = !isStarted ? 'idle' : isPlaying ? 'muted' : vadStatus;

  return (
    <div className="app">
      <header className="app-header">
        <h1>🎙 Conversation Agent</h1>
        <ModelSelector
          selectedModel={selectedModel}
          onSelect={setSelectedModel}
          disabled={isStarted}
        />
      </header>
      <StatusBar wsStatus={wsStatus} vadStatus={derivedVadStatus} onReconnect={reconnect} />
      <ChatWindow messages={messages} />
      <div className="controls">
        <button
          className={`control-btn ${isStarted ? 'control-btn--active' : ''}`}
          onClick={handleToggle}
          disabled={wsStatus !== 'open'}
          title={wsStatus !== 'open' ? 'Connect to backend first' : isStarted ? 'Pause conversation' : 'Start conversation'}
        >
          {isStarted ? '⏸ Pause' : '▶ Start'}
        </button>
      </div>
    </div>
  );
}
