import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { api, foiCancelada, type Analise, type CategoriaTaxonomia } from '../lib/api'
import { enviarFoto } from '../lib/supabase'

/**
 * Funcionalidades 6.2.1 e 6.2.2: foto → análise → confirmação → registro.
 *
 * A tela de confirmação não é burocracia. O modelo é zero-shot e erra; deixar o
 * usuário corrigir em dois toques custa menos que um catálogo cheio de peça
 * errada, e é o que a operação 6.2.2.1 descreve.
 */
export default function Cadastro({ usuarioId }: { usuarioId: string }) {
  const navegar = useNavigate()
  const entradaArquivo = useRef<HTMLInputElement>(null)

  const [arquivo, setArquivo] = useState<File | null>(null)
  const [previa, setPrevia] = useState<string | null>(null)
  const [analise, setAnalise] = useState<Analise | null>(null)
  const [catalogo, setCatalogo] = useState<CategoriaTaxonomia[]>([])
  const [estado, setEstado] = useState<'ocioso' | 'analisando' | 'salvando'>('ocioso')
  const [erro, setErro] = useState<string | null>(null)
  const [duracao, setDuracao] = useState<number | null>(null)

  useEffect(() => {
    const controle = new AbortController()
    api
      .taxonomia(controle.signal)
      .then(setCatalogo)
      .catch((e) => {
        if (!foiCancelada(e)) setCatalogo([])
      })
    return () => controle.abort()
  }, [])

  useEffect(() => {
    if (!arquivo) return
    const url = URL.createObjectURL(arquivo)
    setPrevia(url)
    return () => URL.revokeObjectURL(url)
  }, [arquivo])

  async function selecionar(evento: React.ChangeEvent<HTMLInputElement>) {
    const escolhido = evento.target.files?.[0]
    if (!escolhido) return
    setArquivo(escolhido)
    setAnalise(null)
    setErro(null)
    setEstado('analisando')

    const inicio = performance.now()
    try {
      setAnalise(await api.analisarFoto(escolhido))
      setDuracao(Math.round(performance.now() - inicio))
    } catch (e) {
      if (foiCancelada(e)) return
      setErro(e instanceof Error ? e.message : 'Falha ao analisar a foto.')
    } finally {
      setEstado('ocioso')
    }
  }

  async function confirmar() {
    if (!analise || !arquivo) return
    setEstado('salvando')
    setErro(null)
    try {
      // em modo demonstração não há bucket: a peça é salva sem foto
      const caminho = await enviarFoto(arquivo, usuarioId)
      await api.registrarPeca({ ...analise, imagem_path: caminho })
      navegar('/guarda-roupa')
    } catch (e) {
      setErro(e instanceof Error ? e.message : 'Falha ao registrar a peça.')
      setEstado('ocioso')
    }
  }

  function alterarCategoria(chave: string) {
    const cat = catalogo.find((c) => c.chave === chave)
    if (!cat || !analise) return
    // trocar a categoria arrasta papel, formalidade e faixa térmica junto:
    // são propriedades da categoria, não escolhas independentes do usuário
    setAnalise({
      ...analise,
      categoria: cat.chave,
      rotulo: cat.rotulo,
      papel: cat.papel,
      formalidade: cat.formalidade,
      temp_min: cat.temp_min,
      temp_max: cat.temp_max,
      resiste_chuva: cat.resiste_chuva,
    })
  }

  return (
    <>
      <h1>Cadastrar peça</h1>
      <p className="legenda">
        Fotografe a peça sobre um fundo liso, ocupando a maior parte do quadro.
      </p>

      <input
        ref={entradaArquivo}
        type="file"
        accept="image/*"
        capture="environment"
        onChange={selecionar}
        hidden
      />
      <button className="primario" onClick={() => entradaArquivo.current?.click()}>
        {arquivo ? 'Trocar foto' : 'Tirar ou escolher foto'}
      </button>

      {previa && (
        <div className="cartao" style={{ marginTop: 12 }}>
          <img src={previa} alt="Prévia da peça fotografada" style={{ width: '100%', borderRadius: 8 }} />
        </div>
      )}

      {estado === 'analisando' && (
        <div aria-live="polite" aria-busy="true">
          <p className="aviso">Analisando a foto…</p>
          <div className="esqueleto" style={{ height: 120, marginTop: 8 }} />
        </div>
      )}
      {erro && <div className="erro">{erro}</div>}

      {analise?.aviso && (
        <div className="painel atencao" role="status">
          <strong>Confira a categoria antes de salvar</strong>
          <p>{analise.aviso}</p>
        </div>
      )}

      {analise && (
        <section className="cartao">
          <h2>Confirme os dados</h2>

          <label htmlFor="categoria">Categoria</label>
          <select
            id="categoria"
            value={analise.categoria}
            onChange={(e) => alterarCategoria(e.target.value)}
          >
            {catalogo.map((c) => (
              <option key={c.chave} value={c.chave}>
                {c.rotulo}
              </option>
            ))}
          </select>

          <label htmlFor="cor">Cor identificada</label>
          <input
            id="cor"
            value={analise.cor_nome}
            onChange={(e) => setAnalise({ ...analise, cor_nome: e.target.value })}
          />
          <p className="aviso">
            <span className="amostra" style={{ background: analise.cor_hex }} />
            {analise.cor_nome} ({analise.cor_hex})
          </p>

          <label htmlFor="formalidade">Formalidade (1 esportiva … 5 social)</label>
          <input
            id="formalidade"
            type="number"
            min={1}
            max={5}
            value={analise.formalidade}
            onChange={(e) =>
              setAnalise({ ...analise, formalidade: Number(e.target.value) })
            }
          />

          {duracao !== null && (
            <p className="aviso" style={{ marginTop: 12 }}>
              Análise concluída em {(duracao / 1000).toFixed(1)} s
              {duracao > 5000 && ' — acima da meta de 5 s do RNF01'}
            </p>
          )}

          <button
            className="primario"
            onClick={confirmar}
            disabled={estado === 'salvando'}
            style={{ marginTop: 12 }}
          >
            {estado === 'salvando' ? 'Salvando…' : 'Adicionar ao guarda-roupa'}
          </button>
        </section>
      )}
    </>
  )
}
