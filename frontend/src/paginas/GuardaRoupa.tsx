import { Ellipsis, Plus, Search, Shirt, Trash2 } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { useAviso } from '../componentes/Avisos'
import { ColagemLook } from '../componentes/ColagemLook'
import { EditorPeca, type CamposPeca } from '../componentes/EditorPeca'
import { ErroBloco, GradeFantasma, Vazio } from '../componentes/Estados'
import { Folha } from '../componentes/Folha'
import { FotoPeca } from '../componentes/FotoPeca'
import { api, mensagemDe, type Categoria, type Cor, type Look, type Peca } from '../lib/api'
import { usePecas } from '../lib/dados'
import { useFotos } from '../lib/fotos'
import { gerador } from '../lib/gerador'
import { nomeDaCor, semAcento } from '../lib/texto'

const FILTROS = [
  { chave: 'todas', rotulo: 'Todas', papeis: null },
  { chave: 'cima', rotulo: 'Camisetas', papeis: ['superior'] },
  { chave: 'baixo', rotulo: 'Calças', papeis: ['inferior'] },
  { chave: 'calcados', rotulo: 'Sapatos', papeis: ['calcado'] },
  { chave: 'outros', rotulo: 'Outros', papeis: ['sobreposicao', 'acessorio'] },
  { chave: 'looks', rotulo: 'Looks salvos', papeis: [] },
] as const

export function GuardaRoupa() {
  const navegar = useNavigate()
  const avisar = useAviso()
  const [parametros, setParametros] = useSearchParams()
  const filtro = parametros.get('filtro') ?? 'todas'
  const busca = parametros.get('busca') ?? ''
  const { pecas, erro, recarregar, atualizar } = usePecas()
  const [salvos, setSalvos] = useState<Look[] | null>(null)
  const [categorias, setCategorias] = useState<Categoria[]>([])
  const [cores, setCores] = useState<Cor[]>([])
  const [editando, setEditando] = useState<Peca | null>(null)
  const [campos, setCampos] = useState<CamposPeca | null>(null)
  const [confirmandoRemocao, setConfirmandoRemocao] = useState(false)
  const [ocupado, setOcupado] = useState(false)
  const [erroFolha, setErroFolha] = useState<string | null>(null)

  useEffect(() => {
    api.taxonomia().then(setCategorias).catch(() => undefined)
    api.cores().then(setCores).catch(() => undefined)
  }, [])
  useEffect(() => {
    if (filtro === 'looks') api.looksSalvos().then(setSalvos).catch(() => setSalvos([]))
  }, [filtro])

  const visiveis = useMemo(() => {
    const papeis = FILTROS.find((f) => f.chave === filtro)?.papeis as readonly string[] | null | undefined
    const termo = semAcento(busca.trim())
    return (pecas ?? []).filter(
      (p) =>
        (!papeis || papeis.includes(p.papel)) &&
        (!termo || semAcento(`${p.rotulo} ${p.cor_nome} ${p.categoria} ${p.codigo}`).includes(termo)),
    )
  }, [pecas, filtro, busca])

  const fotos = useFotos([
    ...visiveis.map((p) => p.imagem_path),
    ...(salvos ?? []).flatMap((l) => l.pecas.map((p) => p.imagem_path)),
  ])

  function mudar(chave: 'filtro' | 'busca', valor: string) {
    const novos = new URLSearchParams(parametros)
    if (valor && valor !== 'todas') novos.set(chave, valor)
    else novos.delete(chave)
    setParametros(novos, { replace: true })
  }

  function abrir(peca: Peca) {
    setEditando(peca)
    setCampos({ categoria: peca.categoria, cor_nome: peca.cor_nome, cor_hex: peca.cor_hex, formalidade: peca.formalidade })
    setConfirmandoRemocao(false)
    setErroFolha(null)
  }

  async function aplicar(mudancas: Partial<Peca>, recado: string) {
    if (!editando || !pecas) return
    setOcupado(true)
    setErroFolha(null)
    try {
      const nova = await api.atualizarPeca(editando.id, mudancas)
      atualizar(pecas.map((p) => (p.id === nova.id ? nova : p)))
      setEditando(null)
      avisar(recado)
    } catch (e) {
      setErroFolha(mensagemDe(e))
    } finally {
      setOcupado(false)
    }
  }

  function salvarEdicao() {
    if (!editando || !campos) return
    const mudancas: Partial<Peca> = {}
    if (campos.categoria !== editando.categoria) mudancas.categoria = campos.categoria
    if (campos.cor_hex !== editando.cor_hex || campos.cor_nome !== editando.cor_nome) {
      mudancas.cor_nome = campos.cor_nome
      mudancas.cor_hex = campos.cor_hex
    }
    if (campos.formalidade !== editando.formalidade) mudancas.formalidade = campos.formalidade
    if (!Object.keys(mudancas).length) return setEditando(null)
    void aplicar(mudancas, 'Peça atualizada')
  }

  async function remover() {
    if (!editando || !pecas) return
    setOcupado(true)
    setErroFolha(null)
    try {
      await api.removerPeca(editando.id)
      atualizar(pecas.filter((p) => p.id !== editando.id))
      setEditando(null)
      avisar('Peça removida')
    } catch (e) {
      setErroFolha(mensagemDe(e))
    } finally {
      setOcupado(false)
    }
  }

  return (
    <main className="pagina">
      <header className="topo-pagina">
        <h1 className="titulo-pagina">Meu Guarda-Roupa</h1>
        <Link to="/guarda-roupa/nova" className="botao-mais" aria-label="Cadastrar peça">
          <Plus size={24} aria-hidden="true" />
        </Link>
      </header>

      <div className="chips" role="tablist" aria-label="Filtrar guarda-roupa">
        {FILTROS.map((f) => (
          <button key={f.chave} type="button" role="tab" aria-selected={filtro === f.chave}
                  className={`chip ${filtro === f.chave ? 'chip--ativo' : ''}`} onClick={() => mudar('filtro', f.chave)}>
            {f.rotulo}
          </button>
        ))}
      </div>

      {filtro !== 'looks' && (pecas?.length ?? 0) > 6 && (
        <label className="busca busca--compacta">
          <Search size={18} aria-hidden="true" />
          <input type="search" value={busca} onChange={(e) => mudar('busca', e.target.value)}
                 placeholder="Buscar por nome ou cor" aria-label="Buscar peças" />
        </label>
      )}

      {erro && pecas && <p className="aviso aviso--info" role="status">Sem conexão: mostrando a última cópia do seu guarda-roupa.</p>}
      {erro && !pecas && <ErroBloco mensagem={erro} aoTentar={recarregar} />}

      {filtro === 'looks' ? (
        salvos === null ? <GradeFantasma itens={2} /> : salvos.length === 0 ? (
          <Vazio icone={<Shirt size={34} />} titulo="Nenhum look salvo ainda"
                 acao={<Link to="/gerador" className="botao botao--primario">Gerar um look</Link>}>
            Quando gostar de uma sugestão, toque em “Salvar no Guarda-Roupa” e ela aparece aqui.
          </Vazio>
        ) : (
          <div className="grade-pecas">
            {salvos.map((look) => (
              <button key={look.id} type="button" className="cartao-peca cartao-peca--look"
                      onClick={() => { gerador.abrirSalvo(look); navegar('/gerador/look') }}>
                <div className="cartao-peca__foto cartao-peca__foto--escura"><ColagemLook pecas={look.pecas} fotos={fotos} compacta /></div>
                <div className="cartao-peca__texto">
                  <strong>{look.titulo || 'Look salvo'}</strong>
                  <span>{look.pecas.length} peças</span>
                </div>
              </button>
            ))}
          </div>
        )
      ) : pecas === null ? (
        !erro && <GradeFantasma />
      ) : pecas.length === 0 ? (
        <Vazio icone={<Shirt size={34} />} titulo="Seu guarda-roupa está vazio"
               acao={<Link to="/guarda-roupa/nova" className="botao botao--primario"><Plus size={18} aria-hidden="true" /> Cadastrar primeira peça</Link>}>
          Fotografe uma peça e o Style Up identifica o tipo e a cor. Com uma parte de cima, uma de baixo e um
          calçado você já recebe o primeiro look.
        </Vazio>
      ) : visiveis.length === 0 ? (
        <Vazio icone={<Search size={34} />} titulo="Nada encontrado">
          Nenhuma peça corresponde a este filtro{busca ? ` e à busca “${busca}”` : ''}.
        </Vazio>
      ) : (
        <ul className="grade-pecas">
          {visiveis.map((p) => (
            <li key={p.id} className={`cartao-peca ${p.disponivel ? '' : 'cartao-peca--indisponivel'}`}>
              <div className="cartao-peca__foto">
                <FotoPeca categoria={p.categoria} papel={p.papel} corHex={p.cor_hex}
                          url={p.imagem_path ? fotos[p.imagem_path] : undefined} alt="" />
                {!p.disponivel && <span className="etiqueta-mini">Indisponível</span>}
              </div>
              <div className="cartao-peca__texto">
                <strong>{p.rotulo}</strong>
                <span>{nomeDaCor(p.cor_nome)}</span>
              </div>
              <button type="button" className="cartao-peca__mais" onClick={() => abrir(p)}
                      aria-label={`Opções de ${p.rotulo} ${p.cor_nome}`}>
                <Ellipsis size={20} aria-hidden="true" />
              </button>
            </li>
          ))}
        </ul>
      )}

      <Folha aberta={!!editando} titulo={editando ? `${editando.rotulo} · ${editando.codigo}` : ''} aoFechar={() => setEditando(null)}>
        {editando && campos && (
          <>
            <div className="previa-peca">
              <FotoPeca categoria={campos.categoria} papel={categorias.find((c) => c.chave === campos.categoria)?.papel ?? editando.papel}
                        corHex={campos.cor_hex} url={editando.imagem_path ? fotos[editando.imagem_path] : undefined}
                        alt={`${editando.rotulo}, ${nomeDaCor(campos.cor_nome)}`} />
            </div>
            <EditorPeca valor={campos} categorias={categorias} cores={cores} aoMudar={setCampos} />
            <label className="alternar">
              <span>
                <strong>Disponível para looks</strong>
                <small>Desligue enquanto estiver lavando ou emprestada.</small>
              </span>
              <input type="checkbox" role="switch" checked={editando.disponivel} disabled={ocupado}
                     onChange={(e) => void aplicar({ disponivel: e.target.checked }, e.target.checked ? 'Peça disponível de novo' : 'Peça marcada como indisponível')} />
            </label>
            {erroFolha && <p className="aviso aviso--erro" role="alert">{erroFolha}</p>}
            <button type="button" className="botao botao--primario" disabled={ocupado} onClick={salvarEdicao}>Salvar alterações</button>
            {confirmandoRemocao ? (
              <div className="confirmar">
                <p>Remover esta peça e a foto dela? Não dá para desfazer.</p>
                <button type="button" className="botao botao--perigo" disabled={ocupado} onClick={remover}>Sim, remover</button>
                <button type="button" className="botao botao--texto" onClick={() => setConfirmandoRemocao(false)}>Cancelar</button>
              </div>
            ) : (
              <button type="button" className="botao botao--texto botao--texto-perigo" onClick={() => setConfirmandoRemocao(true)}>
                <Trash2 size={18} aria-hidden="true" /> Remover peça
              </button>
            )}
          </>
        )}
      </Folha>
    </main>
  )
}
