import { useCallback, useEffect, useRef, useState } from 'react'

export function capitalizar(texto: string): string {
  return texto ? texto.charAt(0).toUpperCase() + texto.slice(1) : texto
}

/** "verde-oliva" -> "Verde-oliva". É este texto que atende ao RNF05. */
export const nomeDaCor = capitalizar

export function primeiroNome(nome: string | null | undefined): string {
  return capitalizar((nome ?? '').trim().split(/[\s@.]+/)[0] ?? '')
}

export function semAcento(texto: string): string {
  return texto.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()
}

export interface Carga<T> {
  dados: T | null
  erro: string | null
  carregando: boolean
  recarregar: () => void
  definir: (valor: T | ((antes: T | null) => T | null)) => void
}

/** Carrega dados assíncronos com os três estados que toda tela precisa tratar. */
export function useCarga<T>(buscar: () => Promise<T>, dependencias: unknown[] = []): Carga<T> {
  const [dados, setDados] = useState<T | null>(null)
  const [erro, setErro] = useState<string | null>(null)
  const [carregando, setCarregando] = useState(true)
  const [versao, setVersao] = useState(0)
  const funcao = useRef(buscar)
  funcao.current = buscar

  useEffect(() => {
    let ativo = true
    setCarregando(true)
    setErro(null)
    funcao.current()
      .then((valor) => ativo && setDados(valor))
      .catch((e: unknown) => ativo && setErro(e instanceof Error ? e.message : 'Falha ao carregar.'))
      .finally(() => ativo && setCarregando(false))
    return () => {
      ativo = false
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [versao, ...dependencias])

  const recarregar = useCallback(() => setVersao((v) => v + 1), [])
  return { dados, erro, carregando, recarregar, definir: setDados as Carga<T>['definir'] }
}
