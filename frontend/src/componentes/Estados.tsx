import { CloudOff, LoaderCircle } from 'lucide-react'
import type { ReactNode } from 'react'

export function Carregando({ rotulo = 'Carregando…' }: { rotulo?: string }) {
  return (
    <p className="estado" role="status">
      <LoaderCircle aria-hidden className="girando" size={22} />
      {rotulo}
    </p>
  )
}

export function Esqueleto({ quantidade = 4 }: { quantidade?: number }) {
  return (
    <div className="grade" aria-hidden>
      {Array.from({ length: quantidade }, (_, i) => (
        <div key={i} className="cartao-peca cartao-peca--esqueleto">
          <div className="cartao-peca__foto" />
          <div className="cartao-peca__texto">
            <span className="linha-esqueleto" />
            <span className="linha-esqueleto linha-esqueleto--curta" />
          </div>
        </div>
      ))}
    </div>
  )
}

export function Falha({ mensagem, aoTentar }: { mensagem: string; aoTentar?: () => void }) {
  return (
    <div className="estado estado--bloco" role="alert">
      <CloudOff aria-hidden size={28} />
      <p>{mensagem}</p>
      {aoTentar && (
        <button type="button" className="botao botao--contorno" onClick={aoTentar}>
          Tentar de novo
        </button>
      )}
    </div>
  )
}

export function Vazio({ icone, titulo, children }: { icone: ReactNode; titulo: string; children?: ReactNode }) {
  return (
    <div className="estado estado--bloco">
      <span className="estado__icone">{icone}</span>
      <h2>{titulo}</h2>
      {children}
    </div>
  )
}
