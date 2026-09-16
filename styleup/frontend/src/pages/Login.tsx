import { useState } from 'react'

import { obterCliente } from '../lib/supabase'

/**
 * Operações 6.1.1.1 e 6.1.1.2 do Documento de Visão.
 * O Supabase Auth cuida de hash de senha, sessão e refresh — o RNF10 sai de graça.
 */
export default function Login() {
  const [modo, setModo] = useState<'entrar' | 'criar'>('entrar')
  const [email, setEmail] = useState('')
  const [senha, setSenha] = useState('')
  const [nome, setNome] = useState('')
  const [erro, setErro] = useState<string | null>(null)
  const [aviso, setAviso] = useState<string | null>(null)
  const [enviando, setEnviando] = useState(false)

  async function enviar(evento: React.FormEvent) {
    evento.preventDefault()
    setErro(null)
    setAviso(null)
    setEnviando(true)
    try {
      const supabase = await obterCliente()
      if (modo === 'criar') {
        const { error } = await supabase.auth.signUp({
          email,
          password: senha,
          options: { data: { nome } },
        })
        if (error) throw error
        setAviso('Conta criada. Confirme o e-mail e depois entre.')
        setModo('entrar')
      } else {
        const { error } = await supabase.auth.signInWithPassword({ email, password: senha })
        if (error) throw error
      }
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Não foi possível concluir.')
    } finally {
      setEnviando(false)
    }
  }

  return (
    <main className="app">
      <h1>StyleUp</h1>
      <p className="legenda">
        Fotografe suas peças uma vez. Depois é só dizer para onde você vai.
      </p>

      <form className="cartao" onSubmit={enviar}>
        {modo === 'criar' && (
          <>
            <label htmlFor="nome">Nome</label>
            <input
              id="nome"
              value={nome}
              onChange={(e) => setNome(e.target.value)}
              autoComplete="name"
              required
            />
          </>
        )}

        <label htmlFor="email">E-mail</label>
        <input
          id="email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          autoComplete="email"
          required
        />

        <label htmlFor="senha">Senha</label>
        <input
          id="senha"
          type="password"
          value={senha}
          onChange={(e) => setSenha(e.target.value)}
          autoComplete={modo === 'criar' ? 'new-password' : 'current-password'}
          minLength={8}
          required
        />

        {erro && <div className="erro">{erro}</div>}
        {aviso && <p className="aviso">{aviso}</p>}

        <button className="primario" type="submit" disabled={enviando} style={{ marginTop: 16 }}>
          {enviando ? 'Aguarde…' : modo === 'entrar' ? 'Entrar' : 'Criar conta'}
        </button>
      </form>

      <button onClick={() => setModo(modo === 'entrar' ? 'criar' : 'entrar')}>
        {modo === 'entrar' ? 'Não tenho conta' : 'Já tenho conta'}
      </button>
    </main>
  )
}
