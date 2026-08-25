// AuthCallback.js
import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { supabase } from './supabaseClient';
import { resolvePostLoginPath } from './v3/api';
import toast from 'react-hot-toast';

function AuthCallback() {
  const navigate = useNavigate();
  const [error, setError] = useState(null);

  useEffect(() => {
    const handleCallback = async () => {
      try {
        console.log('🔄 Processing OAuth callback...');
        console.log('📍 Current URL:', window.location.href);
        console.log('📍 URL params:', new URLSearchParams(window.location.search).toString());
        
        // Get the session
        const { data: { session }, error: sessionError } = await supabase.auth.getSession();
        
        if (sessionError) {
          console.error('❌ Session error:', sessionError);
          setError(sessionError.message);
          toast.error('Authentication failed');
          setTimeout(() => navigate('/login'), 2000);
          return;
        }
        
        if (session) {
          console.log('✅ OAuth callback successful!');
          console.log('👤 User:', session.user.email);
          toast.success(`Welcome ${session.user.email || 'to CarbonTally'}!`);
          // D29/F5 — land on the actor's server-authoritative workspace.
          navigate(await resolvePostLoginPath(), { replace: true });
        } else {
          console.log('⏳ No session found, waiting...');
          // Wait and retry
          await new Promise(resolve => setTimeout(resolve, 2000));
          
          const { data: { session: retrySession } } = await supabase.auth.getSession();
          
          if (retrySession) {
            console.log('✅ Retry successful!');
            navigate(await resolvePostLoginPath(), { replace: true });
          } else {
            console.error('❌ No session after retry');
            setError('Authentication failed - no session');
            toast.error('Failed to authenticate');
            navigate('/login');
          }
        }
      } catch (error) {
        console.error('❌ OAuth callback error:', error);
        setError(error.message);
        toast.error('Authentication failed');
        setTimeout(() => navigate('/login'), 2000);
      }
    };

    handleCallback();
  }, [navigate]);

  if (error) {
    return (
      <div className="loading-screen">
        <div className="loader">Error: {error}</div>
        <p style={{ marginTop: '1rem', color: '#64748b' }}>Redirecting to login...</p>
      </div>
    );
  }

  return (
    <div className="loading-screen">
      <div className="loader">Completing sign in...</div>
      <p style={{ marginTop: '1rem', color: '#64748b' }}>Please wait while we verify your account</p>
    </div>
  );
}

export default AuthCallback;