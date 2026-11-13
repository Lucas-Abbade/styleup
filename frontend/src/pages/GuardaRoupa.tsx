import { useCallback, useEffect, useState } from 'react'

import { api, type Peca } from '../lib/api'
import { urlAssinada } from '../lib/supabase'

const PAPEIS = [
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
  const [papel, setPapel] = useState('')
  const [erro, setErro] = useState<string | null>(null)
  const [carregando, setCarregando] = useState(true)

  const carregar = useCallback(async () => {
    setCarregando(true)
    try {
      const lista = await api.listarPecas(papel ? { papel } : {})
      setPecas(lista)
      setErro(null)

      // as fotos ficam em bucket privado: cada uma precisa de URL assinada
      const pares = await Promise.all(
        lista
          .filter((p) => p.imagem_path)
          .map(async (p) => [p.id, await urlAssinada(p.imagem_path!)] as const),
      )
      setUrls(Object.fromEntries(pares.filter(([, u]) => u)) as Record<string, string>)
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Falha ao carregar o guarda-roupa.')
    } finally {
      setCarregando(false)
    }
  }, [papel])

  useEffect(() => {
    carregar()
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
    if (!confirm(`Remover ${peca.rotulo ?? peca.categoria} (${peca.codigo})?`)) return
    try {
      await api.removerPeca(peca.id)
      setPecas((atual) => atual.filter((p) => p.id !== peca.id))
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Falha ao remover a peça.')
    }
  }

  return (
    <>
      <h1>Guarda-roupa</h1>
      <p className="legenda">
        {pecas.length} {pecas.length === 1 ? 'peça cadastrada' : 'peças cadastradas'}
      </p>

      <label htmlFor="papel">Filtrar</label>
      <select id="papel" value={papel} onChange={(e) => setPapel(e.target.value)}>
        {PAPEIS.map((p) => (
          <option key={p.chave} value={p.chave}>
            {p.rotulo}
          </option>
        ))}
      </select>

      {erro && <div className="erro">{erro}</div>}
      {carregando && <p className="aviso">Carregando…</p>}

      {!carregando && pecas.length === 0 && (
        <p className="aviso" style={{ marginTop: 24 }}>
          Nenhuma peça ainda. Comece cadastrando uma parte de cima, uma de baixo e um
          calçado — é o mínimo para a primeira recomendação.
        </p>
      )}

      <div className="grade">
        {pecas.map((peca) => (
          <article
            key={peca.id}
            className={`cartao peca ${peca.disponivel ? '' : 'indisponivel'}`}
          >
            {urls[peca.id] ? (
              <img src={urls[peca.id]} alt={`${peca.rotulo ?? peca.categoria} ${peca.cor_nome}`} />
            ) : (
              <div className="sem-foto">sem foto</div>
            )}

            <div className="meta">
              <strong>{peca.rotulo ?? peca.categoria}</strong>
              <div>
                <span className="amostra" style={{ background: peca.cor_hex }} />
                {peca.cor_nome}
              </div>
              <div className="codigo">
                {peca.codigo} · formalidade {peca.formalidade}
              </div>
            </div>

            <div className="acoes" style={{ marginTop: 8 }}>
              <button onClick={() => alternarDisponibilidade(peca)}>
                {peca.disponivel ? 'Indisponível' : 'Disponível'}
              </button>
              <button onClick={() => remover(peca)} aria-label={`Remover ${peca.codigo}`}>
                Remover
              </button>
            </div>
          </article>
        ))}
      </div>
    </>
  )
}
