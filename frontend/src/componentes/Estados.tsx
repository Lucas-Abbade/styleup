import { RotateCw } from 'lucide-react'
import type { ReactNode } from 'react'

/** Blocos-fantasma no formato do conteúdo que vai chegar (evita salto de layout). */
export function GradeFantasma({ itens = 6 }: { itens?: number }) {
  return (
    <div className="grade-pecas" aria-hidden="true">
      {Array.from({ length: itens }, (_, i) => (
        <div key={i} className="cartao-peca cartao-peca--fantasma">
          <div className="cartao-peca__foto fantasma" />
          <div className="cartao-peca__texto">
            <span className="fantasma fantasma--linha" />
            <span className="fantasma fantasma--linha fantasma--curta" />
          </div>
        </div>
      ))}
    </div>
  )
}

export function Carregando({ texto = 'Carregando…' }: { texto?: string }) {
  return (
    <p className="carregando" role="status">
      <span className="rodinha" aria-hidden="true" />
      {texto}
    </p>
  )
}

interface VazioProps {
  icone: ReactNode
  titulo: string
  children?: ReactNode
  acao?: ReactNode
}

export function Vazio({ icone, titulo, children, acao }: VazioProps) {
  return (
    <div className="vazio">
      <div className="vazio__icone" aria-hidden="true">{icone}</div>
      <h2>{titulo}</h2>
      {children && <p>{children}</p>}
      {acao}
    </div>
  )
}

export function ErroBloco({ mensagem, aoTentar }: { mensagem: string; aoTentar?: () => void }) {
  return (
    <div className="aviso aviso--erro" role="alert">
      <p>{mensagem}</p>
      {aoTentar && (
        <button type="button" className="botao botao--contorno botao--pequeno" onClick={aoTentar}>
          <RotateCw size={16} aria-hidden="true" /> Tentar de novo
        </button>
      )}
    </div>
  )
}
