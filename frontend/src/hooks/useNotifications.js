// frontend/src/hooks/useNotifications.js
import { useState, useEffect, useCallback } from 'react';
import { supabase } from '../supabaseClient';
import { notificationService } from '../services/NotificationService';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const getToken = async () => {
  const { data: { session } } = await supabase.auth.getSession();
  return session?.access_token || localStorage.getItem('access_token');
};

export function useNotifications() {
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [pushEnabled, setPushEnabled] = useState(false);

  // Check push notification permission
  useEffect(() => {
    const checkPush = async () => {
      const enabled = await notificationService.requestPermission();
      setPushEnabled(enabled);
    };
    checkPush();
  }, []);

  // Load notifications
  useEffect(() => {
    fetchNotifications();
  }, []);

  // Realtime subscription
  useEffect(() => {
    const channel = supabase.channel('notifications');
    
    channel.on('postgres_changes', {
      event: 'INSERT',
      schema: 'public',
      table: 'notifications'
    }, (payload) => {
      const notification = payload.new;
      
      // Update state
      setNotifications(prev => [notification, ...prev]);
      if (!notification.is_read) {
        setUnreadCount(prev => prev + 1);
      }
      
      // Show notification
      showNotification(notification);
    });
    
    channel.subscribe();
    
    return () => {
      channel.unsubscribe();
    };
  }, []);

  const fetchNotifications = async () => {
    try {
      const token = await getToken();
      // ISC-6 — the V3 notification surface is the authoritative endpoint; the
      // legacy `/api/notifications` route was removed (404 on every page).
      const response = await fetch(`${API_URL}/api/v3/notifications?limit=50`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!response.ok) throw new Error('Failed to fetch notifications');

      const data = await response.json();
      const items = data.notifications || [];
      setNotifications(items);
      setUnreadCount(items.filter((n) => !n.is_read).length);

    } catch (error) {
      console.error('Error fetching notifications:', error);
    }
  };

  const showNotification = useCallback((notification) => {
    // In-app notification
    notificationService.sendInApp({
      title: notification.title,
      message: notification.message,
      type: notification.type,
      link: notification.link
    });

    // Push notification
    if (pushEnabled) {
      notificationService.sendPush({
        id: notification.id,
        title: notification.title,
        message: notification.message,
        type: notification.type,
        link: notification.link
      });
    }
  }, [pushEnabled]);

  const markAsRead = useCallback(async (notificationId) => {
    try {
      const token = await getToken();
      await fetch(`${API_URL}/api/v3/notifications/${notificationId}/read`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      setNotifications(prev => 
        prev.map(n => n.id === notificationId ? { ...n, is_read: true } : n)
      );
      setUnreadCount(prev => Math.max(0, prev - 1));
      
    } catch (error) {
      console.error('Error marking notification as read:', error);
    }
  }, []);

  const markAllAsRead = useCallback(async () => {
    try {
      const token = await getToken();
      await fetch(`${API_URL}/api/v3/notifications/read-all`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      setNotifications(prev => 
        prev.map(n => ({ ...n, is_read: true }))
      );
      setUnreadCount(0);
      
    } catch (error) {
      console.error('Error marking all as read:', error);
    }
  }, []);

  const clearAll = useCallback(() => {
    setNotifications([]);
    setUnreadCount(0);
  }, []);

  return {
    notifications,
    unreadCount,
    pushEnabled,
    markAsRead,
    markAllAsRead,
    clearAll,
    refresh: fetchNotifications
  };
}