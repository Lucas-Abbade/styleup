/**
 * Cópia local do guarda-roupa, por usuário (RNF09: consulta sem rede).
 *
 * Fica no localStorage, com o id da conta na chave, e é apagada ao sair — em vez
 * de no cache do service worker, que serviria os dados de um usuário para o
 * próximo num aparelho compartilhado.
 */
import { usuarioIdAtual } from './sessao'

const chave = (nome: string) => `styleup.cache.${usuarioIdAtual() ?? 'demo'}.${nome}`

export function guardar<T>(nome: string, valor: T): void {
  try {
    localStorage.setItem(chave(nome), JSON.stringify(valor))
  } catch {
    /* sem espaço ou modo privado: o app segue sem cópia local */
  }
}

export function recuperar<T>(nome: string): T | null {
  try {
    const bruto = localStorage.getItem(chave(nome))
    return bruto ? (JSON.parse(bruto) as T) : null
  } catch {
    return null
  }
}
