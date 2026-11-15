import { Component, lazy, Suspense, useCallback, useEffect, useState, type ReactNode } from 'react'
import { Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { useRegisterSW } from 'virtual:pwa-register/react'
import BarraInferior from './componentes/BarraInferior'
import { Carregando, Falha } from './componentes/Estados'
import { api, EVENTO_CONSENTIMENTO, mensagemDe, type Perfil } from './lib/api'
import { ContextoPerfil } from './lib/dados'
import { useSessao } from './lib/sessao'
import Abertura from './paginas/Abertura'
import Consentimento from './paginas/Consentimento'
import Entrar from './paginas/Entrar'
import Inicio from './paginas/Inicio'

// As telas fora do primeiro acesso carregam sob demanda: menos código para
// baixar até a tela inicial aparecer.
const GuardaRoupa = lazy(() => import('./paginas/GuardaRoupa'))
const CadastrarPeca = lazy(() => import('./paginas/CadastrarPeca'))
const Gerador = lazy(() => import('./paginas/Gerador'))
const LookGerado = lazy(() => import('./paginas/LookGerado'))
const Comunidade = lazy(() => import('./paginas/Comunidade'))
const PaginaPerfil = lazy(() => import('./paginas/Perfil'))

class Protecao extends Component<{ children: ReactNode }, { quebrou: boolean }> {
  state = { quebrou: false }
  static getDerivedStateFromError() {
    return { quebrou: true }
  }
  render() {
    if (!this.state.quebrou) return this.props.children
    return (
      <main className="tela tela--sem-barra">
        <Falha
          mensagem="Esta tela encontrou um problema. Seus dados estão a salvo."
          aoTentar={() => window.location.assign('/')}
        />
      </main>
    )
  }
}

function AvisoDeAtualizacao() {
  const { needRefresh, updateServiceWorker } = useRegisterSW()
  if (!needRefresh[0]) return null
  return (
    <div className="mensagem mensagem--info" role="status" style={{ margin: 12 }}>
      Há uma versão nova do Style Up.{' '}
      <button type="button" className="link" style={{ border: 0, background: 'none' }}
        onClick={() => void updateServiceWorker(true)}>
        Atualizar agora
      </button>
    </div>
  )
}

function AreaLogada() {
  const [perfil, setPerfil] = useState<Perfil | null>(null)
  const [erro, setErro] = useState<string | null>(null)
  const [pedirTermo, setPedirTermo] = useState(false)

  // devolve uma promessa: quem muda o perfil (nome, localização) espera os dados novos
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
  }, [recarregar])
  const local = useLocation()

  useEffect(() => {
    const avisar = () => setPedirTermo(true)
    window.addEventListener(EVENTO_CONSENTIMENTO, avisar)
    return () => window.removeEventListener(EVENTO_CONSENTIMENTO, avisar)
  }, [])

  // corpo com chaves: no Chrome atual scrollTo devolve uma Promise, e o React
  // trataria esse retorno como função de limpeza
  useEffect(() => {
    window.scrollTo(0, 0)
  }, [local.pathname])

  if (!perfil && !erro) {
    return <main className="tela tela--sem-barra"><Carregando /></main>
  }
  if (!perfil) {
    return (
      <main className="tela tela--sem-barra">
        <Falha mensagem={erro ?? 'Não foi possível carregar o seu perfil.'}
          aoTentar={() => void recarregar()} />
      </main>
    )
  }

  const consentimento = perfil.consentimento
  if ((consentimento.exigido && !consentimento.aceito) || pedirTermo) {
    return (
      <Consentimento
        aoAceitar={() => {
          setPedirTermo(false)
          void recarregar()
        }}
      />
    )
  }

  return (
    <ContextoPerfil.Provider value={{ perfil, recarregar }}>
      <AvisoDeAtualizacao />
      <Protecao>
        <Suspense fallback={<main className="tela"><Carregando /></main>}>
          <Routes>
            <Route path="/" element={<Inicio perfil={perfil} />} />
            <Route path="/guarda-roupa" element={<GuardaRoupa />} />
            <Route path="/guarda-roupa/nova" element={<CadastrarPeca />} />
            <Route path="/gerador" element={<Gerador />} />
            <Route path="/gerador/look" element={<LookGerado />} />
            <Route path="/comunidade" element={<Comunidade />} />
            <Route path="/perfil" element={<PaginaPerfil />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </Protecao>
      <BarraInferior />
    </ContextoPerfil.Provider>
  )
}

export default function App() {
  const { sessao, carregando } = useSessao()

  if (carregando) {
    return <div className="app"><main className="tela tela--sem-barra"><Carregando /></main></div>
  }
  if (!sessao) {
    return (
      <div className="app">
        <Routes>
          <Route path="/" element={<Abertura />} />
          <Route path="/entrar" element={<Entrar modo="entrar" />} />
          <Route path="/criar-conta" element={<Entrar modo="criar" />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    )
  }
  // a chave força recarregar perfil e telas quando troca o usuário
  return <div className="app" key={sessao.email ?? 'sessao'}><AreaLogada /></div>
}
