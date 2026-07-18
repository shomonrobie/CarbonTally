import { createClient } from '@supabase/supabase-js'

const supabaseUrl = 'https://pvwiojoyaqywtydzcpbg.supabase.co' // e.g., https://abc123.supabase.co
const supabaseAnonKey = 'sb_publishable_eGUfRB5UC_u0TL8DF4XPrw_Bcsw8UA9' // starts with eyJ...

export const supabase = createClient(supabaseUrl, supabaseAnonKey)