// Login.js - Fixed redirect logic

import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate, Link } from 'react-router-dom';

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  
  const { user, isStaff, loading: authLoading, authInitialized, signIn } = useAuth();
  const navigate = useNavigate();

  // Handle redirect based on auth state - REMOVED redirectAttempted
  useEffect(() => {
    console.log('🔄 Login useEffect triggered');
    console.log('📊 State:', { 
      authInitialized, 
      authLoading, 
      user: user?.email, 
      isStaff,
      userObject: user 
    });

    // Don't redirect if auth hasn't initialized yet
    if (!authInitialized || authLoading) {
      console.log('⏳ Auth initializing, waiting...');
      return;
    }

    // If no user, stay on login page
    if (!user) {
      console.log('ℹ️ No user, staying on login page');
      return;
    }

    console.log('🔄 Checking user role for redirect...');
    console.log('📊 isStaff from context:', isStaff);
    console.log('👤 User:', user?.email);

    // Staff user - redirect to admin/staff dashboard
    if (isStaff) {
      console.log('✅ Staff user - redirecting to staff dashboard');
      navigate('/staff-dashboard');
    } else {
      // Regular user - redirect to customer dashboard
      console.log('⚠️ User is not staff - redirecting to customer dashboard');
      navigate('/dashboard');
    }
  }, [user, isStaff, authLoading, authInitialized, navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      console.log('🔐 Submitting login for:', email);
      
      const result = await signIn(email, password);
      
      if (result.success) {
        console.log('✅ Login successful');
        // The useEffect will handle the redirect
      } else {
        setError(result.error || 'Login failed. Please try again.');
      }
    } catch (err) {
      console.error('❌ Login error:', err);
      setError('An unexpected error occurred. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // If auth is still loading, show a loading state
  if (!authInitialized || authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Admin Login
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Enter your credentials to access the admin dashboard
          </p>
        </div>
        
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {error && (
            <div className="rounded-md bg-red-50 p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-red-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-red-800">{error}</h3>
                </div>
              </div>
            </div>
          )}
          
          <div className="rounded-md shadow-sm -space-y-px">
            <div>
              <label htmlFor="email" className="sr-only">
                Email address
              </label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-green-500 focus:border-green-500 focus:z-10 sm:text-sm"
                placeholder="Email address"
                disabled={loading}
              />
            </div>
            <div>
              <label htmlFor="password" className="sr-only">
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-green-500 focus:border-green-500 focus:z-10 sm:text-sm"
                placeholder="Password"
                disabled={loading}
              />
            </div>
          </div>

          <div>
            <button
              type="submit"
              disabled={loading}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <span className="flex items-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="fill-current" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Signing in...
                </span>
              ) : (
                'Sign in'
              )}
            </button>
          </div>
          
          <div className="text-sm text-center">
            <Link to="/" className="font-medium text-green-600 hover:text-green-500">
              ← Back to Home
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Login;