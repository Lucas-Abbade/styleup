import type { SupabaseClient } from '@supabase/supabase-js'

const url = import.meta.env.VITE_SUPABASE_URL
const chave = import.meta.env.VITE_SUPABASE_ANON_KEY

/**
 * O Supabase está configurado nesta cópia do frontend?
 *
 * Lido do ambiente na carga do módulo, sem tocar no SDK. A versão anterior
 * lançava erro no import quando faltavam as chaves, o que derrubava a aplicação
 * inteira em tela branca. Agora a ausência de credenciais é um estado previsto:
 * o app entra em modo demonstração e conversa com a API local.
 */
export const supabaseConfigurado = Boolean(url && chave)

/**
 * O SDK é importado sob demanda, não na carga da página.
 *
 * `@supabase/supabase-js` são 219 kB (58 kB comprimidos) — mais que React,
 * react-dom e react-router somados. Em modo demonstração ele nunca é usado, e
 * mesmo com Supabase configurado a tela de recomendação só precisa dele para ler
 * o token. Com o import dinâmico ele sai do carregamento inicial e entra apenas
 * quando a primeira chamada autenticada acontece.
 *
 * A promessa é memoizada: chamadas concorrentes compartilham a mesma
 * inicialização, e não criamos dois clientes (dois canais de auth, duas
 * assinaturas de sessão).
 */
let clientePromessa: Promise<SupabaseClient> | null = null

export function obterCliente(): Promise<SupabaseClient> {
  if (!supabaseConfigurado) {
    return Promise.reject(
      new Error('Supabase não configurado nesta instalação (modo demonstração).'),
    )
  }
  if (!clientePromessa) {
    clientePromessa = import('@supabase/supabase-js').then(({ createClient }) =>
      createClient(url, chave, {
        auth: { persistSession: true, autoRefreshToken: true },
      }),
    )
  }
  return clientePromessa
}

/** Token da sessão atual, ou `null` em demonstração e sem sessão. */
export async function tokenAtual(): Promise<string | null> {
  if (!supabaseConfigurado) return null
  const cliente = await obterCliente()
  const { data } = await cliente.auth.getSession()
  return data.session?.access_token ?? null
}

/** Envia a foto para o bucket privado, na pasta do próprio usuário. */
export async function enviarFoto(
  arquivo: File,
  usuarioId: string,
): Promise<string | null> {
  if (!supabaseConfigurado) return null // demonstração: a peça fica sem foto

  const cliente = await obterCliente()
  const extensao = arquivo.name.split('.').pop() ?? 'jpg'
  const caminho = `${usuarioId}/${crypto.randomUUID()}.${extensao}`
  const { error } = await cliente.storage.from('pecas').upload(caminho, arquivo, {
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
export async function urlAssinada(
  caminho: string,
  segundos = 3600,
): Promise<string | null> {
  if (!supabaseConfigurado) return null
  const cliente = await obterCliente()
  const { data } = await cliente.storage.from('pecas').createSignedUrl(caminho, segundos)
  return data?.signedUrl ?? null
}
