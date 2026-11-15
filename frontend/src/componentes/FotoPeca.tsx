import { useState } from 'react'
import type { Papel } from '../lib/api'
import { silhuetaComoUrl } from '../lib/silhuetas'

interface Props {
  categoria: string
  papel: Papel
  corHex: string
  url?: string // foto real; sem ela (ou se falhar), entra a silhueta na cor da peça
  alt: string
  className?: string
}

/**
 * Imagem de uma peça: a foto recortada quando existe, a silhueta quando não.
 *
 * A foto é pedida primeiro em modo CORS (`crossOrigin`): só assim a resposta
 * pode ser guardada pelo service worker (uso offline) e desenhada no canvas da
 * exportação. Se o servidor de arquivos não mandar o cabeçalho de CORS, a
 * segunda tentativa é um `<img>` comum; se nem assim carregar, entra a silhueta.
 */
export function FotoPeca({ categoria, papel, corHex, url, alt, className }: Props) {
  const [tentativa, setTentativa] = useState<{ url?: string; etapa: 0 | 1 | 2 }>({ url, etapa: 0 })
  // foto nova (por exemplo, a URL assinada chegou): recomeça do modo CORS
  const etapa = tentativa.url === url ? tentativa.etapa : 0
  const usarFoto = url && etapa < 2
  return (
    <img
      key={`${url}-${etapa}`}
      className={`foto-peca ${usarFoto ? '' : 'foto-peca--silhueta'} ${className ?? ''}`}
      src={usarFoto ? url : silhuetaComoUrl(categoria, papel, corHex)}
      crossOrigin={usarFoto && etapa === 0 ? 'anonymous' : undefined}
      alt={alt}
      loading="lazy"
      decoding="async"
      draggable={false}
      onError={() => usarFoto && setTentativa({ url, etapa: (etapa + 1) as 1 | 2 })}
    />
  )
}
