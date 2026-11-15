import { ShieldCheck } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Carregando, ErroBloco } from '../componentes/Estados'
import { api, mensagemDe, type Termo } from '../lib/api'
import { sair } from '../lib/sessao'

/**
 * Termo de uso dos dados, antes do primeiro uso (LGPD).
 * O aceite essencial é obrigatório; a localização é uma escolha à parte,
 * desmarcada por padrão.
 */
export function Consentimento({ aoAceitar }: { aoAceitar: () => Promise<void> }) {
  const [termo, setTermo] = useState<Termo | null>(null)
  const [aceito, setAceito] = useState(false)
  const [localizacao, setLocalizacao] = useState(false)
  const [erro, setErro] = useState<string | null>(null)
  const [enviando, setEnviando] = useState(false)

  const carregar = () => api.termo().then(setTermo).catch((e) => setErro(mensagemDe(e)))
  useEffect(() => void carregar(), [])

  async function aceitar() {
    if (!termo) return
    setEnviando(true)
    setErro(null)
    try {
      await api.aceitarTermo(termo.versao, localizacao)
      await aoAceitar()
    } catch (e) {
      setErro(mensagemDe(e))
      void carregar() // o termo pode ter mudado de versão
    } finally {
      setEnviando(false)
    }
  }

  if (!termo)
    return (
      <main className="pagina pagina--centro">
        {erro ? <ErroBloco mensagem={erro} aoTentar={carregar} /> : <Carregando />}
      </main>
    )

  return (
    <main className="pagina pagina--formulario">
      <div className="selo" aria-hidden="true"><ShieldCheck size={28} /></div>
      <h1 className="titulo-grande">{termo.titulo}</h1>
      <p className="suave">{termo.resumo}</p>

      <div className="termo">
        {termo.secoes.map((secao, i) => (
          <details key={secao.titulo} open={i < 2}>
            <summary>{secao.titulo}</summary>
            <ul>{secao.itens.map((item) => <li key={item}>{item}</li>)}</ul>
          </details>
        ))}
        <p className="termo__rodape">Responsável: {termo.controlador} · Versão {termo.versao}</p>
      </div>

      <label className="marcar">
        <input type="checkbox" checked={aceito} onChange={(e) => setAceito(e.target.checked)} />
        <span>Li e concordo: {termo.finalidades[0]?.rotulo.toLowerCase()} Tenho 18 anos ou mais.</span>
      </label>
      <label className="marcar">
        <input type="checkbox" checked={localizacao} onChange={(e) => setLocalizacao(e.target.checked)} />
        <span><strong>Opcional.</strong> {termo.finalidades[1]?.rotulo}</span>
      </label>

      {erro && <p className="aviso aviso--erro" role="alert">{erro}</p>}

      <button type="button" className="botao botao--primario" disabled={!aceito || enviando} onClick={aceitar}>
        {enviando ? 'Registrando…' : 'Aceitar e continuar'}
      </button>
      <button type="button" className="botao botao--texto" onClick={() => void sair()}>Agora não</button>
    </main>
  )
}
