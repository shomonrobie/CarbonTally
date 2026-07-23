// src/components/AppHeader.js - Updated with responsive improvements
import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { supabase } from '../supabaseClient';
import './AppHeader.css';

export default function AppHeader({ showAuthButtons = true, isBetaMode = true }) {
  const navigate = useNavigate();
  const [session, setSession] = useState(null);
  const [organization, setOrganization] = useState(null);
  const [userProfile, setUserProfile] = useState(null);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [showWaitlistModal, setShowWaitlistModal] = useState(false);

  // ... rest of your existing AppHeader code ...

  const toggleMobileMenu = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen);
  };

  return (
    <>
      <header className="main-header">
        <div className="header-container">
          <div className="header-left">
            <Link to="/" className="logo" onClick={() => setIsMobileMenuOpen(false)}>
              <span className="logo-icon">🌱</span>
              <span className="logo-text">CarbonTally</span>
            </Link>
          </div>
          
          {/* Mobile Menu Toggle */}
          <button 
            className={`mobile-menu-toggle ${isMobileMenuOpen ? 'active' : ''}`}
            onClick={toggleMobileMenu}
            aria-label={isMobileMenuOpen ? "Close menu" : "Open menu"}
          >
            <span className="hamburger-line"></span>
            <span className="hamburger-line"></span>
            <span className="hamburger-line"></span>
          </button>

          {/* Desktop Navigation */}
          <nav className={`landing-nav ${isMobileMenuOpen ? 'mobile-open' : ''}`}>
            <ul className="nav-links">
              <li><a href="/#features" onClick={() => setIsMobileMenuOpen(false)}>Features</a></li>
              <li><a href="/#pricing" onClick={() => setIsMobileMenuOpen(false)}>Pricing</a></li>
              <li><Link to="/about" onClick={() => setIsMobileMenuOpen(false)}>About</Link></li>
              <li><Link to="/carbon-reduction-plan" onClick={() => setIsMobileMenuOpen(false)}>Carbon Plan</Link></li>
            </ul>
          </nav>
          
          <div className="header-right">
            {isBetaMode && (
              <span className="beta-badge-header">🧪 Beta</span>
            )}
            <button onClick={() => setShowWaitlistModal(true)} className="header-cta btn-gradient">
              Request Beta Access
            </button>
          </div>
        </div>
      </header>

      {/* Mobile Menu Overlay - Add this for better mobile experience */}
      {isMobileMenuOpen && (
        <div className="mobile-menu-overlay" onClick={toggleMobileMenu}>
          <div className="mobile-menu-content" onClick={(e) => e.stopPropagation()}>
            <button className="mobile-menu-close" onClick={toggleMobileMenu}>✕</button>
            <nav className="mobile-nav">
              <a href="/#features" onClick={toggleMobileMenu}>Features</a>
              <a href="/#pricing" onClick={toggleMobileMenu}>Pricing</a>
              <Link to="/about" onClick={toggleMobileMenu}>About</Link>
              <Link to="/carbon-reduction-plan" onClick={toggleMobileMenu}>Carbon Plan</Link>
              <button className="mobile-cta btn-gradient" onClick={() => {
                toggleMobileMenu();
                setShowWaitlistModal(true);
              }}>
                Request Beta Access
              </button>
            </nav>
          </div>
        </div>
      )}

      {/* Waitlist Modal */}
      {showWaitlistModal && (
        <div className="modal-overlay" onClick={() => setShowWaitlistModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close" onClick={() => setShowWaitlistModal(false)}>✕</button>
            <div className="modal-header">
              <span className="modal-icon">🧪</span>
              <h2>Request Beta Access</h2>
              <p>All features are ready. Be among the first to try CarbonTally.</p>
            </div>
            <form className="modal-form" onSubmit={(e) => e.preventDefault()}>
              <div className="form-group">
                <label htmlFor="header-email">Email Address</label>
                <input
                  id="header-email"
                  type="email"
                  placeholder="you@company.com"
                  required
                />
              </div>
              <button type="submit" className="modal-submit btn-gradient">
                Request Beta Access →
              </button>
              <p className="modal-subtext">✅ No spam. Unsubscribe anytime.</p>
            </form>
          </div>
        </div>
      )}
    </>
  );
}