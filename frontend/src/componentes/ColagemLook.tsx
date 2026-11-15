import type { PecaDoLook } from '../lib/api'
import Colagem from './Colagem'

interface Props {
  pecas: PecaDoLook[]
  fotos: Record<string, string>
  compacta?: boolean
}

/** Colagem do look na tela "Look Gerado" (mesma disposição de lib/colagem.ts). */
export function ColagemLook({ pecas, fotos }: Props) {
  return <Colagem pecas={pecas} urls={fotos} />
}
