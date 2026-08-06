// context/RealtimeContext.jsx - Add message subscription

import React, { createContext, useContext, useEffect, useState, useRef } from 'react';
import { supabase } from '../supabaseClient';
import toast from 'react-hot-toast';

// Create contexts
const RealtimeContext = createContext();
const NotificationsContext = createContext();
const DocumentStatusContext = createContext();

// Custom hooks
export const useRealtime = () => useContext(RealtimeContext);
export const useNotifications = () => useContext(NotificationsContext);
export const useDocumentStatus = () => useContext(DocumentStatusContext);

// Message counter hook for unread messages
// Message counter hook for unread messages
export const useMessageCount = () => {
  const [unreadMessageCount, setUnreadMessageCount] = useState(0);
  const { isConnected } = useRealtime();
  const channelRef = useRef(null);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  useEffect(() => {
    if (!isConnected) {
      // Clean up when disconnected
      if (channelRef.current) {
        try {
          supabase.removeChannel(channelRef.current);
        } catch (err) {
          console.error('Error removing channel:', err);
        }
        channelRef.current = null;
      }
      return;
    }

    const fetchUnreadCount = async () => {
      try {
        const { data: { user } } = await supabase.auth.getUser();
        if (!user || !mountedRef.current) return;

        const { count, error } = await supabase
          .from('messages')
          .select('*', { count: 'exact', head: true })
          .eq('receiver_id', user.id)
          .eq('is_read', false);

        if (!error && mountedRef.current) {
          setUnreadMessageCount(count || 0);
        }
      } catch (error) {
        console.error('Error fetching unread count:', error);
      }
    };

    // Initial fetch
    fetchUnreadCount();

    // Force cleanup of any existing channel
    if (channelRef.current) {
      try {
        supabase.removeChannel(channelRef.current);
      } catch (err) {
        console.error('Error cleaning up channel:', err);
      }
      channelRef.current = null;
    }

    // Create channel with a unique name
    const channelName = `msg_count_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const channel = supabase.channel(channelName);

    // Add all callbacks BEFORE subscribing
    channel
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'messages'
        },
        (payload) => {
          console.log('📩 New message detected:', payload);
          fetchUnreadCount();
        }
      )
      .on(
        'postgres_changes',
        {
          event: 'UPDATE',
          schema: 'public',
          table: 'messages'
        },
        (payload) => {
          console.log('✏️ Message updated:', payload);
          fetchUnreadCount();
        }
      );

    // Now subscribe after all callbacks are added
    channel.subscribe((status) => {
      console.log(`📊 Message count subscription (${channelName}) status:`, status);
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
  }, [isConnected]);

  return unreadMessageCount;
};
// Realtime Provider
export function RealtimeProvider({ children, user }) {
  const [isConnected, setIsConnected] = useState(false);
  const [onlineStaff, setOnlineStaff] = useState([]);
  const [socket, setSocket] = useState(null);
  const subscriptionRef = useRef(null);

  useEffect(() => {
    if (!user) {
      console.log('❌ No user provided to RealtimeProvider');
      return;
    }

    console.log('🔄 Setting up Realtime for user:', user.id);

    // Set up Supabase Realtime subscriptions
    const setupRealtime = async () => {
      try {
        // Subscribe to presence (online status)
        const presenceChannel = supabase.channel('presence', {
          config: {
            presence: {
              key: user.id
            }
          }
        });

        presenceChannel
          .on('presence', { event: 'sync' }, () => {
            const state = presenceChannel.presenceState();
            const online = Object.keys(state).filter(key => key !== user.id);
            setOnlineStaff(online);
          })
          .on('presence', { event: 'join' }, ({ key }) => {
            if (key !== user.id) {
              setOnlineStaff(prev => [...prev, key]);
              toast('👤 Staff member came online', {
                icon: 'ℹ️', // Adds an info icon manually
                });
              
            }
          })
          .on('presence', { event: 'leave' }, ({ key }) => {
            setOnlineStaff(prev => prev.filter(id => id !== key));
            
            toast('👤 Staff member went offline', {
                icon: 'ℹ️', // Adds an info icon manually
                });
          })
            .subscribe(async (status) => {
                const connected = status === 'SUBSCRIBED';
                setIsConnected(connected);
                console.log('🔄 Realtime connection status:', status);
                
                if (connected) {
                await presenceChannel.track({
                    user_id: user.id,
                    user_email: user.email,
                    online_at: new Date().toISOString()
                });
                console.log('✅ Presence tracked for user:', user.id);
                }
            });


        subscriptionRef.current = presenceChannel;
        setSocket(presenceChannel);

      } catch (error) {
        console.error('Error setting up realtime:', error);
        setIsConnected(false);
      }
    };

    setupRealtime();

    return () => {
      if (subscriptionRef.current) {
        console.log('🔄 Cleaning up Realtime subscription');
        subscriptionRef.current.unsubscribe();
      }
    };
  }, [user]);

  const sendTyping = (conversationId, isTyping) => {
    if (!socket || !isConnected) return;
    
    socket.send({
      type: 'typing',
      payload: {
        conversation_id: conversationId,
        user_id: user.id,
        is_typing: isTyping
      }
    });
  };

  const sendReadReceipt = (conversationId, messageId) => {
    if (!socket || !isConnected) return;
    
    socket.send({
      type: 'read_receipt',
      payload: {
        conversation_id: conversationId,
        message_id: messageId,
        user_id: user.id
      }
    });
  };

  return (
    <RealtimeContext.Provider value={{
      isConnected,
      onlineStaff,
      socket,
      sendTyping,
      sendReadReceipt
    }}>
      {children}
    </RealtimeContext.Provider>
  );
}

// Notifications Provider
export function NotificationsProvider({ children, user }) {
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    if (!user) return;

    // Fetch initial notifications
    const fetchNotifications = async () => {
      try {
        const { data, error } = await supabase
          .from('notifications')
          .select('*')
          .eq('user_id', user.id)
          .order('created_at', { ascending: false })
          .limit(50);

        if (error) throw error;
        setNotifications(data || []);
        setUnreadCount(data?.filter(n => !n.is_read).length || 0);
      } catch (error) {
        console.error('Error fetching notifications:', error);
      }
    };

    fetchNotifications();

    // Subscribe to new notifications
    const notificationChannel = supabase
      .channel('notifications')
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'notifications',
          filter: `user_id=eq.${user.id}`
        },
        (payload) => {
          const newNotification = payload.new;
          setNotifications(prev => [newNotification, ...prev]);
          setUnreadCount(prev => prev + 1);
          toast(`🔔 ${newNotification.title}`, {icon: 'ℹ️', });
          
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(notificationChannel);
    };
  }, [user]);

  const markAsRead = async (notificationId) => {
    try {
      const { error } = await supabase
        .from('notifications')
        .update({ is_read: true })
        .eq('id', notificationId);

      if (error) throw error;

      setNotifications(prev =>
        prev.map(n =>
          n.id === notificationId ? { ...n, is_read: true } : n
        )
      );
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (error) {
      console.error('Error marking notification as read:', error);
    }
  };

  const markAllAsRead = async () => {
    try {
      const { error } = await supabase
        .from('notifications')
        .update({ is_read: true })
        .eq('user_id', user.id)
        .eq('is_read', false);

      if (error) throw error;

      setNotifications(prev =>
        prev.map(n => ({ ...n, is_read: true }))
      );
      setUnreadCount(0);
      toast.success('All notifications marked as read');
    } catch (error) {
      console.error('Error marking all as read:', error);
    }
  };

  const clearAll = async () => {
    try {
      const { error } = await supabase
        .from('notifications')
        .delete()
        .eq('user_id', user.id);

      if (error) throw error;

      setNotifications([]);
      setUnreadCount(0);
      toast.success('All notifications cleared');
    } catch (error) {
      console.error('Error clearing notifications:', error);
    }
  };

  return (
    <NotificationsContext.Provider value={{
      notifications,
      unreadCount,
      markAsRead,
      markAllAsRead,
      clearAll
    }}>
      {children}
    </NotificationsContext.Provider>
  );
}

// Document Status Provider
export function DocumentStatusProvider({ children, organization }) {
  const [documents, setDocuments] = useState([]);
  const [statusCounts, setStatusCounts] = useState({
    pending: 0,
    processing: 0,
    extracted: 0,
    approved: 0,
    rejected: 0
  });

  // ✅ Listen for organization changes and update subscriptions
  useEffect(() => {
    if (!organization?.id) {
      console.log('DocumentStatusProvider: No organization provided, waiting...');
      return;
    }

    console.log('DocumentStatusProvider: Setting up for organization:', organization.id);

    const fetchDocuments = async () => {
      try {
        const { data, error } = await supabase
          .from('documents')
          .select('*')
          .eq('organization_id', organization.id)
          .order('created_at', { ascending: false });

        if (error) throw error;

        setDocuments(data || []);
        updateStatusCounts(data || []);
      } catch (error) {
        console.error('Error fetching documents:', error);
      }
    };

    fetchDocuments();

    const documentChannel = supabase
      .channel(`documents_${organization.id}`)
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'documents',
          filter: `organization_id=eq.${organization.id}`
        },
        (payload) => {
          if (payload.eventType === 'INSERT') {
            setDocuments(prev => [payload.new, ...prev]);
          } else if (payload.eventType === 'UPDATE') {
            setDocuments(prev =>
              prev.map(doc =>
                doc.id === payload.new.id ? payload.new : doc
              )
            );
          } else if (payload.eventType === 'DELETE') {
            setDocuments(prev =>
              prev.filter(doc => doc.id !== payload.old.id)
            );
          }
          // Update counts
          setDocuments(current => {
            updateStatusCounts(current);
            return current;
          });
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(documentChannel);
    };
  }, [organization?.id]); // ✅ Only re-run when organization ID changes

  const updateStatusCounts = (docs) => {
    const counts = {
      pending: 0,
      processing: 0,
      extracted: 0,
      approved: 0,
      rejected: 0
    };

    docs.forEach(doc => {
      if (counts[doc.status] !== undefined) {
        counts[doc.status]++;
      }
    });

    setStatusCounts(counts);
  };

  return (
    <DocumentStatusContext.Provider value={{
      documents,
      statusCounts
    }}>
      {children}
    </DocumentStatusContext.Provider>
  );
}
// Main provider that wraps everything
export function RealtimeProviderWrapper({ children, user, organization = null }) {
  return (
    <RealtimeProvider user={user}>
      <NotificationsProvider user={user}>
        <DocumentStatusProvider organization={organization}>
          {children}
        </DocumentStatusProvider>
      </NotificationsProvider>
    </RealtimeProvider>
  );
}

