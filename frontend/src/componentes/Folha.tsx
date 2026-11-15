import { X } from 'lucide-react'
import { useEffect, useRef, type ReactNode } from 'react'

interface Props {
  aberta: boolean
  titulo: string
  aoFechar: () => void
  children: ReactNode
}

/**
 * Folha que sobe da base da tela. Usa <dialog>: o navegador cuida do foco
 * preso dentro dela, do Esc para fechar e de deixar o resto da página inerte.
 */
export default function Folha({ aberta, titulo, aoFechar, children }: Props) {
  const ref = useRef<HTMLDialogElement>(null)

  useEffect(() => {
    const dialogo = ref.current
    if (!dialogo) return
    if (aberta && !dialogo.open) dialogo.showModal()
    if (!aberta && dialogo.open) dialogo.close()
  }, [aberta])

  return (
    <dialog
      ref={ref}
      className="folha"
      aria-label={titulo}
      onClose={aoFechar}
      onClick={(e) => e.target === ref.current && aoFechar()}
    >
      {aberta && (
        <div className="folha__conteudo">
          <header className="folha__topo">
            <h2>{titulo}</h2>
            <button type="button" className="botao-icone" onClick={aoFechar} aria-label="Fechar">
              <X aria-hidden size={22} />
            </button>
          </header>
          {children}
        </div>
      )}
    </dialog>
  )
}

export { Folha }
