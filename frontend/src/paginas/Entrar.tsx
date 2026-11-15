import { ChevronLeft } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { MODO_DEMO } from '../lib/config'
import { criarConta, entrar, recuperarSenha } from '../lib/sessao'

export function Entrar({ modo }: { modo: 'entrar' | 'criar' }) {
  const navegar = useNavigate()
  const criando = modo === 'criar'
  const [nome, setNome] = useState('')
  const [email, setEmail] = useState('')
  const [senha, setSenha] = useState('')
  const [erro, setErro] = useState<string | null>(null)
  const [recado, setRecado] = useState<string | null>(null)
  const [enviando, setEnviando] = useState(false)

  async function enviar(evento: FormEvent) {
    evento.preventDefault()
    setErro(null)
    setRecado(null)
    setEnviando(true)
    if (criando) {
      const { erro: falha, confirmar } = await criarConta(nome.trim(), email.trim(), senha)
      if (falha) setErro(falha)
      else if (confirmar) setRecado('Conta criada. Confirme pelo link que enviamos ao seu e-mail e depois entre.')
      else navegar('/', { replace: true })
    } else {
      const falha = await entrar(email.trim(), senha)
      if (falha) setErro(falha)
      else navegar('/', { replace: true })
    }
    setEnviando(false)
  }

  async function esqueci() {
    setErro(null)
    if (!email.trim()) return setErro('Digite seu e-mail acima para receber o link de recuperação.')
    const falha = await recuperarSenha(email.trim())
    if (falha) setErro(falha)
    else setRecado('Se houver uma conta com este e-mail, o link de recuperação está a caminho.')
  }

  return (
    <main className="pagina pagina--formulario">
      <Link to="/" className="botao-icone" aria-label="Voltar">
        <ChevronLeft size={26} aria-hidden="true" />
      </Link>
      <h1 className="titulo-grande">{criando ? 'Criar conta' : 'Entrar'}</h1>
      <p className="suave">
        {criando ? 'Monte seu guarda-roupa digital em poucos minutos.' : 'Que bom ver você de novo.'}
      </p>

      {MODO_DEMO && (
        <p className="aviso aviso--info">
          Modo demonstração: qualquer e-mail e senha entram, e nada sai deste computador.
        </p>
      )}

      <form onSubmit={enviar} className="formulario" noValidate={false}>
        {criando && (
          <label className="campo">
            <span>Nome</span>
            <input value={nome} onChange={(e) => setNome(e.target.value)} required autoComplete="given-name" maxLength={80} />
          </label>
        )}
        <label className="campo">
          <span>E-mail</span>
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required autoComplete="email" inputMode="email" />
        </label>
        <label className="campo">
          <span>Senha</span>
          <input
            type="password"
            value={senha}
            onChange={(e) => setSenha(e.target.value)}
            required
            minLength={6}
            autoComplete={criando ? 'new-password' : 'current-password'}
          />
          {criando && <small>Pelo menos 6 caracteres.</small>}
        </label>

        {erro && <p className="aviso aviso--erro" role="alert">{erro}</p>}
        {recado && <p className="aviso aviso--ok" role="status">{recado}</p>}

        <button className="botao botao--primario" disabled={enviando}>
          {enviando ? 'Aguarde…' : criando ? 'Criar conta' : 'Entrar'}
        </button>
      </form>

      {!criando && !MODO_DEMO && (
        <button type="button" className="botao botao--texto" onClick={esqueci}>Esqueci minha senha</button>
      )}
      <p className="rodape-formulario">
        {criando ? 'Já tem conta? ' : 'Ainda não tem conta? '}
        <Link to={criando ? '/entrar' : '/criar-conta'}>{criando ? 'Entrar' : 'Criar conta'}</Link>
      </p>
    </main>
  )
}
