// frontend/src/services/NotificationService.js
import toast from 'react-hot-toast';

class NotificationService {
  constructor() {
    this.permission = 'default';
    this.registration = null;
    this.swUrl = '/sw.js';
  }

  // Request permission
  async requestPermission() {
    try {
      if (!('Notification' in window)) {
        console.warn('This browser does not support notifications');
        return false;
      }

      const permission = await Notification.requestPermission();
      this.permission = permission;
      
      if (permission === 'granted') {
        await this.registerServiceWorker();
        return true;
      }
      
      return false;
    } catch (error) {
      console.error('Error requesting notification permission:', error);
      return false;
    }
  }

  // Register Service Worker
  async registerServiceWorker() {
    try {
      if ('serviceWorker' in navigator) {
        this.registration = await navigator.serviceWorker.register('/sw.js');
        console.log('✅ Service Worker registered');
        return this.registration;
      }
    } catch (error) {
      console.error('Service Worker registration failed:', error);
    }
    return null;
  }

  // Send notification (in-app toast)
  sendInApp(notification) {
    const { title, message, type, link } = notification;
    
    // Show toast notification
    toast.custom((t) => (
      <div 
        className={`notification-toast ${type || 'info'}`}
        onClick={() => {
          toast.dismiss(t.id);
          if (link) window.location.href = link;
        }}
      >
        <div className="toast-icon">
          {this.getNotificationIcon(type)}
        </div>
        <div className="toast-content">
          <div className="toast-title">{title}</div>
          <div className="toast-message">{message}</div>
        </div>
        <button 
          className="toast-close"
          onClick={(e) => {
            e.stopPropagation();
            toast.dismiss(t.id);
          }}
        >
          ✕
        </button>
      </div>
    ), { duration: 5000 });
  }

  // Send push notification (browser)
  async sendPush(notification) {
    try {
      if (this.permission !== 'granted') {
        console.warn('Notification permission not granted');
        return false;
      }

      const { title, message, icon, link, type } = notification;

      // Show browser notification
      const browserNotification = new Notification(title, {
        body: message,
        icon: icon || '/favicon.ico',
        tag: `${type}-${Date.now()}`,
        data: { link, type },
        requireInteraction: true,
        silent: false,
        vibrate: [200, 100, 200]
      });

      browserNotification.onclick = (event) => {
        event.preventDefault();
        browserNotification.close();
        
        if (link) {
          window.focus();
          window.location.href = link;
        }
      };

      browserNotification.onclose = () => {
        // Mark notification as read in backend
        this.markAsRead(notification.id);
      };

      return true;
      
    } catch (error) {
      console.error('Error sending push notification:', error);
      return false;
    }
  }

  // Mark notification as read in backend
  async markAsRead(notificationId) {
    try {
      const token = await getToken();
      await fetch(`${API_URL}/api/notifications/${notificationId}/read`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
    } catch (error) {
      console.error('Error marking notification as read:', error);
    }
  }

  // Get notification icon
  getNotificationIcon(type) {
    const icons = {
      'document_uploaded': '📤',
      'document_processed': '⚙️',
      'document_extracted': '📋',
      'document_approved': '✅',
      'document_rejected': '❌',
      'document_verified': '🔍',
      'message_received': '💬',
      'review_assigned': '📌',
      'review_completed': '✔️',
      'emissions_logged': '📊',
      'report_generated': '📄',
      'staff_joined': '👤',
      'system_alert': '⚠️',
      'sla_breach': '🚨'
    };
    return icons[type] || '🔔';
  }

  // Get notification color
  getNotificationColor(type) {
    const colors = {
      'document_uploaded': '#3b82f6',
      'document_processed': '#8b5cf6',
      'document_extracted': '#06b6d4',
      'document_approved': '#22c55e',
      'document_rejected': '#ef4444',
      'document_verified': '#f59e0b',
      'message_received': '#3b82f6',
      'review_assigned': '#f59e0b',
      'review_completed': '#22c55e',
      'system_alert': '#ef4444',
      'sla_breach': '#dc2626'
    };
    return colors[type] || '#94a3b8';
  }

  // Check for new notifications (polling fallback)
  async checkNotifications() {
    try {
      const token = await getToken();
      const response = await fetch(`${API_URL}/api/notifications?limit=5`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (!response.ok) throw new Error('Failed to fetch notifications');
      
      const data = await response.json();
      const unread = data.notifications?.filter(n => !n.is_read) || [];
      
      for (const notification of unread) {
        // Show in-app notification
        this.sendInApp({
          title: notification.title,
          message: notification.message,
          type: notification.type,
          link: notification.link
        });
        
        // Show push notification if permission granted
        if (this.permission === 'granted') {
          this.sendPush({
            id: notification.id,
            title: notification.title,
            message: notification.message,
            type: notification.type,
            link: notification.link
          });
        }
      }
      
      return unread.length;
      
    } catch (error) {
      console.error('Error checking notifications:', error);
      return 0;
    }
  }
}

export const notificationService = new NotificationService();