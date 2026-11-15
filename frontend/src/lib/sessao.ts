/**
 * Sessão do usuário, igual para o Supabase e para o modo demonstração.
 * O resto do app só conhece `useSessao`, `tokenAtual` e as ações daqui.
 */
import { useEffect, useState } from 'react'
import { API_URL, MODO_DEMO } from './config'
import { supabase } from './supabase'

export interface Sessao {
  token: string
  usuarioId: string | null // no modo demonstração vem depois, do /perfil
  email: string | null
  nome: string | null
  demo: boolean
}

const CHAVE_DEMO = 'styleup.demo'
const ouvintes = new Set<(s: Sessao | null) => void>()
let atual: Sessao | null = null
let pronta = false

function avisar(sessao: Sessao | null) {
  atual = sessao
  pronta = true
  ouvintes.forEach((o) => o(sessao))
}

function lerDemo(): Sessao | null {
  try {
    const bruto = localStorage.getItem(CHAVE_DEMO)
    if (!bruto) return null
    const { nome, email } = JSON.parse(bruto)
    const apelido = String(email || nome || 'visitante')
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .slice(0, 40)
    return { token: `demo:${apelido}`, usuarioId: null, email, nome, demo: true }
  } catch {
    return null
  }
}

function iniciar() {
  if (MODO_DEMO) {
    avisar(lerDemo())
    return
  }
  const paraSessao = (s: any): Sessao | null =>
    s
      ? {
          token: s.access_token,
          usuarioId: s.user.id,
          email: s.user.email ?? null,
          nome: s.user.user_metadata?.nome ?? null,
          demo: false,
        }
      : null
  supabase!.auth.getSession().then(({ data }) => avisar(paraSessao(data.session)))
  // O callback fica síncrono de propósito: chamar outro método do Supabase aqui
  // dentro pode travar o cliente (deadlock documentado do auth-js).
  supabase!.auth.onAuthStateChange((_evento, s) => avisar(paraSessao(s)))
}
iniciar()

export function useSessao(): { sessao: Sessao | null; carregando: boolean } {
  const [estado, setEstado] = useState({ sessao: atual, carregando: !pronta })
  useEffect(() => {
    const ouvinte = (sessao: Sessao | null) => setEstado({ sessao, carregando: false })
    ouvintes.add(ouvinte)
    if (pronta) ouvinte(atual)
    return () => void ouvintes.delete(ouvinte)
  }, [])
  return estado
}

/** Token para o cabeçalho Authorization; renovado pelo Supabase quando preciso. */
export async function tokenAtual(): Promise<string | null> {
  if (MODO_DEMO) return atual?.token ?? null
  const { data } = await supabase!.auth.getSession()
  return data.session?.access_token ?? null
}

export function usuarioIdAtual(): string | null {
  return atual?.usuarioId ?? null
}

function traduzir(mensagem: string): string {
  const m = mensagem.toLowerCase()
  if (m.includes('invalid login')) return 'E-mail ou senha incorretos.'
  if (m.includes('already registered')) return 'Já existe uma conta com este e-mail.'
  if (m.includes('email not confirmed')) return 'Confirme seu e-mail antes de entrar.'
  if (m.includes('password should be')) return 'A senha precisa ter pelo menos 6 caracteres.'
  if (m.includes('rate limit') || m.includes('too many'))
    return 'Muitas tentativas. Aguarde um pouco e tente de novo.'
  if (m.includes('fetch') || m.includes('network'))
    return 'Sem conexão. Verifique a internet e tente de novo.'
  return 'Não foi possível concluir. Tente de novo.'
}

/** Devolve `null` quando deu certo, ou a mensagem de erro para a tela. */
export async function entrar(email: string, senha: string): Promise<string | null> {
  if (MODO_DEMO) {
    localStorage.setItem(CHAVE_DEMO, JSON.stringify({ email, nome: email.split('@')[0] }))
    avisar(lerDemo())
    return null
  }
  const { error } = await supabase!.auth.signInWithPassword({ email, password: senha })
  return error ? traduzir(error.message) : null
}

/** `confirmar: true` quando o Supabase exige confirmação por e-mail. */
export async function criarConta(
  nome: string,
  email: string,
  senha: string,
): Promise<{ erro: string | null; confirmar: boolean }> {
  if (MODO_DEMO) {
    localStorage.setItem(CHAVE_DEMO, JSON.stringify({ email, nome }))
    const demo = lerDemo()
    // no Supabase o nome vai nos metadados do cadastro; aqui, direto ao perfil
    await fetch(`${API_URL}/perfil`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${demo?.token}` },
      body: JSON.stringify({ nome }),
    }).catch(() => undefined)
    avisar(demo)
    return { erro: null, confirmar: false }
  }
  const { data, error } = await supabase!.auth.signUp({
    email,
    password: senha,
    options: { data: { nome } },
  })
  if (error) return { erro: traduzir(error.message), confirmar: false }
  return { erro: null, confirmar: !data.session }
}

export async function recuperarSenha(email: string): Promise<string | null> {
  if (MODO_DEMO) return null
  const { error } = await supabase!.auth.resetPasswordForEmail(email, {
    redirectTo: window.location.origin,
  })
  return error ? traduzir(error.message) : null
}

export async function sair(): Promise<void> {
  // nada do usuário anterior pode sobrar num aparelho compartilhado
  try {
    Object.keys(localStorage)
      .filter((k) => k.startsWith('styleup.'))
      .forEach((k) => localStorage.removeItem(k))
    if ('caches' in window) await caches.delete('fotos-pecas')
  } catch {
    /* armazenamento indisponível: segue */
  }
  if (MODO_DEMO) avisar(null)
  else await supabase!.auth.signOut()
}
