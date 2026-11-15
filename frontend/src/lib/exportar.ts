/** Exporta o look como imagem PNG (botão de download da tela "Look Gerado"). */
import type { Look, PecaDoLook } from './api'
import { silhuetaComoUrl } from './silhuetas'

const LARGURA = 1080
const ALTURA = 1350

function carregar(src: string): Promise<HTMLImageElement> {
  return new Promise((ok, falha) => {
    const img = new Image()
    img.crossOrigin = 'anonymous' // sem isto o canvas fica "contaminado" e não exporta
    img.onload = () => ok(img)
    img.onerror = () => falha(new Error('imagem indisponível'))
    img.src = src
  })
}

async function imagemDaPeca(p: PecaDoLook, fotos: Record<string, string>): Promise<HTMLImageElement> {
  const silhueta = () => carregar(silhuetaComoUrl(p.categoria, p.papel, p.cor_hex))
  const url = p.imagem_path ? fotos[p.imagem_path] : undefined
  if (!url) return silhueta()
  try {
    // baixa como blob: funciona com as URLs assinadas e evita contaminar o canvas
    const blob = await (await fetch(url)).blob()
    const local = URL.createObjectURL(blob)
    try {
      return await carregar(local)
    } finally {
      URL.revokeObjectURL(local)
    }
  } catch {
    return silhueta()
  }
}

function encaixar(ctx: CanvasRenderingContext2D, img: HTMLImageElement, x: number, y: number, l: number, a: number) {
  const escala = Math.min(l / img.width, a / img.height)
  const [w, h] = [img.width * escala, img.height * escala]
  ctx.drawImage(img, x + (l - w) / 2, y + (a - h) / 2, w, h)
}

export async function exportarLook(look: Look, fotos: Record<string, string>): Promise<Blob> {
  const tela = document.createElement('canvas')
  tela.width = LARGURA
  tela.height = ALTURA
  const ctx = tela.getContext('2d')!
  const fundo = ctx.createLinearGradient(0, 0, LARGURA, ALTURA)
  fundo.addColorStop(0, '#5a5a57')
  fundo.addColorStop(1, '#3c3c3a')
  ctx.fillStyle = fundo
  ctx.fillRect(0, 0, LARGURA, ALTURA)

  const por = (papel: string) => look.pecas.filter((p) => p.papel === papel)
  const sobreposicao = por('sobreposicao')[0]
  const superior = por('superior')[0]
  const esquerda = sobreposicao ?? superior
  const direita = por('inferior')[0]
  const meio = [...(sobreposicao && superior ? [superior] : []), ...por('acessorio'), ...por('calcado')]

  const topo = 70
  const area = 960
  const margem = 50
  if (esquerda) encaixar(ctx, await imagemDaPeca(esquerda, fotos), margem, topo, 400, area)
  if (direita) encaixar(ctx, await imagemDaPeca(direita, fotos), LARGURA - margem - 340, topo, 340, area)
  const fatia = area / Math.max(meio.length, 1)
  for (const [i, p] of meio.entries())
    encaixar(ctx, await imagemDaPeca(p, fotos), 470, topo + i * fatia + 16, 220, fatia - 32)

  ctx.fillStyle = '#f3f0e7'
  ctx.fillRect(0, 1090, LARGURA, ALTURA - 1090)
  ctx.fillStyle = '#24251f'
  ctx.font = '700 46px "DM Sans Variable", system-ui, sans-serif'
  ctx.fillText(look.titulo.toUpperCase(), 60, 1170)
  ctx.font = '400 32px "DM Sans Variable", system-ui, sans-serif'
  ctx.fillStyle = '#5f5e55'
  ctx.fillText(look.pecas.map((p) => p.rotulo).join(' · ').slice(0, 62), 60, 1230)
  ctx.font = '600 28px "DM Sans Variable", system-ui, sans-serif'
  ctx.fillStyle = '#4d5141'
  ctx.fillText('Style Up', 60, 1300)

  return new Promise((ok, falha) =>
    tela.toBlob((blob) => (blob ? ok(blob) : falha(new Error('falha ao gerar a imagem'))), 'image/png'),
  )
}

/** Compartilha pelo sistema quando o aparelho permite; senão, baixa o arquivo. */
export async function entregar(blob: Blob, nome: string): Promise<'compartilhado' | 'baixado'> {
  const arquivo = new File([blob], nome, { type: 'image/png' })
  if (navigator.canShare?.({ files: [arquivo] })) {
    try {
      await navigator.share({ files: [arquivo], title: 'Meu look no Style Up' })
      return 'compartilhado'
    } catch (erro) {
      if ((erro as DOMException).name === 'AbortError') return 'compartilhado'
    }
  }
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = nome
  link.click()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
  return 'baixado'
}
