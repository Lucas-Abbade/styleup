/** Envio e leitura das fotos das peças (Storage do Supabase ou modo demonstração). */
import { useEffect, useState } from 'react'
import { api } from './api'
import { API_URL, BUCKET, MODO_DEMO } from './config'
import { usuarioIdAtual } from './sessao'
import { supabase } from './supabase'

const VALIDADE_S = 60 * 60
const urls = new Map<string, { url: string; expira: number }>()

/** Envia o recorte da peça e devolve o caminho para gravar em `imagem_path`. */
export async function enviarFoto(foto: Blob): Promise<string> {
  if (MODO_DEMO) return (await api.enviarFotoDemo(foto)).caminho
  const uid = usuarioIdAtual()
  if (!uid) throw new Error('Sessão expirada. Entre novamente.')
  const extensao = foto.type === 'image/webp' ? 'webp' : 'jpg'
  const caminho = `${uid}/${crypto.randomUUID()}.${extensao}`
  const { error } = await supabase!.storage.from(BUCKET).upload(caminho, foto, {
    contentType: foto.type || 'image/jpeg',
    cacheControl: '31536000',
    upsert: false,
  })
  if (error) throw new Error('Não foi possível enviar a foto. Tente de novo.')
  return caminho
}

/**
 * URLs de exibição para vários caminhos de uma vez. No Supabase é UMA chamada
 * (`createSignedUrls`), não uma por peça como antes; o resultado fica em memória
 * até perto de expirar.
 */
export async function urlsDasFotos(caminhos: string[]): Promise<Record<string, string>> {
  const agora = Date.now()
  const saida: Record<string, string> = {}
  const faltando: string[] = []
  for (const caminho of new Set(caminhos)) {
    const guardada = urls.get(caminho)
    if (guardada && guardada.expira > agora) saida[caminho] = guardada.url
    else faltando.push(caminho)
  }
  if (!faltando.length) return saida

  if (MODO_DEMO) {
    for (const caminho of faltando) {
      const url = `${API_URL}/demo/fotos/${caminho}`
      urls.set(caminho, { url, expira: Infinity })
      saida[caminho] = url
    }
    return saida
  }
  const { data } = await supabase!.storage.from(BUCKET).createSignedUrls(faltando, VALIDADE_S)
  for (const item of data ?? []) {
    if (item.signedUrl && item.path) {
      urls.set(item.path, { url: item.signedUrl, expira: agora + (VALIDADE_S - 300) * 1000 })
      saida[item.path] = item.signedUrl
    }
  }
  return saida
}

/** Hook: mapa caminho → URL para as fotos de uma lista de peças. */
export function useFotos(caminhos: (string | null | undefined)[]): Record<string, string> {
  const validos = caminhos.filter((c): c is string => !!c)
  const chave = validos.join('|')
  const [mapa, setMapa] = useState<Record<string, string>>({})
  useEffect(() => {
    let vivo = true
    if (validos.length)
      urlsDasFotos(validos)
        .then((m) => vivo && setMapa(m))
        .catch(() => undefined)
    return () => {
      vivo = false
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [chave])
  return mapa
}
