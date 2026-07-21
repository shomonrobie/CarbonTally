// src/context/AuthContext.js
import React, { createContext, useContext, useEffect, useState } from 'react';
import { supabase } from '../supabaseClient';

const AuthContext = createContext({});

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isStaff, setIsStaff] = useState(false);
  const [staffRole, setStaffRole] = useState(null);

  const checkStaffStatus = async (userId) => {
    try {
      console.log('🔍 Checking staff status for user:', userId);
      
      // Check staff_profiles table
      const { data: staffData, error: staffError } = await supabase
        .from('staff_profiles')
        .select('role')
        .eq('id', userId)
        .maybeSingle();

      if (staffError) {
        console.error('❌ Staff profile error:', staffError);
        setIsStaff(false);
        setStaffRole(null);
        return;
      }

      if (staffData) {
        console.log('✅ User is staff with role:', staffData.role);
        setIsStaff(true);
        setStaffRole(staffData.role);
        return;
      }

      // If not in staff_profiles, check if user is org admin
      const { data: orgData, error: orgError } = await supabase
        .from('organization_members')
        .select('role')
        .eq('user_id', userId)
        .eq('role', 'admin')
        .limit(1);

      if (!orgError && orgData && orgData.length > 0) {
        console.log('✅ User is an organization admin');
        setIsStaff(true);
        setStaffRole('admin');
        return;
      }

      console.log('ℹ️ User is not a staff member or admin');
      setIsStaff(false);
      setStaffRole(null);
    } catch (error) {
      console.error('❌ Error checking staff status:', error);
      setIsStaff(false);
      setStaffRole(null);
    }
  };

  useEffect(() => {
    const initAuth = async () => {
      try {
        console.log('🔐 Initializing auth...');
        const { data: { session }, error } = await supabase.auth.getSession();
        
        if (error) {
          console.error('❌ Auth session error:', error);
          setLoading(false);
          return;
        }
        
        console.log('✅ Auth initialized:', session?.user?.email || 'No user');
        setSession(session);
        setUser(session?.user ?? null);
        
        if (session?.user) {
          await checkStaffStatus(session.user.id);
        }
        setLoading(false);
      } catch (err) {
        console.error('❌ Auth initialization error:', err);
        setLoading(false);
      }
    };

    initAuth();

    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        console.log('🔄 Auth state changed:', event);
        setSession(session);
        setUser(session?.user ?? null);
        if (session?.user) {
          await checkStaffStatus(session.user.id);
        } else {
          setIsStaff(false);
          setStaffRole(null);
        }
        setLoading(false);
      }
    );

    return () => subscription.unsubscribe();
  }, []);

  const signIn = async (email, password) => {
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });
    return { data, error };
  };

  const signOut = async () => {
    const { error } = await supabase.auth.signOut();
    return { error };
  };

  const value = {
    user,
    session,
    loading,
    isStaff,
    staffRole,
    signIn,
    signOut,
    checkStaffStatus,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export default AuthProvider;