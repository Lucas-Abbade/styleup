import { createContext, useCallback, useContext, useRef, useState, type ReactNode } from 'react'

type Tipo = 'ok' | 'erro'
type Avisar = (texto: string, tipo?: Tipo) => void
const Contexto = createContext<Avisar>(() => undefined)

/** Mensagens curtas de confirmação ("Peça salva"). Lidas por leitores de tela. */
export function ProvedorDeAvisos({ children }: { children: ReactNode }) {
  const [aviso, setAviso] = useState<{ texto: string; tipo: Tipo } | null>(null)
  const temporizador = useRef<number>()
  const avisar = useCallback<Avisar>((texto, tipo = 'ok') => {
    setAviso({ texto, tipo })
    window.clearTimeout(temporizador.current)
    temporizador.current = window.setTimeout(() => setAviso(null), tipo === 'erro' ? 5000 : 3200)
  }, [])
  return (
    <Contexto.Provider value={avisar}>
      {children}
      <div className="aviso-flutuante" role="status" aria-live="polite">
        {aviso && <span className={aviso.tipo === 'erro' ? 'aviso-flutuante--erro' : ''}>{aviso.texto}</span>}
      </div>
    </Contexto.Provider>
  )
}

export const useAviso = () => useContext(Contexto)
