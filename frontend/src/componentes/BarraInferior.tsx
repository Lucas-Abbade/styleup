import { CircleUserRound, House, Shirt, Sparkles, UsersRound } from 'lucide-react'
import { NavLink } from 'react-router-dom'

const ABAS = [
  { para: '/', rotulo: 'Início', Icone: House, fim: true },
  { para: '/guarda-roupa', rotulo: 'Guarda-Roupa', Icone: Shirt },
  { para: '/gerador', rotulo: 'Gerador', Icone: Sparkles },
  { para: '/comunidade', rotulo: 'Comunidade', Icone: UsersRound },
  { para: '/perfil', rotulo: 'Perfil', Icone: CircleUserRound },
]

/** Navegação principal: cinco destinos, sempre visíveis, com rótulo. */
export function BarraInferior() {
  return (
    <nav className="barra-inferior" aria-label="Navegação principal">
      {ABAS.map(({ para, rotulo, Icone, fim }) => (
        <NavLink key={para} to={para} end={fim} className="barra-inferior__aba">
          {({ isActive }) => (
            <>
              <Icone size={24} strokeWidth={isActive ? 2.4 : 1.7} aria-hidden="true" />
              <span>{rotulo}</span>
            </>
          )}
        </NavLink>
      ))}
    </nav>
  )
}
