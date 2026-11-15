// Ilustração da arara de roupas usada no destaque da tela inicial, no gerador e
// na abertura. Vetorial: fica nítida em qualquer tela. Se existir uma foto em
// public/img/ com o nome indicado, ela cobre a ilustração.
import { useState } from 'react'

const TONS = ['#3f4433', '#565c44', '#484d3a', '#626950', '#3a3f30', '#50563f']

function Jaqueta({ x, tom, largura = 74 }: { x: number; tom: string; largura?: number }) {
  const m = largura / 2
  return (
    <g transform={`translate(${x} 0)`}>
      <path d={`M0 38c0-7 9-7 9-13a9 9 0 1 0-18 0`} fill="none" stroke="#b9b6aa" strokeWidth="2.4" />
      <path
        d={`M0 38 ${-m} 62c-6 3-8 8-8 14l-6 150c0 6 4 10 10 10h${largura + 8}c6 0 10-4 10-10L${m + 8} 76c0-6-2-11-8-14Z`}
        fill={tom}
      />
      <path d={`M0 38 ${-m * 0.42} 56 0 92 ${m * 0.42} 56Z`} fill="rgba(0,0,0,.22)" />
      <path d="M0 92v144" stroke="rgba(0,0,0,.25)" strokeWidth="2" />
      <path d={`M${-m * 0.7} 150h${m * 0.5}M${m * 0.2} 150h${m * 0.5}`} stroke="rgba(255,255,255,.12)" strokeWidth="3" />
    </g>
  )
}

export default function Arara({ foto, className = '' }: { foto?: string; className?: string }) {
  const [temFoto, setTemFoto] = useState(Boolean(foto))
  return (
    <div className={`arara ${className}`} aria-hidden>
      <svg viewBox="0 0 400 280" preserveAspectRatio="xMidYMid slice">
        <defs>
          <linearGradient id="parede" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#6a6966" />
            <stop offset="1" stopColor="#3d3c3a" />
          </linearGradient>
        </defs>
        <rect width="400" height="280" fill="url(#parede)" />
        <rect x="0" y="12" width="400" height="5" rx="2.5" fill="#c9c6ba" />
        {[150, 205, 258, 312, 364, 418].map((x, i) => (
          <Jaqueta key={x} x={x} tom={TONS[i]} largura={i % 2 ? 66 : 76} />
        ))}
      </svg>
      {temFoto && <img src={foto} alt="" onError={() => setTemFoto(false)} />}
    </div>
  )
}
