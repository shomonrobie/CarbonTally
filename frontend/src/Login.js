// Login.jsx
import React, { useState, useEffect } from 'react';
import { supabase } from './supabaseClient';
import { useNavigate } from 'react-router-dom';
import './Login.css';

function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [isSignup, setIsSignup] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  // Check if user is already logged in
  useEffect(() => {
    const getUser = async () => {
      const { data: { user } } = await supabase.auth.getUser();
      if (user) {
        navigate('/dashboard');
      }
    };
    getUser();

    // Listen for auth state changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (event, session) => {
        if (event === 'SIGNED_IN' && session) {
          navigate('/dashboard');
        }
      }
    );

    return () => {
      subscription.unsubscribe();
    };
  }, [navigate]);

  const handleAuth = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setMessage('');

    try {
      if (isSignup) {
        // SIGN UP
        const { data, error } = await supabase.auth.signUp({
          email,
          password,
          options: {
            data: {
              company_name: companyName,
            },
            emailRedirectTo: window.location.origin + '/login',
          },
        });

        if (error) throw error;
        
        if (data.user && data.user.identities && data.user.identities.length === 0) {
          setError('This email is already registered. Please sign in instead.');
        } else {
          setMessage('✅ Check your email for the confirmation link! You must confirm your email before signing in.');
        }
        setEmail('');
        setPassword('');
        setCompanyName('');
      } else {
        // SIGN IN
        const { data, error } = await supabase.auth.signInWithPassword({
          email,
          password,
        });

        if (error) throw error;
        navigate('/dashboard');
      }
    } catch (err) {
      console.error("FULL ERROR OBJECT:", err);
      
      let errorMessage = err.message;
      if (err.message === 'Invalid login credentials') {
        errorMessage = '❌ Invalid email or password. Please try again.';
      } else if (err.message.includes('Email not confirmed')) {
        errorMessage = '❌ Please confirm your email address before signing in. Check your inbox for the confirmation link.';
      } else if (err.message.includes('User not found')) {
        errorMessage = '❌ No account found with this email. Please sign up first.';
      }
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  // 🆕 Google Sign-In Handler with Organization Support
  const handleGoogleSignIn = async () => {
    setLoading(true);
    setError('');
    
    try {
      const { data, error } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
          redirectTo: window.location.origin + '/dashboard',
          queryParams: {
            access_type: 'offline',
            prompt: 'consent',
          },
          // This passes through to user metadata
          scopes: 'email profile',
        },
      });

      if (error) throw error;
      
      console.log('Google sign-in initiated');
    } catch (err) {
      console.error('Google sign-in error:', err);
      setError('❌ Failed to sign in with Google. Please try again.');
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-box">
        <h1>🌱 CarbonTally</h1>
        <p className="tagline">Automated Carbon Accounting for UK Businesses</p>
        
        {/* 🆕 Google Sign-In Button */}
        <button 
          onClick={handleGoogleSignIn}
          disabled={loading}
          className="google-button"
        >
          <img 
            src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" 
            alt="Google"
            className="google-icon"
          />
          {loading ? 'Please wait...' : 'Continue with Google'}
        </button>

        <div className="divider">
          <span>or</span>
        </div>

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
              minLength={6}
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
              <button onClick={() => { setIsSignup(false); setError(''); setMessage(''); }} className="link-button">
                Sign In
              </button>
            </p>
          ) : (
            <p>
              New to CarbonTally?{' '}
              <button onClick={() => { setIsSignup(true); setError(''); setMessage(''); }} className="link-button">
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