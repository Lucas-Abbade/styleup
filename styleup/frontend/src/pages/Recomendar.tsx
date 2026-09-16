import { useCallback, useEffect, useState } from 'react'

import CartaoLook, { type Voto } from '../components/CartaoLook'
import { Carregando, Falha, GuardaRoupaVazio, Orientacao } from '../components/Estados'
import {
  ErroApi,
  api,
  foiCancelada,
  posicaoAtual,
  type Evento,
  type PedidoRecomendacao,
  type Recomendacao,
  type ResumoGuardaRoupa,
} from '../lib/api'

/**
 * Funcionalidade principal do StyleUp (seções 6.4, 6.5 e 6.6 do Documento de
 * Visão): escolher o contexto, ver os três looks e dizer se gostou.
 *
 * O feedback fica junto da recomendação de propósito. Numa tela separada quase
 * ninguém responde, e sem resposta o Hit Rate@3 do RNF04 não tem como ser medido.
 */

type Fase =
  | { tipo: 'inicial' }
  | { tipo: 'carregando' }
  | { tipo: 'pronto'; dados: Recomendacao }
  | { tipo: 'conflito'; mensagem: string }
  | { tipo: 'falha'; mensagem: string }

export default function Recomendar() {
  const [eventos, setEventos] = useState<Evento[]>([])
  const [evento, setEvento] = useState('trabalho')
  const [resumo, setResumo] = useState<ResumoGuardaRoupa | null>(null)
  const [fase, setFase] = useState<Fase>({ tipo: 'inicial' })
  const [votos, setVotos] = useState<Record<string, Voto>>({})
  const [duracao, setDuracao] = useState<number | null>(null)

  // Clima manual: só aparece depois de a geolocalização falhar ou ser negada.
  const [pedirTemperatura, setPedirTemperatura] = useState(false)
  const [temperatura, setTemperatura] = useState('')
  const [chuva, setChuva] = useState(false)

  // Cada efeito aborta a própria requisição ao desmontar. Sem isto, sair da tela
  // durante o carregamento deixava um `setState` pendente sobre um componente
  // que já não existe — e, no caso do resumo, pintava a orientação de
  // guarda-roupa incompleto por um instante na tela seguinte.
  useEffect(() => {
    const controle = new AbortController()
    api
      .eventos(controle.signal)
      .then(setEventos)
      .catch((e) => {
        if (!foiCancelada(e)) setEventos([])
      })
    return () => controle.abort()
  }, [])

  const [recarregarResumo, setRecarregarResumo] = useState(0)

  const carregarResumo = useCallback(() => setRecarregarResumo((n) => n + 1), [])

  useEffect(() => {
    const controle = new AbortController()
    api
      .resumo(controle.signal)
      .then(setResumo)
      .catch((e) => {
        if (!foiCancelada(e)) setResumo(null)
      })
    return () => controle.abort()
  }, [recarregarResumo])

  const pedir = useCallback(async () => {
    setFase({ tipo: 'carregando' })
    setVotos({})
    setDuracao(null)

    const inicio = performance.now()
    try {
      const pedido: PedidoRecomendacao = { evento }

      if (pedirTemperatura) {
        // o usuário já informou o clima à mão; não insistimos na localização
        const valor = Number(temperatura)
        if (temperatura.trim() !== '' && Number.isFinite(valor)) {
          pedido.temperatura = valor
          pedido.chuva_prob = chuva ? 0.9 : 0
        }
        // campo em branco: segue sem clima, como manda o RNF07
      } else {
        const coords = await posicaoAtual()
        if (coords) {
          pedido.latitude = coords.latitude
          pedido.longitude = coords.longitude
        } else {
          // negou ou não respondeu: passa a pedir a temperatura na próxima vez
          setPedirTemperatura(true)
        }
      }

      const dados = await api.recomendar(pedido)
      setDuracao(Math.round(performance.now() - inicio))

      // clima pedido mas não obtido: o backend avisa e a tela passa ao manual
      if (!dados.contexto.clima_automatico && dados.contexto.temperatura === null) {
        setPedirTemperatura(true)
      }
      setFase({ tipo: 'pronto', dados })
    } catch (e) {
      if (foiCancelada(e)) return
      if (e instanceof ErroApi && e.ehConflito) {
        setFase({ tipo: 'conflito', mensagem: e.message })
        carregarResumo() // o acervo mudou desde a última checagem
      } else {
        setFase({
          tipo: 'falha',
          mensagem: e instanceof Error ? e.message : 'Erro inesperado.',
        })
      }
    }
  }, [evento, pedirTemperatura, temperatura, chuva, carregarResumo])

  // useCallback com dependência vazia: a identidade não muda entre renderizações,
  // o que é o que faz o React.memo do cartão realmente evitar re-renderização.
  const votar = useCallback(async (lookId: string, aprovado: boolean) => {
    setVotos((atual) => ({ ...atual, [lookId]: 'enviando' }))
    try {
      await api.enviarFeedback(lookId, aprovado)
      setVotos((atual) => ({ ...atual, [lookId]: aprovado ? 'aprovado' : 'rejeitado' }))
    } catch (e) {
      if (foiCancelada(e)) return
      setVotos((atual) => ({ ...atual, [lookId]: undefined }))
    }
  }, [])

  const acervoIncompleto = resumo !== null && !resumo.pode_recomendar
  const contexto = fase.tipo === 'pronto' ? fase.dados.contexto : null

  return (
    <>
      <header className="cabecalho">
        <h1>O que vestir hoje</h1>
        <p className="legenda">
          Escolha o compromisso e receba três combinações do seu guarda-roupa.
        </p>
      </header>

      {acervoIncompleto ? (
        <GuardaRoupaVazio faltando={resumo.faltando} />
      ) : (
        <section className="cartao painel-contexto">
          <div className="campo">
            <label htmlFor="evento">Compromisso</label>
            <select
              id="evento"
              value={evento}
              onChange={(e) => setEvento(e.target.value)}
              disabled={fase.tipo === 'carregando'}
            >
              {eventos.length === 0 && <option value="trabalho">Trabalho</option>}
              {eventos.map((ev) => (
                <option key={ev.chave} value={ev.chave}>
                  {ev.rotulo}
                </option>
              ))}
            </select>
          </div>

          {pedirTemperatura && (
            <>
              <div className="campo">
                <label htmlFor="temperatura">Temperatura agora (°C)</label>
                <input
                  id="temperatura"
                  type="number"
                  inputMode="numeric"
                  min={-10}
                  max={50}
                  placeholder="ex.: 24"
                  value={temperatura}
                  onChange={(e) => setTemperatura(e.target.value)}
                />
                <p className="dica">
                  {temperatura.trim() === ''
                    ? 'Sem acesso à sua localização. Informe a temperatura para que o clima entre na conta, ou deixe em branco para considerar só o compromisso.'
                    : 'A próxima recomendação vai usar esta temperatura.'}
                </p>
              </div>

              <label className="caixa">
                <input
                  type="checkbox"
                  checked={chuva}
                  onChange={(e) => setChuva(e.target.checked)}
                />
                Previsão de chuva
              </label>
            </>
          )}

          <button
            className="primario"
            type="button"
            onClick={pedir}
            disabled={fase.tipo === 'carregando'}
          >
            {fase.tipo === 'carregando' ? 'Montando os looks…' : 'Recomendar'}
          </button>
        </section>
      )}

      {contexto && (
        <p className="tira-contexto">
          <span className="etiqueta">{contexto.rotulo_evento}</span>
          {contexto.temperatura !== null ? (
            <>
              <span className="etiqueta">{contexto.temperatura.toFixed(0)} °C</span>
              {contexto.sensacao !== null &&
                Math.abs(contexto.sensacao - contexto.temperatura) >= 2 && (
                  <span className="etiqueta">
                    sensação {contexto.sensacao.toFixed(0)} °C
                  </span>
                )}
              {contexto.chuva_prob !== null && contexto.chuva_prob > 0.3 && (
                <span className="etiqueta">
                  {Math.round(contexto.chuva_prob * 100)}% de chuva
                </span>
              )}
            </>
          ) : (
            <span className="etiqueta neutra">clima não considerado</span>
          )}
          {contexto.clima_automatico && (
            <span className="etiqueta neutra">clima automático</span>
          )}
          {duracao !== null && (
            <span className="etiqueta neutra">{(duracao / 1000).toFixed(1)} s</span>
          )}
        </p>
      )}

      {fase.tipo === 'carregando' && <Carregando />}

      {fase.tipo === 'conflito' && (
        <Orientacao
          titulo="Nenhuma combinação possível para este contexto"
          mensagem={fase.mensagem}
          acao={{ para: '/guarda-roupa', texto: 'Revisar o guarda-roupa' }}
        />
      )}

      {fase.tipo === 'falha' && <Falha mensagem={fase.mensagem} onTentarDeNovo={pedir} />}

      {fase.tipo === 'pronto' &&
        fase.dados.looks.map((look) => (
          <CartaoLook
            key={look.id}
            look={look}
            voto={votos[look.id]}
            onVotar={votar}
          />
        ))}
    </>
  )
}
