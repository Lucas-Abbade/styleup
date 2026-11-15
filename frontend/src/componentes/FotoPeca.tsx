import { useState } from 'react'
import { silhuetaComoUrl } from '../lib/silhuetas'

interface Props {
  categoria: string
  papel: string
  corHex: string
  url?: string
  alt?: string
  className?: string
}

/** Foto da peça; sem foto (ou se ela falhar), a silhueta na cor da peça. */
export default function FotoPeca({ categoria, papel, corHex, url, alt = '', className }: Props) {
  const [falhou, setFalhou] = useState(false)
  const usarFoto = url && !falhou
  return (
    <img
      className={`foto-peca ${usarFoto ? '' : 'foto-peca--silhueta'} ${className ?? ''}`}
      src={usarFoto ? url : silhuetaComoUrl(categoria, papel, corHex)}
      alt={alt}
      loading="lazy"
      decoding="async"
      onError={() => setFalhou(true)}
    />
  )
}

export { FotoPeca }
