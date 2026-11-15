import { createClient, type SupabaseClient } from '@supabase/supabase-js'
import { MODO_DEMO, SUPABASE_ANON_KEY, SUPABASE_URL } from './config'

// Só existe fora do modo demonstração. Quem importa precisa checar MODO_DEMO.
export const supabase: SupabaseClient | null = MODO_DEMO
  ? null
  : createClient(SUPABASE_URL, SUPABASE_ANON_KEY)

export const BUCKET = 'pecas'
