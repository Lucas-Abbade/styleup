import { ChevronLeft } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { mensagemDe } from '../lib/api'
import { MODO_DEMO } from '../lib/config'
import { criarConta, entrar, recuperarSenha } from '../lib/sessao'

export default function Entrar({ modo }: { modo: 'entrar' | 'criar' }) {
  const criando = modo === 'criar'
  const [nome, setNome] = useState('')
  const [email, setEmail] = useState('')
  const [senha, setSenha] = useState('')
  const [erro, setErro] = useState('')
  const [info, setInfo] = useState('')
  const [enviando, setEnviando] = useState(false)

  async function enviar(evento: FormEvent) {
    evento.preventDefault()
    setErro('')
    setInfo('')
    setEnviando(true)
    try {
      if (MODO_DEMO) {
        await criarConta(nome.trim() || 'Visitante', '', '')
      } else if (criando) {
        const precisaConfirmar = await criarConta(nome.trim(), email.trim(), senha)
        if (precisaConfirmar) {
          setInfo('Conta criada. Abra o e-mail que enviamos para confirmar e depois entre.')
        }
      } else {
        await entrar(email.trim(), senha)
      }
    } catch (e) {
      setErro(mensagemDe(e))
    } finally {
      setEnviando(false)
    }
  }

  async function esqueci() {
    setErro('')
    if (!email.trim()) return setErro('Digite o seu e-mail para receber o link de recuperação.')
    try {
      await recuperarSenha(email.trim())
      setInfo('Se houver uma conta com este e-mail, o link de recuperação está a caminho.')
    } catch (e) {
      setErro(mensagemDe(e))
    }
  }

  return (
    <main className="tela tela--sem-barra">
      <header className="topo topo--centro">
        <Link to="/" className="botao-icone" aria-label="Voltar"><ChevronLeft aria-hidden /></Link>
        <h1>{criando ? 'Criar conta' : 'Entrar'}</h1>
        <span style={{ width: 44 }} />
      </header>

      <form onSubmit={enviar} noValidate={false}>
        {(criando || MODO_DEMO) && (
          <label className="campo">
            <span>Como quer ser chamado</span>
            <input value={nome} onChange={(e) => setNome(e.target.value)} autoComplete="given-name"
              required={criando} maxLength={80} placeholder="Seu nome" />
          </label>
        )}
        {!MODO_DEMO && (
          <>
            <label className="campo">
              <span>E-mail</span>
              <input type="email" value={email} onChange={(e) => setEmail(e.target.value)}
                autoComplete="email" inputMode="email" required placeholder="voce@exemplo.com" />
            </label>
            <label className="campo">
              <span>Senha</span>
              <input type="password" value={senha} onChange={(e) => setSenha(e.target.value)}
                autoComplete={criando ? 'new-password' : 'current-password'} required minLength={6} />
              {criando && <small>Pelo menos 6 caracteres.</small>}
            </label>
          </>
        )}

        {MODO_DEMO && (
          <p className="mensagem mensagem--info">
            Modo demonstração: não há senha. Você entra com um guarda-roupa de exemplo.
          </p>
        )}
        {erro && <p className="mensagem mensagem--erro" role="alert">{erro}</p>}
        {info && <p className="mensagem mensagem--ok" role="status">{info}</p>}

        <div className="botoes">
          <button className="botao" disabled={enviando}>
            {enviando ? 'Aguarde…' : criando ? 'Criar conta' : 'Entrar'}
          </button>
        </div>
      </form>

      <p style={{ marginTop: 20, textAlign: 'center' }}>
        {criando
          ? <>Já tem conta? <Link className="link" to="/entrar">Entrar</Link></>
          : <>Ainda não tem conta? <Link className="link" to="/criar-conta">Criar conta</Link></>}
      </p>
      {!criando && !MODO_DEMO && (
        <p style={{ marginTop: 10, textAlign: 'center' }}>
          <button type="button" className="link" style={{ border: 0, background: 'none' }} onClick={esqueci}>
            Esqueci minha senha
          </button>
        </p>
      )}
    </main>
  )
}
