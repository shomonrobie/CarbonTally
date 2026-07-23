// src/pages/Login.js
import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { supabase } from '../supabaseClient';
import toast from 'react-hot-toast';

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [redirecting, setRedirecting] = useState(false);
  const { signIn, user, isStaff, checkStaffStatus } = useAuth();
  const navigate = useNavigate();
  const redirectAttempted = useRef(false);

  useEffect(() => {
    if (user && !redirecting && !redirectAttempted.current) {
      const timer = setTimeout(() => {
        handleRedirect(user.id);
      }, 500);
      return () => clearTimeout(timer);
    }
  }, [user, isStaff]);

  const handleRedirect = async (userId) => {
    if (redirectAttempted.current || redirecting) return;
    redirectAttempted.current = true;
    setRedirecting(true);

    try {
      console.log('🔄 Checking user role for redirect...');
      console.log('📊 isStaff from context:', isStaff);

      // ✅ Staff user - redirect to staff dashboard
      if (isStaff === true) {
        console.log('✅ Staff user - redirecting to staff dashboard');
        // The basename is /admin, so /staff/dashboard becomes /admin/staff/dashboard
        navigate('/staff/dashboard');
        setRedirecting(false);
        return;
      }

      // ✅ Double-check staff status
      const { data: staffData } = await supabase
        .from('staff_profiles')
        .select('role')
        .eq('id', userId)
        .maybeSingle();

      if (staffData) {
        console.log('✅ Staff found via direct query');
        await checkStaffStatus(userId);
        navigate('/staff/dashboard');
        setRedirecting(false);
        return;
      }

      // ✅ Check organization admin
      const { data: orgData } = await supabase
        .from('organization_members')
        .select('role')
        .eq('user_id', userId)
        .eq('role', 'admin')
        .maybeSingle();

      if (orgData) {
        console.log('✅ Organization admin - redirecting to admin');
        navigate('/admin');
        setRedirecting(false);
        return;
      }

      // ❌ No role found
      console.warn('⚠️ No role found for user');
      toast.error('Access denied. No valid role found.');
      await supabase.auth.signOut();
      navigate('/login');
      setRedirecting(false);

    } catch (error) {
      console.error('❌ Redirect error:', error);
      toast.error('Error determining user role');
      setRedirecting(false);
      redirectAttempted.current = false;
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setRedirecting(false);
    redirectAttempted.current = false;

    try {
      const { data, error } = await signIn(email, password);
      
      if (error) {
        toast.error(error.message || 'Failed to sign in');
        setLoading(false);
        return;
      }

      if (data.user) {
        console.log('✅ User signed in, checking staff status...');
        await checkStaffStatus(data.user.id);
        setTimeout(() => {
          setLoading(false);
        }, 300);
      }
    } catch (error) {
      toast.error(error.message || 'Failed to sign in');
      setLoading(false);
    }
  };

  if (redirecting) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 to-secondary-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Redirecting to dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 to-secondary-50 flex items-center justify-center px-4">
      <div className="max-w-md w-full">
        <div className="bg-white rounded-2xl shadow-xl p-8">
          <div className="text-center mb-8">
            <div className="text-4xl mb-3">🌱</div>
            <h1 className="text-2xl font-bold text-gray-900">CarbonTally Admin</h1>
            <p className="text-gray-600 mt-1">Staff login portal</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Email Address
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none transition-all duration-200"
                placeholder="staff@carbontally.co.uk"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none transition-all duration-200"
                placeholder="••••••••"
                required
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors duration-200 font-medium disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></span>
                  Signing in...
                </span>
              ) : (
                'Sign In'
              )}
            </button>
          </form>

          <div className="mt-6 text-center">
            <p className="text-sm text-gray-600">
              This portal is for staff members only.
            </p>
            <p className="text-sm text-gray-500 mt-1">
              Customers please use the main application.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;