// src/components/chat/ChatHeader.jsx
import React from 'react';

function ChatHeader({ participants, onlineStaff, isConnected }) {
  const getParticipantName = () => {
    const otherParticipant = participants?.find(p => 
      !onlineStaff.includes(p.user_id)
    );
    return otherParticipant?.full_name || otherParticipant?.email || 'Unknown';
  };

  return (
    <div className="chat-header" style={{
      padding: '1rem',
      borderBottom: '1px solid #e2e8f0',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      background: 'white'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <span style={{ fontWeight: '600' }}>
          {participants?.length > 0 ? getParticipantName() : 'Chat'}
        </span>
        {isConnected && (
          <span style={{
            fontSize: '0.75rem',
            color: '#22c55e',
            background: '#dcfce7',
            padding: '0.15rem 0.5rem',
            borderRadius: '12px'
          }}>
            ● Online
          </span>
        )}
      </div>
      <div style={{ fontSize: '0.8rem', color: '#64748b' }}>
        {participants?.length || 0} participant{participants?.length !== 1 ? 's' : ''}
      </div>
    </div>
  );
}

// ✅ Add default export
export default ChatHeader;