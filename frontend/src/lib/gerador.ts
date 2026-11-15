/** Resultado em exibição na tela "Look Gerado". Sobrevive à troca de aba. */
import { useSyncExternalStore } from 'react'
import type { Look, Pedido, Recomendacao } from './api'

export interface Exibicao {
  pedido: Pedido | null // null: look aberto a partir dos salvos (não dá para "gerar outro")
  recomendacao: Recomendacao
  indice: number
}

let estado: Exibicao | null = null
const ouvintes = new Set<() => void>()

function publicar(novo: Exibicao | null) {
  estado = novo
  ouvintes.forEach((o) => o())
}

export const gerador = {
  mostrar: (pedido: Pedido, recomendacao: Recomendacao) => publicar({ pedido, recomendacao, indice: 0 }),
  abrirSalvo: (look: Look) =>
    publicar({
      pedido: null,
      indice: 0,
      recomendacao: {
        looks: [look],
        avisos: [],
        contexto: {
          id: '', evento: '', evento_rotulo: '', estilo: null, temperatura: null,
          sensacao: null, chuva_prob: null, clima_automatico: false, entendido: [],
        },
      },
    }),
  irPara: (indice: number) => estado && publicar({ ...estado, indice }),
  atualizarLook(look: Look) {
    if (!estado) return
    const looks = estado.recomendacao.looks.map((l) => (l.id === look.id ? look : l))
    publicar({ ...estado, recomendacao: { ...estado.recomendacao, looks } })
  },
  limpar: () => publicar(null),
}

export function useExibicao(): Exibicao | null {
  return useSyncExternalStore(
    (ouvinte) => {
      ouvintes.add(ouvinte)
      return () => void ouvintes.delete(ouvinte)
    },
    () => estado,
  )
}
