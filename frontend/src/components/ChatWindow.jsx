import React, { useEffect, useRef } from 'react';
import MessageBubble from './MessageBubble.jsx';

/**
 * Scrollable list of conversation messages.
 * Auto-scrolls to bottom when new messages arrive.
 */
export default function ChatWindow({ messages }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <main className="chat-window">
      {messages.length === 0 && (
        <p className="chat-empty">Start speaking — I'm listening...</p>
      )}
      {messages.map(msg => (
        <MessageBubble key={msg.id} role={msg.role} text={msg.text} />
      ))}
      <div ref={bottomRef} />
    </main>
  );
}
