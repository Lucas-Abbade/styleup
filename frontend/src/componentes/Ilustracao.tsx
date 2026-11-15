import { useState } from 'react'

/**
 * Cena de fundo dos destaques: uma arara de roupas em tons de oliva.
 *
 * É desenho vetorial para ficar nítido em qualquer tela e não depender de
 * fotos. Se a equipe colocar uma foto em `public/img/<nome>.jpg` (por exemplo
 * as do protótipo), ela cobre a ilustração automaticamente.
 */
export function CenaArara({ foto, className }: { foto?: string; className?: string }) {
  const [temFoto, setTemFoto] = useState(Boolean(foto))
  const pecas = [
    { x: 150, cor: '#565b45', sombra: '#474b39' },
    { x: 214, cor: '#6b7052', sombra: '#585d44' },
    { x: 278, cor: '#4d5141', sombra: '#3f4335' },
    { x: 342, cor: '#7a7d63', sombra: '#666952' },
  ]
  return (
    <div className={`cena ${className ?? ''}`} aria-hidden="true">
      <svg viewBox="0 0 390 260" preserveAspectRatio="xMidYMid slice">
        <defs>
          <linearGradient id="cena-parede" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0" stopColor="#6a6964" />
            <stop offset="1" stopColor="#3a3a37" />
          </linearGradient>
          <radialGradient id="cena-luz" cx="0.72" cy="0.3" r="0.7">
            <stop offset="0" stopColor="#fff" stopOpacity="0.16" />
            <stop offset="1" stopColor="#fff" stopOpacity="0" />
          </radialGradient>
        </defs>
        <rect width="390" height="260" fill="url(#cena-parede)" />
        <rect width="390" height="260" fill="url(#cena-luz)" />
        <path d="M104 52 H390" stroke="#1f1f1c" strokeWidth="5" strokeLinecap="round" />
        {pecas.map(({ x, cor, sombra }) => (
          <g key={x} transform={`translate(${x} 52)`}>
            <path d="M0 0 v14 M-30 34 L0 14 L30 34" fill="none" stroke="#d8d5cb" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" />
            <path d="M-12 22 L-36 34 L-44 150 L-30 153 L-27 78 L-27 214 L27 214 L27 78 L30 153 L44 150 L36 34 L12 22 L0 34 Z" fill={cor} />
            <path d="M-12 22 L0 34 L12 22 L18 30 L4 52 L0 44 L-4 52 L-18 30 Z" fill={sombra} />
            <path d="M0 44 V214 M-27 120 H-10 M27 120 H10" stroke={sombra} strokeWidth="2" fill="none" />
          </g>
        ))}
      </svg>
      {temFoto && <img src={foto} alt="" onError={() => setTemFoto(false)} />}
    </div>
  )
}
