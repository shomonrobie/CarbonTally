// src/SelfServiceSignup.jsx - Public self-service account creation (D35)
// A brand-new visitor can create a CarbonTally account WITHOUT a beta code.
// Supabase Auth remains authoritative. After signup the customer is routed
// through the server-authoritative post-login resolver (a new user with no
// organization lands on /onboarding). The beta-code path is preserved as an
// OPTIONAL administrative mechanism at /beta/signup.
import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { supabase } from './supabaseClient';
import { resolvePostLoginPath } from './v3/api';
import './css/BetaSignup.css';

export default function SelfServiceSignup() {
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [confirmEmail, setConfirmEmail] = useState(false);

  const handleSignup = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const { data: authData, error: authError } = await supabase.auth.signUp({
        email: email.trim(),
        password,
        options: {
          data: {
            full_name: fullName.trim(),
            company_name: companyName.trim(),
            is_beta_user: false,
            onboarding: true,
          },
        },
      });

      if (authError) {
        if (authError.message && authError.message.includes('User already registered')) {
          setError('This email is already registered. Please sign in instead.');
          setLoading(false);
          return;
        }
        throw authError;
      }

      // If Supabase returns a session immediately (email confirmation disabled)
      // route straight into the server-authoritative destination. Otherwise the
      // customer confirms their email first and lands back via /auth/callback.
      if (authData?.session) {
        resolvePostLoginPath().then((path) => navigate(path, { replace: true }));
        return;
      }
      setConfirmEmail(true);
    } catch (err) {
      console.error('Signup error:', err);
      setError(err.message || 'Failed to create account. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  if (confirmEmail) {
    return (
      <div className="beta-signup-container">
        <div className="beta-signup-card">
          <div className="success-icon">📧</div>
          <h2>Check your email</h2>
          <p>
            We sent a confirmation link to <strong>{email.trim()}</strong>. Click it to
            activate your account — you will then be guided to set up your organisation.
          </p>
          <button onClick={() => navigate('/login')} className="btn-primary">
            Return to Sign In
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="beta-signup-container">
      <div className="beta-signup-card">
        <div className="beta-header">
          <span className="beta-badge">🌱 Create your account</span>
          <h2>Start with CarbonTally</h2>
          <p>
            Measure, verify and report your carbon emissions. Create your account — it
            takes a minute, and you will be guided through setting up your organisation.
          </p>
        </div>

        <form onSubmit={handleSignup} className="beta-form">
          <div className="form-group">
            <label>Email Address</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@yourcompany.com"
              required
            />
          </div>

          <div className="form-group">
            <label>Full Name</label>
            <input
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder="Jane Smith"
              required
            />
          </div>

          <div className="form-group">
            <label>Company / Organisation Name</label>
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
            {loading ? 'Creating Account...' : 'Create Account →'}
          </button>

          <p className="beta-terms">
            By creating an account, you agree to our{' '}
            <Link to="/terms">Terms of Service</Link> and{' '}
            <Link to="/privacy">Privacy Policy</Link>.
          </p>
        </form>

        <div className="beta-footer-links">
          <p>
            Already have an account? <Link to="/login">Sign in</Link>
          </p>
          <p>
            Have an access code? <Link to="/beta/signup">Use your beta access code</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
