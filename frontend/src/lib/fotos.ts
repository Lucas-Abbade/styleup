// Fotos das peças: envio e endereços de exibição.
//
// No modo real, o navegador fala direto com o Storage do Supabase (bucket
// privado; a política do bucket só deixa o usuário mexer na própria pasta). No
// modo demonstração, o backend guarda as fotos em memória.
import { useEffect, useState } from 'react'
import { api } from './api'
import { API_URL, MODO_DEMO } from './config'
import { BUCKET, supabase } from './supabase'

const VALIDADE_S = 60 * 60
const assinadas = new Map<string, { url: string; expira: number }>()

/** Envia o recorte da peça e devolve o caminho a gravar em `imagem_path`. */
export async function enviarFoto(arquivo: Blob): Promise<string> {
  if (MODO_DEMO || !supabase) return (await api.enviarFotoDemo(arquivo)).caminho
  const { data } = await supabase.auth.getUser()
  if (!data.user) throw new Error('Sessão expirada. Entre novamente.')
  const extensao = arquivo.type === 'image/webp' ? 'webp' : 'jpg'
  const caminho = `${data.user.id}/${crypto.randomUUID()}.${extensao}`
  const { error } = await supabase.storage
    .from(BUCKET)
    .upload(caminho, arquivo, { contentType: arquivo.type, upsert: false })
  if (error) throw new Error('Não foi possível enviar a foto. Tente de novo.')
  return caminho
}

/** Apaga uma foto enviada cuja peça acabou não sendo registrada. */
export async function descartarFoto(caminho: string): Promise<void> {
  if (MODO_DEMO || !supabase) return
  await supabase.storage.from(BUCKET).remove([caminho])
}

/**
 * Endereços de exibição para vários caminhos de uma vez.
 * Uma chamada só (`createSignedUrls`) em vez de uma por peça — com 40 peças no
 * guarda-roupa, eram 40 idas ao Supabase para abrir a tela.
 */
export async function urlsDasFotos(caminhos: string[]): Promise<Record<string, string>> {
  const saida: Record<string, string> = {}
  const unicos = [...new Set(caminhos.filter(Boolean))]
  if (MODO_DEMO || !supabase) {
    unicos.forEach((c) => (saida[c] = `${API_URL}/demo/fotos/${c}`))
    return saida
  }
  const agora = Date.now()
  const faltam = unicos.filter((c) => {
    const guardada = assinadas.get(c)
    if (guardada && guardada.expira > agora) {
      saida[c] = guardada.url
      return false
    }
    return true
  })
  if (faltam.length) {
    const { data } = await supabase.storage.from(BUCKET).createSignedUrls(faltam, VALIDADE_S)
    data?.forEach((item) => {
      if (item.path && item.signedUrl) {
        saida[item.path] = item.signedUrl
        // renova 10 min antes de vencer, para a imagem não quebrar na tela aberta
        assinadas.set(item.path, { url: item.signedUrl, expira: agora + (VALIDADE_S - 600) * 1000 })
      }
    })
  }
  return saida
}

export function useFotos(caminhos: (string | null | undefined)[]): Record<string, string> {
  const chave = caminhos.filter(Boolean).join('|')
  const [urls, setUrls] = useState<Record<string, string>>({})
  useEffect(() => {
    let ativo = true
    const lista = chave ? chave.split('|') : []
    if (!lista.length) return
    urlsDasFotos(lista)
      .then((novas) => ativo && setUrls((antes) => ({ ...antes, ...novas })))
      .catch(() => undefined) // sem URL, a tela mostra a silhueta da peça
    return () => {
      ativo = false
    }
  }, [chave])
  return urls
}
