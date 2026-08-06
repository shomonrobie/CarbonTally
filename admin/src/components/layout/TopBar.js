// admin/src/components/layout/TopBar.jsx
import React, { useState, useRef, useEffect } from 'react';
import { 
  FaBell, 
  FaSearch, 
  FaBars,
  FaCheck,
  FaTimes,
  FaCircle,
  FaUser
} from 'react-icons/fa';
import { useAuth } from '../../context/AuthContext';
import { useRealtime } from '../../context/RealtimeContext';

const TopBar = ({ sidebarOpen, setSidebarOpen }) => {
  const { user } = useAuth();
  const { isConnected, unreadCount, notifications, markAsRead } = useRealtime();
  const [isNotificationOpen, setIsNotificationOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const notificationRef = useRef(null);
  const buttonRef = useRef(null);

  // Close notification dropdown on click outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (
        notificationRef.current && 
        !notificationRef.current.contains(event.target) &&
        buttonRef.current && 
        !buttonRef.current.contains(event.target)
      ) {
        setIsNotificationOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const getNotificationIcon = (type) => {
    const icons = {
      'document_uploaded': '📤',
      'document_processed': '⚙️',
      'document_extracted': '📋',
      'document_approved': '✅',
      'document_rejected': '❌',
      'document_verified': '🔍',
      'review_assigned': '📌',
      'review_completed': '✔️',
      'sla_breach': '🚨',
      'system_alert': '⚠️',
      'user_joined': '👤',
      'organization_created': '🏢',
    };
    return icons[type] || '🔔';
  };

  const getNotificationColor = (type) => {
    const colors = {
      'document_uploaded': 'border-blue-500',
      'document_processed': 'border-purple-500',
      'document_extracted': 'border-cyan-500',
      'document_approved': 'border-green-500',
      'document_rejected': 'border-red-500',
      'document_verified': 'border-yellow-500',
      'review_assigned': 'border-yellow-500',
      'review_completed': 'border-green-500',
      'sla_breach': 'border-red-500',
      'system_alert': 'border-red-500',
    };
    return colors[type] || 'border-gray-300';
  };

  const formatTime = (timestamp) => {
    const now = new Date();
    const then = new Date(timestamp);
    const diff = now - then;
    
    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    if (diff < 604800000) return `${Math.floor(diff / 86400000)}d ago`;
    return then.toLocaleDateString();
  };

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      // Navigate to search results or filter content
      console.log('Searching for:', searchQuery);
    }
  };

  const handleNotificationClick = (notification) => {
    if (!notification.is_read) {
      markAsRead(notification.id);
    }
    // Navigate to the relevant page
    if (notification.link) {
      window.location.href = notification.link;
    }
    setIsNotificationOpen(false);
  };

  return (
    <header className="bg-white border-b border-gray-200 h-16 flex items-center px-6 sticky top-0 z-30">
      {/* Left side */}
      <div className="flex items-center gap-4 flex-1">
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="lg:hidden p-2 rounded-lg hover:bg-gray-100 transition-colors"
        >
          <FaBars className="text-xl" />
        </button>
        
        {/* Live Status Indicator */}
        <div className={`hidden sm:flex items-center gap-2 px-2 py-1 rounded-lg text-xs ${
          isConnected ? 'text-green-600' : 'text-yellow-600'
        }`}>
          <span className={`w-1.5 h-1.5 rounded-full ${
            isConnected ? 'bg-green-500 animate-pulse' : 'bg-yellow-500'
          }`} />
          <span>{isConnected ? 'Live' : 'Connecting...'}</span>
        </div>

        {/* Search */}
        <form onSubmit={handleSearch} className="relative hidden md:block flex-1 max-w-md">
          <FaSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm" />
          <input
            type="text"
            placeholder="Search reviews, organizations, users..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9 pr-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none w-full text-sm"
          />
        </form>
      </div>

      {/* Right side */}
      <div className="flex items-center gap-3 ml-auto">
        {/* Notifications */}
        <div className="relative">
          <button
            ref={buttonRef}
            onClick={() => setIsNotificationOpen(!isNotificationOpen)}
            className="p-2 rounded-lg hover:bg-gray-100 transition-colors relative"
          >
            <FaBell className="text-xl text-gray-600" />
            {unreadCount > 0 && (
              <span className="absolute -top-0.5 -right-0.5 min-w-[20px] h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center px-1.5 font-bold">
                {unreadCount > 99 ? '99+' : unreadCount}
              </span>
            )}
            {!isConnected && (
              <span className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 bg-yellow-500 rounded-full border-2 border-white" />
            )}
          </button>

          {/* Notification Dropdown */}
          {isNotificationOpen && (
            <div 
              ref={notificationRef}
              className="absolute right-0 mt-2 w-96 bg-white rounded-lg shadow-xl border border-gray-200 z-50 max-h-[480px] overflow-hidden"
            >
              <div className="p-4 border-b border-gray-200 flex justify-between items-center bg-gray-50">
                <h3 className="font-semibold text-sm flex items-center gap-2">
                  <span>🔔</span>
                  Notifications
                  {unreadCount > 0 && (
                    <span className="bg-red-100 text-red-600 text-xs px-2 py-0.5 rounded-full">
                      {unreadCount} new
                    </span>
                  )}
                </h3>
                <div className="flex gap-2">
                  {unreadCount > 0 && (
                    <button 
                      onClick={() => {
                        notifications.forEach(n => {
                          if (!n.is_read) markAsRead(n.id);
                        });
                      }}
                      className="text-xs text-blue-600 hover:text-blue-800"
                    >
                      Mark all read
                    </button>
                  )}
                </div>
              </div>
              
              <div className="overflow-y-auto max-h-80">
                {notifications.length === 0 ? (
                  <div className="p-8 text-center text-gray-500">
                    <span className="text-3xl block mb-2">📭</span>
                    <p className="text-sm">No notifications yet</p>
                  </div>
                ) : (
                  notifications.slice(0, 50).map((notification) => (
                    <div
                      key={notification.id}
                      onClick={() => handleNotificationClick(notification)}
                      className={`p-4 border-b border-gray-100 hover:bg-gray-50 cursor-pointer transition-colors ${
                        !notification.is_read ? 'bg-blue-50/50' : ''
                      }`}
                    >
                      <div className="flex items-start gap-3">
                        <div className={`text-2xl flex-shrink-0 ${getNotificationColor(notification.type)}`}>
                          {getNotificationIcon(notification.type)}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-start justify-between gap-2">
                            <div className="font-medium text-sm text-gray-900">
                              {notification.title}
                            </div>
                            {!notification.is_read && (
                              <span className="w-2 h-2 bg-blue-500 rounded-full flex-shrink-0 mt-1.5" />
                            )}
                          </div>
                          <div className="text-sm text-gray-600 mt-0.5 line-clamp-2">
                            {notification.message}
                          </div>
                          <div className="flex items-center gap-2 mt-1.5">
                            <span className="text-xs text-gray-400">
                              {formatTime(notification.created_at)}
                            </span>
                            {notification.type && (
                              <span className="text-xs px-1.5 py-0.5 bg-gray-100 text-gray-600 rounded">
                                {notification.type.replace('_', ' ')}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>

              {notifications.length > 0 && (
                <div className="p-2 border-t border-gray-200 text-center bg-gray-50">
                  <a 
                    href="/admin/notifications" 
                    className="text-sm text-blue-600 hover:text-blue-800"
                    onClick={() => setIsNotificationOpen(false)}
                  >
                    View all notifications →
                  </a>
                </div>
              )}
            </div>
          )}
        </div>

        {/* User */}
        <div className="flex items-center gap-3 border-l border-gray-200 pl-3">
          <div className="text-right hidden sm:block">
            <p className="text-sm font-medium text-gray-700">
              {user?.email?.split('@')[0] || 'User'}
            </p>
            <p className="text-xs text-gray-500 flex items-center gap-1">
              <span className={`w-1.5 h-1.5 rounded-full ${
                isConnected ? 'bg-green-500' : 'bg-yellow-500'
              }`} />
              {isConnected ? 'Online' : 'Offline'}
            </p>
          </div>
          <div className="w-9 h-9 rounded-full bg-primary-100 text-primary-600 flex items-center justify-center font-medium text-sm">
            {user?.email?.[0]?.toUpperCase() || 'U'}
          </div>
        </div>
      </div>
    </header>
  );
};

export default TopBar;