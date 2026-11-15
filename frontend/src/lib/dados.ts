/** Hooks de dados compartilhados entre as telas. */
import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, mensagemDe, type Peca, type Pedido, type Perfil } from './api'
import { guardar, recuperar } from './cache'
import { gerador } from './gerador'

export const ContextoPerfil = createContext<{ perfil: Perfil; recarregar: () => Promise<void> } | null>(null)

export function usePerfil() {
  const valor = useContext(ContextoPerfil)
  if (!valor) throw new Error('usePerfil fora do ContextoPerfil')
  return valor
}

/**
 * Guarda-roupa do usuário. Mostra na hora a cópia local (se houver) e atualiza
 * pela rede; sem rede, a cópia continua na tela com um aviso (RNF09).
 */
export function usePecas() {
  const [pecas, setPecas] = useState<Peca[] | null>(() => recuperar<Peca[]>('pecas'))
  const [erro, setErro] = useState<string | null>(null)

  const recarregar = useCallback(async () => {
    try {
      const lista = await api.listarPecas()
      setPecas(lista)
      guardar('pecas', lista)
      setErro(null)
    } catch (e) {
      setErro(mensagemDe(e))
    }
  }, [])

  useEffect(() => {
    void recarregar()
  }, [recarregar])

  const atualizar = useCallback((nova: Peca[]) => {
    setPecas(nova)
    guardar('pecas', nova)
  }, [])

  return { pecas, erro, recarregar, atualizar }
}

const CHAVE_CLIMA = 'styleup.clima-local'
export const climaLocalLigado = () => localStorage.getItem(CHAVE_CLIMA) === '1'
export const ligarClimaLocal = (ligado: boolean) => localStorage.setItem(CHAVE_CLIMA, ligado ? '1' : '0')

function posicao(): Promise<{ latitude: number; longitude: number } | null> {
  return new Promise((ok) => {
    if (!('geolocation' in navigator)) return ok(null)
    navigator.geolocation.getCurrentPosition(
      (p) => ok({ latitude: p.coords.latitude, longitude: p.coords.longitude }),
      () => ok(null), // negou ou falhou: segue sem clima automático
      { timeout: 4000, maximumAge: 10 * 60 * 1000 },
    )
  })
}

/** Pede a recomendação e abre a tela do look. */
export function useGerar() {
  const navegar = useNavigate()
  const { perfil } = usePerfil()
  const [gerando, setGerando] = useState(false)
  const [erro, setErro] = useState<string | null>(null)

  const gerar = useCallback(
    async (pedido: Pedido): Promise<boolean> => {
      setGerando(true)
      setErro(null)
      try {
        const completo = { ...pedido }
        // a posição só é lida com o consentimento dessa finalidade E a chave ligada
        if (completo.temperatura === undefined && perfil.consentimento.localizacao && climaLocalLigado())
          Object.assign(completo, await posicao())
        gerador.mostrar(pedido, await api.recomendar(completo))
        navegar('/gerador/look')
        return true
      } catch (e) {
        setErro(mensagemDe(e))
        return false
      } finally {
        setGerando(false)
      }
    },
    [navegar, perfil.consentimento.localizacao],
  )
  return { gerar, gerando, erro, limparErro: () => setErro(null) }
}
