import { useEffect, useState } from 'react'

import { api, posicaoAtual, type Evento, type Look, type Recomendacao } from '../lib/api'
import { urlAssinada } from '../lib/supabase'

/**
 * Funcionalidades 6.4.1, 6.5.1 e 6.6.2 numa tela só: escolher o contexto, ver os
 * três looks e dizer se gostou.
 *
 * O feedback fica junto da recomendação de propósito. Numa tela separada quase
 * ninguém responde, e sem resposta o RNF04 não tem como ser medido.
 */
export default function Recomendar() {
  const [eventos, setEventos] = useState<Evento[]>([])
  const [evento, setEvento] = useState('trabalho')
  const [resultado, setResultado] = useState<Recomendacao | null>(null)
  const [urls, setUrls] = useState<Record<string, string>>({})
  const [votos, setVotos] = useState<Record<string, boolean>>({})
  const [erro, setErro] = useState<string | null>(null)
  const [carregando, setCarregando] = useState(false)
  const [duracao, setDuracao] = useState<number | null>(null)

  useEffect(() => {
    api.eventos().then(setEventos).catch(() => setEventos([]))
  }, [])

  async function pedir() {
    setCarregando(true)
    setErro(null)
    setResultado(null)
    setVotos({})

    const inicio = performance.now()
    try {
      const coords = await posicaoAtual()
      const recomendacao = await api.recomendar({
        evento,
        latitude: coords?.latitude,
        longitude: coords?.longitude,
      })
      setResultado(recomendacao)
      setDuracao(Math.round(performance.now() - inicio))

      const caminhos = recomendacao.looks.flatMap((l) =>
        l.pecas.filter((p) => p.imagem_path).map((p) => [p.id, p.imagem_path!] as const),
      )
      const pares = await Promise.all(
        caminhos.map(async ([id, caminho]) => [id, await urlAssinada(caminho)] as const),
      )
      setUrls(Object.fromEntries(pares.filter(([, u]) => u)) as Record<string, string>)
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Falha ao gerar a recomendação.')
    } finally {
      setCarregando(false)
    }
  }

  async function votar(look: Look, aprovado: boolean) {
    setVotos((atual) => ({ ...atual, [look.id]: aprovado }))
    try {
      await api.enviarFeedback(look.id, aprovado)
    } catch {
      setVotos((atual) => {
        const copia = { ...atual }
        delete copia[look.id]
        return copia
      })
      setErro('Não foi possível registrar o feedback.')
    }
  }

  const clima = resultado?.contexto

  return (
    <>
      <h1>O que vestir hoje</h1>
      <p className="legenda">Escolha para onde você vai e receba três combinações.</p>

      <label htmlFor="evento">Compromisso</label>
      <select id="evento" value={evento} onChange={(e) => setEvento(e.target.value)}>
        {eventos.map((ev) => (
          <option key={ev.chave} value={ev.chave}>
            {ev.rotulo}
          </option>
        ))}
      </select>

      <button className="primario" onClick={pedir} disabled={carregando} style={{ marginTop: 16 }}>
        {carregando ? 'Montando os looks…' : 'Recomendar'}
      </button>

      {erro && <div className="erro">{erro}</div>}

      {clima && (
        <p className="aviso" style={{ marginTop: 16 }}>
          {clima.clima_automatico
            ? `Clima obtido pela sua localização: ${clima.temperatura?.toFixed(0)} °C` +
              (clima.sensacao != null ? `, sensação ${clima.sensacao.toFixed(0)} °C` : '') +
              (clima.chuva_prob != null
                ? `, ${Math.round(clima.chuva_prob * 100)}% de chance de chuva`
                : '')
            : 'Sem dados de clima: as sugestões consideram apenas o tipo de compromisso.'}
          {duracao !== null && ` · ${(duracao / 1000).toFixed(1)} s`}
        </p>
      )}

      {resultado?.looks.map((look) => (
        <article key={look.id} className="cartao">
          <h2 style={{ marginTop: 0 }}>Opção {look.posicao}</h2>

          <div className="linha-look">
            {look.pecas.map((peca) => (
              <div key={peca.id} className="item">
                {urls[peca.id] ? (
                  <img src={urls[peca.id]} alt={`${peca.rotulo} ${peca.cor_nome}`} />
                ) : (
                  <div className="sem-foto">sem foto</div>
                )}
                <div>{peca.rotulo}</div>
                <div className="codigo">
                  <span className="amostra" style={{ background: peca.cor_hex }} />
                  {peca.cor_nome}
                </div>
              </div>
            ))}
          </div>

          <p className="explicacao">{look.explicacao}</p>

          <div className="acoes">
            <button
              className={votos[look.id] === true ? 'escolhido' : ''}
              onClick={() => votar(look, true)}
            >
              Gostei
            </button>
            <button
              className={votos[look.id] === false ? 'escolhido' : ''}
              onClick={() => votar(look, false)}
            >
              Não gostei
            </button>
          </div>
        </article>
      ))}
    </>
  )
}
