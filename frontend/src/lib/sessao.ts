// Sessão do usuário, com a mesma interface no modo real (Supabase Auth) e no
// modo demonstração (nome guardado no aparelho, sem senha).
import { useSyncExternalStore } from 'react'
import { MODO_DEMO } from './config'
import { supabase } from './supabase'

export interface Sessao {
  id: string
  token: string
  email: string | null
  nome: string | null
  demo: boolean
}

const CHAVE_DEMO = 'styleup.demo'
let atual: Sessao | null = null
let carregada = false
const ouvintes = new Set<() => void>()

function publicar(nova: Sessao | null) {
  atual = nova
  carregada = true
  ouvintes.forEach((avisar) => avisar())
}

function ler(chave: string): string | null {
  try {
    return localStorage.getItem(chave)
  } catch {
    return null // navegação privada ou armazenamento bloqueado
  }
}

function sessaoDemo(nome: string): Sessao {
  const apelido = nome.trim().toLowerCase().replace(/[^a-z0-9]+/g, '-') || 'visitante'
  return { id: `demo-${apelido}`, token: `demo:${apelido}`, email: `${apelido}@demo.styleup.app`, nome, demo: true }
}

function iniciar() {
  if (MODO_DEMO || !supabase) {
    const nome = ler(CHAVE_DEMO)
    publicar(nome ? sessaoDemo(nome) : null)
    return
  }
  const converter = (s: { access_token: string; user: { id: string; email?: string; user_metadata?: Record<string, unknown> } } | null): Sessao | null =>
    s && {
      id: s.user.id,
      token: s.access_token,
      email: s.user.email ?? null,
      nome: (s.user.user_metadata?.nome as string | undefined) ?? null,
      demo: false,
    }
  supabase.auth.getSession().then(({ data }) => publicar(converter(data.session)))
  // O retorno é síncrono de propósito: chamar outros métodos do Supabase dentro
  // deste callback pode travar a renovação do token.
  supabase.auth.onAuthStateChange((_evento, s) => publicar(converter(s)))
}
iniciar()

export function useSessao(): { sessao: Sessao | null; carregando: boolean } {
  const sessao = useSyncExternalStore(
    (avisar) => {
      ouvintes.add(avisar)
      return () => ouvintes.delete(avisar)
    },
    () => atual,
  )
  return { sessao, carregando: !carregada }
}

export function sessaoAtual(): Sessao | null {
  return atual
}

export function usuarioIdAtual(): string | null {
  return atual?.id ?? null
}

/** Token válido para chamar a API (o Supabase renova quando está perto de expirar). */
export async function tokenAtual(): Promise<string | null> {
  if (MODO_DEMO || !supabase) return atual?.token ?? null
  const { data } = await supabase.auth.getSession()
  return data.session?.access_token ?? null
}

const TRADUCOES: [RegExp, string][] = [
  [/invalid login credentials/i, 'E-mail ou senha incorretos.'],
  [/email not confirmed/i, 'Confirme o seu e-mail antes de entrar (veja a caixa de entrada).'],
  [/already registered|already been registered/i, 'Este e-mail já tem conta. Tente entrar.'],
  [/password should be at least/i, 'A senha precisa ter pelo menos 6 caracteres.'],
  [/rate limit|too many/i, 'Muitas tentativas. Espere um minuto e tente de novo.'],
  [/failed to fetch|network/i, 'Sem conexão. Verifique a internet e tente de novo.'],
]

function traduzir(mensagem: string): string {
  return TRADUCOES.find(([padrao]) => padrao.test(mensagem))?.[1] ?? mensagem
}

export async function entrar(email: string, senha: string): Promise<void> {
  if (MODO_DEMO || !supabase) return entrarDemo(email.split('@')[0])
  const { error } = await supabase.auth.signInWithPassword({ email, password: senha })
  if (error) throw new Error(traduzir(error.message))
}

/** Devolve true quando a conta depende de confirmação por e-mail. */
export async function criarConta(nome: string, email: string, senha: string): Promise<boolean> {
  if (MODO_DEMO || !supabase) {
    entrarDemo(nome)
    return false
  }
  const { data, error } = await supabase.auth.signUp({
    email,
    password: senha,
    options: { data: { nome } },
  })
  if (error) throw new Error(traduzir(error.message))
  return !data.session
}

export async function recuperarSenha(email: string): Promise<void> {
  if (MODO_DEMO || !supabase) return
  const { error } = await supabase.auth.resetPasswordForEmail(email)
  if (error) throw new Error(traduzir(error.message))
}

export function entrarDemo(nome: string): void {
  const limpo = nome.trim() || 'Visitante'
  try {
    localStorage.setItem(CHAVE_DEMO, limpo)
  } catch {
    /* sem armazenamento: a sessão vale só até recarregar */
  }
  publicar(sessaoDemo(limpo))
}

export async function sair(): Promise<void> {
  // nada do usuário anterior pode ficar no aparelho (ele pode ser compartilhado)
  try {
    Object.keys(localStorage)
      .filter((k) => k.startsWith('styleup.'))
      .forEach((k) => localStorage.removeItem(k))
    if ('caches' in window) await caches.delete('fotos-pecas')
  } catch {
    /* limpeza é melhor esforço */
  }
  if (MODO_DEMO || !supabase) return publicar(null)
  await supabase.auth.signOut()
}
