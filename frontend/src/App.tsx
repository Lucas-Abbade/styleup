import { Component, lazy, Suspense, useCallback, useEffect, useState, type ReactNode } from 'react'
import { Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { BarraInferior } from './componentes/BarraInferior'
import { Carregando, ErroBloco } from './componentes/Estados'
import { api, EVENTO_CONSENTIMENTO, EVENTO_SESSAO_EXPIRADA, mensagemDe, type Perfil } from './lib/api'
import { ContextoPerfil } from './lib/dados'
import { sair, useSessao } from './lib/sessao'
import { Comunidade } from './paginas/Comunidade'
import { Consentimento } from './paginas/Consentimento'
import { Entrar } from './paginas/Entrar'
import { Gerador } from './paginas/Gerador'
import { GuardaRoupa } from './paginas/GuardaRoupa'
import { Inicio } from './paginas/Inicio'
import { Splash } from './paginas/Splash'

// telas menos frequentes saem do pacote inicial
const CadastrarPeca = lazy(() => import('./paginas/CadastrarPeca'))
const LookGerado = lazy(() => import('./paginas/LookGerado'))
const PerfilPagina = lazy(() => import('./paginas/Perfil'))

/** Um erro de renderização numa tela não pode deixar o app em branco. */
class Barreira extends Component<{ children: ReactNode }, { erro: boolean }> {
  state = { erro: false }
  static getDerivedStateFromError() {
    return { erro: true }
  }
  render() {
    if (!this.state.erro) return this.props.children
    return (
      <main className="pagina">
        <ErroBloco
          mensagem="Esta tela encontrou um problema. Seus dados estão guardados."
          aoTentar={() => window.location.reload()}
        />
      </main>
    )
  }
}

function RolarParaOTopo() {
  const { pathname } = useLocation()
  // com chaves: nos navegadores novos scrollTo devolve uma Promise, e um efeito
  // só pode devolver a função de limpeza
  useEffect(() => {
    window.scrollTo(0, 0)
  }, [pathname])
  return null
}

function AreaLogada() {
  const [perfil, setPerfil] = useState<Perfil | null>(null)
  const [erro, setErro] = useState<string | null>(null)

  const recarregar = useCallback(async () => {
    try {
      setPerfil(await api.perfil())
      setErro(null)
    } catch (e) {
      setErro(mensagemDe(e))
    }
  }, [])

  useEffect(() => {
    void recarregar()
    const aoPedirTermo = () => void recarregar()
    const aoExpirar = () => void sair()
    window.addEventListener(EVENTO_CONSENTIMENTO, aoPedirTermo)
    window.addEventListener(EVENTO_SESSAO_EXPIRADA, aoExpirar)
    return () => {
      window.removeEventListener(EVENTO_CONSENTIMENTO, aoPedirTermo)
      window.removeEventListener(EVENTO_SESSAO_EXPIRADA, aoExpirar)
    }
  }, [recarregar])

  if (!perfil)
    return (
      <main className="pagina pagina--centro">
        {erro ? <ErroBloco mensagem={erro} aoTentar={recarregar} /> : <Carregando />}
        {erro && (
          <button type="button" className="botao botao--texto" onClick={() => void sair()}>
            Sair
          </button>
        )}
      </main>
    )

  if (perfil.consentimento.exigido && !perfil.consentimento.aceito)
    return <Consentimento aoAceitar={recarregar} />

  return (
    <ContextoPerfil.Provider value={{ perfil, recarregar }}>
      <RolarParaOTopo />
      <Barreira>
        <Suspense fallback={<main className="pagina pagina--centro"><Carregando /></main>}>
          <Routes>
            <Route path="/" element={<Inicio />} />
            <Route path="/guarda-roupa" element={<GuardaRoupa />} />
            <Route path="/guarda-roupa/nova" element={<CadastrarPeca />} />
            <Route path="/gerador" element={<Gerador />} />
            <Route path="/gerador/look" element={<LookGerado />} />
            <Route path="/comunidade" element={<Comunidade />} />
            <Route path="/perfil" element={<PerfilPagina />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </Barreira>
      <BarraInferior />
    </ContextoPerfil.Provider>
  )
}

export function App() {
  const { sessao, carregando } = useSessao()

  if (carregando)
    return (
      <div className="app">
        <main className="pagina pagina--centro"><Carregando /></main>
      </div>
    )

  return (
    <div className="app">
      <Barreira>
      {sessao ? (
        <AreaLogada key={sessao.token.slice(-12)} />
      ) : (
        <Routes>
          <Route path="/" element={<Splash />} />
          <Route path="/entrar" element={<Entrar modo="entrar" />} />
          <Route path="/criar-conta" element={<Entrar modo="criar" />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      )}
      </Barreira>
    </div>
  )
}
