//frontend/src/Login.js
import React, { useState, useEffect } from 'react';
import { supabase } from './supabaseClient';
import { useNavigate, useLocation } from 'react-router-dom';
import { resolvePostLoginPath } from './v3/api';
import './css/Login.css';

function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [isSignup, setIsSignup] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  // Check for existing session and OAuth callback
  useEffect(() => {
    const checkSession = async () => {
      try {
        console.log('🔍 Checking session...');
        const { data: { session }, error: sessionError } = await supabase.auth.getSession();
        
        console.log('📊 Session data:', session ? 'Session exists' : 'No session');
        
        if (sessionError) {
          console.error('❌ Session error:', sessionError);
          return;
        }
        
        if (session) {
          console.log('✅ User already logged in:', session.user.email);
          // D29/F5 — land on the actor's server-authoritative workspace.
          resolvePostLoginPath().then((path) => navigate(path, { replace: true }));
          return;
        }

        // Check if this is an OAuth callback (after Google redirect)
        const params = new URLSearchParams(location.search);
        const code = params.get('code');
        const errorParam = params.get('error');
        const errorDescription = params.get('error_description');
        
        console.log('🔍 URL params:', { code: !!code, error: errorParam });

        if (errorParam) {
          console.error('OAuth Error:', errorDescription);
          setError(`Authentication failed: ${errorDescription || errorParam}`);
          // Remove error params from URL
          window.history.replaceState({}, document.title, '/login');
          return;
        }

        if (code) {
          console.log('🔄 OAuth callback detected with code');
          // Supabase should automatically exchange the code for a session
          // Wait a moment for the session to be set
          await new Promise(resolve => setTimeout(resolve, 1000));
          
          // Check if session is now available
          const { data: { session: newSession } } = await supabase.auth.getSession();
          
          if (newSession) {
            console.log('✅ OAuth callback successful! User:', newSession.user.email);
            // D29/F5 — land on the actor's server-authoritative workspace.
            resolvePostLoginPath().then((path) => navigate(path, { replace: true }));
          } else {
            console.log('⏳ Session not ready yet, waiting for auth state change...');
          }
        }
      } catch (error) {
        console.error('Session check error:', error);
      }
    };

    checkSession();

    // Listen for auth state changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (event, session) => {
        console.log('🔐 Login auth event:', event);
        
        if (event === 'SIGNED_IN' && session) {
          console.log('✅ User signed in:', session.user.email);
          // D29/F5 — land on the actor's server-authoritative workspace.
          resolvePostLoginPath().then((path) => navigate(path, { replace: true }));
        } else if (event === 'SIGNED_OUT') {
          console.log('👋 User signed out');
        }
      }
    );

    return () => {
      subscription.unsubscribe();
    };
    // ✅ Fixed: Removed 'location' from dependencies and used proper dependency array
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [navigate]); // Only navigate is needed

  // Handle email/password authentication
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
        // D29/F5 — land on the actor's server-authoritative workspace
        // (org member -> /home, staff -> /ops, consultant -> /consultant).
        navigate(await resolvePostLoginPath());
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
const handleGoogleSignIn = async () => {
  console.log('🔄 Starting Google sign-in...');
  setLoading(true);
  setError('');
  
  try {
    // Environment-driven redirect: defaults to the app's own origin + the V3
    // auth callback so every OAuth session resolves through the
    // server-authoritative post-login path (D29/D35) — never the legacy
    // /dashboard. Override with REACT_APP_OAUTH_REDIRECT_URL when needed.
    const redirectUrl =
      process.env.REACT_APP_OAUTH_REDIRECT_URL ||
      `${window.location.origin}/auth/callback`;
    
    console.log('📍 Using Client ID:', process.env.REACT_APP_GOOGLE_CLIENT_ID || 'Not set');
    console.log('📍 Redirect URL:', redirectUrl);
    console.log('📍 Supabase URL:', process.env.REACT_APP_SUPABASE_URL);
    
    const { data, error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: redirectUrl,
        queryParams: {
          access_type: 'offline',
          prompt: 'consent',
        },
        // Force fresh OAuth flow
        skipBrowserRedirect: false,
      },
    });

    if (error) {
      console.error('❌ OAuth error details:', error);
      throw error;
    }
    
    console.log('✅ OAuth initiated successfully');
    
  } catch (err) {
    console.error('❌ Google sign-in error:', err);
    setError(`Failed to sign in: ${err.message || 'Unknown error'}`);
    setLoading(false);
  }
};


  return (
    <div className="login-container">
      <div className="login-box">
        <h1>🌱 CarbonTally</h1>
        <p className="tagline">Automated Carbon Accounting for UK Businesses</p>
        
        {/* Google Sign-In Button */}
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