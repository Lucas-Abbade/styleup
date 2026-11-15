// Configuração lida do ambiente (arquivo .env.local).
const url = (import.meta.env.VITE_SUPABASE_URL as string | undefined)?.trim() ?? ''
const chave = (import.meta.env.VITE_SUPABASE_ANON_KEY as string | undefined)?.trim() ?? ''

export const API_URL = (
  (import.meta.env.VITE_API_URL as string | undefined) ?? 'http://localhost:8000'
).replace(/\/$/, '')

export const SUPABASE_URL = url
export const SUPABASE_ANON_KEY = chave

// Sem Supabase configurado, o app roda em modo demonstração: login fictício e
// fotos guardadas pelo backend. Serve para desenvolver e para apresentar.
export const MODO_DEMO = !url || !chave || url.includes('xxxxxxxx')
