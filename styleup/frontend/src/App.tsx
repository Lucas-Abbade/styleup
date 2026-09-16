import type { Session } from '@supabase/supabase-js'
import { Suspense, lazy, useEffect, useMemo, useState } from 'react'
import { NavLink, Navigate, Route, Routes } from 'react-router-dom'

import LimiteDeErro from './components/LimiteDeErro'
import { EsqueletoLook } from './components/Estados'
import { obterCliente, supabaseConfigurado } from './lib/supabase'

/**
 * Rotas carregadas sob demanda.
 *
 * A tela inicial é a de recomendação; Cadastro e Guarda-roupa só entram no
 * pacote quando o usuário navega até elas. Cadastro é a mais pesada das três
 * (câmera, prévia da imagem, catálogo de categorias) e é a menos visitada.
 */
const Recomendar = lazy(() => import('./pages/Recomendar'))
const GuardaRoupa = lazy(() => import('./pages/GuardaRoupa'))
const Cadastro = lazy(() => import('./pages/Cadastro'))
const Login = lazy(() => import('./pages/Login'))

/** Mesmo id do backend em modo demonstração (`app/auth.py`). */
const USUARIO_DEMO = '00000000-0000-4000-8000-000000000001'

function Aguardando() {
  return (
    <div aria-busy="true">
      <div className="esqueleto" style={{ height: 30, width: '55%' }} />
      <div className="esqueleto" style={{ height: 16, width: '80%', marginTop: 10 }} />
      <EsqueletoLook />
    </div>
  )
}

export default function App() {
  const [sessao, setSessao] = useState<Session | null>(null)
  const [carregando, setCarregando] = useState(supabaseConfigurado)

  useEffect(() => {
    if (!supabaseConfigurado) return

    let ativo = true
    let cancelarInscricao: (() => void) | null = null

    // O SDK entra por import dinâmico, então a leitura da sessão é assíncrona.
    obterCliente()
      .then(async (cliente) => {
        const { data } = await cliente.auth.getSession()
        if (!ativo) return
        setSessao(data.session)
        setCarregando(false)

        const { data: inscricao } = cliente.auth.onAuthStateChange((_evento, nova) => {
          if (ativo) setSessao(nova)
        })
        cancelarInscricao = () => inscricao.subscription.unsubscribe()
        // desmontou enquanto o SDK carregava: cancela na hora
        if (!ativo) cancelarInscricao()
      })
      .catch((e) => {
        console.error('[StyleUp] falha ao inicializar o Supabase:', e)
        if (ativo) setCarregando(false)
      })

    return () => {
      ativo = false
      cancelarInscricao?.()
    }
  }, [])

  const usuarioId = useMemo(
    () => sessao?.user.id ?? USUARIO_DEMO,
    [sessao?.user.id],
  )

  if (carregando) {
    return (
      <main className="app">
        <Aguardando />
      </main>
    )
  }

  // Sem Supabase configurado o app roda em demonstração: não há login a fazer.
  if (supabaseConfigurado && !sessao) {
    return (
      <main className="app">
        <Suspense fallback={<Aguardando />}>
          <Login />
        </Suspense>
      </main>
    )
  }

  return (
    <>
      {!supabaseConfigurado && (
        <div className="faixa-demo" role="status">
          Modo demonstração — dados em memória, com guarda-roupa de exemplo.
        </div>
      )}

      <main className="app">
        {/* Um limite por rota: a falha de uma tela não apaga a navegação. */}
        <LimiteDeErro area="tela">
          <Suspense fallback={<Aguardando />}>
            <Routes>
              <Route path="/" element={<Recomendar />} />
              <Route path="/guarda-roupa" element={<GuardaRoupa />} />
              <Route path="/cadastrar" element={<Cadastro usuarioId={usuarioId} />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </Suspense>
        </LimiteDeErro>
      </main>

      <nav className="barra-inferior" aria-label="Navegação principal">
        <NavLink to="/" end className={({ isActive }) => (isActive ? 'ativo' : '')}>
          Hoje
        </NavLink>
        <NavLink to="/cadastrar" className={({ isActive }) => (isActive ? 'ativo' : '')}>
          Cadastrar
        </NavLink>
        <NavLink to="/guarda-roupa" className={({ isActive }) => (isActive ? 'ativo' : '')}>
          Guarda-roupa
        </NavLink>
      </nav>
    </>
  )
}
