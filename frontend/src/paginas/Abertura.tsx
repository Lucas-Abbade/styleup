import { Link } from 'react-router-dom'
import Arara from '../componentes/Arara'
import { MODO_DEMO } from '../lib/config'

// foto opcional (public/img/LEIA-ME.txt); sem ela, a ilustração vetorial
const FOTO = (import.meta.env.VITE_FOTO_ABERTURA as string | undefined) ?? '/img/splash.jpg'

export default function Abertura() {
  return (
    <main className="abertura">
      <Arara foto={FOTO} />
      <div className="abertura__marca">
        <h1>Style Up</h1>
        <p>Seu estilo, do seu jeito</p>
      </div>
      <div className="botoes">
        <Link className="botao" to="/criar-conta">COMEÇAR</Link>
        <Link className="botao botao--claro" to="/entrar">Já tenho uma conta</Link>
      </div>
      {MODO_DEMO && (
        <p className="abertura__demo">
          Modo demonstração: os dados ficam só neste servidor de testes.
        </p>
      )}
    </main>
  )
}
