import { ArrowRight, Search, Shirt, Sparkles, Users } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import Arara from '../componentes/Arara'
import Colagem from '../componentes/Colagem'
import { api, type Look, type Perfil } from '../lib/api'
import { useFotos } from '../lib/fotos'
import { gerador } from '../lib/gerador'
import { silhuetaComoUrl } from '../lib/silhuetas'
import { primeiroNome, useCarga } from '../lib/util'

const FOTO = import.meta.env.VITE_FOTO_DESTAQUE as string | undefined

// Curadoria da casa: cada cartão abre o gerador já com o estilo escolhido.
const TENDENCIAS = [
  { estilo: 'terroso', titulo: 'Tons terrosos', texto: 'Marrom, cáqui e oliva',
    fundo: '#ddd3bf', pecas: [['jaqueta-jeans', '#6b7340'], ['calca-sarja', '#b09a6b'], ['bota', '#6b4423']] },
  { estilo: 'all-black', titulo: 'All black', texto: 'Preto dos pés à cabeça',
    fundo: '#cfcdc6', pecas: [['camiseta', '#1a1a1a'], ['calca-jeans', '#232323'], ['tenis', '#1a1a1a']] },
  { estilo: 'minimalista', titulo: 'Minimalista', texto: 'Neutros e peças lisas',
    fundo: '#e6e2d6', pecas: [['camisa-casual', '#f4f4f2'], ['calca-social', '#3d3d40'], ['tenis-casual', '#f4f4f2']] },
  { estilo: 'urbano', titulo: 'Urbano', texto: 'Streetwear do dia a dia',
    fundo: '#d5d8cf', pecas: [['moletom', '#8c8c8c'], ['calca-moletom', '#3d3d40'], ['bone', '#4d5141']] },
  { estilo: 'classico', titulo: 'Clássico', texto: 'Alinhado e discreto',
    fundo: '#d9d6dd', pecas: [['blazer', '#1c2a4a'], ['calca-social', '#8c8c8c'], ['sapato-social', '#3b2616']] },
] as const

export default function Inicio({ perfil }: { perfil: Perfil }) {
  const navegar = useNavigate()
  const [busca, setBusca] = useState('')
  const salvos = useCarga<Look[]>(() => api.looksSalvos())
  const urls = useFotos((salvos.dados ?? []).flatMap((l) => l.pecas.map((p) => p.imagem_path)))

  function buscar(evento: FormEvent) {
    evento.preventDefault()
    navegar(`/guarda-roupa${busca.trim() ? `?q=${encodeURIComponent(busca.trim())}` : ''}`)
  }

  function abrirSalvo(look: Look) {
    gerador.abrirSalvo(look)
    navegar('/gerador/look')
  }

  return (
    <main className="tela">
      <header className="topo">
        <div>
          <h1>Olá, {primeiroNome(perfil.nome ?? perfil.email) || 'bem-vindo'}.</h1>
          <p>Bem-vindo ao seu espaço fashion</p>
        </div>
      </header>

      <form className="busca" role="search" onSubmit={buscar}>
        <Search aria-hidden size={20} />
        <input type="search" value={busca} onChange={(e) => setBusca(e.target.value)}
          placeholder="Buscar peças no guarda-roupa" aria-label="Buscar peças no guarda-roupa" />
      </form>

      <Link to="/gerador" className="destaque">
        <Arara foto={FOTO} />
        <div className="destaque__texto">
          <h2>Novos estilos, mesmas vibes.</h2>
          <p>Descubra combinações perfeitas para o seu dia.</p>
          <span className="destaque__seta"><ArrowRight aria-hidden size={20} /></span>
        </div>
      </Link>

      <nav className="atalhos" aria-label="Atalhos">
        <Link className="atalho" to="/guarda-roupa"><Shirt aria-hidden size={30} strokeWidth={1.6} />Guarda-Roupa</Link>
        <Link className="atalho" to="/gerador"><Sparkles aria-hidden size={30} strokeWidth={1.6} />Gerador de Looks</Link>
        <Link className="atalho" to="/comunidade"><Users aria-hidden size={30} strokeWidth={1.6} />Comunidade</Link>
      </nav>

      <section className="secao" aria-labelledby="tendencias">
        <div className="secao__titulo">
          <h2 id="tendencias">Tendências da semana</h2>
          <Link to="/gerador">Ver todas</Link>
        </div>
        <div className="trilho">
          {TENDENCIAS.map((t) => (
            <button key={t.estilo} type="button" className="tendencia"
              onClick={() => navegar(`/gerador?estilo=${t.estilo}`)}>
              <div className="tendencia__arte" style={{ background: t.fundo }}>
                {t.pecas.map(([categoria, cor]) => (
                  <img key={categoria} src={silhuetaComoUrl(categoria, '', cor)} alt="" />
                ))}
              </div>
              <strong>{t.titulo}</strong>
              <span>{t.texto}</span>
            </button>
          ))}
        </div>
      </section>

      {salvos.dados && salvos.dados.length > 0 && (
        <section className="secao" aria-labelledby="salvos">
          <div className="secao__titulo">
            <h2 id="salvos">Seus looks salvos</h2>
            <Link to="/guarda-roupa?aba=looks">Ver todos</Link>
          </div>
          <div className="trilho">
            {salvos.dados.slice(0, 8).map((look) => (
              <button key={look.id} type="button" className="look-mini" onClick={() => abrirSalvo(look)}>
                <Colagem pecas={look.pecas} urls={urls} />
                <strong>{look.titulo || 'Look salvo'}</strong>
              </button>
            ))}
          </div>
        </section>
      )}
    </main>
  )
}
