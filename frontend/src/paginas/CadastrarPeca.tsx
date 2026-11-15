import { Camera, ChevronLeft, Images, PencilLine } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAviso } from '../componentes/Avisos'
import { EditorPeca, type CamposPeca } from '../componentes/EditorPeca'
import { FotoPeca } from '../componentes/FotoPeca'
import { api, ErroApi, mensagemDe, type Analise, type Categoria, type Cor } from '../lib/api'
import { enviarFoto } from '../lib/fotos'
import { dataUrlParaBlob, prepararFoto } from '../lib/imagem'
import { nomeDaCor } from '../lib/texto'

type Etapa = 'escolher' | 'analisando' | 'confirmar'
const PASSOS = ['Enviando a foto…', 'Removendo o fundo…', 'Identificando a peça…', 'Lendo a cor…']

/**
 * Cadastro de peça (operações 6.2.1 e 6.2.2): foto → análise → confirmação.
 * Nada é gravado até o usuário confirmar; ele sempre pode corrigir a sugestão.
 */
export default function CadastrarPeca() {
  const navegar = useNavigate()
  const avisar = useAviso()
  const camera = useRef<HTMLInputElement>(null)
  const galeria = useRef<HTMLInputElement>(null)
  const [etapa, setEtapa] = useState<Etapa>('escolher')
  const [passo, setPasso] = useState(0)
  const [foto, setFoto] = useState<Blob | null>(null)
  const [previa, setPrevia] = useState<string | null>(null)
  const [analise, setAnalise] = useState<Analise | null>(null)
  const [campos, setCampos] = useState<CamposPeca>({ categoria: 'camiseta', cor_nome: 'preto', cor_hex: '#1a1a1a', formalidade: 1 })
  const [categorias, setCategorias] = useState<Categoria[]>([])
  const [cores, setCores] = useState<Cor[]>([])
  const [erro, setErro] = useState<string | null>(null)
  const [salvando, setSalvando] = useState(false)

  useEffect(() => {
    api.taxonomia().then(setCategorias).catch(() => undefined)
    api.cores().then(setCores).catch(() => undefined)
  }, [])
  useEffect(() => () => { if (previa?.startsWith('blob:')) URL.revokeObjectURL(previa) }, [previa])
  // a análise leva alguns segundos: dizer o que está acontecendo encurta a espera
  useEffect(() => {
    if (etapa !== 'analisando') return
    setPasso(0)
    const relogio = window.setInterval(() => setPasso((p) => Math.min(p + 1, PASSOS.length - 1)), 1300)
    return () => window.clearInterval(relogio)
  }, [etapa])

  async function escolher(arquivo: File | undefined) {
    if (!arquivo) return
    setErro(null)
    setEtapa('analisando')
    setPrevia(URL.createObjectURL(arquivo))
    try {
      const preparada = await prepararFoto(arquivo)
      setFoto(preparada)
      const resultado = await api.analisar(preparada)
      setAnalise(resultado)
      setCampos({ categoria: resultado.categoria, cor_nome: resultado.cor_nome, cor_hex: resultado.cor_hex, formalidade: resultado.formalidade })
      setEtapa('confirmar')
    } catch (e) {
      if (e instanceof ErroApi && e.codigo === 'visao_indisponivel') {
        // servidor sem os modelos de visão: o cadastro continua, à mão
        setAnalise(null)
        setEtapa('confirmar')
        setErro('A análise automática não está disponível agora. Preencha os dados da peça abaixo.')
      } else {
        setErro(mensagemDe(e))
        setEtapa('escolher')
        setPrevia(null)
      }
    }
  }

  function semFoto() {
    setFoto(null)
    setPrevia(null)
    setAnalise(null)
    setErro(null)
    setEtapa('confirmar')
  }

  async function salvar() {
    setSalvando(true)
    setErro(null)
    try {
      const cat = categorias.find((c) => c.chave === campos.categoria)
      // guarda-se o recorte sem fundo, não a foto original: o que estava atrás
      // da peça não sai do aparelho para o armazenamento
      const imagem = analise?.recorte ? await dataUrlParaBlob(analise.recorte) : foto
      const imagem_path = imagem ? await enviarFoto(imagem) : null
      await api.registrarPeca({
        categoria: campos.categoria,
        papel: cat?.papel ?? analise?.papel ?? 'superior',
        formalidade: campos.formalidade,
        cor_nome: campos.cor_nome,
        cor_hex: campos.cor_hex,
        temp_min: cat?.temp_min ?? 0,
        temp_max: cat?.temp_max ?? 45,
        resiste_chuva: cat?.resiste_chuva ?? true,
        atributos: analise?.atributos ?? {},
        confianca: analise?.confianca ?? {},
        imagem_path,
      })
      avisar('Peça cadastrada')
      navegar('/guarda-roupa')
    } catch (e) {
      setErro(mensagemDe(e))
    } finally {
      setSalvando(false)
    }
  }

  const categoriaAtual = categorias.find((c) => c.chave === campos.categoria)

  return (
    <main className="pagina">
      <header className="topo-voltar">
        <Link to="/guarda-roupa" className="botao-icone" aria-label="Voltar ao guarda-roupa"><ChevronLeft size={26} aria-hidden="true" /></Link>
        <h1>Nova peça</h1>
        <span />
      </header>

      {etapa === 'escolher' && (
        <>
          <div className="captura">
            <div className="captura__moldura" aria-hidden="true"><Camera size={44} strokeWidth={1.4} /></div>
            <h2>Fotografe uma peça por vez</h2>
            <ul className="dicas">
              <li>Estenda a peça sobre um fundo liso.</li>
              <li>Enquadre a peça inteira, com boa luz.</li>
              <li>O fundo é removido: só o recorte da peça é guardado.</li>
            </ul>
          </div>
          {erro && <p className="aviso aviso--erro" role="alert">{erro}</p>}
          {/* dois campos: `capture` é só uma dica e nem todo navegador oferece a galeria junto */}
          <input ref={camera} type="file" accept="image/*" capture="environment" hidden onChange={(e) => { void escolher(e.target.files?.[0]); e.target.value = '' }} />
          <input ref={galeria} type="file" accept="image/*" hidden onChange={(e) => { void escolher(e.target.files?.[0]); e.target.value = '' }} />
          <button type="button" className="botao botao--primario" onClick={() => camera.current?.click()}><Camera size={20} aria-hidden="true" /> Tirar foto</button>
          <button type="button" className="botao botao--contorno" onClick={() => galeria.current?.click()}><Images size={20} aria-hidden="true" /> Escolher da galeria</button>
          <button type="button" className="botao botao--texto" onClick={semFoto}><PencilLine size={18} aria-hidden="true" /> Cadastrar sem foto</button>
        </>
      )}

      {etapa === 'analisando' && (
        <div className="analisando" role="status" aria-live="polite">
          {previa && <img src={previa} alt="" className="analisando__foto" />}
          <div className="progresso" aria-hidden="true"><span style={{ width: `${((passo + 1) / PASSOS.length) * 100}%` }} /></div>
          <p>{PASSOS[passo]}</p>
        </div>
      )}

      {etapa === 'confirmar' && (
        <>
          <div className="previa-peca">
            <FotoPeca categoria={campos.categoria} papel={categoriaAtual?.papel ?? 'superior'} corHex={campos.cor_hex}
                      url={analise?.recorte ?? previa ?? undefined} alt={`${categoriaAtual?.rotulo ?? 'Peça'}, ${nomeDaCor(campos.cor_nome)}`} />
          </div>
          <p className="suave centro">
            {analise ? 'Confira o que identifiquei e corrija se precisar.' : 'Informe o tipo e a cor da peça.'}
          </p>
          <EditorPeca valor={campos} categorias={categorias} cores={cores} aoMudar={setCampos} destacarCategoria={analise?.confianca_baixa} />
          {erro && <p className="aviso aviso--erro" role="alert">{erro}</p>}
          <button type="button" className="botao botao--primario" disabled={salvando || !categorias.length} onClick={salvar}>
            {salvando ? 'Salvando…' : 'Salvar no guarda-roupa'}
          </button>
          <button type="button" className="botao botao--texto" disabled={salvando} onClick={() => { setEtapa('escolher'); setErro(null); setPrevia(null) }}>
            {foto ? 'Tirar outra foto' : 'Voltar'}
          </button>
        </>
      )}
    </main>
  )
}
