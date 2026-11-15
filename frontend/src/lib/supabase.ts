import { createClient, type SupabaseClient } from '@supabase/supabase-js'
import { MODO_DEMO, SUPABASE_ANON_KEY, SUPABASE_URL } from './config'

/** Cliente do Supabase; `null` no modo demonstração. */
export const supabase: SupabaseClient | null = MODO_DEMO
  ? null
  : createClient(SUPABASE_URL!, SUPABASE_ANON_KEY!)
