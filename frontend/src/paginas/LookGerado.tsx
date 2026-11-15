import { Bookmark, BookmarkCheck, ChevronLeft, Download, RefreshCw, ThumbsDown, ThumbsUp } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { useAviso } from '../componentes/Avisos'
import { ColagemLook } from '../componentes/ColagemLook'
import { FotoPeca } from '../componentes/FotoPeca'
import { api, mensagemDe, type Look } from '../lib/api'
import { entregar, exportarLook } from '../lib/exportar'
import { useFotos } from '../lib/fotos'
import { gerador, useExibicao } from '../lib/gerador'
import { nomeDaCor } from '../lib/texto'

const CRITERIOS: [string, string][] = [
  ['ocasiao', 'Ocasião'], ['clima', 'Clima'], ['cor', 'Cores'], ['estilo', 'Seu gosto'], ['variedade', 'Variedade'],
]

export default function LookGerado() {
  const navegar = useNavigate()
  const avisar = useAviso()
  const exibicao = useExibicao()
  const [ocupado, setOcupado] = useState(false)
  const looks = exibicao?.recomendacao.looks ?? []
  const fotos = useFotos(looks.flatMap((l) => l.pecas.map((p) => p.imagem_path)))

  // setas do teclado trocam de opção (alternativa ao toque nos pontos)
  useEffect(() => {
    const aoTeclar = (e: KeyboardEvent) => {
      if (!exibicao) return
      if (e.key === 'ArrowRight') gerador.irPara(Math.min(exibicao.indice + 1, looks.length - 1))
      if (e.key === 'ArrowLeft') gerador.irPara(Math.max(exibicao.indice - 1, 0))
    }
    window.addEventListener('keydown', aoTeclar)
    return () => window.removeEventListener('keydown', aoTeclar)
  }, [exibicao, looks.length])

  if (!exibicao || !looks.length) return <Navigate to="/gerador" replace />
  const { recomendacao, indice, pedido } = exibicao
  const look = looks[indice]
  const contexto = recomendacao.contexto

  async function reagir(aprovado: boolean) {
    const anterior = look.aprovado
    gerador.atualizarLook({ ...look, aprovado }) // resposta imediata; desfaz se falhar
    try {
      await api.feedback(look.id, aprovado)
      avisar(aprovado ? 'Anotado: você gostou deste look' : 'Anotado: vou evitar combinações assim')
    } catch (e) {
      gerador.atualizarLook({ ...look, aprovado: anterior })
      avisar(mensagemDe(e), 'erro')
    }
  }

  async function alternarSalvo() {
    const salvo = !look.salvo
    const novo: Look = { ...look, salvo, aprovado: salvo ? true : look.aprovado }
    gerador.atualizarLook(novo)
    try {
      await api.salvarLook(look.id, salvo)
      // salvar é a aprovação mais forte que existe: conta como "gostei"
      if (salvo && look.aprovado !== true) await api.feedback(look.id, true)
      avisar(salvo ? 'Look salvo no guarda-roupa' : 'Look removido dos salvos')
    } catch (e) {
      gerador.atualizarLook(look)
      avisar(mensagemDe(e), 'erro')
    }
  }

  async function outro() {
    if (indice < looks.length - 1) return gerador.irPara(indice + 1)
    if (!pedido) return navegar('/gerador')
    setOcupado(true)
    try {
      gerador.mostrar(pedido, await api.recomendar(pedido))
      window.scrollTo({ top: 0, behavior: 'smooth' })
    } catch (e) {
      avisar(mensagemDe(e), 'erro')
    } finally {
      setOcupado(false)
    }
  }

  async function baixar() {
    setOcupado(true)
    try {
      const resultado = await entregar(await exportarLook(look, fotos), 'look-style-up.png')
      if (resultado === 'baixado') avisar('Imagem do look baixada')
    } catch {
      avisar('Não foi possível gerar a imagem do look.', 'erro')
    } finally {
      setOcupado(false)
    }
  }

  const clima = contexto.temperatura !== null
    ? `${Math.round(contexto.temperatura)} °C${contexto.clima_automatico ? ' agora' : ''}${(contexto.chuva_prob ?? 0) >= 0.5 ? ' · chuva' : ''}`
    : null

  return (
    <main className="pagina pagina--look">
      <header className="topo-voltar">
        <button type="button" className="botao-icone" onClick={() => navegar(pedido ? '/gerador' : -1 as never)} aria-label="Voltar">
          <ChevronLeft size={26} aria-hidden="true" />
        </button>
        <h1>Look Gerado</h1>
        <button type="button" className="botao-icone" onClick={baixar} disabled={ocupado} aria-label="Baixar imagem do look">
          <Download size={22} aria-hidden="true" />
        </button>
      </header>

      <ColagemLook pecas={look.pecas} fotos={fotos} />

      {looks.length > 1 && (
        <div className="pontos" role="tablist" aria-label="Opções de look">
          {looks.map((l, i) => (
            <button key={l.id} type="button" role="tab" aria-selected={i === indice} aria-label={`Opção ${i + 1} de ${looks.length}`}
                    className={i === indice ? 'ativo' : ''} onClick={() => gerador.irPara(i)} />
          ))}
        </div>
      )}

      <div className="look-info" aria-live="polite">
        <div className="look-etiquetas">
          <span className="etiqueta">{look.titulo}</span>
          {clima && <span className="etiqueta etiqueta--clara">{clima}</span>}
        </div>
        <p className="look-resumo">{look.resumo}</p>
        {recomendacao.avisos.map((a) => <p key={a} className="aviso aviso--info">{a}</p>)}

        <details className="porque">
          <summary>Por que este look?</summary>
          <p>{look.explicacao}</p>
          {contexto.entendido.length > 0 && <p className="suave">Entendi do seu pedido: {contexto.entendido.join(' · ')}.</p>}
          <dl className="barras">
            {CRITERIOS.map(([chave, rotulo]) => (
              <div key={chave}>
                <dt>{rotulo}</dt>
                <dd>
                  <span className="barra" aria-hidden="true"><span style={{ width: `${Math.round((look.parcelas[chave] ?? 0) * 100)}%` }} /></span>
                  <span>{Math.round((look.parcelas[chave] ?? 0) * 100)}%</span>
                </dd>
              </div>
            ))}
          </dl>
        </details>
      </div>

      {/* tabIndex: a lista rola na horizontal e precisa ser alcançável pelo teclado */}
      <ul className="tira-pecas" aria-label="Peças do look" tabIndex={0}>
        {look.pecas.map((p) => (
          <li key={p.id}>
            <span className="tira-pecas__foto">
              <FotoPeca categoria={p.categoria} papel={p.papel} corHex={p.cor_hex} url={p.imagem_path ? fotos[p.imagem_path] : undefined} alt="" />
            </span>
            <strong>{p.rotulo}</strong>
            <span>{nomeDaCor(p.cor_nome)}</span>
          </li>
        ))}
      </ul>

      <div className="reacao" role="group" aria-label="O que achou deste look?">
        <span>O que achou?</span>
        <button type="button" aria-pressed={look.aprovado === true} className={look.aprovado === true ? 'ativo' : ''} onClick={() => void reagir(true)}>
          <ThumbsUp size={18} aria-hidden="true" /> Gostei
        </button>
        <button type="button" aria-pressed={look.aprovado === false} className={look.aprovado === false ? 'ativo' : ''} onClick={() => void reagir(false)}>
          <ThumbsDown size={18} aria-hidden="true" /> Não gostei
        </button>
      </div>

      <div className="acoes-look">
        <button type="button" className="botao botao--contorno" disabled={ocupado} onClick={outro}>
          <RefreshCw size={18} aria-hidden="true" /> Gerar outro look
        </button>
        <button type="button" className="botao botao--contorno" aria-pressed={look.salvo} onClick={() => void alternarSalvo()}>
          {look.salvo ? <BookmarkCheck size={18} aria-hidden="true" /> : <Bookmark size={18} aria-hidden="true" />}
          {look.salvo ? 'Salvo no Guarda-Roupa' : 'Salvar no Guarda-Roupa'}
        </button>
      </div>
    </main>
  )
}
