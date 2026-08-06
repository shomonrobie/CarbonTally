// admin/src/components/admin/AdminNotificationBell.jsx
import React, { useState } from 'react';
import { useRealtime } from '../../context/RealtimeContext';

function AdminNotificationBell() {
  const { notifications, unreadCount, markAsRead, isConnected } = useRealtime();
  const [isOpen, setIsOpen] = useState(false);

  const getNotificationIcon = (type) => {
    const icons = {
      'document_uploaded': '📤',
      'review_assigned': '📌',
      'review_completed': '✅',
      'sla_breach': '🚨',
      'system_alert': '⚠️',
      'user_joined': '👤',
      'organization_created': '🏢',
    };
    return icons[type] || '🔔';
  };

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 rounded-lg hover:bg-gray-100 transition-colors"
      >
        <span className="text-xl">🔔</span>
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
        {!isConnected && (
          <span className="absolute -bottom-1 -right-1 w-3 h-3 bg-yellow-500 rounded-full border-2 border-white" />
        )}
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-96 bg-white rounded-lg shadow-xl border border-gray-200 z-50 max-h-96 overflow-hidden">
          <div className="p-4 border-b border-gray-200 flex justify-between items-center">
            <h3 className="font-semibold">Notifications</h3>
            <span className="text-sm text-gray-500">
              {unreadCount} unread
            </span>
          </div>
          
          <div className="overflow-y-auto max-h-80">
            {notifications.length === 0 ? (
              <div className="p-8 text-center text-gray-500">
                <span className="text-2xl">📭</span>
                <p className="mt-2">No notifications</p>
              </div>
            ) : (
              notifications.slice(0, 50).map((notification) => (
                <div
                  key={notification.id}
                  className={`p-4 border-b border-gray-100 hover:bg-gray-50 cursor-pointer transition-colors ${
                    !notification.is_read ? 'bg-blue-50' : ''
                  }`}
                  onClick={() => {
                    if (!notification.is_read) {
                      markAsRead(notification.id);
                    }
                    if (notification.link) {
                      window.location.href = notification.link;
                    }
                  }}
                >
                  <div className="flex items-start gap-3">
                    <span className="text-xl">{getNotificationIcon(notification.type)}</span>
                    <div className="flex-1 min-w-0">
                      <div className="font-medium text-gray-900">
                        {notification.title}
                      </div>
                      <div className="text-sm text-gray-600 truncate">
                        {notification.message}
                      </div>
                      <div className="text-xs text-gray-400 mt-1">
                        {new Date(notification.created_at).toLocaleString()}
                      </div>
                    </div>
                    {!notification.is_read && (
                      <span className="w-2 h-2 bg-blue-500 rounded-full flex-shrink-0 mt-2" />
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default AdminNotificationBell;