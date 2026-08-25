// src/BetaSignup.jsx - Beta access signup page
import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { supabase } from './supabaseClient';
import { resolvePostLoginPath } from './v3/api';
import './css/BetaSignup.css';

export default function BetaSignup() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const betaCode = searchParams.get('code');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [validCode, setValidCode] = useState(false);
  const [checkingCode, setCheckingCode] = useState(true);

  // Form state
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [companyName, setCompanyName] = useState('');

  // Validate beta code on load
  useEffect(() => {
    const validateCode = async () => {
      if (!betaCode) {
        setError('No beta access code provided');
        setCheckingCode(false);
        return;
      }

      try {
        const { data, error } = await supabase
          .from('beta_access_codes')
          .select('code, email, status, expires_at')
          .eq('code', betaCode)
          .single();

        if (error || !data) {
          setError('Invalid beta access code');
          setCheckingCode(false);
          return;
        }

        if (data.status === 'used') {
          setError('This beta code has already been used');
          setCheckingCode(false);
          return;
        }

        if (new Date(data.expires_at) < new Date()) {
          setError('This beta code has expired');
          setCheckingCode(false);
          return;
        }

        // Code is valid
        setValidCode(true);
        setEmail(data.email || '');
        setError('');
        setCheckingCode(false);

      } catch (err) {
        console.error('Code validation error:', err);
        setError('Error validating beta code');
        setCheckingCode(false);
      }
    };

    validateCode();
  }, [betaCode]);

  
  const handleSignup = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
    // ✅ Check if user already exists
      const { data: existingUser, error: checkError } = await supabase
        .from('beta_users')
        .select('email')
        .eq('email', email)
        .single();

        if (existingUser) {
            setError('This email is already registered for beta access. Please sign in.');
            setLoading(false);
            return;
        }
        
    
      // 1. Create user account
      const { data: authData, error: authError } = await supabase.auth.signUp({
        email: email,
        password: password,
        options: {
          data: {
            full_name: fullName,
            company_name: companyName,
            is_beta_user: true,
            beta_code: betaCode
          }
        }
      });

        if (authError) {
        // ✅ Handle existing auth user
        if (authError.message.includes('User already registered')) {
            setError('This email is already registered. Please sign in instead.');
            setLoading(false);
            return;
        }
        throw authError;
        }



      // 2. Mark beta code as used
      await supabase
        .from('beta_access_codes')
        .update({ 
          status: 'used', 
          used_at: new Date().toISOString() 
        })
        .eq('code', betaCode);

      // 3. Add to beta_users table
      await supabase
        .from('beta_users')
        .insert({
          user_id: authData.user.id,
          email: email,
          beta_code: betaCode,
          access_level: 'beta'
        });

      // 4. Update waitlist status
      await supabase
        .from('waitlist')
        .update({ 
          status: 'active', 
          activated_at: new Date().toISOString() 
        })
        .eq('email', email);

      setSuccess(true);
      // D35 — never land a customer on the legacy /dashboard. Route through
      // the server-authoritative resolver (new users go to /onboarding).
      setTimeout(() => {
        resolvePostLoginPath().then((path) => navigate(path, { replace: true }));
      }, 2000);

    } catch (err) {
      console.error('Signup error:', err);
      setError(err.message || 'Failed to create account');
    } finally {
      setLoading(false);
    }
  };

  if (checkingCode) {
    return (
      <div className="beta-signup-container">
        <div className="beta-signup-card">
          <div className="loading-spinner">Verifying beta access...</div>
        </div>
      </div>
    );
  }

  if (error && !validCode) {
    return (
      <div className="beta-signup-container">
        <div className="beta-signup-card">
          <div className="error-icon">🚫</div>
          <h2>Invalid Beta Access</h2>
          <p>{error}</p>
          <button onClick={() => navigate('/')} className="btn-primary">
            Return to Home
          </button>
        </div>
      </div>
    );
  }

  if (success) {
    return (
      <div className="beta-signup-container">
        <div className="beta-signup-card">
          <div className="success-icon">🎉</div>
          <h2>Welcome to CarbonTally Beta!</h2>
          <p>Your account has been created. Redirecting to dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="beta-signup-container">
      <div className="beta-signup-card">
        <div className="beta-header">
          <span className="beta-badge">🧪 Beta Access</span>
          <h2>Create Your Beta Account</h2>
          <p>You've been invited to try CarbonTally. Set up your account to get started.</p>
        </div>

        <form onSubmit={handleSignup} className="beta-form">
          <div className="form-group">
            <label>Email Address</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              disabled
              className="input-disabled"
            />
            <small>Email is pre-filled from your beta invite</small>
          </div>

          <div className="form-group">
            <label>Full Name</label>
            <input
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder="John Smith"
              required
            />
          </div>

          <div className="form-group">
            <label>Company Name</label>
            <input
              type="text"
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              placeholder="ABC Logistics Ltd"
              required
            />
          </div>

          <div className="form-group">
            <label>Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Minimum 8 characters"
              required
              minLength={8}
            />
          </div>

          {error && <div className="form-error">{error}</div>}

          <button type="submit" className="btn-primary btn-gradient" disabled={loading}>
            {loading ? 'Creating Account...' : 'Create Beta Account →'}
          </button>

          <p className="beta-terms">
            By creating an account, you agree to our 
            <a href="/terms"> Terms of Service</a> and 
            <a href="/privacy"> Privacy Policy</a>.
          </p>
        </form>
      </div>
    </div>
  );
}