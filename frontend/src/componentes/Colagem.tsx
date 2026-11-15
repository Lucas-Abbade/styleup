import type { PecaDoLook } from '../lib/api'
import { disporPecas } from '../lib/colagem'
import FotoPeca from './FotoPeca'

/** O look montado como um "flat lay" sobre fundo escuro, como no design. */
export default function Colagem({ pecas, urls }: { pecas: PecaDoLook[]; urls: Record<string, string> }) {
  const descricao = pecas.map((p) => `${p.rotulo} ${p.cor_nome}`).join(', ')
  return (
    <div className="colagem" role="img" aria-label={`Look: ${descricao}`}>
      {disporPecas(pecas).map(({ peca, x, y, l, a }) => (
        <div key={peca.id} className="colagem__peca"
          style={{ left: `${x * 100}%`, top: `${y * 100}%`, width: `${l * 100}%`, height: `${a * 100}%` }}>
          <FotoPeca categoria={peca.categoria} papel={peca.papel} corHex={peca.cor_hex}
            url={peca.imagem_path ? urls[peca.imagem_path] : undefined} />
        </div>
      ))}
    </div>
  )
}
