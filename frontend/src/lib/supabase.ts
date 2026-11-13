import { createClient } from '@supabase/supabase-js'

const url = import.meta.env.VITE_SUPABASE_URL
const chave = import.meta.env.VITE_SUPABASE_ANON_KEY

if (!url || !chave) {
  throw new Error(
    'Configure VITE_SUPABASE_URL e VITE_SUPABASE_ANON_KEY em frontend/.env.local',
  )
}

export const supabase = createClient(url, chave, {
  auth: { persistSession: true, autoRefreshToken: true },
})

/** Envia a foto para o bucket privado, na pasta do próprio usuário. */
export async function enviarFoto(arquivo: File, usuarioId: string): Promise<string> {
  const extensao = arquivo.name.split('.').pop() ?? 'jpg'
  const caminho = `${usuarioId}/${crypto.randomUUID()}.${extensao}`
  const { error } = await supabase.storage.from('pecas').upload(caminho, arquivo, {
    contentType: arquivo.type,
    upsert: false,
  })
  if (error) throw error
  return caminho
}

/**
 * URL temporária para exibir uma foto. O bucket é privado, então não existe
 * link permanente — é o que o RNF10 pede.
 */
export async function urlAssinada(caminho: string, segundos = 3600): Promise<string | null> {
  const { data } = await supabase.storage.from('pecas').createSignedUrl(caminho, segundos)
  return data?.signedUrl ?? null
}
