import { useCallback, useEffect, useMemo, useState } from 'react'

import { Falha, GuardaRoupaVazio } from '../components/Estados'
import { ErroApi, api, foiCancelada, type Papel, type Peca } from '../lib/api'
import { urlAssinada } from '../lib/supabase'

const FILTROS: { chave: '' | Papel; rotulo: string }[] = [
  { chave: '', rotulo: 'Todas' },
  { chave: 'superior', rotulo: 'Parte de cima' },
  { chave: 'inferior', rotulo: 'Parte de baixo' },
  { chave: 'calcado', rotulo: 'Calçados' },
  { chave: 'sobreposicao', rotulo: 'Sobreposição' },
]

/** Funcionalidade 6.3.1: consulta, filtro, disponibilidade e remoção. */
export default function GuardaRoupa() {
  const [pecas, setPecas] = useState<Peca[]>([])
  const [urls, setUrls] = useState<Record<string, string>>({})
  const [papel, setPapel] = useState<'' | Papel>('')
  const [erro, setErro] = useState<string | null>(null)
  const [carregando, setCarregando] = useState(true)

  const carregar = useCallback(
    async (signal?: AbortSignal) => {
      setCarregando(true)
      try {
        const lista = await api.listarPecas(papel ? { papel } : {}, signal)
        if (signal?.aborted) return
        setPecas(lista)
        setErro(null)

        // as fotos ficam em bucket privado: cada uma precisa de URL assinada
        const comFoto = lista.filter((p) => p.imagem_path)
        if (comFoto.length) {
          const pares = await Promise.all(
            comFoto.map(async (p) => [p.id, await urlAssinada(p.imagem_path!)] as const),
          )
          if (signal?.aborted) return
          setUrls(Object.fromEntries(pares.filter(([, u]) => u)) as Record<string, string>)
        }
      } catch (e) {
        if (foiCancelada(e)) return
        setErro(e instanceof ErroApi ? e.message : 'Falha ao carregar o guarda-roupa.')
      } finally {
        if (!signal?.aborted) setCarregando(false)
      }
    },
    [papel],
  )

  // Trocar o filtro dispara nova busca e cancela a anterior: sem isto, uma
  // resposta lenta do filtro antigo podia chegar depois e sobrescrever a lista
  // do filtro novo.
  useEffect(() => {
    const controle = new AbortController()
    carregar(controle.signal)
    return () => controle.abort()
  }, [carregar])

  async function alternarDisponibilidade(peca: Peca) {
    // atualização otimista: a lista responde na hora e reverte se der erro
    setPecas((atual) =>
      atual.map((p) => (p.id === peca.id ? { ...p, disponivel: !p.disponivel } : p)),
    )
    try {
      await api.atualizarPeca(peca.id, { disponivel: !peca.disponivel })
    } catch {
      setPecas((atual) =>
        atual.map((p) => (p.id === peca.id ? { ...p, disponivel: peca.disponivel } : p)),
      )
      setErro('Não foi possível alterar a disponibilidade.')
    }
  }

  async function remover(peca: Peca) {
    if (!confirm(`Remover ${peca.rotulo} ${peca.cor_nome} (${peca.codigo})?`)) return
    try {
      await api.removerPeca(peca.id)
      setPecas((atual) => atual.filter((p) => p.id !== peca.id))
    } catch (e) {
      setErro(e instanceof ErroApi ? e.message : 'Falha ao remover a peça.')
    }
  }

  const disponiveis = useMemo(
    () => pecas.filter((p) => p.disponivel).length,
    [pecas],
  )

  return (
    <>
      <header className="cabecalho">
        <h1>Guarda-roupa</h1>
        <p className="legenda">
          {carregando
            ? 'Carregando…'
            : `${pecas.length} ${pecas.length === 1 ? 'peça' : 'peças'}` +
              (disponiveis !== pecas.length ? ` · ${disponiveis} disponíveis` : '')}
        </p>
      </header>

      <div className="campo">
        <label htmlFor="papel">Filtrar</label>
        <select
          id="papel"
          value={papel}
          onChange={(e) => setPapel(e.target.value as '' | Papel)}
        >
          {FILTROS.map((f) => (
            <option key={f.chave} value={f.chave}>
              {f.rotulo}
            </option>
          ))}
        </select>
      </div>

      {erro && <Falha mensagem={erro} onTentarDeNovo={() => carregar()} />}

      {carregando && (
        // Classe própria e aria-hidden: o esqueleto não pode se passar por peça
        // real nem para o leitor de tela nem para os testes de interface.
        <div className="grade" aria-busy="true" aria-hidden="true">
          {[0, 1, 2, 3].map((i) => (
            <div key={i} className="cartao esqueleto-peca">
              <div className="esqueleto" style={{ aspectRatio: '1', width: '100%' }} />
              <div className="esqueleto" style={{ height: 12, marginTop: 10 }} />
              <div className="esqueleto" style={{ height: 12, width: '55%', marginTop: 6 }} />
            </div>
          ))}
        </div>
      )}

      {!carregando && pecas.length === 0 && papel === '' && (
        <GuardaRoupaVazio faltando={['superior', 'inferior', 'calcado']} />
      )}

      {!carregando && pecas.length === 0 && papel !== '' && (
        <p className="aviso">Nenhuma peça neste filtro.</p>
      )}

      <div className="grade">
        {pecas.map((peca) => (
          <article
            key={peca.id}
            className={`cartao peca ${peca.disponivel ? '' : 'indisponivel'}`}
          >
            {urls[peca.id] ? (
              <img
                src={urls[peca.id]}
                alt={`${peca.rotulo} ${peca.cor_nome}`}
                loading="lazy"
                decoding="async"
              />
            ) : (
              <div className="sem-foto">
                <span className="amostra-grande" style={{ background: peca.cor_hex }} />
              </div>
            )}

            <div className="meta">
              <strong>{peca.rotulo}</strong>
              <div>
                {/* RNF05: nome da cor em texto, ao lado da amostra */}
                <span className="amostra" style={{ background: peca.cor_hex }} />
                {peca.cor_nome}
              </div>
              <div className="codigo">
                {peca.codigo} · formalidade {peca.formalidade}
                {!peca.disponivel && ' · indisponível'}
              </div>
            </div>

            <div className="acoes compactas">
              <button type="button" onClick={() => alternarDisponibilidade(peca)}>
                {peca.disponivel ? 'Marcar indisponível' : 'Marcar disponível'}
              </button>
              <button
                type="button"
                onClick={() => remover(peca)}
                aria-label={`Remover ${peca.rotulo} ${peca.codigo}`}
              >
                Remover
              </button>
            </div>
          </article>
        ))}
      </div>
    </>
  )
}
