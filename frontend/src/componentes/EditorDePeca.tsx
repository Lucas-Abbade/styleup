import { useState } from 'react'
import { api, mensagemDe, type Categoria, type Cor, type Peca } from '../lib/api'
import { nomeDaCor } from '../lib/util'
import { useAviso } from './Avisos'
import Folha from './Folha'
import FotoPeca from './FotoPeca'

const PAPEIS: [string, string][] = [
  ['superior', 'Partes de cima'], ['inferior', 'Partes de baixo'], ['calcado', 'Calçados'],
  ['sobreposicao', 'Sobreposições'], ['acessorio', 'Acessórios'],
]
const FORMALIDADES = ['Esportiva', 'Casual', 'Casual arrumada', 'Social', 'Formal']

interface Props {
  peca: Peca | null
  url?: string
  categorias: Categoria[]
  cores: Cor[]
  aoFechar: () => void
  aoMudar: (peca: Peca) => void
  aoRemover: (id: string) => void
}

/** Folha de detalhes: corrigir categoria e cor, marcar como indisponível, remover. */
export default function EditorDePeca({ peca, url, categorias, cores, aoFechar, aoMudar, aoRemover }: Props) {
  const avisar = useAviso()
  const [erro, setErro] = useState('')
  const [ocupado, setOcupado] = useState(false)
  const [confirmando, setConfirmando] = useState(false)

  function fechar() {
    setErro('')
    setConfirmando(false)
    aoFechar()
  }

  async function mudar(campos: Record<string, unknown>, mensagem: string) {
    if (!peca) return
    setErro('')
    setOcupado(true)
    try {
      aoMudar(await api.atualizarPeca(peca.id, campos))
      avisar(mensagem)
    } catch (e) {
      setErro(mensagemDe(e))
    } finally {
      setOcupado(false)
    }
  }

  async function remover() {
    if (!peca) return
    setOcupado(true)
    try {
      await api.removerPeca(peca.id)
      aoRemover(peca.id)
      avisar('Peça removida')
      fechar()
    } catch (e) {
      setErro(mensagemDe(e))
    } finally {
      setOcupado(false)
    }
  }

  return (
    <Folha aberta={peca !== null} titulo={peca ? peca.rotulo : 'Peça'} aoFechar={fechar}>
      {peca && (
        <>
          <div className="folha__previa">
            <FotoPeca categoria={peca.categoria} papel={peca.papel} corHex={peca.cor_hex} url={url} />
            <div>
              <strong>{peca.rotulo}</strong>
              <p className="dica" style={{ marginTop: 2 }}>
                <span className="amostra" style={{ background: peca.cor_hex }} /> {nomeDaCor(peca.cor_nome)} · {peca.codigo}
              </p>
            </div>
          </div>

          <label className="campo">
            <span>Categoria</span>
            <select value={peca.categoria} disabled={ocupado}
              onChange={(e) => void mudar({ categoria: e.target.value }, 'Categoria atualizada')}>
              {PAPEIS.map(([papel, rotulo]) => (
                <optgroup key={papel} label={rotulo}>
                  {categorias.filter((c) => c.papel === papel).map((c) => (
                    <option key={c.chave} value={c.chave}>{c.rotulo}</option>
                  ))}
                </optgroup>
              ))}
            </select>
          </label>

          <label className="campo">
            <span>Formalidade</span>
            <select value={peca.formalidade} disabled={ocupado}
              onChange={(e) => void mudar({ formalidade: Number(e.target.value) }, 'Formalidade atualizada')}>
              {FORMALIDADES.map((rotulo, i) => <option key={rotulo} value={i + 1}>{i + 1} — {rotulo}</option>)}
            </select>
          </label>

          <div className="campo">
            <span id="rotulo-cor">Cor</span>
            <div className="cores" role="group" aria-labelledby="rotulo-cor">
              {cores.map((cor) => (
                <button key={cor.nome} type="button" className="chip" disabled={ocupado}
                  aria-pressed={cor.nome === peca.cor_nome}
                  onClick={() => void mudar({ cor_nome: cor.nome, cor_hex: cor.hex }, 'Cor atualizada')}>
                  <span className="amostra" style={{ background: cor.hex }} />
                  {nomeDaCor(cor.nome)}
                </button>
              ))}
            </div>
          </div>

          {erro && <p className="mensagem mensagem--erro" role="alert">{erro}</p>}

          <div className="botoes">
            <button type="button" className="botao botao--contorno" disabled={ocupado}
              onClick={() => void mudar({ disponivel: !peca.disponivel },
                peca.disponivel ? 'Fora dos looks por enquanto' : 'De volta aos looks')}>
              {peca.disponivel ? 'Marcar como indisponível (lavando, emprestada)' : 'Marcar como disponível'}
            </button>
            {confirmando ? (
              <button type="button" className="botao botao--perigo" disabled={ocupado} onClick={() => void remover()}>
                {ocupado ? 'Removendo…' : 'Confirmar: apagar peça e foto'}
              </button>
            ) : (
              <button type="button" className="botao botao--contorno" style={{ color: 'var(--perigo)', borderColor: 'var(--perigo)' }}
                onClick={() => setConfirmando(true)}>
                Remover do guarda-roupa
              </button>
            )}
          </div>
        </>
      )}
    </Folha>
  )
}
