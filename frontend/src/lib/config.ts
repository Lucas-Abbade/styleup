/** Configuração lida do ambiente do Vite. */
export const API_URL: string = (import.meta.env.VITE_API_URL ?? 'http://localhost:8000').replace(/\/$/, '')
export const SUPABASE_URL: string | undefined = import.meta.env.VITE_SUPABASE_URL
export const SUPABASE_ANON_KEY: string | undefined = import.meta.env.VITE_SUPABASE_ANON_KEY

/**
 * Sem Supabase configurado, o app roda em modo demonstração: login fictício e
 * fotos guardadas pelo backend (que também precisa estar em modo demonstração).
 */
export const MODO_DEMO: boolean =
  !SUPABASE_URL || !SUPABASE_ANON_KEY || SUPABASE_URL.includes('xxxxxxxx')

export const BUCKET = 'pecas'
