import { createContext, useCallback, useContext, useRef, useState, type ReactNode } from 'react'

type Avisar = (texto: string, tipo?: 'ok' | 'erro') => void
const Contexto = createContext<Avisar>(() => undefined)

/** Mensagem breve no rodapé ("Look salvo"). Anunciada a leitores de tela. */
export function ProvedorDeAvisos({ children }: { children: ReactNode }) {
  const [aviso, setAviso] = useState<{ texto: string; tipo: 'ok' | 'erro'; id: number } | null>(null)
  const relogio = useRef<number>()
  const avisar = useCallback<Avisar>((texto, tipo = 'ok') => {
    window.clearTimeout(relogio.current)
    setAviso({ texto, tipo, id: Date.now() })
    relogio.current = window.setTimeout(() => setAviso(null), tipo === 'erro' ? 6000 : 3200)
  }, [])
  return (
    <Contexto.Provider value={avisar}>
      {children}
      <div className="torrada-area" role="status" aria-live="polite">
        {aviso && (
          <div key={aviso.id} className={`torrada torrada--${aviso.tipo}`}>
            {aviso.texto}
          </div>
        )}
      </div>
    </Contexto.Provider>
  )
}

export const useAviso = () => useContext(Contexto)
