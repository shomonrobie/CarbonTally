// admin/src/components/layout/Layout.jsx
import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useRealtime } from '../../context/RealtimeContext';
import Sidebar from './Sidebar';
import TopBar from './TopBar';
import { Toaster } from 'react-hot-toast';

const Layout = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const { user } = useAuth();
  const { isConnected } = useRealtime(); // ✅ Add Realtime

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <Sidebar open={sidebarOpen} setOpen={setSidebarOpen} />
      
      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <TopBar sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />
        
        <main className="flex-1 overflow-y-auto p-6">
          <div className="max-w-7xl mx-auto">
            {children}
          </div>
        </main>
      </div>
      
      <Toaster position="top-right" />
      
      {/* ✅ Realtime Status Indicator (optional floating badge) */}
      <div className="fixed bottom-4 right-4 z-50">
        <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium shadow-lg ${
          isConnected 
            ? 'bg-green-100 text-green-700 border border-green-200' 
            : 'bg-yellow-100 text-yellow-700 border border-yellow-200'
        }`}>
          <span className={`w-2 h-2 rounded-full ${
            isConnected ? 'bg-green-500 animate-pulse' : 'bg-yellow-500'
          }`} />
          {isConnected ? '🟢 Live' : '🟡 Connecting...'}
        </div>
      </div>
    </div>
  );
};

export default Layout;