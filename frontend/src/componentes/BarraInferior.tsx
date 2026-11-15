import { CircleUser, House, Shirt, Sparkles, Users } from 'lucide-react'
import { NavLink } from 'react-router-dom'

const ABAS = [
  { para: '/', rotulo: 'Início', Icone: House, exato: true },
  { para: '/guarda-roupa', rotulo: 'Guarda-Roupa', Icone: Shirt },
  { para: '/gerador', rotulo: 'Gerador', Icone: Sparkles },
  { para: '/comunidade', rotulo: 'Comunidade', Icone: Users },
  { para: '/perfil', rotulo: 'Perfil', Icone: CircleUser },
]

export default function BarraInferior() {
  return (
    <nav className="barra-inferior" aria-label="Navegação principal">
      {ABAS.map(({ para, rotulo, Icone, exato }) => (
        <NavLink key={para} to={para} end={exato} className="barra-inferior__aba">
          {({ isActive }) => (
            <>
              <Icone
                aria-hidden
                size={24}
                strokeWidth={isActive ? 2.4 : 1.8}
                fill={isActive ? 'currentColor' : 'none'}
                fillOpacity={isActive ? 0.18 : 0}
              />
              <span>{rotulo}</span>
            </>
          )}
        </NavLink>
      ))}
    </nav>
  )
}
