import { X } from 'lucide-react'
import { useEffect, useRef, type ReactNode } from 'react'

interface Props {
  aberta: boolean
  titulo: string
  aoFechar: () => void
  children: ReactNode
}

/**
 * Folha que sobe da base da tela. Usa `<dialog>` nativo: o navegador cuida de
 * prender o foco, fechar com Esc e tornar o resto da página inerte.
 */
export function Folha({ aberta, titulo, aoFechar, children }: Props) {
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
              <X size={22} aria-hidden="true" />
            </button>
          </header>
          {children}
        </div>
      )}
    </dialog>
  )
}
