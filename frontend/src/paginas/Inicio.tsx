import { ArrowRight, Bell, Search, Shirt, Sparkles, UsersRound } from 'lucide-react'
import { useEffect, useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ColagemLook } from '../componentes/ColagemLook'
import { Folha } from '../componentes/Folha'
import { CenaArara } from '../componentes/Ilustracao'
import { api, type Look, type Papel } from '../lib/api'
import { useGerar, usePecas, usePerfil } from '../lib/dados'
import { useFotos } from '../lib/fotos'
import { gerador } from '../lib/gerador'
import { silhuetaComoUrl } from '../lib/silhuetas'
import { primeiroNome } from '../lib/texto'

/** Vitrine "Tendências da semana": cada cartão é um pedido pronto ao gerador. */
const TENDENCIAS: { estilo: string; titulo: string; fundo: string; pecas: [string, Papel, string][] }[] = [
  { estilo: 'terroso', titulo: 'Tons terrosos', fundo: '#e2d9c6',
    pecas: [['camisa-casual', 'superior', '#b5651d'], ['calca-sarja', 'inferior', '#b09a6b'], ['bota', 'calcado', '#6b4423']] },
  { estilo: 'all-black', titulo: 'All black', fundo: '#cfcec9',
    pecas: [['camiseta', 'superior', '#1a1a1a'], ['calca-jeans', 'inferior', '#1a1a1a'], ['tenis', 'calcado', '#1a1a1a']] },
  { estilo: 'minimalista', titulo: 'Minimalista', fundo: '#dddbd2',
    pecas: [['camiseta', 'superior', '#f4f4f2'], ['calca-sarja', 'inferior', '#8c8c8c'], ['tenis-casual', 'calcado', '#f4f4f2']] },
  { estilo: 'esportivo', titulo: 'Esportivo', fundo: '#d6dccf',
    pecas: [['moletom', 'superior', '#8c8c8c'], ['calca-moletom', 'inferior', '#3d3d40'], ['tenis', 'calcado', '#2f5fb3']] },
  { estilo: 'classico', titulo: 'Clássico', fundo: '#d8d5cc',
    pecas: [['camisa-social', 'superior', '#9cc3e6'], ['calca-social', 'inferior', '#1c2a4a'], ['sapato-social', 'calcado', '#6b4423']] },
]

const NOME_PAPEL: Record<string, string> = { superior: 'parte de cima', inferior: 'parte de baixo', calcado: 'calçado' }

export function Inicio() {
  const navegar = useNavigate()
  const { perfil } = usePerfil()
  const { pecas } = usePecas()
  const { gerar, gerando, erro } = useGerar()
  const [busca, setBusca] = useState('')
  const [avisosAbertos, setAvisosAbertos] = useState(false)
  const [salvos, setSalvos] = useState<Look[]>([])
  const fotos = useFotos(salvos.flatMap((l) => l.pecas.map((p) => p.imagem_path)))

  useEffect(() => {
    api.looksSalvos().then(setSalvos).catch(() => undefined)
  }, [])

  // o "sininho" mostra o que falta para o app funcionar bem — avisos de verdade
  const faltando = pecas
    ? (['superior', 'inferior', 'calcado'] as const).filter((papel) => !pecas.some((p) => p.papel === papel && p.disponivel))
    : []
  const avisos = [
    ...(pecas && pecas.length === 0 ? ['Seu guarda-roupa está vazio. Cadastre as primeiras peças para receber looks.'] : []),
    ...(pecas && pecas.length > 0 && faltando.length
      ? [`Falta cadastrar ${faltando.map((p) => NOME_PAPEL[p]).join(' e ')} para montar um look completo.`]
      : []),
    ...(pecas?.some((p) => !p.disponivel)
      ? [`${pecas.filter((p) => !p.disponivel).length} peça(s) marcadas como indisponíveis não entram nos looks.`]
      : []),
  ]

  function buscar(evento: FormEvent) {
    evento.preventDefault()
    navegar(`/guarda-roupa${busca.trim() ? `?busca=${encodeURIComponent(busca.trim())}` : ''}`)
  }

  return (
    <main className="pagina">
      <header className="saudacao">
        <div>
          <h1>Olá, {primeiroNome(perfil.nome ?? perfil.email) || 'bem-vindo'}.</h1>
          <p>Vamos montar seu look de hoje?</p>
        </div>
        <button type="button" className="botao-icone sino" onClick={() => setAvisosAbertos(true)}
                aria-label={avisos.length ? `Avisos: ${avisos.length}` : 'Avisos'}>
          <Bell size={24} aria-hidden="true" />
          {avisos.length > 0 && <span className="sino__ponto" aria-hidden="true" />}
        </button>
      </header>

      <form className="busca" role="search" onSubmit={buscar}>
        <Search size={20} aria-hidden="true" />
        <input type="search" value={busca} onChange={(e) => setBusca(e.target.value)}
               placeholder="Buscar peças, looks, estilos…" aria-label="Buscar no guarda-roupa" enterKeyHint="search" />
      </form>

      <Link to="/gerador" className="destaque">
        <CenaArara foto="/img/hero.jpg" />
        <div className="destaque__texto">
          <h2>Novos estilos,<br />mesmas vibes.</h2>
          <p>Descubra looks que combinam com você.</p>
        </div>
        <span className="destaque__seta" aria-hidden="true"><ArrowRight size={22} /></span>
      </Link>

      <nav className="atalhos" aria-label="Atalhos">
        <Link to="/guarda-roupa" className="atalho"><Shirt size={28} strokeWidth={1.6} aria-hidden="true" /><span>Guarda-Roupa</span></Link>
        <Link to="/gerador" className="atalho"><Sparkles size={28} strokeWidth={1.6} aria-hidden="true" /><span>Gerador de Looks</span></Link>
        <Link to="/comunidade" className="atalho"><UsersRound size={28} strokeWidth={1.6} aria-hidden="true" /><span>Comunidade</span></Link>
      </nav>

      <section aria-labelledby="titulo-tendencias">
        <div className="secao-topo">
          <h2 id="titulo-tendencias">Tendências da semana</h2>
          <Link to="/gerador">Ver todas</Link>
        </div>
        {erro && <p className="aviso aviso--erro" role="alert">{erro}</p>}
        <div className="carrossel">
          {TENDENCIAS.map((t) => (
            <button key={t.estilo} type="button" className="tendencia" disabled={gerando}
                    onClick={() => void gerar({ estilo: t.estilo })} aria-label={`Gerar look ${t.titulo}`}>
              <span className="tendencia__arte" style={{ background: t.fundo }}>
                {t.pecas.map(([categoria, papel, cor]) => (
                  <img key={categoria} src={silhuetaComoUrl(categoria, papel, cor)} alt="" />
                ))}
              </span>
              <span className="tendencia__titulo">{t.titulo}</span>
            </button>
          ))}
        </div>
      </section>

      {salvos.length > 0 && (
        <section aria-labelledby="titulo-salvos">
          <div className="secao-topo">
            <h2 id="titulo-salvos">Seus looks salvos</h2>
            <Link to="/guarda-roupa?filtro=looks">Ver todos</Link>
          </div>
          <div className="carrossel">
            {salvos.slice(0, 8).map((look) => (
              <button key={look.id} type="button" className="tendencia"
                      onClick={() => { gerador.abrirSalvo(look); navegar('/gerador/look') }}>
                <span className="tendencia__arte tendencia__arte--look"><ColagemLook pecas={look.pecas} fotos={fotos} compacta /></span>
                <span className="tendencia__titulo">{look.titulo || 'Look salvo'}</span>
              </button>
            ))}
          </div>
        </section>
      )}

      <Folha aberta={avisosAbertos} titulo="Avisos" aoFechar={() => setAvisosAbertos(false)}>
        {avisos.length ? (
          <ul className="lista-avisos">{avisos.map((a) => <li key={a}>{a}</li>)}</ul>
        ) : (
          <p className="suave">Tudo certo por aqui. Nenhum aviso no momento.</p>
        )}
        {pecas?.length === 0 && (
          <Link to="/guarda-roupa/nova" className="botao botao--primario">Cadastrar primeira peça</Link>
        )}
      </Folha>
    </main>
  )
}
