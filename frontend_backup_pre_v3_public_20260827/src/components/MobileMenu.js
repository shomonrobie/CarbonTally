// src/components/MobileMenu.js

import React from 'react';

function MobileMenu({ isOpen, onClose, activeTab, setActiveTab, userRole, fetchHistory, organization }) {
  if (!isOpen) return null;

  const handleNavClick = (tab) => {
    setActiveTab(tab);
    if (tab === 'history' && organization) {
      fetchHistory();
    }
    onClose();
  };

  return (
    <div className="mobile-menu-overlay">
      <div className="mobile-menu-content">
        <button 
          className="mobile-menu-close"
          onClick={onClose}
        >
          ✕ Close
        </button>
        <button 
          className={`mobile-nav-btn ${activeTab === 'dashboard' ? 'active' : ''}`}
          onClick={() => handleNavClick('dashboard')}
        >
          📊 Dashboard
        </button>
        <button 
          className={`mobile-nav-btn ${activeTab === 'upload' ? 'active' : ''}`}
          onClick={() => handleNavClick('upload')}
        >
          ⬆️ Upload Data
        </button>
        <button 
          className={`mobile-nav-btn ${activeTab === 'history' ? 'active' : ''}`}
          onClick={() => handleNavClick('history')}
        >
          📈 History & Trends
        </button>
        {userRole === 'admin' && (
          <button 
            className={`mobile-nav-btn ${activeTab === 'team' ? 'active' : ''}`}
            onClick={() => handleNavClick('team')}
          >
            👥 Team Management
          </button>
        )}
        <button 
          className={`mobile-nav-btn ${activeTab === 'assets' ? 'active' : ''}`}
          onClick={() => handleNavClick('assets')}
        >
          🏢 Assets
        </button>
      </div>
    </div>
  );
}

export default MobileMenu;