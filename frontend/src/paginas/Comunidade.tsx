import { Sparkles, UsersRound } from 'lucide-react'
import { Link } from 'react-router-dom'
import { Vazio } from '../componentes/Estados'

/**
 * A aba existe no protótipo, mas a comunidade ainda não tem backend. Em vez de
 * simular publicações que não existem, a tela diz o que vem e aponta para o que
 * já funciona.
 */
export function Comunidade() {
  return (
    <main className="pagina">
      <h1 className="titulo-pagina">Comunidade</h1>
      <Vazio
        icone={<UsersRound size={34} />}
        titulo="Em breve"
        acao={
          <Link to="/gerador" className="botao botao--primario">
            <Sparkles size={18} aria-hidden="true" /> Gerar um look agora
          </Link>
        }
      >
        Aqui você vai poder compartilhar seus looks e se inspirar nos de outras pessoas. Por enquanto, dá para
        exportar qualquer look como imagem pela tela do look gerado.
      </Vazio>
    </main>
  )
}
