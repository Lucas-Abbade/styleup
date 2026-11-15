import { Download, LogOut, MapPin, Pencil, ShieldCheck, Trash2 } from 'lucide-react'
import { useEffect, useState, type FormEvent } from 'react'
import { useAviso } from '../componentes/Avisos'
import { Folha } from '../componentes/Folha'
import { api, mensagemDe, type Metricas } from '../lib/api'
import { MODO_DEMO } from '../lib/config'
import { ligarClimaLocal, usePecas, usePerfil } from '../lib/dados'
import { sair, useSessao } from '../lib/sessao'
import { primeiroNome } from '../lib/texto'

const CRITERIOS: [string, string][] = [
  ['ocasiao', 'Adequação à ocasião'], ['clima', 'Conforto no clima'], ['cor', 'Harmonia de cores'],
  ['estilo', 'O que você já aprovou'], ['variedade', 'Variar as peças'],
]
const porcento = (v: number | null) => (v === null ? '—' : `${Math.round(v * 100)}%`)

export default function Perfil() {
  const avisar = useAviso()
  const { perfil, recarregar } = usePerfil()
  const { pecas } = usePecas()
  const { sessao } = useSessao()
  // no modo demonstração o e-mail do servidor é fictício; vale o que a pessoa digitou
  const email = sessao?.demo ? sessao.email : perfil.email
  const [metricas, setMetricas] = useState<Metricas | null>(null)
  const [salvos, setSalvos] = useState<number | null>(null)
  const [editandoNome, setEditandoNome] = useState(false)
  const [nome, setNome] = useState(perfil.nome ?? '')
  const [excluindo, setExcluindo] = useState(false)
  const [confirmacao, setConfirmacao] = useState('')
  const [erro, setErro] = useState<string | null>(null)
  const [ocupado, setOcupado] = useState(false)

  useEffect(() => {
    api.metricas().then(setMetricas).catch(() => undefined)
    api.looksSalvos().then((l) => setSalvos(l.length)).catch(() => undefined)
  }, [])

  async function executar(acao: () => Promise<unknown>, recado?: string) {
    setOcupado(true)
    setErro(null)
    try {
      await acao()
      if (recado) avisar(recado)
      return true
    } catch (e) {
      setErro(mensagemDe(e))
      return false
    } finally {
      setOcupado(false)
    }
  }

  async function salvarNome(evento: FormEvent) {
    evento.preventDefault()
    if (await executar(async () => { await api.atualizarNome(nome); await recarregar() }, 'Nome atualizado'))
      setEditandoNome(false)
  }

  // mudar a finalidade de localização é um novo aceite, registrado com data
  const alternarLocalizacao = (ligar: boolean) =>
    executar(async () => {
      await api.aceitarTermo(perfil.consentimento.versao_vigente, ligar)
      ligarClimaLocal(ligar)
      await recarregar()
    }, ligar ? 'Localização permitida para o clima' : 'Localização desativada')

  const baixarDados = () =>
    executar(async () => {
      const dados = await api.exportarDados()
      const url = URL.createObjectURL(new Blob([JSON.stringify(dados, null, 2)], { type: 'application/json' }))
      const link = Object.assign(document.createElement('a'), { href: url, download: 'meus-dados-style-up.json' })
      link.click()
      setTimeout(() => URL.revokeObjectURL(url), 1000)
    }, 'Arquivo com seus dados baixado')

  const revogar = () => executar(async () => { await api.revogarTermo(); await recarregar() })

  async function excluirConta(evento: FormEvent) {
    evento.preventDefault()
    if (await executar(() => api.excluirConta(confirmacao))) await sair()
  }

  const aceitoEm = perfil.consentimento.aceito_em
    ? new Date(perfil.consentimento.aceito_em).toLocaleDateString('pt-BR', { day: '2-digit', month: 'long', year: 'numeric' })
    : null

  return (
    <main className="pagina">
      <h1 className="titulo-pagina">Perfil</h1>

      <section className="cartao perfil-topo">
        <span className="avatar" aria-hidden="true">{(primeiroNome(perfil.nome ?? perfil.email) || 'S').charAt(0)}</span>
        {editandoNome ? (
          <form onSubmit={salvarNome} className="perfil-nome">
            <label className="campo"><span>Nome</span>
              <input value={nome} onChange={(e) => setNome(e.target.value)} maxLength={80} required autoFocus />
            </label>
            <button className="botao botao--primario botao--pequeno" disabled={ocupado}>Salvar</button>
            <button type="button" className="botao botao--texto botao--pequeno" onClick={() => setEditandoNome(false)}>Cancelar</button>
          </form>
        ) : (
          <div className="perfil-nome">
            <strong>{perfil.nome || 'Sem nome'}</strong>
            <span>{email}{MODO_DEMO && ' · modo demonstração'}</span>
          </div>
        )}
        {!editandoNome && (
          <button type="button" className="botao-icone" onClick={() => { setNome(perfil.nome ?? ''); setEditandoNome(true) }} aria-label="Editar nome">
            <Pencil size={18} aria-hidden="true" />
          </button>
        )}
      </section>

      <section className="numeros" aria-label="Resumo">
        <div><strong>{pecas?.length ?? '—'}</strong><span>peças</span></div>
        <div><strong>{salvos ?? '—'}</strong><span>looks salvos</span></div>
        <div><strong>{metricas?.consultas ?? '—'}</strong><span>consultas</span></div>
      </section>

      <section className="cartao">
        <h2>O que pesa nas suas sugestões</h2>
        <p className="suave">Começa igual para todos e muda conforme você aprova ou rejeita looks.</p>
        <dl className="barras">
          {CRITERIOS.map(([chave, rotulo]) => (
            <div key={chave}>
              <dt>{rotulo}</dt>
              <dd>
                <span className="barra" aria-hidden="true"><span style={{ width: `${Math.round((perfil.pesos[chave] ?? 0) * 250)}%` }} /></span>
                <span>{porcento(perfil.pesos[chave] ?? 0)}</span>
              </dd>
            </div>
          ))}
        </dl>
      </section>

      <section className="cartao">
        <h2>As sugestões estão acertando?</h2>
        {metricas && metricas.consultas_avaliadas > 0 ? (
          <>
            <div className="numeros numeros--dois">
              <div><strong>{porcento(metricas.hit_rate_3)}</strong><span>das consultas tiveram ao menos um look aprovado</span></div>
              <div><strong>{porcento(metricas.precision_3)}</strong><span>dos looks mostrados foram aprovados</span></div>
            </div>
            <p className="suave">Com base em {metricas.consultas_avaliadas} consulta(s) avaliada(s) e {metricas.looks_aprovados} aprovação(ões).</p>
          </>
        ) : (
          <p className="suave">Avalie alguns looks com “Gostei” ou “Não gostei” para ver este número.</p>
        )}
      </section>

      <section className="cartao">
        <h2><ShieldCheck size={18} aria-hidden="true" /> Privacidade</h2>
        {aceitoEm && <p className="suave">Termo versão {perfil.consentimento.versao_vigente}, aceito em {aceitoEm}.</p>}
        <label className="alternar">
          <span><strong><MapPin size={16} aria-hidden="true" /> Localização para o clima</strong>
            <small>Posição aproximada, usada só no momento do pedido e nunca gravada.</small></span>
          <input type="checkbox" role="switch" checked={perfil.consentimento.localizacao} disabled={ocupado}
                 onChange={(e) => void alternarLocalizacao(e.target.checked)} />
        </label>
        <button type="button" className="botao botao--contorno" disabled={ocupado} onClick={() => void baixarDados()}>
          <Download size={18} aria-hidden="true" /> Baixar meus dados
        </button>
        <button type="button" className="botao botao--texto" disabled={ocupado} onClick={() => void revogar()}>Retirar meu consentimento</button>
      </section>

      {erro && !excluindo && <p className="aviso aviso--erro" role="alert">{erro}</p>}

      <button type="button" className="botao botao--contorno" onClick={() => void sair()}><LogOut size={18} aria-hidden="true" /> Sair</button>
      <button type="button" className="botao botao--texto botao--texto-perigo" onClick={() => { setExcluindo(true); setConfirmacao(''); setErro(null) }}>
        <Trash2 size={18} aria-hidden="true" /> Excluir minha conta
      </button>

      <Folha aberta={excluindo} titulo="Excluir conta" aoFechar={() => setExcluindo(false)}>
        <form onSubmit={excluirConta} className="formulario">
          <p>Isto apaga de forma definitiva suas peças, fotos, looks, avaliações e a própria conta. Não dá para desfazer.</p>
          <label className="campo"><span>Digite EXCLUIR para confirmar</span>
            <input value={confirmacao} onChange={(e) => setConfirmacao(e.target.value)} autoCapitalize="characters" autoComplete="off" />
          </label>
          {erro && <p className="aviso aviso--erro" role="alert">{erro}</p>}
          <button className="botao botao--perigo" disabled={ocupado || confirmacao.trim().toUpperCase() !== 'EXCLUIR'}>
            {ocupado ? 'Excluindo…' : 'Excluir tudo'}
          </button>
        </form>
      </Folha>
    </main>
  )
}
