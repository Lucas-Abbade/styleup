import { Component, type ErrorInfo, type ReactNode } from 'react'

interface Props {
  children: ReactNode
  /** Identifica a área na mensagem e no log. */
  area?: string
}

interface Estado {
  erro: Error | null
}

/**
 * Error Boundary da aplicação.
 *
 * O que resolve: uma exceção durante a renderização derruba a árvore inteira do
 * React e o usuário fica com a tela branca, sem nenhuma pista. Com o limite, a
 * falha é contida, registrada no console com o componente que quebrou, e a
 * pessoa recebe um caminho de volta.
 *
 * Precisa ser classe: `componentDidCatch` e `getDerivedStateFromError` não têm
 * equivalente em hooks. É o único componente de classe do projeto.
 */
export default class LimiteDeErro extends Component<Props, Estado> {
  state: Estado = { erro: null }

  static getDerivedStateFromError(erro: Error): Estado {
    return { erro }
  }

  componentDidCatch(erro: Error, info: ErrorInfo) {
    // Em produção, é aqui que entraria o envio para um serviço de rastreamento.
    console.error(
      `[StyleUp] falha de renderização em ${this.props.area ?? 'componente'}:`,
      erro,
      info.componentStack,
    )
  }

  private recarregar = () => {
    this.setState({ erro: null })
  }

  render() {
    const { erro } = this.state
    if (!erro) return this.props.children

    return (
      <div className="app">
        <div className="painel erro" role="alert">
          <strong>Algo quebrou nesta tela</strong>
          <p>
            A falha foi contida aqui, então o resto do aplicativo continua
            funcionando. Se persistir, recarregue a página.
          </p>
          <p className="detalhe-tecnico">{erro.message}</p>
          <div className="acoes">
            <button type="button" onClick={this.recarregar}>
              Tentar renderizar de novo
            </button>
            <button type="button" onClick={() => window.location.reload()}>
              Recarregar a página
            </button>
          </div>
        </div>
      </div>
    )
  }
}
