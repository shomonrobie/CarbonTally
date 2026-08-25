import { createClient } from '@supabase/supabase-js'

// Local development overrides via CRA env vars (REACT_APP_*); the live project
// values remain the fallback so production builds are unaffected.
const supabaseUrl = process.env.REACT_APP_SUPABASE_URL || 'https://pvwiojoyaqywtydzcpbg.supabase.co' // e.g., https://abc123.supabase.co
const supabaseAnonKey = process.env.REACT_APP_SUPABASE_ANON_KEY || 'sb_publishable_eGUfRB5UC_u0TL8DF4XPrw_Bcsw8UA9' // starts with eyJ...

export const supabase = createClient(supabaseUrl, supabaseAnonKey)