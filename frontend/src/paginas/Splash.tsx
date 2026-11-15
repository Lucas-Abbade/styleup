import { Link } from 'react-router-dom'
import { CenaArara } from '../componentes/Ilustracao'

/** Primeira tela para quem ainda não entrou. */
export function Splash() {
  return (
    <main className="splash">
      <CenaArara foto="/img/splash.jpg" className="splash__fundo" />
      <div className="splash__marca">
        <h1>Style Up</h1>
        <p>Seu estilo, do seu jeito</p>
      </div>
      <div className="splash__acoes">
        <Link to="/criar-conta" className="botao botao--vidro">Começar</Link>
        <Link to="/entrar" className="splash__link">Já tenho uma conta</Link>
      </div>
    </main>
  )
}
