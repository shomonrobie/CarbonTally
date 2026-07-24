// src/components/AppHeader.js - Beta Mode (No Login) - With Beta Modal Disabled
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
  // ✅ Removed showWaitlistModal state - we're using the one on the landing page

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      if (session) {
        fetchOrganization(session.user.id);
        setUserProfile(session.user);
      }
    });

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
      if (session) {
        fetchOrganization(session.user.id);
        setUserProfile(session.user);
      } else {
        setOrganization(null);
        setUserProfile(null);
      }
    });

    return () => subscription.unsubscribe();
  }, []);

  const fetchOrganization = async (userId) => {
    const { data, error } = await supabase
      .from('organization_members')
      .select(`organizations (id, name)`)
      .eq('user_id', userId)
      .single();

    if (!error && data) {
      setOrganization(data.organizations);
    }
  };

  const handleLogout = async () => {
    await supabase.auth.signOut();
    setSession(null);
    setOrganization(null);
    setUserProfile(null);
    setIsMobileMenuOpen(false);
    navigate('/');
  };

  const handleLogin = () => {
    setIsMobileMenuOpen(false);
    navigate('/login');
  };

  const handleGetStarted = () => {
    setIsMobileMenuOpen(false);
    // ✅ Scroll to the waitlist modal on the landing page instead
    const waitlistSection = document.querySelector('.beta-banner');
    if (waitlistSection) {
      waitlistSection.scrollIntoView({ behavior: 'smooth' });
    } else {
      // Fallback: navigate to landing page
      navigate('/');
    }
  };

  const handleDashboard = () => {
    setIsMobileMenuOpen(false);
    navigate('/dashboard');
  };

  const toggleMobileMenu = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen);
  };

  // Get user display name
  const getUserDisplayName = () => {
    if (!userProfile) return 'User';
    
    const metadata = userProfile.user_metadata || {};
    const fullName = metadata.full_name || 
                    metadata.name || 
                    metadata.display_name ||
                    userProfile.email?.split('@')[0] || 
                    'User';
    
    return {
      fullName,
      firstName: fullName.split(' ')[0],
      email: userProfile.email
    };
  };

  const userDisplay = getUserDisplayName();

  return (
    <>
      <header className="main-header">
        <div className="header-container">
          <div className="header-left">
            <Link to="/" className="logo" onClick={() => setIsMobileMenuOpen(false)}>
              <span className="logo-icon logo-icon-animated">🌱</span>
              <span className="logo-text logo-text-animated">CarbonTally</span>
            </Link>
          </div>
          
          {/* Mobile Menu Toggle */}
          <button 
            className="mobile-menu-toggle"
            onClick={toggleMobileMenu}
            aria-label={isMobileMenuOpen ? "Close menu" : "Open menu"}
          >
            <span className="hamburger-line"></span>
            <span className="hamburger-line"></span>
            <span className="hamburger-line"></span>
          </button>

          {/* Navigation */}
          <nav className={`landing-nav ${isMobileMenuOpen ? 'mobile-open' : ''}`}>
            <ul className="nav-links">
              <li><a href="/#features" onClick={() => setIsMobileMenuOpen(false)}>Features</a></li>
              <li><a href="/#pricing" onClick={() => setIsMobileMenuOpen(false)}>Pricing</a></li>
              <li><Link to="/about" onClick={() => setIsMobileMenuOpen(false)}>About</Link></li>
              <li><Link to="/carbon-reduction-plan" onClick={() => setIsMobileMenuOpen(false)}>Carbon Plan</Link></li>
            </ul>
          </nav>
          
          <div className="header-right">
            {session && organization ? (
              // Logged in user view
              <>
                <div className="user-info-group">
                  <div className="user-avatar-wrapper" title={`${userDisplay.fullName} (${userDisplay.email})`}>
                    <div className="user-avatar">
                      {userDisplay.fullName.charAt(0).toUpperCase()}
                    </div>
                    <div className="user-details">
                      <span className="user-name">{userDisplay.fullName}</span>
                      <span className="company-name-badge">{organization.name}</span>
                    </div>
                  </div>
                </div>

                <div className="action-buttons">
                  <button onClick={handleDashboard} className="header-dashboard-btn">
                    Dashboard
                  </button>
                  <button onClick={handleLogout} className="header-logout">
                    Logout
                  </button>
                </div>
              </>
            ) : (
              // Beta Mode: Show "Request Beta Access" button
              <>
                {/* Beta Badge */}
                {isBetaMode && (
                  <span className="beta-badge-header">🧪 Beta</span>
                )}
                
                {/* ✅ Beta Access Button - Scrolls to landing page beta section */}
                <button onClick={handleGetStarted} className="header-cta btn-gradient">
                  {isBetaMode ? 'Request Beta Access' : 'Start Free Trial'}
                </button>
              </>
            )}
          </div>
        </div>
      </header>

      {/* ✅ REMOVED: Waitlist Modal - Now using the one on the landing page */}
    </>
  );
}