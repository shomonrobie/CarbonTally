// src/components/chat/ChatList.jsx
import React, { useState, useEffect, useCallback } from 'react';
import { supabase } from '../../supabaseClient';
import { useRealtime } from '../../context/RealtimeContext';
import { listMembers } from '../../v3/api';

function ChatList({ 
  conversations, 
  selectedId, 
  onSelectConversation,
  loading,
  compact = false,
  organization
}) {
  const [currentUser, setCurrentUser] = useState(null);
  const [participantNames, setParticipantNames] = useState({});
  const [memberNames, setMemberNames] = useState({});
  const { onlineStaff } = useRealtime();

  useEffect(() => {
    const getCurrentUser = async () => {
      const { data: { user } } = await supabase.auth.getUser();
      setCurrentUser(user);
    };
    getCurrentUser();
  }, []);

  // P8-FIN-01b (D-9) — participant identity is resolved through the authorised,
  // org-scoped member projection (GET /api/v3/organizations/{org_id}/members).
  // `users` stays self-scoped: no direct peer read of `users` is performed.
  useEffect(() => {
    let active = true;

    const loadMemberNames = async () => {
      const orgId = organization?.id;
      if (!orgId) return;
      try {
        const data = await listMembers(orgId);
        if (!active) return;
        const map = {};
        (data?.members || []).forEach((member) => {
          // Field names follow the projection contract of
          // backend/data/organizations.py::_row_to_member_with_email:
          // email / first_name / last_name.
          const name = [member.first_name, member.last_name]
            .filter(Boolean)
            .join(' ')
            .trim();
          map[member.user_id] = name || member.email || null;
        });
        setMemberNames(map);
      } catch (error) {
        // Identity is presentational only — an unavailable projection must never
        // break the conversation list; the generic fallback is preserved.
        console.warn('Member identity unavailable:', error?.message || error);
      }
    };

    loadMemberNames();
    return () => { active = false; };
  }, [organization?.id]);

  // ✅ Wrap getParticipantName in useCallback
  const getParticipantName = useCallback(async (conversation) => {
    if (!currentUser) return 'Unknown';
    
    const otherParticipant = conversation.participants?.find(
      p => p.user_id !== currentUser.id
    );

    if (!otherParticipant) return 'Unknown';

    // P8-FIN-01b (D-9): authorised org-member projection only; unresolved => generic fallback.
    return memberNames[otherParticipant.user_id] || 'Unknown';
  }, [currentUser, memberNames]);

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