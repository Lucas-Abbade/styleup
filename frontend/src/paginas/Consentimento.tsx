import { useState } from 'react'
import { Carregando, Falha } from '../componentes/Estados'
import { api, mensagemDe, type Termo } from '../lib/api'
import { sair } from '../lib/sessao'
import { useCarga } from '../lib/util'

/** Tela do termo: aparece antes do primeiro uso e sempre que a versão mudar. */
export default function Consentimento({ aoAceitar }: { aoAceitar: () => void }) {
  const termo = useCarga<Termo>(() => api.termo())
  const [essencial, setEssencial] = useState(false)
  const [localizacao, setLocalizacao] = useState(false)
  const [erro, setErro] = useState('')
  const [enviando, setEnviando] = useState(false)

  async function aceitar() {
    if (!termo.dados) return
    setErro('')
    setEnviando(true)
    try {
      await api.aceitarTermo(termo.dados.versao, localizacao)
      aoAceitar()
    } catch (e) {
      setErro(mensagemDe(e))
      termo.recarregar() // o termo pode ter mudado enquanto a tela estava aberta
    } finally {
      setEnviando(false)
    }
  }

  if (termo.carregando && !termo.dados) return <main className="tela tela--sem-barra"><Carregando /></main>
  if (!termo.dados) {
    return <main className="tela tela--sem-barra">
      <Falha mensagem={termo.erro ?? 'Não foi possível carregar o termo.'} aoTentar={termo.recarregar} />
    </main>
  }
  const t = termo.dados

  return (
    <main className="tela tela--sem-barra termo">
      <header className="topo">
        <div>
          <h1>{t.titulo}</h1>
          <p>Versão {t.versao}</p>
        </div>
      </header>

      <p className="termo__resumo">{t.resumo}</p>

      {t.secoes.map((secao) => (
        <section key={secao.titulo}>
          <h3>{secao.titulo}</h3>
          <ul>{secao.itens.map((item) => <li key={item}>{item}</li>)}</ul>
        </section>
      ))}
      <p className="dica" style={{ marginTop: 16 }}>Responsável: {t.controlador}.</p>

      <section className="secao">
        <label className="marcador">
          <input type="checkbox" checked={essencial} onChange={(e) => setEssencial(e.target.checked)} />
          <span>
            <strong>Li e concordo.</strong> {t.finalidades.find((f) => f.chave === 'essencial')?.rotulo}
          </span>
        </label>
        <label className="marcador">
          <input type="checkbox" checked={localizacao} onChange={(e) => setLocalizacao(e.target.checked)} />
          <span>
            <strong>Opcional.</strong> {t.finalidades.find((f) => f.chave === 'localizacao')?.rotulo}
          </span>
        </label>
      </section>

      {erro && <p className="mensagem mensagem--erro" role="alert">{erro}</p>}

      <div className="botoes">
        <button type="button" className="botao" disabled={!essencial || enviando} onClick={aceitar}>
          {enviando ? 'Registrando…' : 'Aceitar e continuar'}
        </button>
        <button type="button" className="botao botao--contorno" onClick={() => void sair()}>
          Não aceito — sair
        </button>
      </div>
    </main>
  )
}
