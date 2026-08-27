// src/components/chat/ChatWidget.jsx
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { supabase } from '../../supabaseClient';
import { useRealtime, useMessageCount } from '../../context/RealtimeContext';
import ChatWindow from './ChatWindow';
import ChatList from './ChatList';
import toast from 'react-hot-toast';
import '../../css/ChatWidget.css';

const ChatWidget = ({ organization, user }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [conversations, setConversations] = useState([]);
  const [selectedConversation, setSelectedConversation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [unreadCount, setUnreadCount] = useState(0);
  const [showStaffList, setShowStaffList] = useState(false);
  const [staffMembers, setStaffMembers] = useState([]);
  const widgetRef = useRef(null);
  const channelRef = useRef(null);
  const { isConnected } = useRealtime();
  const unreadMessageCount = useMessageCount();

  // Debug mount
  useEffect(() => {
    console.log('🔍 ChatWidget mounted');
    console.log('📦 Organization:', organization);
    console.log('👤 User:', user);
    console.log('🔄 isConnected:', isConnected);
  }, [organization, user, isConnected]);

  // Fetch conversations
  const fetchConversations = useCallback(async () => {
    if (!organization || !user) return;
    
    try {
      setLoading(true);
      
      // First get conversations where user is a participant
      const { data: participantData, error: participantError } = await supabase
        .from('conversation_participants')
        .select('conversation_id')
        .eq('user_id', user.id)
        .eq('is_active', true);

      if (participantError) throw participantError;
      
      if (!participantData || participantData.length === 0) {
        setConversations([]);
        setLoading(false);
        return;
      }

      const conversationIds = participantData.map(p => p.conversation_id);

      // Then get the conversations
      const { data: convData, error: convError } = await supabase
        .from('conversations')
        .select(`
          *,
          participants:conversation_participants(
            user_id,
            joined_at,
            is_active
          )
        `)
        .in('id', conversationIds)
        .eq('organization_id', organization.id)
        .order('updated_at', { ascending: false });

      if (convError) throw convError;

      // Get last message for each conversation
      const conversationsWithMessages = await Promise.all(
        (convData || []).map(async (conv) => {
          const { data: msgData, error: msgError } = await supabase
            .from('messages')
            .select('*')
            .eq('conversation_id', conv.id)
            .order('created_at', { ascending: false })
            .limit(1);

          if (msgError) throw msgError;

          return {
            ...conv,
            last_message: msgData?.[0] || null,
            unread_count: 0
          };
        })
      );

      setConversations(conversationsWithMessages);
      
    } catch (error) {
      console.error('Error fetching conversations:', error);
      toast.error('Failed to load conversations');
    } finally {
      setLoading(false);
    }
  }, [organization, user]);

  // Subscribe to messages - FIXED: Callbacks added BEFORE subscribe
  const subscribeToMessages = useCallback(() => {
    // Clean up existing channel first
    if (channelRef.current) {
      try {
        supabase.removeChannel(channelRef.current);
      } catch (err) {
        console.error('Error removing existing channel:', err);
      }
      channelRef.current = null;
    }

    // Create channel with unique name
    const channelName = `chat_widget_${Date.now()}`;
    const channel = supabase.channel(channelName);

    // ✅ IMPORTANT: Add ALL callbacks BEFORE calling .subscribe()
    channel.on(
      'postgres_changes',
      {
        event: 'INSERT',
        schema: 'public',
        table: 'messages'
      },
      (payload) => {
        if (payload.new.receiver_id === user.id) {
          fetchConversations();
          if (!isOpen) {
            toast.success('💬 New message');
          }
        }
      }
    );

    // ✅ Now subscribe after all callbacks are added
    channel.subscribe((status) => {
      console.log(`💬 Chat widget subscription (${channelName}) status:`, status);
    });

    channelRef.current = channel;

    return () => {
      if (channelRef.current) {
        try {
          supabase.removeChannel(channelRef.current);
        } catch (err) {
          console.error('Error removing channel in cleanup:', err);
        }
        channelRef.current = null;
      }
    };
  }, [user, isOpen, fetchConversations]);

  // Effect: Initial fetch and subscription
  useEffect(() => {
    if (user && organization) {
      fetchConversations();
      const cleanup = subscribeToMessages();
      return cleanup;
    }
  }, [user, organization, fetchConversations, subscribeToMessages]);

  // Update unread count
  useEffect(() => {
    setUnreadCount(unreadMessageCount);
  }, [unreadMessageCount]);

  // Close widget on escape key
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape' && isOpen) {
        setIsOpen(false);
      }
    };
    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen]);

  // Cleanup channel on unmount
  useEffect(() => {
    return () => {
      if (channelRef.current) {
        try {
          supabase.removeChannel(channelRef.current);
        } catch (err) {
          console.error('Error removing channel on unmount:', err);
        }
        channelRef.current = null;
      }
    };
  }, []);

  const fetchStaffMembers = async () => {
    try {
      // Get staff members from the organization
      const { data, error } = await supabase
        .from('users')
        .select('id, email, full_name, avatar_url, raw_user_meta_data')
        .eq('raw_user_meta_data->>is_staff', 'true');

      if (error) throw error;
      setStaffMembers(data || []);
      setShowStaffList(true);
    } catch (error) {
      console.error('Error fetching staff:', error);
      toast.error('Failed to load staff members');
    }
  };

  const handleStartConversation = async (staffId) => {
    try {
      // Check if conversation already exists
      let existingConversationId = null;
      
      const { data: userConvs, error: userConvError } = await supabase
        .from('conversation_participants')
        .select('conversation_id')
        .eq('user_id', user.id)
        .eq('is_active', true);

      if (userConvError) throw userConvError;

      if (userConvs && userConvs.length > 0) {
        const convIds = userConvs.map(c => c.conversation_id);
        
        const { data: staffConvs, error: staffConvError } = await supabase
          .from('conversation_participants')
          .select('conversation_id')
          .in('conversation_id', convIds)
          .eq('user_id', staffId)
          .eq('is_active', true);

        if (staffConvError) throw staffConvError;

        if (staffConvs && staffConvs.length > 0) {
          existingConversationId = staffConvs[0].conversation_id;
        }
      }

      if (existingConversationId) {
        setSelectedConversation(existingConversationId);
        setShowStaffList(false);
        setIsOpen(true);
        return;
      }

      // Create new conversation
      const { data: conversation, error: convError } = await supabase
        .from('conversations')
        .insert({
          organization_id: organization.id,
          created_by: user.id,
          is_group: false,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        })
        .select()
        .single();

      if (convError) throw convError;

      // Add participants
      const { error: participantError } = await supabase
        .from('conversation_participants')
        .insert([
          { 
            conversation_id: conversation.id, 
            user_id: user.id,
            joined_at: new Date().toISOString(),
            is_active: true
          },
          { 
            conversation_id: conversation.id, 
            user_id: staffId,
            joined_at: new Date().toISOString(),
            is_active: true
          }
        ]);

      if (participantError) throw participantError;

      await fetchConversations();
      setSelectedConversation(conversation.id);
      setShowStaffList(false);
      setIsOpen(true);
      toast.success('Conversation started!');
      
    } catch (error) {
      console.error('Error starting conversation:', error);
      toast.error('Failed to start conversation');
    }
  };

  const handleSelectConversation = (conversationId) => {
    setSelectedConversation(conversationId);
    setShowStaffList(false);
  };

  const handleBack = () => {
    setSelectedConversation(null);
    setShowStaffList(false);
  };

  const toggleWidget = () => {
    console.log('🔄 Toggle widget clicked, current state:', isOpen);
    setIsOpen(!isOpen);
    if (!isOpen) {
      markAllAsRead();
    }
  };

  const markAllAsRead = async () => {
    try {
      // Get all unread messages for current user
      const { error } = await supabase
        .from('messages')
        .update({ is_read: true, read_at: new Date().toISOString() })
        .eq('receiver_id', user.id)
        .eq('is_read', false);

      if (error) throw error;
      setUnreadCount(0);
      
    } catch (error) {
      console.error('Error marking messages as read:', error);
    }
  };

  if (!organization || !user) {
    console.log('❌ ChatWidget not rendering - missing organization or user');
    return null;
  }

  return (
    <>
      {/* Chat Toggle Button */}
      <button 
        className={`chat-widget-toggle ${isOpen ? 'open' : ''}`}
        onClick={toggleWidget}
        aria-label="Open chat"
        style={{
          position: 'fixed',
          bottom: '24px',
          right: '24px',
          width: '60px',
          height: '60px',
          borderRadius: '50%',
          background: isOpen ? '#ef4444' : '#3b82f6',
          color: 'white',
          border: 'none',
          fontSize: '28px',
          cursor: 'pointer',
          boxShadow: '0 4px 20px rgba(59, 130, 246, 0.4)',
          zIndex: 9999,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          transition: 'all 0.3s ease'
        }}
      >
        {isOpen ? '✕' : '💬'}
        {!isOpen && unreadCount > 0 && (
          <span style={{
            position: 'absolute',
            top: '-4px',
            right: '-4px',
            background: '#ef4444',
            color: 'white',
            fontSize: '12px',
            fontWeight: '700',
            minWidth: '22px',
            height: '22px',
            borderRadius: '50%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            border: '2px solid white'
          }}>
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {/* Chat Widget Window */}
      {isOpen && (
        <div 
          className={`chat-widget-window ${isMinimized ? 'minimized' : ''}`}
          ref={widgetRef}
          style={{
            position: 'fixed',
            bottom: '96px',
            right: '24px',
            width: '380px',
            height: isMinimized ? '52px' : '500px',
            maxHeight: '70vh',
            background: 'white',
            borderRadius: '16px',
            boxShadow: '0 10px 40px rgba(0, 0, 0, 0.2)',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            zIndex: 9998,
            animation: 'slideUp 0.3s ease'
          }}
        >
          {/* Header */}
          <div style={{
            padding: '12px 16px',
            background: '#3b82f6',
            color: 'white',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexShrink: 0
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: '600', fontSize: '14px' }}>
              <span>💬 Messages</span>
              {isConnected && (
                <span style={{
                  fontSize: '10px',
                  padding: '2px 8px',
                  borderRadius: '12px',
                  fontWeight: '500',
                  background: 'rgba(34, 197, 94, 0.2)',
                  color: '#86efac'
                }}>
                  ● Online
                </span>
              )}
            </div>
            <div style={{ display: 'flex', gap: '4px' }}>
              <button 
                onClick={() => setIsMinimized(!isMinimized)}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: 'white',
                  cursor: 'pointer',
                  padding: '4px 8px',
                  borderRadius: '4px',
                  fontSize: '18px',
                  transition: 'background 0.2s'
                }}
                onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.2)'}
                onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
              >
                {isMinimized ? '□' : '−'}
              </button>
              <button 
                onClick={() => setIsOpen(false)}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: 'white',
                  cursor: 'pointer',
                  padding: '4px 8px',
                  borderRadius: '4px',
                  fontSize: '16px',
                  transition: 'background 0.2s'
                }}
                onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.2)'}
                onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
              >
                ✕
              </button>
            </div>
          </div>

          {/* Content */}
          {!isMinimized && (
            <div style={{
              flex: 1,
              overflow: 'hidden',
              display: 'flex',
              flexDirection: 'column',
              background: '#f8fafc'
            }}>
              {selectedConversation ? (
                // Chat Window
                <div style={{
                  flex: 1,
                  display: 'flex',
                  flexDirection: 'column',
                  height: '100%'
                }}>
                  <button 
                    onClick={handleBack}
                    style={{
                      padding: '8px 12px',
                      background: 'transparent',
                      border: 'none',
                      color: '#3b82f6',
                      cursor: 'pointer',
                      fontWeight: '500',
                      fontSize: '13px',
                      textAlign: 'left',
                      transition: 'background 0.2s',
                      flexShrink: 0
                    }}
                    onMouseEnter={(e) => e.currentTarget.style.background = '#f1f5f9'}
                    onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                  >
                    ← Back
                  </button>
                  <ChatWindow 
                    conversationId={selectedConversation}
                    organization={organization}
                    compact={true}
                    onBack={handleBack}
                  />
                </div>
              ) : showStaffList ? (
                // Staff Selection
                <div style={{
                  flex: 1,
                  padding: '12px',
                  overflowY: 'auto'
                }}>
                  <button 
                    onClick={() => setShowStaffList(false)}
                    style={{
                      padding: '8px 12px',
                      background: 'transparent',
                      border: 'none',
                      color: '#3b82f6',
                      cursor: 'pointer',
                      fontWeight: '500',
                      fontSize: '13px',
                      textAlign: 'left'
                    }}
                  >
                    ← Back
                  </button>
                  <h4 style={{ margin: '8px 0 16px', color: '#0f172a', fontSize: '14px' }}>
                    Select a staff member
                  </h4>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {staffMembers.map(staff => (
                      <div 
                        key={staff.id}
                        onClick={() => handleStartConversation(staff.id)}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '12px',
                          padding: '10px 12px',
                          background: 'white',
                          borderRadius: '8px',
                          cursor: 'pointer',
                          transition: 'all 0.2s',
                          border: '1px solid #e2e8f0'
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.background = '#f1f5f9';
                          e.currentTarget.style.borderColor = '#3b82f6';
                          e.currentTarget.style.transform = 'translateX(4px)';
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.background = 'white';
                          e.currentTarget.style.borderColor = '#e2e8f0';
                          e.currentTarget.style.transform = 'translateX(0)';
                        }}
                      >
                        <div style={{
                          width: '40px',
                          height: '40px',
                          borderRadius: '50%',
                          background: '#3b82f6',
                          color: 'white',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontWeight: '600',
                          fontSize: '16px',
                          flexShrink: 0
                        }}>
                          {staff.full_name?.charAt(0) || staff.email?.charAt(0) || 'S'}
                        </div>
                        <div style={{ flex: 1 }}>
                          <div style={{ fontWeight: '600', color: '#0f172a', fontSize: '14px' }}>
                            {staff.full_name || staff.email}
                          </div>
                          <div style={{ fontSize: '12px', color: '#64748b' }}>
                            Support Staff
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                // Chat List
                <>
                  <div style={{
                    padding: '8px 12px',
                    borderBottom: '1px solid #e2e8f0',
                    background: 'white'
                  }}>
                    <button 
                      onClick={fetchStaffMembers}
                      style={{
                        padding: '6px 12px',
                        background: '#3b82f6',
                        color: 'white',
                        border: 'none',
                        borderRadius: '6px',
                        cursor: 'pointer',
                        fontSize: '13px',
                        fontWeight: '500',
                        transition: 'all 0.2s',
                        width: '100%'
                      }}
                      onMouseEnter={(e) => e.currentTarget.style.background = '#2b6cb0'}
                      onMouseLeave={(e) => e.currentTarget.style.background = '#3b82f6'}
                    >
                      ✏️ New Chat
                    </button>
                  </div>
                  <ChatList 
                    conversations={conversations}
                    selectedId={selectedConversation}
                    onSelectConversation={handleSelectConversation}
                    loading={loading}
                    compact={true}
                  />
                </>
              )}
            </div>
          )}
        </div>
      )}
    </>
  );
};

export default ChatWidget;