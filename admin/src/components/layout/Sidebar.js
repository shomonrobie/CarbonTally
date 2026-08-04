// admin/src/components/layout/Sidebar.jsx
import React, { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useRealtime } from '../../context/RealtimeContext';
import {
  FaTachometerAlt,
  FaTasks,
  FaUserFriends,
  FaBuilding,
  FaBoxes,
  FaChartBar,
  FaCog,
  FaLeaf,
  FaUsers,
  FaExclamationTriangle,
  FaUserCheck,
  FaBook,
  FaClipboardList,
  FaUserCog,
  FaHistory,
  FaFileAlt,
  FaSignOutAlt,
  FaBars,
  FaBell,
  FaCircle,
  FaRobot,
} from 'react-icons/fa';
import '../../css/Sidebar.css';

const Sidebar = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { isConnected, unreadCount } = useRealtime();
  const [isMobileOpen, setIsMobileOpen] = useState(false);

  const handleLogout = async () => {
    await logout();
    navigate('/admin/login');
  };

  const toggleMobile = () => setIsMobileOpen(!isMobileOpen);
  const closeMobile = () => setIsMobileOpen(false);

  // Notification badge
  const notificationBadge = unreadCount > 0 ? (
    <span className="badge">{unreadCount > 99 ? '99+' : unreadCount}</span>
  ) : null;

  // Live status indicator
  const liveStatus = (
    <span className={`live-status ${isConnected ? 'connected' : 'disconnected'}`}>
      <FaCircle className={`status-dot ${isConnected ? 'active' : ''}`} />
      {isConnected ? 'Live' : 'Offline'}
    </span>
  );

  return (
    <>
      {/* Mobile Toggle Button */}
      <button className="mobile-toggle" onClick={toggleMobile}>
        <FaBars />
      </button>

      {/* Mobile Overlay */}
      <div 
        className={`sidebar-overlay ${isMobileOpen ? 'active' : ''}`} 
        onClick={closeMobile}
      />

      {/* Sidebar */}
      <div className={`sidebar ${isMobileOpen ? 'open' : ''}`}>
        {/* Brand */}
        <div className="sidebar-brand">
          <h2>🌱 CarbonTally</h2>
          <div className="brand-sub">
            Admin Panel
            {liveStatus}
          </div>
        </div>

        {/* Navigation */}
        <nav className="sidebar-nav">
          <NavLink to="/admin" className="nav-link" end onClick={closeMobile}>
            <FaTachometerAlt /> Dashboard
          </NavLink>

          <NavLink to="/admin/reviews" className="nav-link" onClick={closeMobile}>
            <FaTasks /> Reviews
          </NavLink>

          <NavLink to="/admin/assignments" className="nav-link" onClick={closeMobile}>
            <FaUserCheck /> Assignments
          </NavLink>

          <NavLink to="/admin/reviews-queue" className="nav-link" onClick={closeMobile}>
            <FaClipboardList /> My Queue
          </NavLink>

          <div className="nav-section">Management</div>

          <NavLink to="/admin/users" className="nav-link" onClick={closeMobile}>
            <FaUserFriends /> Users
          </NavLink>

          <NavLink to="/admin/review-assignment" className="nav-link" onClick={closeMobile}>
            <FaUserCog /> Staff Management
          </NavLink>

          <NavLink to="/admin/organizations" className="nav-link" onClick={closeMobile}>
            <FaBuilding /> Organizations
          </NavLink>

          <NavLink to="/admin/batches" className="nav-link" onClick={closeMobile}>
            <FaBoxes /> Batches
          </NavLink>

          <NavLink to="/admin/customers" className="nav-link" onClick={closeMobile}>
            <FaUsers /> Customers
          </NavLink>

          <div className="nav-section">Data & Settings</div>

          <NavLink to="/admin/defra" className="nav-link" onClick={closeMobile}>
            <FaLeaf /> DEFRA Factors
          </NavLink>

          <NavLink to="/admin/analytics" className="nav-link" onClick={closeMobile}>
            <FaChartBar /> Analytics
          </NavLink>

          <NavLink to="/admin/log-viewer" className="nav-link" onClick={closeMobile}>
            <FaHistory /> Activity Logs
          </NavLink>

          <NavLink to="/admin/errors" className="nav-link" onClick={closeMobile}>
            <FaExclamationTriangle /> Extraction Errors
          </NavLink>

          <NavLink to="/admin/beta-management" className="nav-link" onClick={closeMobile}>
            <FaFileAlt /> Beta Management
          </NavLink>

          <NavLink to="/admin/glossary-management" className="nav-link" onClick={closeMobile}>
            <FaBook /> Glossary
          </NavLink>

          {/* ✅ Notifications with badge */}
          <NavLink to="/admin/notifications" className="nav-link" onClick={closeMobile}>
            <FaBell /> Notifications {notificationBadge}
          </NavLink>
          <NavLink to="/admin/work-hub" className="nav-link" onClick={closeMobile}>
            <FaHome /> Work Hub
            {unreadCount > 0 && (
              <span className="badge">{unreadCount}</span>
            )}
          </NavLink>

          <NavLink to="/admin/settings" className="nav-link" onClick={closeMobile}>
            <FaCog /> Settings
          </NavLink>
        </nav>

        {/* Footer */}
        <div className="sidebar-footer">
          <div className="user-info">
            <div className="avatar">
              {user?.email?.[0]?.toUpperCase() || 'A'}
            </div>
            <div className="user-details">
              <div className="user-name">{user?.email || 'Admin'}</div>
              <div className="user-role">Administrator</div>
            </div>
            <button className="logout-btn" onClick={handleLogout} title="Logout">
              <FaSignOutAlt />
            </button>
          </div>
          
          {/* ✅ Realtime status in footer */}
          <div className="sidebar-footer-status">
            <span className={`status-indicator ${isConnected ? 'connected' : 'disconnected'}`}>
              {isConnected ? '●' : '○'}
            </span>
            <span className="status-text">
              {isConnected ? 'Realtime Connected' : 'Realtime Disconnected'}
            </span>
          </div>
        </div>
      </div>
    </>
  );
};

export default Sidebar;