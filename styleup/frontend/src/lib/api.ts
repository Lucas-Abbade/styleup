import { supabaseConfigurado, tokenAtual } from './supabase'

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
  /** false quando o modelo de visão não está instalado: a categoria é palpite. */
  modelo_disponivel: boolean
  aviso: string | null
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

export interface ResumoGuardaRoupa {
  total: number
  por_papel: Record<Papel, number>
  faltando: Papel[]
  pode_recomendar: boolean
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

export interface ContextoRecomendacao {
  id: string
  evento: string
  rotulo_evento: string
  formalidade_alvo: number
  temperatura: number | null
  sensacao: number | null
  chuva_prob: number | null
  clima_automatico: boolean
}

export interface Recomendacao {
  contexto: ContextoRecomendacao
  looks: Look[]
}

export interface Evento {
  chave: string
  rotulo: string
  formalidade: number
}

export interface Saude {
  status: string
  ambiente: string
  modo_demo: boolean
  supabase_configurado: boolean
  visao_disponivel: boolean
}

/**
 * Erro de API que preserva o status HTTP.
 *
 * A tela precisa distinguir os casos: 409 é uma situação do guarda-roupa do
 * usuário (falta peça) e merece uma orientação; 401 pede novo login; 5xx e falha
 * de rede pedem apenas "tentar de novo". Com `Error` puro tudo virava a mesma
 * mensagem genérica.
 */
export class ErroApi extends Error {
  constructor(
    readonly status: number,
    mensagem: string,
  ) {
    super(mensagem)
    this.name = 'ErroApi'
  }

  /** Situação dos dados do usuário, não falha do sistema. */
  get ehConflito() {
    return this.status === 409
  }

  get ehSessaoExpirada() {
    return this.status === 401
  }

  /** Vale oferecer um botão de "tentar de novo". */
  get vaiTentarDeNovo() {
    return this.status === 0 || this.status >= 500
  }
}

/**
 * Sinal de cancelamento reconhecido como "não é erro".
 *
 * Quando o componente desmonta, abortamos as requisições em voo. Sem esta
 * distinção, cada navegação entre telas pintava um painel vermelho de falha em
 * cima de uma tela que o usuário já deixou.
 */
export class RequisicaoCancelada extends Error {
  constructor() {
    super('Requisição cancelada.')
    this.name = 'RequisicaoCancelada'
  }
}

export function foiCancelada(erro: unknown): boolean {
  return erro instanceof RequisicaoCancelada
}

async function requisitar<T>(caminho: string, init: RequestInit = {}): Promise<T> {
  const cabecalhos = new Headers(init.headers)

  // Em modo demonstração não há sessão: a API local aceita a requisição sem token.
  if (supabaseConfigurado) {
    const token = await tokenAtual()
    if (!token) throw new ErroApi(401, 'Sessão expirada. Entre novamente.')
    cabecalhos.set('Authorization', `Bearer ${token}`)
  }

  if (init.body && !(init.body instanceof FormData)) {
    cabecalhos.set('Content-Type', 'application/json')
  }

  let resposta: Response
  try {
    resposta = await fetch(`${BASE}${caminho}`, { ...init, headers: cabecalhos })
  } catch (e) {
    if (e instanceof DOMException && e.name === 'AbortError') {
      throw new RequisicaoCancelada()
    }
    // status 0 = não chegou ao servidor (API desligada, rede caída, CORS)
    throw new ErroApi(
      0,
      `Não foi possível falar com a API em ${BASE}. Confirme se o backend está rodando.`,
    )
  }

  if (!resposta.ok) {
    const corpo = await resposta.json().catch(() => null)
    throw new ErroApi(resposta.status, extrairMensagem(corpo, resposta.status))
  }
  return resposta.status === 204 ? (undefined as T) : resposta.json()
}

/** O FastAPI usa `detail`, que pode ser texto ou a lista de erros do Pydantic. */
function extrairMensagem(corpo: unknown, status: number): string {
  const detalhe = (corpo as { detail?: unknown } | null)?.detail
  if (typeof detalhe === 'string') return detalhe
  if (Array.isArray(detalhe)) {
    const primeiro = detalhe[0] as { msg?: string } | undefined
    if (primeiro?.msg) return primeiro.msg
  }
  return `Falha na requisição (${status}).`
}

export interface PedidoRecomendacao {
  evento: string
  latitude?: number
  longitude?: number
  temperatura?: number
  chuva_prob?: number
}

export interface Metricas {
  consultas: number
  looks_aprovados: number
  hit_rate_3: number | null
  precision_3: number | null
}

/** `signal` é opcional em tudo: quem monta em `useEffect` deve passá-lo. */
export const api = {
  saude: (signal?: AbortSignal) => requisitar<Saude>('/saude', { signal }),

  taxonomia: (signal?: AbortSignal) =>
    requisitar<CategoriaTaxonomia[]>('/pecas/taxonomia', { signal }),

  eventos: (signal?: AbortSignal) => requisitar<Evento[]>('/eventos', { signal }),

  resumo: (signal?: AbortSignal) =>
    requisitar<ResumoGuardaRoupa>('/pecas/resumo', { signal }),

  analisarFoto: (arquivo: File, signal?: AbortSignal) => {
    const corpo = new FormData()
    corpo.append('foto', arquivo)
    return requisitar<Analise>('/pecas/analisar', {
      method: 'POST',
      body: corpo,
      signal,
    })
  },

  registrarPeca: (
    peca: Partial<Analise> & { imagem_path?: string | null },
    signal?: AbortSignal,
  ) => requisitar<Peca>('/pecas', { method: 'POST', body: JSON.stringify(peca), signal }),

  listarPecas: (filtros: Record<string, string> = {}, signal?: AbortSignal) => {
    const q = new URLSearchParams(filtros).toString()
    return requisitar<Peca[]>(`/pecas${q ? `?${q}` : ''}`, { signal })
  },

  atualizarPeca: (
    id: string,
    mudancas: Record<string, unknown>,
    signal?: AbortSignal,
  ) =>
    requisitar<Peca>(`/pecas/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(mudancas),
      signal,
    }),

  removerPeca: (id: string, signal?: AbortSignal) =>
    requisitar<void>(`/pecas/${id}`, { method: 'DELETE', signal }),

  recomendar: (pedido: PedidoRecomendacao, signal?: AbortSignal) =>
    requisitar<Recomendacao>('/recomendacoes', {
      method: 'POST',
      body: JSON.stringify(pedido),
      signal,
    }),

  enviarFeedback: (look_id: string, aprovado: boolean, signal?: AbortSignal) =>
    requisitar<{ registrado: boolean; pesos: Record<string, number> }>('/feedback', {
      method: 'POST',
      body: JSON.stringify({ look_id, aprovado }),
      signal,
    }),

  metricas: (signal?: AbortSignal) => requisitar<Metricas>('/metricas', { signal }),
}

/**
 * Geolocalização opcional. Resolve com `null` se o usuário negar, se o navegador
 * não oferecer, ou se demorar — o contexto segue sem clima automático e a tela
 * pede a temperatura à mão (RNF07).
 */
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
