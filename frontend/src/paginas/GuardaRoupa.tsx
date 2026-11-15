import { Ellipsis, Plus, Search, Shirt, Sparkles } from 'lucide-react'
import { useMemo, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import Colagem from '../componentes/Colagem'
import EditorDePeca from '../componentes/EditorDePeca'
import { Esqueleto, Falha, Vazio } from '../componentes/Estados'
import FotoPeca from '../componentes/FotoPeca'
import { api, type Categoria, type Cor, type Look, type Peca } from '../lib/api'
import { usePecas } from '../lib/dados'
import { useFotos } from '../lib/fotos'
import { gerador } from '../lib/gerador'
import { nomeDaCor, semAcento, useCarga } from '../lib/util'

const FILTROS: { chave: string; rotulo: string; papeis: string[] }[] = [
  { chave: 'todas', rotulo: 'Todas', papeis: [] },
  { chave: 'camisetas', rotulo: 'Camisetas', papeis: ['superior'] },
  { chave: 'calcas', rotulo: 'Calças', papeis: ['inferior'] },
  { chave: 'sapatos', rotulo: 'Sapatos', papeis: ['calcado'] },
  { chave: 'outros', rotulo: 'Outros', papeis: ['sobreposicao', 'acessorio'] },
]

export default function GuardaRoupa() {
  const navegar = useNavigate()
  const [parametros, setParametros] = useSearchParams()
  const aba = parametros.get('aba') === 'looks' ? 'looks' : 'pecas'
  const [filtro, setFiltro] = useState('todas')
  const [busca, setBusca] = useState(parametros.get('q') ?? '')
  const [aberta, setAberta] = useState<Peca | null>(null)

  const { pecas: lista, erro: erroPecas, recarregar: recarregarPecas, atualizar } = usePecas()
  const looks = useCarga<Look[]>(() => api.looksSalvos())
  const catalogos = useCarga<[Categoria[], Cor[]]>(() => Promise.all([api.taxonomia(), api.cores()]))
  const urls = useFotos([
    ...(lista ?? []).map((p) => p.imagem_path),
    ...(looks.dados ?? []).flatMap((l) => l.pecas.map((p) => p.imagem_path)),
  ])

  const visiveis = useMemo(() => {
    const papeis = FILTROS.find((f) => f.chave === filtro)?.papeis ?? []
    const termo = semAcento(busca.trim())
    return (lista ?? []).filter((p) =>
      (!papeis.length || papeis.includes(p.papel)) &&
      (!termo || semAcento(`${p.rotulo} ${p.cor_nome} ${p.codigo}`).includes(termo)))
  }, [lista, filtro, busca])

  function abrirLook(look: Look) {
    gerador.abrirSalvo(look)
    navegar('/gerador/look')
  }

  return (
    <main className="tela">
      <header className="topo">
        <div><h1>Meu Guarda-Roupa</h1><p>Organize suas peças e crie combinações</p></div>
        <Link to="/guarda-roupa/nova" className="botao-icone botao-icone--cheio" aria-label="Adicionar peça">
          <Plus aria-hidden size={24} />
        </Link>
      </header>

      <div className="segmentos" role="group" aria-label="O que mostrar">
        <button type="button" aria-pressed={aba === 'pecas'} onClick={() => setParametros({})}>Peças</button>
        <button type="button" aria-pressed={aba === 'looks'} onClick={() => setParametros({ aba: 'looks' })}>
          Looks salvos
        </button>
      </div>

      {aba === 'pecas' ? (
        <>
          <div className="chips" role="group" aria-label="Filtrar por tipo">
            {FILTROS.map((f) => (
              <button key={f.chave} type="button" className="chip" aria-pressed={filtro === f.chave}
                onClick={() => setFiltro(f.chave)}>{f.rotulo}</button>
            ))}
          </div>
          <label className="busca" style={{ margin: '10px 0 14px' }}>
            <Search aria-hidden size={20} />
            <input type="search" value={busca} onChange={(e) => setBusca(e.target.value)}
              placeholder="Buscar por peça ou cor" aria-label="Buscar por peça ou cor" />
          </label>

          {!lista && !erroPecas && <Esqueleto />}
          {erroPecas && !lista && <Falha mensagem={erroPecas} aoTentar={() => void recarregarPecas()} />}
          {erroPecas && lista && (
            <p className="mensagem mensagem--info" role="status">
              Sem conexão: mostrando a última cópia salva neste aparelho.
            </p>
          )}
          {lista && lista.length === 0 && (
            <Vazio icone={<Shirt aria-hidden size={30} />} titulo="Seu guarda-roupa está vazio">
              <p>Fotografe uma peça: o Style Up identifica o tipo e a cor para você.</p>
              <Link className="botao" to="/guarda-roupa/nova">Adicionar a primeira peça</Link>
            </Vazio>
          )}
          {lista && lista.length > 0 && visiveis.length === 0 && (
            <p className="estado">Nenhuma peça encontrada com esse filtro.</p>
          )}

          <ul className="grade" style={{ listStyle: 'none', padding: 0, margin: 0 }}>
            {visiveis.map((p) => (
              <li key={p.id} className={`cartao-peca ${p.disponivel ? '' : 'cartao-peca--indisponivel'}`}>
                <button type="button" className="cartao-peca__abrir" onClick={() => setAberta(p)}
                  aria-label={`${p.rotulo}, ${p.cor_nome}${p.disponivel ? '' : ', indisponível'}. Abrir detalhes`}>
                  <div className="cartao-peca__foto">
                    <FotoPeca categoria={p.categoria} papel={p.papel} corHex={p.cor_hex}
                      url={p.imagem_path ? urls[p.imagem_path] : undefined} />
                  </div>
                  <div className="cartao-peca__texto">
                    <strong>{p.rotulo}</strong>
                    <span>{nomeDaCor(p.cor_nome)}</span>
                  </div>
                </button>
                {!p.disponivel && <span className="selo">Indisponível</span>}
                <span className="cartao-peca__menu botao-icone" aria-hidden><Ellipsis size={20} /></span>
              </li>
            ))}
          </ul>
        </>
      ) : (
        <>
          {looks.carregando && !looks.dados && <Esqueleto quantidade={2} />}
          {looks.erro && <Falha mensagem={looks.erro} aoTentar={looks.recarregar} />}
          {looks.dados && looks.dados.length === 0 && (
            <Vazio icone={<Sparkles aria-hidden size={30} />} titulo="Nenhum look salvo ainda">
              <p>Gere um look e toque em “Salvar no Guarda-Roupa” para guardá-lo aqui.</p>
              <Link className="botao" to="/gerador">Gerar um look</Link>
            </Vazio>
          )}
          <ul className="grade" style={{ listStyle: 'none', padding: 0, margin: 0 }}>
            {(looks.dados ?? []).map((look) => (
              <li key={look.id}>
                <button type="button" className="look-mini" style={{ width: '100%' }} onClick={() => abrirLook(look)}>
                  <Colagem pecas={look.pecas} urls={urls} />
                  <strong>{look.titulo || 'Look salvo'}</strong>
                </button>
              </li>
            ))}
          </ul>
        </>
      )}

      <EditorDePeca
        peca={aberta}
        url={aberta?.imagem_path ? urls[aberta.imagem_path] : undefined}
        categorias={catalogos.dados?.[0] ?? []}
        cores={catalogos.dados?.[1] ?? []}
        aoFechar={() => setAberta(null)}
        aoMudar={(nova) => {
          setAberta(nova)
          atualizar((lista ?? []).map((p) => (p.id === nova.id ? nova : p)))
        }}
        aoRemover={(id) => atualizar((lista ?? []).filter((p) => p.id !== id))}
      />
    </main>
  )
}
