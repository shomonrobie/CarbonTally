// frontend/src/MagicLink.jsx
import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { supabase } from './supabaseClient';
import toast from 'react-hot-toast';

export default function MagicLink() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const handleMagicLink = async () => {
      const token = searchParams.get('token');
      const email = searchParams.get('email');

      if (!token || !email) {
        setError('Invalid magic link. Missing token or email.');
        setLoading(false);
        return;
      }

      try {
        // ✅ Call your backend to validate the token and auto-login
        const response = await fetch(
          `${process.env.REACT_APP_API_URL || 'https://carbontally-api.onrender.com'}/api/auth/magic?token=${token}&email=${email}`
        );

        const data = await response.json();

        if (!response.ok) {
          throw new Error(data.detail || 'Invalid or expired magic link');
        }

        if (data.status === 'user_exists') {
          toast.info('Account already exists. Please sign in.');
          navigate('/beta-login');
          return;
        }

        if (data.status === 'success' && data.session) {
          // ✅ Set the session and redirect to dashboard
          await supabase.auth.setSession(data.session);
          toast.success('🎉 Welcome to CarbonTally Beta!');
          navigate('/dashboard');
        } else {
          throw new Error('Failed to authenticate');
        }
      } catch (err) {
        console.error('Magic link error:', err);
        setError(err.message || 'Authentication failed');
        toast.error('Authentication failed. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    handleMagicLink();
  }, [searchParams, navigate]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 to-secondary-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Logging you in...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 to-secondary-50 px-4">
        <div className="max-w-md w-full bg-white rounded-2xl shadow-xl p-8 text-center">
          <div className="text-4xl mb-4">❌</div>
          <h2 className="text-xl font-bold text-gray-900 mb-2">Magic Link Error</h2>
          <p className="text-gray-600 mb-6">{error}</p>
          <button
            onClick={() => navigate('/beta-login')}
            className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
          >
            Go to Login
          </button>
        </div>
      </div>
    );
  }

  return null;
}