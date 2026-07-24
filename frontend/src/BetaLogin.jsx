// frontend/src/BetaLogin.jsx - Fixed version

import React, { useState, useEffect } from 'react';
import { supabase } from './supabaseClient';
import { useNavigate } from 'react-router-dom';
import './css/BetaLogin.css';

function BetaLogin() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [betaCode, setBetaCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [activeTab, setActiveTab] = useState('login'); // 'login' or 'signup'

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

  // Handle beta login
  const handleBetaLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setMessage('');

    try {
      const { data, error } = await supabase.auth.signInWithPassword({
        email: email.toLowerCase().trim(),
        password,
      });

      if (error) {
        if (error.message.includes('Invalid login credentials')) {
          setError('❌ Invalid email or password. Please try again.');
        } else if (error.message.includes('Email not confirmed')) {
          setError('❌ Please confirm your email address before signing in. Check your inbox.');
        } else {
          setError(`❌ ${error.message}`);
        }
        setLoading(false);
        return;
      }

      // Success
      navigate('/dashboard');
      
    } catch (err) {
      console.error('Login error:', err);
      setError('❌ An unexpected error occurred. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Handle beta signup
  const handleBetaSignup = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setMessage('');

    try {
      // 1. Validate beta code
      if (!betaCode.trim()) {
        setError('❌ Please enter your beta access code.');
        setLoading(false);
        return;
      }

      // 2. Check if email already exists in Supabase Auth
      // We'll try to sign up and handle the error
      const { data: signUpData, error: signUpError } = await supabase.auth.signUp({
        email: email.toLowerCase().trim(),
        password,
        options: {
          data: {
            is_beta_user: true,
            beta_code: betaCode.trim().toUpperCase(),
          },
          emailRedirectTo: window.location.origin + '/beta-login',
        },
      });

      // ✅ Handle existing user error properly
      if (signUpError) {
        if (signUpError.message.includes('User already registered')) {
          // ✅ User exists - offer to login instead
          setError('❌ This email is already registered.');
          setMessage('💡 Please sign in with your existing account.');
          setActiveTab('login');
          setLoading(false);
          return;
        } else {
          setError(`❌ ${signUpError.message}`);
          setLoading(false);
          return;
        }
      }

      // If we got here, user was created successfully
      if (signUpData.user) {
        // Check if beta code is valid and mark it as used
        const { data: codeData, error: codeError } = await supabase
          .from('beta_access_codes')
          .select('status')
          .eq('code', betaCode.trim().toUpperCase())
          .single();

        if (!codeError && codeData) {
          // Mark beta code as used
          await supabase
            .from('beta_access_codes')
            .update({ 
              status: 'used', 
              used_at: new Date().toISOString(),
              used_by: signUpData.user.id
            })
            .eq('code', betaCode.trim().toUpperCase());

          // Add to beta_users table
          await supabase
            .from('beta_users')
            .insert({
              user_id: signUpData.user.id,
              email: email.toLowerCase().trim(),
              beta_code: betaCode.trim().toUpperCase(),
              access_level: 'beta',
              created_at: new Date().toISOString()
            });
        }

        setMessage('✅ Account created! Please check your email to confirm your address.');
        setEmail('');
        setPassword('');
        setBetaCode('');
        setActiveTab('login');
        
        setTimeout(() => {
          setMessage('✅ Please confirm your email, then sign in.');
        }, 3000);
      }

    } catch (err) {
      console.error('Signup error:', err);
      setError('❌ Signup failed. Please try again.');
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
          <p className="beta-subtitle">Beta Access Program</p>
        </div>

        {/* Beta Notice */}
        <div className="beta-notice">
          <span className="beta-badge">🧪 Beta</span>
          <span className="beta-message">Limited beta access — by invitation only</span>
        </div>

        {/* Tabs: Login / Signup */}
        <div className="beta-tabs">
          <button 
            className={`beta-tab ${activeTab === 'login' ? 'active' : ''}`}
            onClick={() => {
              setActiveTab('login');
              setError('');
              setMessage('');
            }}
          >
            Sign In
          </button>
          <button 
            className={`beta-tab ${activeTab === 'signup' ? 'active' : ''}`}
            onClick={() => {
              setActiveTab('signup');
              setError('');
              setMessage('');
            }}
          >
            Sign Up
          </button>
        </div>

        {/* Login Form */}
        {activeTab === 'login' && (
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
            {message && <div className="success-message">{message}</div>}

            <button type="submit" disabled={loading} className="beta-btn-primary">
              {loading ? 'Signing in...' : 'Sign In'}
            </button>

            <p className="beta-help-text">
              Don't have an account? <span className="switch-tab" onClick={() => {
                setActiveTab('signup');
                setError('');
                setMessage('');
              }}>Sign up with your beta code</span>
            </p>
          </form>
        )}

        {/* Signup Form */}
        {activeTab === 'signup' && (
          <form onSubmit={handleBetaSignup} className="beta-form">
            <div className="form-group">
              <label>Beta Access Code</label>
              <input
                type="text"
                value={betaCode}
                onChange={(e) => setBetaCode(e.target.value)}
                placeholder="e.g., BETA-XXXXXX"
                required
                disabled={loading}
                style={{ textTransform: 'uppercase', letterSpacing: '1px' }}
              />
              <small className="form-hint">Enter the code from your beta invite email</small>
            </div>

            <div className="form-group">
              <label>Email Address</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                placeholder="you@company.com"
                disabled={loading}
              />
            </div>

            <div className="form-group">
              <label>Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                placeholder="•••••••• (min 6 characters)"
                minLength={6}
                disabled={loading}
              />
              <small className="form-hint">Must be at least 6 characters</small>
            </div>

            {error && <div className="error-message">{error}</div>}
            {message && <div className="success-message">{message}</div>}

            <button type="submit" disabled={loading} className="beta-btn-primary">
              {loading ? 'Creating Account...' : 'Create Beta Account'}
            </button>

            <p className="beta-help-text">
              Already have an account? <span className="switch-tab" onClick={() => {
                setActiveTab('login');
                setError('');
                setMessage('');
              }}>Sign in instead</span>
            </p>
          </form>
        )}

        <div className="beta-footer">
          <p>🧪 Beta version — All features are functional</p>
          <p className="beta-legal">🔒 Secure, UK GDPR Compliant</p>
        </div>
      </div>
    </div>
  );
}

export default BetaLogin;