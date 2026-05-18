import React from 'react';

/**
 * A single chat message bubble.
 * Role determines alignment and color.
 */
export default function MessageBubble({ role, text }) {
  return (
    <div className={`message message--${role}`}>
      <span className="message__label">
        {role === 'user' ? 'You' : role === 'assistant' ? 'Agent' : '⚠️'}
      </span>
      <p className="message__text">{text}</p>
    </div>
  );
}
