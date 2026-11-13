import { supabase } from './supabase'

const BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export type Papel = 'superior' | 'inferior' | 'calcado' | 'sobreposicao'

export interface Analise {
  categoria: string
  rotulo: string
  papel: Papel
  formalidade: number
  temp_min: number
  temp_max: number
  resiste_chuva: boolean
  atributos: Record<string, string>
  cor_nome: string
  cor_hex: string
  cor_hsv: number[]
  neutra: boolean
  confianca: Record<string, number>
}

export interface Peca extends Analise {
  id: string
  codigo: string
  disponivel: boolean
  imagem_path: string | null
  criado_em: string
}

/** Entrada do catálogo de categorias. Note `chave`, não `categoria`. */
export interface CategoriaTaxonomia {
  chave: string
  rotulo: string
  papel: Papel
  formalidade: number
  temp_min: number
  temp_max: number
  resiste_chuva: boolean
}

export interface PecaDoLook {
  id: string
  codigo: string
  papel: Papel
  categoria: string
  rotulo: string
  cor_nome: string
  cor_hex: string
  imagem_path: string | null
}

export interface Look {
  id: string
  posicao: number
  score: number
  parcelas: Record<string, number>
  explicacao: string
  pecas: PecaDoLook[]
}

export interface Recomendacao {
  contexto: {
    id: string
    evento: string
    formalidade_alvo: number
    temperatura: number | null
    sensacao: number | null
    chuva_prob: number | null
    clima_automatico: boolean
  }
  looks: Look[]
}

export interface Evento {
  chave: string
  rotulo: string
  formalidade: number
}

/** Toda chamada leva o token do Supabase; é ele que a RLS usa no banco. */
async function requisitar<T>(caminho: string, init: RequestInit = {}): Promise<T> {
  const { data } = await supabase.auth.getSession()
  const token = data.session?.access_token
  if (!token) throw new Error('Sessão expirada. Entre novamente.')

  const cabecalhos = new Headers(init.headers)
  cabecalhos.set('Authorization', `Bearer ${token}`)
  if (init.body && !(init.body instanceof FormData)) {
    cabecalhos.set('Content-Type', 'application/json')
  }

  const resposta = await fetch(`${BASE}${caminho}`, { ...init, headers: cabecalhos })
  if (!resposta.ok) {
    const corpo = await resposta.json().catch(() => ({}))
    throw new Error(corpo.detail ?? `Falha na requisição (${resposta.status})`)
  }
  return resposta.status === 204 ? (undefined as T) : resposta.json()
}

export const api = {
  taxonomia: () => requisitar<CategoriaTaxonomia[]>('/pecas/taxonomia'),
  eventos: () => requisitar<Evento[]>('/eventos'),

  analisarFoto: (arquivo: File) => {
    const corpo = new FormData()
    corpo.append('foto', arquivo)
    return requisitar<Analise>('/pecas/analisar', { method: 'POST', body: corpo })
  },

  registrarPeca: (peca: Partial<Analise> & { imagem_path?: string }) =>
    requisitar<Peca>('/pecas', { method: 'POST', body: JSON.stringify(peca) }),

  listarPecas: (filtros: Record<string, string> = {}) => {
    const q = new URLSearchParams(filtros).toString()
    return requisitar<Peca[]>(`/pecas${q ? `?${q}` : ''}`)
  },

  atualizarPeca: (id: string, mudancas: Record<string, unknown>) =>
    requisitar<Peca>(`/pecas/${id}`, { method: 'PATCH', body: JSON.stringify(mudancas) }),

  removerPeca: (id: string) =>
    requisitar<void>(`/pecas/${id}`, { method: 'DELETE' }),

  recomendar: (contexto: {
    evento: string
    latitude?: number
    longitude?: number
    temperatura?: number
  }) =>
    requisitar<Recomendacao>('/recomendacoes', {
      method: 'POST',
      body: JSON.stringify(contexto),
    }),

  enviarFeedback: (look_id: string, aprovado: boolean) =>
    requisitar<{ registrado: boolean; pesos: Record<string, number> }>('/feedback', {
      method: 'POST',
      body: JSON.stringify({ look_id, aprovado }),
    }),

  metricas: () => requisitar<Record<string, number | null>>('/metricas'),
}

/** Geolocalização opcional: se o usuário negar, o contexto segue sem clima. */
export function posicaoAtual(): Promise<GeolocationCoordinates | null> {
  return new Promise((resolve) => {
    if (!navigator.geolocation) return resolve(null)
    navigator.geolocation.getCurrentPosition(
      (p) => resolve(p.coords),
      () => resolve(null),
      { timeout: 5000, maximumAge: 600_000 },
    )
  })
}
