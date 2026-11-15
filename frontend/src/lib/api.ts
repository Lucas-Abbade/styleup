/** Cliente da API do StyleUp. Toda chamada leva o JWT do usuário. */
import { API_URL } from './config'
import { tokenAtual } from './sessao'

export type Papel = 'superior' | 'inferior' | 'calcado' | 'sobreposicao' | 'acessorio'

export interface Peca {
  id: string
  codigo: string
  papel: Papel
  categoria: string
  rotulo: string
  formalidade: number
  cor_nome: string
  cor_hex: string
  cor_hsv: number[]
  neutra: boolean
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
  criado_em?: string | null
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
  latitude?: number
  longitude?: number
  temperatura?: number
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

/** Disparado quando a API pede o aceite do termo; o App leva à tela certa. */
export const EVENTO_CONSENTIMENTO = 'styleup:consentimento'
export const EVENTO_SESSAO_EXPIRADA = 'styleup:sessao-expirada'

async function requisitar<T>(caminho: string, opcoes: RequestInit = {}): Promise<T> {
  const token = await tokenAtual()
  let resposta: Response
  try {
    resposta = await fetch(`${API_URL}${caminho}`, {
      ...opcoes,
      headers: {
        ...(opcoes.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...opcoes.headers,
      },
    })
  } catch {
    throw new ErroApi(0, 'sem_conexao', 'Sem conexão com o servidor. Verifique a internet e tente de novo.')
  }

  if (!resposta.ok) {
    const corpo = await resposta.json().catch(() => ({}))
    const erro = new ErroApi(
      resposta.status,
      corpo.codigo ?? 'erro',
      corpo.erro ?? corpo.detail ?? 'Algo deu errado. Tente de novo.',
      corpo,
    )
    if (erro.codigo === 'consentimento_pendente') window.dispatchEvent(new Event(EVENTO_CONSENTIMENTO))
    if (erro.codigo === 'sessao_expirada' || erro.codigo === 'token_invalido')
      window.dispatchEvent(new Event(EVENTO_SESSAO_EXPIRADA))
    throw erro
  }
  return resposta.status === 204 ? (undefined as T) : resposta.json()
}

const json = (corpo: unknown) => JSON.stringify(corpo)

export const api = {
  taxonomia: () => requisitar<Categoria[]>('/pecas/taxonomia'),
  cores: () => requisitar<Cor[]>('/pecas/cores'),
  inspiracoes: () => requisitar<Inspiracao[]>('/inspiracoes'),

  analisar(foto: Blob) {
    const corpo = new FormData()
    corpo.append('foto', foto, 'foto.jpg')
    return requisitar<Analise>('/pecas/analisar', { method: 'POST', body: corpo })
  },
  registrarPeca: (peca: Record<string, unknown>) =>
    requisitar<Peca>('/pecas', { method: 'POST', body: json(peca) }),
  listarPecas: () => requisitar<Peca[]>('/pecas'),
  atualizarPeca: (id: string, mudancas: Partial<Peca>) =>
    requisitar<Peca>(`/pecas/${id}`, { method: 'PATCH', body: json(mudancas) }),
  removerPeca: (id: string) => requisitar<void>(`/pecas/${id}`, { method: 'DELETE' }),

  recomendar: (pedido: Pedido) =>
    requisitar<Recomendacao>('/recomendacoes', { method: 'POST', body: json(pedido) }),
  feedback: (look_id: string, aprovado: boolean) =>
    requisitar<{ registrado: boolean }>('/feedback', { method: 'POST', body: json({ look_id, aprovado }) }),
  salvarLook: (id: string, salvo: boolean) =>
    requisitar<{ salvo: boolean }>(`/looks/${id}/salvo`, { method: 'PUT', body: json({ salvo }) }),
  looksSalvos: () => requisitar<Look[]>('/looks?salvos=true&limite=50'),
  metricas: () => requisitar<Metricas>('/metricas'),

  perfil: () => requisitar<Perfil>('/perfil'),
  atualizarNome: (nome: string) => requisitar<Perfil>('/perfil', { method: 'PUT', body: json({ nome }) }),
  termo: () => requisitar<Termo>('/perfil/termo'),
  aceitarTermo: (versao: string, localizacao: boolean) =>
    requisitar<Consentimento>('/perfil/consentimento', { method: 'POST', body: json({ versao, localizacao }) }),
  revogarTermo: () => requisitar<Consentimento>('/perfil/consentimento', { method: 'DELETE' }),
  exportarDados: () => requisitar<Record<string, unknown>>('/perfil/exportar'),
  excluirConta: (confirmacao: string) =>
    requisitar<{ excluida: boolean }>('/perfil', { method: 'DELETE', body: json({ confirmacao }) }),

  enviarFotoDemo(foto: Blob) {
    const corpo = new FormData()
    corpo.append('foto', foto, 'peca.webp')
    return requisitar<{ caminho: string }>('/demo/fotos', { method: 'POST', body: corpo })
  },
}

export function mensagemDe(erro: unknown): string {
  return erro instanceof Error ? erro.message : 'Algo deu errado. Tente de novo.'
}
