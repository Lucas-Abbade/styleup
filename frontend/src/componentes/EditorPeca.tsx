import { useId } from 'react'
import type { Categoria, Cor, Papel } from '../lib/api'
import { nomeDaCor } from '../lib/texto'

const NOME_PAPEL: Record<Papel, string> = {
  superior: 'Partes de cima', inferior: 'Partes de baixo', calcado: 'Calçados',
  sobreposicao: 'Sobreposições', acessorio: 'Acessórios',
}
const FORMALIDADE = ['Esportiva', 'Casual', 'Casual arrumada', 'Social', 'Formal']

export interface CamposPeca {
  categoria: string
  cor_nome: string
  cor_hex: string
  formalidade: number
}

interface Props {
  valor: CamposPeca
  categorias: Categoria[]
  cores: Cor[]
  aoMudar: (novo: CamposPeca) => void
  destacarCategoria?: boolean
}

/** Campos de categoria, cor e formalidade — usados no cadastro e na edição. */
export function EditorPeca({ valor, categorias, cores, aoMudar, destacarCategoria }: Props) {
  const id = useId()
  const papeis = [...new Set(categorias.map((c) => c.papel))]
  const corConhecida = cores.some((c) => c.nome === valor.cor_nome)

  function trocarCategoria(chave: string) {
    const cat = categorias.find((c) => c.chave === chave)
    aoMudar({ ...valor, categoria: chave, formalidade: cat?.formalidade ?? valor.formalidade })
  }
  function trocarCor(nome: string) {
    const cor = cores.find((c) => c.nome === nome)
    if (cor) aoMudar({ ...valor, cor_nome: cor.nome, cor_hex: cor.hex })
  }

  return (
    <div className="formulario">
      {/* rótulo separado do <select>: dentro dele, o nome acessível incluiria as opções */}
      <div className={`campo ${destacarCategoria ? 'campo--destaque' : ''}`}>
        <label htmlFor={`${id}-categoria`}>Categoria</label>
        <select id={`${id}-categoria`} value={valor.categoria} onChange={(e) => trocarCategoria(e.target.value)}>
          {papeis.map((papel) => (
            <optgroup key={papel} label={NOME_PAPEL[papel]}>
              {categorias.filter((c) => c.papel === papel).map((c) => (
                <option key={c.chave} value={c.chave}>{c.rotulo}</option>
              ))}
            </optgroup>
          ))}
        </select>
        {destacarCategoria && <small>Não tive certeza desta. Confira antes de salvar.</small>}
      </div>

      {/* O nome da cor vem sempre escrito: quem não distingue a amostra confere pelo texto (RNF05). */}
      <div className="campo">
        <label htmlFor={`${id}-cor`}>Cor</label>
        <span className="campo-cor">
          <span className="amostra" style={{ background: valor.cor_hex }} aria-hidden="true" />
          <select id={`${id}-cor`} value={corConhecida ? valor.cor_nome : ''} onChange={(e) => trocarCor(e.target.value)}>
            {!corConhecida && <option value="">{nomeDaCor(valor.cor_nome)}</option>}
            {cores.map((c) => <option key={c.nome} value={c.nome}>{nomeDaCor(c.nome)}</option>)}
          </select>
        </span>
      </div>

      <fieldset className="campo">
        <legend>Formalidade</legend>
        <div className="segmentos" role="radiogroup">
          {FORMALIDADE.map((rotulo, i) => (
            <label key={rotulo} className={valor.formalidade === i + 1 ? 'ativo' : ''}>
              <input type="radio" name="formalidade" checked={valor.formalidade === i + 1}
                     onChange={() => aoMudar({ ...valor, formalidade: i + 1 })} />
              <span aria-hidden="true">{i + 1}</span>
              <span className="so-leitor">{rotulo}</span>
            </label>
          ))}
        </div>
        <small>{FORMALIDADE[valor.formalidade - 1]}</small>
      </fieldset>
    </div>
  )
}
