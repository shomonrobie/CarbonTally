import React, { useState } from 'react';
import { FaBell, FaSearch, FaBars } from 'react-icons/fa';
import { useAuth } from '../../context/AuthContext';

const TopBar = ({ sidebarOpen, setSidebarOpen }) => {
  const { user } = useAuth();
  const [notifications] = useState([
    { id: 1, message: 'New review #247 added', time: '2 mins ago', read: false },
    { id: 2, message: 'Review #245 completed', time: '5 mins ago', read: false },
    { id: 3, message: 'TechCorp Ltd joined', time: '1 hour ago', read: true },
  ]);

  const unreadCount = notifications.filter(n => !n.read).length;

  return (
    <header className="bg-white border-b border-gray-200 h-16 flex items-center px-6">
      {/* Left side */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="lg:hidden p-2 rounded-lg hover:bg-gray-100 transition-colors"
        >
          <FaBars className="text-xl" />
        </button>
        <div className="relative hidden sm:block">
          <FaSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            placeholder="Search..."
            className="pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none w-64"
          />
        </div>
      </div>

      {/* Right side */}
      <div className="flex items-center gap-4 ml-auto">
        {/* Notifications */}
        <div className="relative">
          <button className="p-2 rounded-lg hover:bg-gray-100 transition-colors relative">
            <FaBell className="text-xl text-gray-600" />
            {unreadCount > 0 && (
              <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
                {unreadCount}
              </span>
            )}
          </button>
        </div>

        {/* User */}
        <div className="flex items-center gap-3">
          <div className="text-right hidden sm:block">
            <p className="text-sm font-medium text-gray-700">
              {user?.email?.split('@')[0] || 'User'}
            </p>
            <p className="text-xs text-gray-500">Admin</p>
          </div>
          <div className="w-10 h-10 rounded-full bg-primary-100 text-primary-600 flex items-center justify-center font-medium">
            {user?.email?.[0]?.toUpperCase() || 'U'}
          </div>
        </div>
      </div>
    </header>
  );
};

export default TopBar;