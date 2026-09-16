import { Link } from 'react-router-dom'

/**
 * Estados de tela reunidos num lugar só.
 *
 * Carregamento, erro e ausência de dados aparecem em mais de uma página, e cada
 * cópia solta acabava com um texto e um espaçamento diferentes. Centralizar
 * também obriga a escrever a mensagem uma vez, com cuidado.
 */

/** Silhueta de um cartão de look enquanto a recomendação é montada.
 *
 * Classe própria (`esqueleto-look`), não `cartao-look`: um placeholder não pode
 * ser indistinguível de um resultado real. Leitores de tela o pulam por
 * `aria-hidden`, e testes de interface que esperam por `.cartao-look` não passam
 * a achar que a recomendação já chegou.
 */
export function EsqueletoLook() {
  return (
    <div className="esqueleto-look" aria-hidden="true">
      <div className="cartao-look-topo">
        <div className="esqueleto" style={{ height: 22, width: 84, borderRadius: 999 }} />
        <div className="esqueleto" style={{ height: 22, width: 120, borderRadius: 999 }} />
      </div>
      <div className="pecas-do-look">
        {[0, 1, 2].map((i) => (
          <div key={i} className="peca-do-look">
            <div className="esqueleto" style={{ aspectRatio: '1', width: '100%' }} />
            <div className="esqueleto" style={{ height: 12, marginTop: 8 }} />
            <div className="esqueleto" style={{ height: 12, width: '60%', marginTop: 6 }} />
          </div>
        ))}
      </div>
      <div className="esqueleto" style={{ height: 14, marginTop: 14 }} />
      <div className="esqueleto" style={{ height: 14, width: '75%', marginTop: 6 }} />
    </div>
  )
}

export function Carregando({ quantidade = 3 }: { quantidade?: number }) {
  return (
    <div aria-live="polite" aria-busy="true">
      <p className="aviso">Montando as combinações…</p>
      {Array.from({ length: quantidade }, (_, i) => (
        <EsqueletoLook key={i} />
      ))}
    </div>
  )
}

/**
 * Falha do sistema: rede, API desligada, erro inesperado. O usuário não pode
 * fazer nada além de tentar de novo, então é isso que oferecemos.
 */
export function Falha({ mensagem, onTentarDeNovo }: {
  mensagem: string
  onTentarDeNovo?: () => void
}) {
  return (
    <div className="painel erro" role="alert">
      <strong>Não deu para gerar as sugestões</strong>
      <p>{mensagem}</p>
      {onTentarDeNovo && (
        <button type="button" onClick={onTentarDeNovo}>
          Tentar de novo
        </button>
      )}
    </div>
  )
}

/**
 * Situação do guarda-roupa, não falha do sistema: falta peça, nada serve ao
 * contexto. Tem cor e tom próprios porque a ação que resolve é outra.
 */
export function Orientacao({ titulo, mensagem, acao }: {
  titulo: string
  mensagem: string
  acao?: { para: string; texto: string }
}) {
  return (
    <div className="painel atencao" role="status">
      <strong>{titulo}</strong>
      <p>{mensagem}</p>
      {acao && (
        <Link className="botao" to={acao.para}>
          {acao.texto}
        </Link>
      )}
    </div>
  )
}

/** Primeiro uso: ainda não há acervo para combinar. */
export function GuardaRoupaVazio({ faltando }: { faltando: string[] }) {
  const NOMES: Record<string, string> = {
    superior: 'uma parte de cima',
    inferior: 'uma parte de baixo',
    calcado: 'um calçado',
  }
  const lista = faltando.map((p) => NOMES[p] ?? p)
  const texto =
    lista.length === 0
      ? 'Cadastre algumas peças para começar.'
      : `Para montar um look o sistema precisa de ${lista.join(', ')}. ` +
        'Fotografe cada peça e confirme os dados sugeridos.'

  return (
    <Orientacao
      titulo="Seu guarda-roupa ainda está incompleto"
      mensagem={texto}
      acao={{ para: '/cadastrar', texto: 'Cadastrar uma peça' }}
    />
  )
}
