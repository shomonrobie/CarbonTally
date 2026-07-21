import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.REACT_APP_SUPABASE_URL;
const supabaseAnonKey = process.env.REACT_APP_SUPABASE_ANON_KEY;
if (!supabaseUrl || !supabaseAnonKey) {
  console.error('❌ Missing Supabase credentials! Check your .env file');
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

// Admin helper to check if user is admin or staff
export const isAdminOrStaff = async (userId) => {
  if (!userId) return false;
  
  try {
    // Check if user is in staff_profiles table
    const { data: staffData, error: staffError } = await supabase
      .from('staff_profiles')
      .select('role')
      .eq('id', userId)
      .single();
    
    if (staffData) {
      return { isStaff: true, role: staffData.role };
    }
    
    // Check if user is an admin in any organization
    const { data: orgData, error: orgError } = await supabase
      .from('organization_members')
      .select('role')
      .eq('user_id', userId)
      .eq('role', 'admin')
      .limit(1);
    
    if (orgData && orgData.length > 0) {
      return { isStaff: false, role: 'admin' };
    }
    
    return { isStaff: false, role: 'user' };
  } catch (error) {
    console.error('Error checking admin status:', error);
    return { isStaff: false, role: 'user' };
  }
};