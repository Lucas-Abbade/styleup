/** Pequenos utilitários de texto em português. */

export function maiuscula(texto: string): string {
  return texto ? texto.charAt(0).toUpperCase() + texto.slice(1) : texto
}

/** "verde-oliva" → "Verde-oliva"; é o nome que acompanha toda amostra de cor (RNF05). */
export const nomeDaCor = (nome: string) => maiuscula(nome)

export function semAcento(texto: string): string {
  return texto.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()
}

export function primeiroNome(nome: string | null | undefined): string {
  return maiuscula((nome ?? '').trim().split(/[\s@._-]+/)[0] ?? '')
}
