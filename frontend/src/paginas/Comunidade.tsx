import { Users } from 'lucide-react'
import { Link } from 'react-router-dom'
import { Vazio } from '../componentes/Estados'

// A aba existe no design, mas a comunidade ainda não tem backend. Em vez de
// simular publicações, a tela diz a verdade e aponta o que já funciona.
export default function Comunidade() {
  return (
    <main className="tela">
      <header className="topo"><div><h1>Comunidade</h1><p>Inspire e seja inspirado</p></div></header>
      <Vazio icone={<Users aria-hidden size={30} />} titulo="Em breve por aqui">
        <p>
          Este espaço vai reunir looks compartilhados por outras pessoas. Enquanto ele não
          chega, você pode gerar um look e enviar a imagem para quem quiser.
        </p>
        <Link className="botao" to="/gerador">Gerar um look</Link>
      </Vazio>
    </main>
  )
}
