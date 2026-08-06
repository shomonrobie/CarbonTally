// src/components/chat/ChatWindow.jsx
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { supabase } from '../../supabaseClient';
import ChatMessage from './ChatMessage';
import ChatInput from './ChatInput';
import toast from 'react-hot-toast';

function ChatWindow({ 
  conversationId, 
  organization, 
  compact = false,
  onBack 
}) {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [participants, setParticipants] = useState([]);
  const [currentUser, setCurrentUser] = useState(null);
  const [participantName, setParticipantName] = useState('Chat');
  const messagesEndRef = useRef(null);
  const chatSubscriptionRef = useRef(null); // ✅ Changed from chatSubscription to chatSubscriptionRef

  useEffect(() => {
    const getCurrentUser = async () => {
      const { data: { user } } = await supabase.auth.getUser();
      setCurrentUser(user);
    };
    getCurrentUser();
  }, []);

  // ✅ Wrap fetchMessages in useCallback
  const fetchMessages = useCallback(async () => {
    if (!conversationId) return;
    
    try {
      setLoading(true);
      
      const { data, error } = await supabase
        .from('messages')
        .select('*')
        .eq('conversation_id', conversationId)
        .order('created_at', { ascending: true });

      if (error) throw error;
      
      setMessages(data || []);
      
      if (currentUser) {
        const unreadMessages = data
          ?.filter(msg => !msg.is_read && msg.receiver_id === currentUser.id)
          .map(msg => msg.id) || [];

        if (unreadMessages.length > 0) {
          await supabase
            .from('messages')
            .update({ is_read: true, read_at: new Date().toISOString() })
            .in('id', unreadMessages);
        }
      }
      
    } catch (error) {
      console.error('Error fetching messages:', error);
      toast.error('Failed to load messages');
    } finally {
      setLoading(false);
    }
  }, [conversationId, currentUser]);

  // ✅ Wrap fetchParticipants in useCallback
  const fetchParticipants = useCallback(async () => {
    try {
      const { data, error } = await supabase
        .from('conversation_participants')
        .select('user_id')
        .eq('conversation_id', conversationId)
        .eq('is_active', true);

      if (error) throw error;
      setParticipants(data || []);
      
    } catch (error) {
      console.error('Error fetching participants:', error);
    }
  }, [conversationId]);

  // ✅ Wrap subscribeToNewMessages in useCallback
  const subscribeToNewMessages = useCallback(() => {
    // Clean up old subscription
    if (chatSubscriptionRef.current) {
      chatSubscriptionRef.current.unsubscribe();
      chatSubscriptionRef.current = null;
    }

    const subscription = supabase
      .channel(`chat_${conversationId}`)
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'messages',
          filter: `conversation_id=eq.${conversationId}`
        },
        (payload) => {
          setMessages(prev => [...prev, payload.new]);
          
          if (currentUser && payload.new.receiver_id === currentUser.id) {
            supabase
              .from('messages')
              .update({ is_read: true, read_at: new Date().toISOString() })
              .eq('id', payload.new.id)
              .then(() => {});
          }
        }
      )
      .subscribe();

    chatSubscriptionRef.current = subscription;
    
    return () => {
      if (chatSubscriptionRef.current) {
        chatSubscriptionRef.current.unsubscribe();
        chatSubscriptionRef.current = null;
      }
    };
  }, [conversationId, currentUser]);

  // ✅ Add all dependencies
  useEffect(() => {
    if (conversationId) {
      fetchMessages();
      fetchParticipants();
      const unsubscribe = subscribeToNewMessages();
      return () => {
        if (unsubscribe) unsubscribe();
        if (chatSubscriptionRef.current) {
          chatSubscriptionRef.current.unsubscribe();
          chatSubscriptionRef.current = null;
        }
      };
    }
  }, [conversationId, fetchMessages, fetchParticipants, subscribeToNewMessages]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // ✅ Wrap getParticipantName in useCallback
  const getParticipantName = useCallback(async () => {
    if (!currentUser || !participants.length) return 'Chat';
    const otherParticipant = participants.find(p => p.user_id !== currentUser.id);
    
    if (!otherParticipant) return 'Chat';
    
    try {
      const { data, error } = await supabase
        .from('users')
        .select('full_name, email')
        .eq('id', otherParticipant.user_id)
        .single();
      
      if (error) throw error;
      return data?.full_name || data?.email || 'Chat';
    } catch (error) {
      return 'Chat';
    }
  }, [currentUser, participants]);

  // ✅ Add getParticipantName to dependency array
  useEffect(() => {
    getParticipantName().then(setParticipantName);
  }, [getParticipantName]);

  const scrollToBottom = () => {
    setTimeout(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, 100);
  };

  const handleSendMessage = async (content) => {
    if (!content.trim() || !conversationId) return;
    
    try {
      const { data: { user } } = await supabase.auth.getUser();
      
      // Get all participants to send to everyone
      const { data: participantsData, error: partError } = await supabase
        .from('conversation_participants')
        .select('user_id')
        .eq('conversation_id', conversationId)
        .eq('is_active', true);

      if (partError) throw partError;

      // Send message to each participant (except sender)
      const messagesToInsert = participantsData
        .filter(p => p.user_id !== user.id)
        .map(p => ({
          conversation_id: conversationId,
          sender_id: user.id,
          receiver_id: p.user_id,
          content: content.trim(),
          is_read: false,
          created_at: new Date().toISOString()
        }));

      if (messagesToInsert.length === 0) {
        toast.error('No participants to send message to');
        return;
      }

      const { data, error } = await supabase
        .from('messages')
        .insert(messagesToInsert)
        .select();

      if (error) throw error;
      
      // Update conversation timestamp
      await supabase
        .from('conversations')
        .update({ updated_at: new Date().toISOString() })
        .eq('id', conversationId);
      
      // Add messages to local state
      setMessages(prev => [...prev, ...data]);
      
    } catch (error) {
      console.error('Error sending message:', error);
      toast.error('Failed to send message');
    }
  };

  const handleTyping = (isTyping) => {
    // Implement typing indicator if needed
  };

  if (!conversationId) {
    return (
      <div className="chat-empty-state" style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        color: '#94a3b8',
        padding: '2rem'
      }}>
        <span style={{ fontSize: '3rem', marginBottom: '1rem' }}>💬</span>
        <h3 style={{ margin: 0, color: '#0f172a' }}>Select a conversation</h3>
        <p style={{ margin: '0.5rem 0 0' }}>Choose a conversation to start chatting</p>
      </div>
    );
  }

  if (loading) {
    return <div className="chat-loading" style={{
      flex: 1,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      color: '#94a3b8',
      padding: '2rem'
    }}>Loading messages...</div>;
  }

  return (
    <div className={`chat-window ${compact ? 'compact' : ''}`} style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100%'
    }}>
      {/* Compact header with back button */}
      {compact && onBack && (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          padding: '8px 12px',
          borderBottom: '1px solid #e2e8f0',
          background: 'white',
          flexShrink: 0
        }}>
          <button 
            onClick={onBack}
            style={{
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              fontSize: '16px',
              padding: '4px 8px',
              color: '#3b82f6',
              fontWeight: '500'
            }}
          >
            ← Back
          </button>
          <span style={{
            fontWeight: '600',
            marginLeft: '8px',
            fontSize: '14px'
          }}>
            {participantName}
          </span>
        </div>
      )}
      
      <div className="chat-messages" style={{
        flex: 1,
        overflowY: 'auto',
        padding: compact ? '8px 12px' : '1rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.5rem',
        background: '#fafbfc',
        maxHeight: compact ? '300px' : 'none'
      }}>
        {messages.map((message, index) => (
          <ChatMessage 
            key={message.id || index} 
            message={message}
            isOwn={currentUser && message.sender_id === currentUser.id}
          />
        ))}
        <div ref={messagesEndRef} />
      </div>
      
      <ChatInput 
        onSendMessage={handleSendMessage}
        onTyping={handleTyping}
        isConnected={true}
        compact={compact}
      />
    </div>
  );
}

export default ChatWindow;