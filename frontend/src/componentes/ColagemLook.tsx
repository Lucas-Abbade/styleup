import type { PecaDoLook } from '../lib/api'
import { nomeDaCor } from '../lib/texto'
import { FotoPeca } from './FotoPeca'

interface Props {
  pecas: PecaDoLook[]
  fotos: Record<string, string>
  compacta?: boolean
}

/**
 * Onde cada peça fica na colagem: a peça de cima (ou o casaco) à esquerda, a
 * parte de baixo à direita e, na coluna do meio, o que sobra — de cima para
 * baixo, acessórios e por fim o calçado. É a disposição do protótipo.
 */
export function distribuir(pecas: PecaDoLook[]) {
  const por = (papel: string) => pecas.filter((p) => p.papel === papel)
  const sobreposicao = por('sobreposicao')[0]
  const superior = por('superior')[0]
  const esquerda = sobreposicao ?? superior
  const direita = por('inferior')[0]
  const meio = [...(sobreposicao && superior ? [superior] : []), ...por('acessorio'), ...por('calcado')]
  return { esquerda, direita, meio }
}

/** Colagem das peças do look sobre fundo escuro, como uma foto de produto. */
export function ColagemLook({ pecas, fotos, compacta }: Props) {
  const { esquerda, direita, meio } = distribuir(pecas)
  const item = (p: PecaDoLook | undefined) =>
    p && (
      <FotoPeca
        key={p.id}
        categoria={p.categoria}
        papel={p.papel}
        corHex={p.cor_hex}
        url={p.imagem_path ? fotos[p.imagem_path] : undefined}
        alt={`${p.rotulo}, ${nomeDaCor(p.cor_nome)}`}
      />
    )
  return (
    <div className={`colagem ${compacta ? 'colagem--compacta' : ''}`}>
      <div className="colagem__lado">{item(esquerda)}</div>
      <div className="colagem__meio" data-itens={meio.length}>{meio.map(item)}</div>
      <div className="colagem__lado">{item(direita)}</div>
    </div>
  )
}
