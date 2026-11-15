// Cliente da API do StyleUp. Toda chamada leva o JWT da sessão atual.
import { API_URL } from './config'
import { sair, tokenAtual } from './sessao'

export type Papel = 'superior' | 'inferior' | 'calcado' | 'sobreposicao' | 'acessorio'

export interface Peca {
  id: string
  codigo: string
  papel: Papel
  categoria: string
  rotulo: string
  cor_nome: string
  cor_hex: string
  cor_hsv: number[]
  neutra: boolean
  formalidade: number
  disponivel: boolean
  imagem_path: string | null
  atributos: Record<string, string>
}

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
  confianca_baixa: boolean
  recorte: string | null
}

export interface Categoria {
  chave: string
  rotulo: string
  papel: Papel
  formalidade: number
  temp_min: number
  temp_max: number
  resiste_chuva: boolean
}

export interface Cor {
  nome: string
  hex: string
  neutra: boolean
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
  titulo: string
  resumo: string
  explicacao: string
  salvo: boolean
  aprovado: boolean | null
  pecas: PecaDoLook[]
}

export interface Contexto {
  id: string
  evento: string
  evento_rotulo: string
  estilo: string | null
  temperatura: number | null
  sensacao: number | null
  chuva_prob: number | null
  clima_automatico: boolean
  entendido: string[]
}

export interface Recomendacao {
  contexto: Contexto
  looks: Look[]
  avisos: string[]
}

export interface Pedido {
  evento?: string
  texto?: string
  estilo?: string
  inspiracao?: string
  temperatura?: number
  latitude?: number
  longitude?: number
}

export interface Inspiracao {
  chave: string
  rotulo: string
  icone: string
}

export interface Consentimento {
  versao_vigente: string
  aceito: boolean
  aceito_em: string | null
  localizacao: boolean
  exigido: boolean
}

export interface Perfil {
  id: string
  nome: string | null
  email: string | null
  consentimento: Consentimento
  pesos: Record<string, number>
}

export interface Termo {
  versao: string
  titulo: string
  resumo: string
  controlador: string
  contato: string
  secoes: { titulo: string; itens: string[] }[]
  finalidades: { chave: string; obrigatoria: boolean; rotulo: string }[]
}

export interface Metricas {
  consultas: number
  consultas_avaliadas: number
  looks_mostrados: number
  looks_aprovados: number
  hit_rate_3: number | null
  precision_3: number | null
}

export class ErroApi extends Error {
  constructor(
    public status: number,
    public codigo: string,
    mensagem: string,
    public extras: Record<string, unknown> = {},
  ) {
    super(mensagem)
  }
}

/** Aviso global: o backend disse que falta aceitar o termo. */
export const EVENTO_CONSENTIMENTO = 'styleup:consentimento'

async function requisitar<T>(caminho: string, opcoes: RequestInit = {}): Promise<T> {
  const token = await tokenAtual()
  const cabecalhos: Record<string, string> = { ...(opcoes.headers as Record<string, string>) }
  if (token) cabecalhos.Authorization = `Bearer ${token}`
  if (opcoes.body && !(opcoes.body instanceof FormData)) {
    cabecalhos['Content-Type'] = 'application/json'
  }

  let resposta: Response
  try {
    resposta = await fetch(`${API_URL}${caminho}`, { ...opcoes, headers: cabecalhos })
  } catch {
    throw new ErroApi(0, 'sem_conexao',
      'Não foi possível falar com o servidor. Verifique a internet e tente de novo.')
  }

  if (resposta.ok) {
    return resposta.status === 204 ? (undefined as T) : ((await resposta.json()) as T)
  }

  const corpo = (await resposta.json().catch(() => ({}))) as Record<string, unknown>
  const codigo = (corpo.codigo as string) ?? 'erro'
  const mensagem =
    (corpo.erro as string) ?? (corpo.detail as string) ?? `Erro ${resposta.status}. Tente de novo.`
  if (codigo === 'consentimento_pendente') {
    window.dispatchEvent(new Event(EVENTO_CONSENTIMENTO))
  }
  if (resposta.status === 401 && (codigo === 'sessao_expirada' || codigo === 'token_invalido')) {
    void sair()
  }
  throw new ErroApi(resposta.status, codigo, mensagem, corpo)
}

const json = (corpo: unknown) => JSON.stringify(corpo)

export const api = {
  // catálogos
  taxonomia: () => requisitar<Categoria[]>('/pecas/taxonomia'),
  cores: () => requisitar<Cor[]>('/pecas/cores'),
  inspiracoes: () => requisitar<Inspiracao[]>('/inspiracoes'),

  // guarda-roupa
  listarPecas: () => requisitar<Peca[]>('/pecas'),
  analisar(arquivo: Blob) {
    const form = new FormData()
    form.append('foto', arquivo, 'foto.jpg')
    return requisitar<Analise>('/pecas/analisar', { method: 'POST', body: form })
  },
  registrarPeca: (peca: Record<string, unknown>) =>
    requisitar<Peca>('/pecas', { method: 'POST', body: json(peca) }),
  atualizarPeca: (id: string, mudancas: Record<string, unknown>) =>
    requisitar<Peca>(`/pecas/${id}`, { method: 'PATCH', body: json(mudancas) }),
  removerPeca: (id: string) => requisitar<void>(`/pecas/${id}`, { method: 'DELETE' }),

  // looks
  recomendar: (pedido: Pedido) =>
    requisitar<Recomendacao>('/recomendacoes', { method: 'POST', body: json(pedido) }),
  feedback: (lookId: string, aprovado: boolean) =>
    requisitar<{ registrado: boolean }>('/feedback', {
      method: 'POST',
      body: json({ look_id: lookId, aprovado }),
    }),
  salvarLook: (lookId: string, salvo: boolean) =>
    requisitar<{ salvo: boolean }>(`/looks/${lookId}/salvo`, {
      method: 'PUT',
      body: json({ salvo }),
    }),
  looksSalvos: () => requisitar<Look[]>('/looks?salvos=true'),
  metricas: () => requisitar<Metricas>('/metricas'),

  // perfil e privacidade
  perfil: () => requisitar<Perfil>('/perfil'),
  atualizarNome: (nome: string) =>
    requisitar<Perfil>('/perfil', { method: 'PUT', body: json({ nome }) }),
  termo: () => requisitar<Termo>('/perfil/termo'),
  aceitarTermo: (versao: string, localizacao: boolean) =>
    requisitar<Consentimento>('/perfil/consentimento', {
      method: 'POST',
      body: json({ versao, localizacao }),
    }),
  revogarTermo: () =>
    requisitar<Consentimento>('/perfil/consentimento', { method: 'DELETE' }),
  exportarDados: () => requisitar<Record<string, unknown>>('/perfil/exportar'),
  excluirConta: (confirmacao: string) =>
    requisitar<{ excluida: boolean }>('/perfil', { method: 'DELETE', body: json({ confirmacao }) }),

  // só no modo demonstração: o backend faz o papel do Storage
  enviarFotoDemo(arquivo: Blob) {
    const form = new FormData()
    form.append('foto', arquivo, 'peca.webp')
    return requisitar<{ caminho: string }>('/demo/fotos', { method: 'POST', body: form })
  },
}

export function mensagemDe(erro: unknown): string {
  return erro instanceof Error ? erro.message : 'Algo deu errado. Tente de novo.'
}
