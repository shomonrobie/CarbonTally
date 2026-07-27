// admin/src/components/layout/Sidebar.jsx
import React, { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
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
  FaTimes
} from 'react-icons/fa';
import '../../css/sidebar.css';

const Sidebar = () => {
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const handleLogout = async () => {
    await logout();
    navigate('/admin/login');
  };

  const toggleMobile = () => setIsMobileOpen(!isMobileOpen);
  const closeMobile = () => setIsMobileOpen(false);

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
          <p className="brand-sub">Admin Panel</p>
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

          <NavLink to="/admin/settings" className="nav-link" onClick={closeMobile}>
            <FaCog /> Settings
          </NavLink>
        </nav>

        {/* Footer */}
        <div className="sidebar-footer">
          <div className="user-info">
            <div className="avatar">{user?.email?.[0]?.toUpperCase() || 'A'}</div>
            <div className="user-details">
              <div className="user-name">{user?.email || 'Admin'}</div>
              <div className="user-role">Administrator</div>
            </div>
            <button className="logout-btn" onClick={handleLogout}>
              <FaSignOutAlt />
            </button>
          </div>
        </div>
      </div>
    </>
  );
};

export default Sidebar;