// src/components/chat/ChatList.jsx
import React, { useState, useEffect, useCallback } from 'react';
import { supabase } from '../../supabaseClient';
import { useRealtime } from '../../context/RealtimeContext';

function ChatList({ 
  conversations, 
  selectedId, 
  onSelectConversation,
  loading,
  compact = false 
}) {
  const [currentUser, setCurrentUser] = useState(null);
  const [participantNames, setParticipantNames] = useState({});
  const { onlineStaff } = useRealtime();

  useEffect(() => {
    const getCurrentUser = async () => {
      const { data: { user } } = await supabase.auth.getUser();
      setCurrentUser(user);
    };
    getCurrentUser();
  }, []);

  // ✅ Wrap getParticipantName in useCallback
  const getParticipantName = useCallback(async (conversation) => {
    if (!currentUser) return 'Unknown';
    
    try {
      const otherParticipant = conversation.participants?.find(
        p => p.user_id !== currentUser.id
      );
      
      if (!otherParticipant) return 'Unknown';
      
      const { data, error } = await supabase
        .from('users')
        .select('email, full_name, raw_user_meta_data')
        .eq('id', otherParticipant.user_id)
        .single();
      
      if (error) throw error;
      
      return data?.full_name || data?.email || 'Unknown';
    } catch (error) {
      console.error('Error getting participant name:', error);
      return 'Unknown';
    }
  }, [currentUser]);

  // ✅ Add getParticipantName to dependency array
  useEffect(() => {
    const loadParticipantNames = async () => {
      if (!currentUser || !conversations.length) return;
      
      const names = {};
      for (const conv of conversations) {
        const name = await getParticipantName(conv);
        names[conv.id] = name;
      }
      setParticipantNames(names);
    };
    
    loadParticipantNames();
  }, [conversations, currentUser, getParticipantName]);

  const getOnlineStatus = (conversation) => {
    if (!currentUser) return false;
    const otherParticipant = conversation.participants?.find(
      p => p.user_id !== currentUser.id
    );
    return onlineStaff.includes(otherParticipant?.user_id);
  };

  if (loading) {
    return <div className="chat-list-loading">Loading conversations...</div>;
  }

  return (
    <div className={`chat-list ${compact ? 'compact' : ''}`}>
      <div className="chat-list-items">
        {conversations.length === 0 ? (
          <div className="chat-empty">
            <p>No conversations yet</p>
            {!compact && (
              <button className="btn-primary">
                Start New Chat
              </button>
            )}
          </div>
        ) : (
          conversations.map(conv => (
            <div
              key={conv.id}
              className={`chat-list-item ${selectedId === conv.id ? 'active' : ''}`}
              onClick={() => onSelectConversation(conv.id)}
            >
              <div className="chat-avatar">
                {getOnlineStatus(conv) && <span className="online-dot" />}
                <span className="avatar-letter">
                  {participantNames[conv.id]?.charAt(0).toUpperCase() || 'U'}
                </span>
              </div>
              <div className="chat-info">
                <div className="chat-name">{participantNames[conv.id] || 'Loading...'}</div>
                {!compact && (
                  <div className="chat-last-message">
                    {conv.last_message?.content || 'No messages yet'}
                  </div>
                )}
              </div>
              {conv.unread_count > 0 && (
                <span className="unread-badge">{conv.unread_count}</span>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default ChatList;