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
  const [userExists, setUserExists] = useState(false);
  const [email, setEmail] = useState('');

  useEffect(() => {
    const handleMagicLink = async () => {
      const token = searchParams.get('token');
      const emailParam = searchParams.get('email');

      if (!token || !emailParam) {
        setError('Invalid magic link. Missing token or email.');
        setLoading(false);
        return;
      }

      setEmail(emailParam);

      try {
        // Call your backend to validate the token
        const response = await fetch(
          `${process.env.REACT_APP_API_URL || 'https://carbontally-api.onrender.com'}/api/auth/magic?token=${token}&email=${emailParam}`
        );

        const data = await response.json();

        if (!response.ok) {
          throw new Error(data.detail || 'Invalid magic link');
        }

        // ✅ User already exists - show clear message
        if (data.status === 'user_exists') {
          setUserExists(true);
          toast.info('🔐 This email is already registered.');
          toast.success('Please sign in with your existing account.');
          setLoading(false);
          return;
        }

        // ✅ New user created and signed in
        if (data.status === 'success') {
          if (data.session) {
            await supabase.auth.setSession(data.session);
            toast.success('🎉 Welcome to CarbonTally Beta! Your account has been created.');
            navigate('/dashboard');
            return;
          }

          if (data.temp_password) {
            localStorage.setItem('temp_password', data.temp_password);
            localStorage.setItem('temp_email', emailParam);
            toast.info('✅ Account created! Please set your password.');
            navigate('/beta-login?auto=true');
            return;
          }

          toast.success('✅ Account created! Please sign in.');
          navigate('/beta-login');
        }
      } catch (err) {
        console.error('Magic link error:', err);
        setError(err.message || 'Failed to authenticate');
        toast.error('Failed to authenticate. Please try again.');
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
          <p className="mt-4 text-gray-600">Setting up your account...</p>
        </div>
      </div>
    );
  }

  // ✅ Special view for existing users
  if (userExists) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 to-secondary-50 px-4">
        <div className="max-w-md w-full bg-white rounded-2xl shadow-xl p-8 text-center">
          <div className="text-5xl mb-4">🔐</div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Account Already Exists</h2>
          <p className="text-gray-600 mb-2">
            The email <strong className="text-gray-900">{email}</strong> is already registered with CarbonTally.
          </p>
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6 text-left">
            <p className="text-sm text-blue-800">
              💡 You already have an account. Please sign in using your existing credentials.
            </p>
          </div>
          <div className="space-y-3">
            <button
              onClick={() => navigate('/beta-login')}
              className="w-full px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors font-medium"
            >
              Go to Login
            </button>
            <button
              onClick={() => {
                // Send password reset email
                supabase.auth.resetPasswordForEmail(email);
                toast.success('📧 Password reset email sent!');
              }}
              className="w-full px-6 py-3 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors font-medium"
            >
              Forgot Password?
            </button>
          </div>
          <p className="mt-4 text-sm text-gray-500">
            Having trouble? <a href="mailto:support@carbontally.co.uk" className="text-primary-600 hover:underline">Contact Support</a>
          </p>
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
            onClick={() => navigate('/')}
            className="px-6 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
          >
            Return Home
          </button>
        </div>
      </div>
    );
  }

  return null;
}