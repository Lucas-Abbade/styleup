import { memo, useEffect, useMemo, useState } from 'react'

import type { Look, PecaDoLook } from '../lib/api'
import { urlAssinada } from '../lib/supabase'

const NOME_DO_PAPEL: Record<string, string> = {
  superior: 'Parte de cima',
  inferior: 'Parte de baixo',
  calcado: 'Calçado',
  sobreposicao: 'Sobreposição',
}

const NOME_DO_CRITERIO: Record<string, string> = {
  ocasiao: 'Ocasião',
  clima: 'Clima',
  cor: 'Harmonia de cor',
  estilo: 'Seu estilo',
  variedade: 'Variedade',
}

/** Ordem de exibição: de cima para baixo, como a pessoa se veste. */
const ORDEM_DOS_PAPEIS = ['sobreposicao', 'superior', 'inferior', 'calcado']

function ordenar(pecas: PecaDoLook[]): PecaDoLook[] {
  return [...pecas].sort(
    (a, b) => ORDEM_DOS_PAPEIS.indexOf(a.papel) - ORDEM_DOS_PAPEIS.indexOf(b.papel),
  )
}

export type Voto = 'aprovado' | 'rejeitado' | 'enviando' | undefined

interface Props {
  look: Look
  voto: Voto
  /** Recebe o id do look para que a identidade da função seja estável no pai. */
  onVotar: (lookId: string, aprovado: boolean) => void
}

function CartaoLookBase({ look, voto, onVotar }: Props) {
  const [urls, setUrls] = useState<Record<string, string>>({})
  const [detalhes, setDetalhes] = useState(false)

  useEffect(() => {
    // As fotos ficam em bucket privado; cada uma precisa de URL assinada. Em modo
    // demonstração não há foto e `urlAssinada` devolve null sem chamar a rede.
    let ativo = true
    const comFoto = look.pecas.filter((p) => p.imagem_path)
    if (comFoto.length === 0) return

    Promise.all(
      comFoto.map(async (p) => [p.id, await urlAssinada(p.imagem_path!)] as const),
    )
      .then((pares) => {
        if (!ativo) return
        setUrls(Object.fromEntries(pares.filter(([, u]) => u)) as Record<string, string>)
      })
      .catch(() => {
        /* sem URL assinada o cartão cai na amostra de cor; não é erro de tela */
      })
    return () => {
      ativo = false
    }
  }, [look])

  const votado = voto === 'aprovado' || voto === 'rejeitado'

  // Reordenar as peças e os critérios a cada renderização era trabalho jogado
  // fora: o cartão re-renderiza ao abrir os detalhes e a cada voto.
  const pecasOrdenadas = useMemo(() => ordenar(look.pecas), [look.pecas])
  const criterios = useMemo(
    () => Object.entries(look.parcelas).sort(([, a], [, b]) => b - a),
    [look.parcelas],
  )

  return (
    <article className={`cartao-look ${votado ? 'votado' : ''}`}>
      <header className="cartao-look-topo">
        <span className="selo-posicao">Opção {look.posicao}</span>
        <div
          className="medidor"
          role="img"
          aria-label={`Compatibilidade de ${Math.round(look.score * 100)} por cento`}
          title="Quanto este look atende ao contexto informado"
        >
          <div className="medidor-trilha">
            <div className="medidor-nivel" style={{ width: `${look.score * 100}%` }} />
          </div>
          <span className="medidor-valor">{Math.round(look.score * 100)}%</span>
        </div>
      </header>

      <ul className="pecas-do-look">
        {pecasOrdenadas.map((peca) => (
          <li key={peca.id} className="peca-do-look">
            {urls[peca.id] ? (
              <img
                src={urls[peca.id]}
                alt={`${peca.rotulo} ${peca.cor_nome}`}
                loading="lazy"
                decoding="async"
                width={104}
                height={104}
              />
            ) : (
              <div className="sem-foto" aria-hidden="true">
                <span className="amostra-grande" style={{ background: peca.cor_hex }} />
              </div>
            )}
            <div className="peca-do-look-texto">
              <span className="papel">{NOME_DO_PAPEL[peca.papel] ?? peca.papel}</span>
              <strong>{peca.rotulo}</strong>
              {/* RNF05: o nome da cor sempre em texto, nunca só a amostra */}
              <span className="cor">
                <span className="amostra" style={{ background: peca.cor_hex }} />
                {peca.cor_nome}
              </span>
            </div>
          </li>
        ))}
      </ul>

      <p className="explicacao">{look.explicacao}</p>

      <button
        type="button"
        className="link-discreto"
        aria-expanded={detalhes}
        onClick={() => setDetalhes(!detalhes)}
      >
        {detalhes ? 'Ocultar como o score foi calculado' : 'Como o score foi calculado'}
      </button>

      {detalhes && (
        <dl className="parcelas">
          {criterios.map(([chave, valor]) => (
            <div key={chave} className="parcela">
              <dt>{NOME_DO_CRITERIO[chave] ?? chave}</dt>
              <dd>
                <div className="medidor-trilha fina">
                  <div className="medidor-nivel" style={{ width: `${valor * 100}%` }} />
                </div>
                <span>{Math.round(valor * 100)}%</span>
              </dd>
            </div>
          ))}
        </dl>
      )}

      {votado ? (
        <p className="confirmacao" role="status">
          {voto === 'aprovado'
            ? 'Anotado. Vamos priorizar combinações parecidas.'
            : 'Anotado. Vamos evitar combinações parecidas.'}
        </p>
      ) : (
        <div className="acoes">
          <button
            type="button"
            onClick={() => onVotar(look.id, true)}
            disabled={voto === 'enviando'}
          >
            Gostei
          </button>
          <button
            type="button"
            onClick={() => onVotar(look.id, false)}
            disabled={voto === 'enviando'}
          >
            Não gostei
          </button>
        </div>
      )}
    </article>
  )
}

/**
 * Memoizado porque um voto em qualquer cartão atualiza o mapa `votos` no pai e
 * re-renderizaria os três. Com `onVotar` estável (useCallback no pai) e o `look`
 * imutável, só o cartão votado refaz o trabalho.
 */
const CartaoLook = memo(CartaoLookBase)
export default CartaoLook
