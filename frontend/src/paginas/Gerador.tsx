import { ArrowRight, Briefcase, CloudSun, Glasses, PartyPopper, Send, Shirt, Snowflake, SunMedium, Thermometer } from 'lucide-react'
import { useEffect, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { CenaArara } from '../componentes/Ilustracao'
import { api, type Inspiracao, type Pedido } from '../lib/api'
import { climaLocalLigado, ligarClimaLocal, useGerar, usePerfil } from '../lib/dados'

const ICONES: Record<string, typeof Shirt> = {
  maleta: Briefcase, festa: PartyPopper, frio: Snowflake, verao: SunMedium, cabide: Glasses, camiseta: Shirt,
}
// se o servidor não responder, a tela ainda oferece os atalhos do protótipo
const PADRAO: Inspiracao[] = [
  { chave: 'trabalho-faculdade', rotulo: 'Trabalho / Faculdade', icone: 'maleta' },
  { chave: 'role-balada', rotulo: 'Rolê / Balada', icone: 'festa' },
  { chave: 'dias-frios', rotulo: 'Dias frios', icone: 'frio' },
  { chave: 'verao', rotulo: 'Verão', icone: 'verao' },
  { chave: 'minimalista', rotulo: 'Minimalista', icone: 'cabide' },
  { chave: 'esportivo', rotulo: 'Esportivo', icone: 'camiseta' },
]

export function Gerador() {
  const { perfil } = usePerfil()
  const { gerar, gerando, erro } = useGerar()
  const [texto, setTexto] = useState('')
  const [inspiracao, setInspiracao] = useState<string | null>(null)
  const [temperatura, setTemperatura] = useState('')
  const [climaLocal, setClimaLocal] = useState(climaLocalLigado)
  const [inspiracoes, setInspiracoes] = useState<Inspiracao[]>(PADRAO)

  useEffect(() => {
    api.inspiracoes().then((lista) => lista.length && setInspiracoes(lista)).catch(() => undefined)
  }, [])

  const graus = temperatura.trim() === '' ? undefined : Number(temperatura.replace(',', '.'))
  const grausInvalidos = graus !== undefined && (Number.isNaN(graus) || graus < -30 || graus > 55)

  function pedir(evento?: FormEvent) {
    evento?.preventDefault()
    if (grausInvalidos) return
    const pedido: Pedido = {}
    if (texto.trim()) pedido.texto = texto.trim()
    if (inspiracao) pedido.inspiracao = inspiracao
    if (graus !== undefined) pedido.temperatura = graus
    void gerar(pedido)
  }

  return (
    <main className="pagina">
      <h1 className="titulo-pagina">Gerador de Looks</h1>

      <form onSubmit={pedir}>
        <label htmlFor="pedido" className="rotulo-suave">Qual look você quer criar hoje?</label>
        <div className="caixa-pedido">
          <textarea id="pedido" value={texto} onChange={(e) => setTexto(e.target.value)} maxLength={300} rows={3}
                    placeholder="Ex: Look para a faculdade, casual, all black, praia…"
                    onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); pedir() } }} />
          <button className="caixa-pedido__enviar" disabled={gerando} aria-label="Gerar look">
            {gerando ? <span className="rodinha rodinha--clara" aria-hidden="true" /> : <Send size={20} aria-hidden="true" />}
          </button>
        </div>

        <h2 className="titulo-secao">Inspirações</h2>
        <div className="inspiracoes" role="group" aria-label="Inspirações">
          {inspiracoes.map((i) => {
            const Icone = ICONES[i.icone] ?? Shirt
            const ativa = inspiracao === i.chave
            return (
              <button key={i.chave} type="button" aria-pressed={ativa} className={`inspiracao ${ativa ? 'inspiracao--ativa' : ''}`}
                      onClick={() => setInspiracao(ativa ? null : i.chave)}>
                <Icone size={18} strokeWidth={1.8} aria-hidden="true" />
                {i.rotulo}
              </button>
            )
          })}
        </div>

        <label className="campo-linha">
          <Thermometer size={20} aria-hidden="true" />
          <span className="so-leitor">Temperatura em graus Celsius</span>
          <input inputMode="decimal" value={temperatura} onChange={(e) => setTemperatura(e.target.value)}
                 placeholder="Inserir temperatura" aria-invalid={grausInvalidos} />
          <span aria-hidden="true">°C</span>
        </label>
        {grausInvalidos && <p className="aviso aviso--erro" role="alert">Informe uma temperatura entre −30 e 55 °C.</p>}

        {perfil.consentimento.localizacao ? (
          <label className="alternar alternar--leve">
            <span><CloudSun size={18} aria-hidden="true" /> Usar o clima de onde estou</span>
            <input type="checkbox" role="switch" checked={climaLocal}
                   onChange={(e) => { setClimaLocal(e.target.checked); ligarClimaLocal(e.target.checked) }} />
          </label>
        ) : (
          <p className="nota">
            <CloudSun size={16} aria-hidden="true" />
            <span>Para usar o clima automático, permita a localização em <Link to="/perfil">Perfil › Privacidade</Link>.</span>
          </p>
        )}

        {erro && <p className="aviso aviso--erro" role="alert">{erro} {erro.includes('adastr') && <Link to="/guarda-roupa/nova">Cadastrar peça</Link>}</p>}
      </form>

      <button type="button" className="destaque destaque--baixo" disabled={gerando} onClick={() => pedir()}>
        <CenaArara foto="/img/hero.jpg" />
        <div className="destaque__texto">
          <h2>{gerando ? 'Montando seus looks…' : 'Looks que combinam com você'}</h2>
        </div>
        <span className="destaque__seta" aria-hidden="true"><ArrowRight size={22} /></span>
      </button>
    </main>
  )
}
