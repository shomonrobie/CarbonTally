// src/components/chat/ChatMessage.jsx
import React from 'react';

function ChatMessage({ message, isOwn }) {
  if (!message) return null;

  return (
    <div className={`chat-message ${isOwn ? 'own-message' : 'other-message'}`} style={{
      maxWidth: '70%',
      padding: '0.6rem 1rem',
      borderRadius: '12px',
      marginBottom: '0.25rem',
      wordWrap: 'break-word',
      alignSelf: isOwn ? 'flex-end' : 'flex-start',
      background: isOwn ? '#3b82f6' : 'white',
      color: isOwn ? 'white' : '#0f172a',
      borderBottomRightRadius: isOwn ? '4px' : '12px',
      borderBottomLeftRadius: isOwn ? '12px' : '4px',
      boxShadow: isOwn ? 'none' : '0 1px 3px rgba(0,0,0,0.1)'
    }}>
      <div className="message-content">
        <div className="message-text" style={{
          fontSize: '0.95rem',
          lineHeight: '1.4'
        }}>
          {message.content}
        </div>
        <div className="message-time" style={{
          fontSize: '0.65rem',
          opacity: 0.7,
          marginTop: '0.25rem',
          textAlign: 'right'
        }}>
          {new Date(message.created_at).toLocaleTimeString([], { 
            hour: '2-digit', 
            minute: '2-digit' 
          })}
        </div>
      </div>
    </div>
  );
}

// ✅ Add default export
export default ChatMessage;