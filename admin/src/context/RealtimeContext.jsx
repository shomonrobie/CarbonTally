// admin/src/context/RealtimeContext.jsx
import React, { createContext, useContext, useEffect, useRef, useState } from 'react';
import { supabase } from '../supabaseClient';

const RealtimeContext = createContext(null);

export function RealtimeProvider({ children, user }) {
  const [isConnected, setIsConnected] = useState(false);
  const [onlineStaff, setOnlineStaff] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const managerRef = useRef(null);

  useEffect(() => {
    if (!user) return;

    const manager = {
      supabase,
      channels: new Map(),
      isConnected: false,
    };

    managerRef.current = manager;

    // Connect to admin channel
    const adminChannel = supabase.channel('admin:global');
    
    adminChannel.on('postgres_changes', {
      event: 'INSERT',
      schema: 'public',
      table: 'notifications',
      filter: `user_id=eq.${user.id}`
    }, (payload) => {
      setNotifications(prev => [payload.new, ...prev]);
      if (!payload.new.is_read) {
        setUnreadCount(prev => prev + 1);
        showAdminNotification(payload.new);
      }
    });

    adminChannel.on('postgres_changes', {
      event: 'UPDATE',
      schema: 'public',
      table: 'manual_review_queue'
    }, (payload) => {
      // Update queue counts
      window.dispatchEvent(new CustomEvent('queue-updated', { detail: payload }));
    });

    adminChannel.on('postgres_changes', {
      event: 'UPDATE',
      schema: 'public',
      table: 'customer_documents'
    }, (payload) => {
      // Update document status
      window.dispatchEvent(new CustomEvent('document-updated', { detail: payload }));
    });

    adminChannel.subscribe((status) => {
      setIsConnected(status === 'SUBSCRIBED');
      manager.isConnected = status === 'SUBSCRIBED';
    });

    // Staff presence
    const presenceChannel = supabase.channel('staff:presence');
    
    presenceChannel.on('presence', { event: 'sync' }, () => {
      const state = presenceChannel.presenceState();
      setOnlineStaff(Object.keys(state));
    });

    presenceChannel.subscribe();

    manager.channels.set('admin', adminChannel);
    manager.channels.set('presence', presenceChannel);

    return () => {
      adminChannel.unsubscribe();
      presenceChannel.unsubscribe();
    };
  }, [user]);

  const showAdminNotification = (notification) => {
    // Show toast notification
    if (window.showToast) {
      window.showToast({
        title: notification.title,
        message: notification.message,
        type: notification.type || 'info',
      });
    }
  };

  const markAsRead = async (notificationId) => {
    try {
      const token = await getToken();
      await fetch(`${API_URL}/api/notifications/${notificationId}/read`, {
        method: 'PUT',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      setNotifications(prev => 
        prev.map(n => n.id === notificationId ? { ...n, is_read: true } : n)
      );
      setUnreadCount(prev => Math.max(0, prev - 1));
      
    } catch (error) {
      console.error('Error marking notification as read:', error);
    }
  };

  const value = {
    isConnected,
    onlineStaff,
    notifications,
    unreadCount,
    markAsRead,
  };

  return (
    <RealtimeContext.Provider value={value}>
      {children}
    </RealtimeContext.Provider>
  );
}

export function useRealtime() {
  const context = useContext(RealtimeContext);
  if (!context) {
    throw new Error('useRealtime must be used within a RealtimeProvider');
  }
  return context;
}