// src/pages/Login.js (AdminSignIn)
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import toast from 'react-hot-toast';

const Login = () => {
  const [email, setEmail] = useState('shomonrobie@gmail.com');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const { signIn, user } = useAuth();
  const navigate = useNavigate();

  // If user is already logged in, redirect
  React.useEffect(() => {
    if (user) {
      navigate('/admin');
    }
  }, [user, navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const { data, error } = await signIn(email, password);
      
      if (error) {
        toast.error(error.message || 'Failed to sign in');
        setLoading(false);
        return;
      }

      if (data.user) {
        // Check if the user is authorized (admin or staff)
        const { data: staffData } = await supabase
          .from('staff_profiles')
          .select('role')
          .eq('id', data.user.id)
          .maybeSingle();

        if (!staffData) {
          // Check if user is org admin
          const { data: orgData } = await supabase
            .from('organization_members')
            .select('role')
            .eq('user_id', data.user.id)
            .eq('role', 'admin')
            .limit(1);

          if (!orgData || orgData.length === 0) {
            toast.error('Access denied. You are not authorized to access the admin dashboard.');
            await supabase.auth.signOut();
            setLoading(false);
            return;
          }
        }

        toast.success('Welcome back!');
        navigate('/admin');
      }
    } catch (error) {
      toast.error(error.message || 'Failed to sign in');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 to-secondary-50 flex items-center justify-center px-4">
      <div className="max-w-md w-full">
        <div className="bg-white rounded-2xl shadow-xl p-8">
          <div className="text-center mb-8">
            <div className="text-4xl mb-3">🌱</div>
            <h1 className="text-2xl font-bold text-gray-900">CarbonTally Admin</h1>
            <p className="text-gray-600 mt-1">Sign in to manage your carbon accounting platform</p>
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
              Need help? Contact support@carbontally.co.uk
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;