import React, { useState } from 'react';
import { supabase } from './supabaseClient';
import './Login.css';

function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [isSignup, setIsSignup] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  const handleAuth = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setMessage('');

    try {
      if (isSignup) {
        // SIGN UP
        const { error } = await supabase.auth.signUp({
          email,
          password,
          options: {
            data: {
              company_name: companyName,
            },
          },
        });

        if (error) throw error;
        
        setMessage('✅ Check your email for the confirmation link!');
        setEmail('');
        setPassword('');
        setCompanyName('');
      } else {
        // SIGN IN
        const { error } = await supabase.auth.signInWithPassword({
          email,
          password,
        });

        if (error) throw error;
        // The App component will detect the login and redirect
      }
    } catch (err) {
      console.error("FULL ERROR OBJECT:", err); // Open F12 in browser to see this
      
      // Supabase sometimes nests the real message inside err.error.message
      const realMessage = err.message || (err.error && err.error.message) || JSON.stringify(err);
      
      if (realMessage === '{}') {
        setError('Signup failed silently. Check browser console (F12) for the real error.');
      } else {
        setError(realMessage);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-box">
        <h1> CarbonTally</h1>
        <p className="tagline">Automated Carbon Accounting for UK Logistics</p>
        
        <form onSubmit={handleAuth} className="auth-form">
          <div className="form-group">
            <label>Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="you@company.com"
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
            />
          </div>

          {isSignup && (
            <div className="form-group">
              <label>Company Name</label>
              <input
                type="text"
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                required
                placeholder="e.g., ABC Logistics Ltd"
              />
            </div>
          )}

          {error && <div className="error-message">{error}</div>}
          {message && <div className="success-message">{message}</div>}

          <button type="submit" disabled={loading} className="auth-button">
            {loading ? 'Please wait...' : (isSignup ? 'Create Account' : 'Sign In')}
          </button>
        </form>

        <div className="toggle-auth">
          {isSignup ? (
            <p>
              Already have an account?{' '}
              <button onClick={() => setIsSignup(false)} className="link-button">
                Sign In
              </button>
            </p>
          ) : (
            <p>
              New to CarbonTally?{' '}
              <button onClick={() => setIsSignup(true)} className="link-button">
                Create Account
              </button>
            </p>
          )}
        </div>

        <div className="trust-badge">
          <span>🔒 Secure, UK GDPR Compliant</span>
        </div>
      </div>
    </div>
  );
}

export default Login;