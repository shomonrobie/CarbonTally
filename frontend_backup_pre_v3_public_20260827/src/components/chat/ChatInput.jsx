// src/components/chat/ChatInput.jsx
import React, { useState, useRef, useEffect } from 'react';
import toast from 'react-hot-toast';

function ChatInput({ 
  onSendMessage, 
  onTyping, 
  isConnected,
  placeholder = "Type a message...",
  compact = false
}) {
  const [message, setMessage] = useState('');
  const [isSending, setIsSending] = useState(false);
  const textareaRef = useRef(null);
  const typingTimeoutRef = useRef(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px';
    }
  }, [message]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!message.trim()) return;
    if (!isConnected) {
      toast.error('You are offline. Please check your connection.');
      return;
    }
    
    setIsSending(true);
    
    try {
      await onSendMessage(message.trim());
      setMessage('');
    } catch (error) {
      console.error('Error sending message:', error);
      toast.error('Failed to send message');
    } finally {
      setIsSending(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleChange = (e) => {
    const value = e.target.value;
    setMessage(value);
    
    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
    }
    
    if (value.length > 0) {
      onTyping?.(true);
    }
    
    typingTimeoutRef.current = setTimeout(() => {
      onTyping?.(false);
    }, 2000);
  };

  return (
    <div className={`chat-input-container ${compact ? 'compact' : ''}`} style={{
      padding: compact ? '8px 12px' : '1rem',
      borderTop: '1px solid #e2e8f0',
      background: 'white'
    }}>
      <form onSubmit={handleSubmit} className="chat-input-form" style={{
        display: 'flex',
        gap: '0.5rem',
        alignItems: 'flex-end'
      }}>
        <textarea
          ref={textareaRef}
          value={message}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          placeholder={isConnected ? placeholder : '🔴 Offline'}
          disabled={!isConnected || isSending}
          rows={1}
          className="chat-input-textarea"
          style={{
            flex: 1,
            padding: compact ? '6px 10px' : '0.5rem 0.75rem',
            border: '1px solid #e2e8f0',
            borderRadius: '8px',
            resize: 'none',
            fontFamily: 'inherit',
            fontSize: compact ? '13px' : '0.95rem',
            lineHeight: '1.4',
            minHeight: compact ? '32px' : '40px',
            maxHeight: compact ? '80px' : '120px',
            transition: 'border-color 0.2s'
          }}
        />
        
        <button
          type="submit"
          className="send-button"
          disabled={!isConnected || isSending || !message.trim()}
          style={{
            padding: compact ? '4px 8px' : '0.5rem 1rem',
            background: '#3b82f6',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer',
            fontSize: compact ? '14px' : '1.2rem',
            transition: 'all 0.2s',
            minHeight: compact ? '32px' : '40px',
            minWidth: compact ? '36px' : '48px',
            opacity: (!isConnected || isSending || !message.trim()) ? 0.6 : 1
          }}
        >
          {isSending ? '⏳' : '📤'}
        </button>
      </form>
      
      {!isConnected && (
        <div className="connection-warning" style={{
          marginTop: '0.5rem',
          padding: '0.5rem',
          background: '#fef3c7',
          borderRadius: '6px',
          color: '#92400e',
          fontSize: '0.85rem',
          textAlign: 'center'
        }}>
          ⚠️ You are offline. Please check your connection.
        </div>
      )}
    </div>
  );
}

// ✅ Add default export
export default ChatInput;