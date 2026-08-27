// frontend/src/BetaLogin.jsx - Fixed version

import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams, useLocation } from 'react-router-dom';
import { supabase } from './supabaseClient';
import toast from 'react-hot-toast';
import './css/BetaLogin.css';

function BetaLogin() {
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams] = useSearchParams();
  
  // ✅ Get email from location state (passed from MagicLink)
  const preFilledEmail = location.state?.email || '';
  
  const [email, setEmail] = useState(preFilledEmail || '');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  // Check if already logged in
  useEffect(() => {
    const checkSession = async () => {
      const { data: { session } } = await supabase.auth.getSession();
      if (session) {
        navigate('/dashboard');
      }
    };
    checkSession();
  }, [navigate]);

  // ✅ Handle auto-login from magic link
  useEffect(() => {
    const autoLogin = searchParams.get('auto') === 'true';
    const firstLogin = searchParams.get('first_login') === 'true';

    if (autoLogin) {
      const tempEmail = localStorage.getItem('temp_email');
      const tempPassword = localStorage.getItem('temp_password');
      
      if (tempEmail && tempPassword) {
        handleAutoLogin(tempEmail, tempPassword);
        localStorage.removeItem('temp_email');
        localStorage.removeItem('temp_password');
      }
    }

    if (firstLogin) {
      setMessage('🎉 Welcome to CarbonTally Beta! Please set your password to continue.');
    }
  }, [searchParams]);

  // ✅ Auto-login handler
  const handleAutoLogin = async (email, password) => {
    setLoading(true);
    try {
      const { data, error } = await supabase.auth.signInWithPassword({
        email: email.toLowerCase().trim(),
        password,
      });

      if (error) {
        console.error('Auto-login error:', error);
        setError('Auto-login failed. Please try signing in manually.');
        setLoading(false);
        return;
      }

      // ✅ Check if user is a beta user
      const { data: betaCheck, error: betaError } = await supabase
        .from('beta_users')
        .select('email')
        .eq('email', email.toLowerCase().trim())
        .maybeSingle();

      if (!betaCheck) {
        await supabase.auth.signOut();
        setError('❌ This is a beta-only application. Please use your beta invite.');
        setLoading(false);
        return;
      }

      navigate('/dashboard');
      
    } catch (err) {
      console.error('Auto-login error:', err);
      setError('Auto-login failed. Please try signing in manually.');
    } finally {
      setLoading(false);
    }
  };

  // ✅ Handle beta login
  const handleBetaLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setMessage('');

    // ✅ Validate email
    const emailTrimmed = email?.trim();
    if (!emailTrimmed) {
      setError('❌ Please enter your email address.');
      setLoading(false);
      return;
    }

    if (!emailTrimmed.includes('@')) {
      setError('❌ Please enter a valid email address.');
      setLoading(false);
      return;
    }

    try {
      const { data, error } = await supabase.auth.signInWithPassword({
        email: emailTrimmed.toLowerCase(),
        password,
      });

      if (error) {
        if (error.message.includes('Invalid login credentials')) {
          setError('❌ Invalid email or password. Please try again.');
        } else if (error.message.includes('Email not confirmed')) {
          setError('❌ Please confirm your email address before signing in.');
        } else {
          setError(`❌ ${error.message}`);
        }
        setLoading(false);
        return;
      }

      // ✅ Check if user is a beta user
      const { data: betaCheck, error: betaError } = await supabase
        .from('beta_users')
        .select('email')
        .eq('email', emailTrimmed.toLowerCase())
        .maybeSingle();

      if (!betaCheck) {
        await supabase.auth.signOut();
        setError('❌ This is a beta-only application. Please use your beta invite.');
        setLoading(false);
        return;
      }

      navigate('/dashboard');
      
    } catch (err) {
      console.error('Login error:', err);
      setError('❌ An unexpected error occurred. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="beta-login-container">
      <div className="beta-login-box">
        <div className="beta-header">
          <div className="beta-logo">🌱</div>
          <h1>CarbonTally</h1>
          <p className="beta-subtitle">Beta Access Login</p>
        </div>

        {/* Beta Notice */}
        <div className="beta-notice">
          <span className="beta-badge">🧪 Beta</span>
          <span className="beta-message">Limited beta access — by invitation only</span>
        </div>

        {message && (
          <div className="success-message" style={{ marginBottom: '1rem' }}>
            {message}
          </div>
        )}

        {/* Login Form */}
        <form onSubmit={handleBetaLogin} className="beta-form">
          <div className="form-group">
            <label>Email Address</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="you@company.com"
              disabled={loading}
              className={!email ? 'input-error' : ''}
            />
          </div>

          <div className="form-group">
            <label>Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              placeholder="••••••••"
              minLength={6}
              disabled={loading}
            />
          </div>

          {error && <div className="error-message">{error}</div>}

          <button type="submit" disabled={loading} className="beta-btn-primary">
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <div className="beta-footer">
          <p>🧪 Beta version — All features are functional</p>
          <p className="beta-legal">🔒 Secure, UK GDPR Compliant</p>
          <p className="beta-help-text" style={{ marginTop: '0.75rem' }}>
            Need help? <a href="mailto:support@carbontally.co.uk">Contact support</a>
          </p>
        </div>
      </div>
    </div>
  );
}

export default BetaLogin;