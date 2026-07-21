import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { supabase } from '../supabaseClient';

export default function AppHeader({ showAuthButtons = true }) {
  const navigate = useNavigate();
  const [session, setSession] = useState(null);
  const [organization, setOrganization] = useState(null);

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      if (session) {
        fetchOrganization(session.user.id);
      }
    });

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
      if (session) {
        fetchOrganization(session.user.id);
      } else {
        setOrganization(null);
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
    navigate('/');
  };

  const handleLogin = () => {
    navigate('/login');
  };

  const handleGetStarted = () => {
    navigate('/login');
  };

  const handleDashboard = () => {
    navigate('/dashboard');
  };

  return (
    <header className="main-header">
      <div className="header-container">
        <div className="header-left">
          <Link to="/" className="logo">
            <span className="logo-icon logo-icon-animated">🌱</span>
            <span className="logo-text logo-text-animated">CarbonTally</span>
          </Link>
        </div>
        
        <nav className="main-nav">
          <ul className="nav-links">
            <li><a href="/#features">Features</a></li>
            <li><a href="/#pricing">Pricing</a></li>
            <li><Link to="/about">About</Link></li>
            <li><Link to="/carbon-reduction-plan">Carbon Plan</Link></li>
          </ul>
        </nav>
        
        <div className="header-right">
          {session && organization ? (
            <>
              <span className="company-name-badge">{organization.name}</span>
              <button onClick={handleDashboard} className="header-dashboard-btn">
                Dashboard
              </button>
              <button onClick={handleLogout} className="header-logout">
                Logout
              </button>
            </>
          ) : showAuthButtons ? (
            <>
              <button onClick={handleLogin} className="header-login">
                Log In
              </button>
              <button onClick={handleGetStarted} className="header-cta btn-gradient">
                Start Free Trial
              </button>
            </>
          ) : null}
        </div>
      </div>
    </header>
  );
}