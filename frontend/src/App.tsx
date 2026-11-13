import type { Session } from '@supabase/supabase-js'
import { useEffect, useState } from 'react'
import { NavLink, Navigate, Route, Routes } from 'react-router-dom'

import { supabase } from './lib/supabase'
import Cadastro from './pages/Cadastro'
import GuardaRoupa from './pages/GuardaRoupa'
import Login from './pages/Login'
import Recomendar from './pages/Recomendar'

export default function App() {
  const [sessao, setSessao] = useState<Session | null>(null)
  const [carregando, setCarregando] = useState(true)

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      setSessao(data.session)
      setCarregando(false)
    })
    const { data: inscricao } = supabase.auth.onAuthStateChange((_evento, nova) =>
      setSessao(nova),
    )
    return () => inscricao.subscription.unsubscribe()
  }, [])

  if (carregando) return <div className="app">Carregando…</div>
  if (!sessao) return <Login />

  return (
    <>
      <main className="app">
        <Routes>
          <Route path="/" element={<Recomendar />} />
          <Route path="/guarda-roupa" element={<GuardaRoupa />} />
          <Route path="/cadastrar" element={<Cadastro usuarioId={sessao.user.id} />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>

      <nav className="barra-inferior">
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
