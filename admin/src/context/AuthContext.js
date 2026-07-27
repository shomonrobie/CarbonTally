// AuthContext.js - COMPLETE FIXED VERSION

import React, { createContext, useContext, useState, useEffect } from 'react';
import { supabase } from '../supabaseClient';

// Create context
const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [isStaff, setIsStaff] = useState(false);
  const [loading, setLoading] = useState(true);
  const [authInitialized, setAuthInitialized] = useState(false);

  useEffect(() => {
    console.log('🔐 Initializing auth...');

    // Get session from Supabase
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        console.log('🔄 Auth state changed:', event);
        console.log('📦 Full session object:', session);
        console.log('📧 Session user object:', session?.user);
        console.log('📧 Session user email:', session?.user?.email);

        if (event === 'SIGNED_IN' || event === 'TOKEN_REFRESHED') {
          if (session?.user) {
            // IMPORTANT: Get email from session.user.email
            const userEmail = session.user.email;
            
            console.log('✅ User signed in with email:', userEmail);
            
            if (!userEmail) {
              console.error('❌ No email found in session user object!');
              // Try to get from user_metadata as fallback
              const fallbackEmail = session.user.user_metadata?.email;
              if (fallbackEmail) {
                console.log('📧 Found email in user_metadata:', fallbackEmail);
                setUser(session.user);
                await checkUserAndStaffStatus(fallbackEmail);
              } else {
                console.error('❌ No email found anywhere in user object');
                setAuthInitialized(true);
                setLoading(false);
              }
              return;
            }
            
            setUser(session.user);
            await checkUserAndStaffStatus(userEmail);
          }
        } else if (event === 'SIGNED_OUT') {
          console.log('👋 User signed out');
          setUser(null);
          setIsStaff(false);
          setAuthInitialized(true);
        }
      }
    );

    // Initial session check
    const initializeAuth = async () => {
      try {
        const { data: { session } } = await supabase.auth.getSession();
        console.log('🔍 Initial session check:', session?.user?.email);

        if (session?.user) {
          const userEmail = session.user.email;
          
          if (!userEmail) {
            console.error('❌ No email in initial session');
            setAuthInitialized(true);
            setLoading(false);
            return;
          }
          
          console.log('🔄 Initial session found with email:', userEmail);
          setUser(session.user);
          await checkUserAndStaffStatus(userEmail);
        } else {
          console.log('🔍 No initial session found');
          setAuthInitialized(true);
          setLoading(false);
        }
      } catch (error) {
        console.error('❌ Auth initialization error:', error);
        setAuthInitialized(true);
        setLoading(false);
      }
    };

    initializeAuth();

    return () => {
      subscription.unsubscribe();
    };
  }, []);

  // Simplified staff check - only checks staff_profiles
  const checkUserAndStaffStatus = async (email) => {
    try {
      console.log('🔍 Checking staff status for email:', email);
      
      // IMPORTANT: Validate email is defined
      if (!email) {
        console.error('❌ No email provided to checkUserAndStaffStatus');
        setIsStaff(false);
        setAuthInitialized(true);
        setLoading(false);
        return;
      }

      // Remove .single() and use normal query to avoid 406 error
      const { data: staffData, error: staffError } = await supabase
        .from('staff_profiles')
        .select('role, is_active')
        .eq('email', email)
        .limit(10); // Add limit to avoid potential issues

      console.log('📊 Staff query results:', { 
        data: staffData, 
        error: staffError,
        email: email 
      });

      if (staffError) {
        console.log('ℹ️ Staff query error:', staffError.message);
        setIsStaff(false);
      } else if (staffData && staffData.length > 0) {
        // Check if any matching record is active
        const activeStaff = staffData.find(record => record.is_active === true);
        if (activeStaff) {
          console.log('✅ User is staff with role:', activeStaff.role);
          setIsStaff(true);
        } else {
          console.log('ℹ️ User found in staff_profiles but inactive');
          setIsStaff(false);
        }
      } else {
        console.log('ℹ️ User not found in staff_profiles');
        setIsStaff(false);
      }

    } catch (error) {
      console.error('❌ Error checking staff status:', error);
      setIsStaff(false);
    } finally {
      setAuthInitialized(true);
      setLoading(false);
    }
  };

  const signIn = async (email, password) => {
    try {
      console.log('🔐 Attempting sign in for:', email);
      
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password
      });

      if (error) throw error;

      if (data.user) {
        console.log('✅ Sign in successful');
        console.log('📧 User email from sign in:', data.user.email);
        
        const userEmail = data.user.email;
        
        // Important: Set user first
        setUser(data.user);
        
        // Then check staff status with the email
        if (userEmail) {
          await checkUserAndStaffStatus(userEmail);
        } else {
          console.error('❌ No email from sign in response');
          setAuthInitialized(true);
          setLoading(false);
        }
        
        return { success: true, user: data.user };
      }

      return { success: false, error: 'No user returned' };
    } catch (error) {
      console.error('❌ Sign in error:', error);
      return { success: false, error: error.message };
    }
  };

  const signOut = async () => {
    try {
      await supabase.auth.signOut();
      setUser(null);
      setIsStaff(false);
      setAuthInitialized(true);
    } catch (error) {
      console.error('❌ Sign out error:', error);
    }
  };

  const value = {
    user,
    isStaff,
    loading,
    authInitialized,
    signIn,
    signOut,
    checkUserAndStaffStatus
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};