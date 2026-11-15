// Disposição das peças na colagem do look e exportação como imagem.
import type { PecaDoLook } from './api'
import { silhuetaComoUrl } from './silhuetas'

export interface Vaga {
  peca: PecaDoLook
  // posição e tamanho em fração da área da colagem (0 a 1)
  x: number
  y: number
  l: number
  a: number
}

/**
 * Arruma as peças como num "flat lay": a peça de cima mais externa à esquerda,
 * a calça à direita e, no meio, o que sobra (camiseta sob a jaqueta, acessórios
 * e, por último, o calçado).
 */
export function disporPecas(pecas: PecaDoLook[]): Vaga[] {
  const de = (papel: string) => pecas.filter((p) => p.papel === papel)
  const sobreposicao = de('sobreposicao')[0]
  const superior = de('superior')[0]
  const inferior = de('inferior')[0]
  const esquerda = sobreposicao ?? superior
  const meio = [
    ...(sobreposicao && superior ? [superior] : []),
    ...de('acessorio'),
    ...de('calcado'),
  ]
  const vagas: Vaga[] = []
  if (esquerda) vagas.push({ peca: esquerda, x: 0.03, y: 0.08, l: 0.4, a: 0.84 })
  if (inferior) vagas.push({ peca: inferior, x: 0.63, y: 0.06, l: 0.34, a: 0.88 })
  const altura = 0.9 / Math.max(meio.length, 1)
  meio.forEach((peca, i) => {
    const a = Math.min(altura, 0.34)
    const folga = (0.9 - a * meio.length) / (meio.length + 1)
    vagas.push({ peca, x: 0.42, y: 0.05 + folga * (i + 1) + a * i, l: 0.22, a })
  })
  return vagas
}

function carregar(src: string): Promise<HTMLImageElement> {
  return new Promise((ok, falha) => {
    const img = new Image()
    img.crossOrigin = 'anonymous' // sem isto o canvas fica "contaminado" e não exporta
    img.onload = () => ok(img)
    img.onerror = () => falha(new Error('imagem indisponível'))
    img.src = src
  })
}

/** Desenha o look num canvas e devolve um PNG, para baixar ou compartilhar. */
export async function exportarLook(
  pecas: PecaDoLook[],
  urls: Record<string, string>,
  titulo: string,
): Promise<Blob> {
  const L = 1080
  const A = 1180
  const tela = document.createElement('canvas')
  tela.width = L
  tela.height = A
  const c = tela.getContext('2d')
  if (!c) throw new Error('Seu navegador não permite gerar a imagem.')

  c.fillStyle = '#4b4b4b'
  c.fillRect(0, 0, L, A)
  const area = { x: 40, y: 40, l: L - 80, a: A - 200 }

  for (const vaga of disporPecas(pecas)) {
    const { peca } = vaga
    const silhueta = silhuetaComoUrl(peca.categoria, peca.papel, peca.cor_hex)
    const foto = peca.imagem_path ? urls[peca.imagem_path] : undefined
    let img: HTMLImageElement
    try {
      img = await carregar(foto ?? silhueta)
    } catch {
      img = await carregar(silhueta)
    }
    const caixa = {
      x: area.x + vaga.x * area.l,
      y: area.y + vaga.y * area.a,
      l: vaga.l * area.l,
      a: vaga.a * area.a,
    }
    const escala = Math.min(caixa.l / img.width, caixa.a / img.height)
    const l = img.width * escala
    const a = img.height * escala
    c.drawImage(img, caixa.x + (caixa.l - l) / 2, caixa.y + (caixa.a - a) / 2, l, a)
  }

  c.fillStyle = '#f3f0e7'
  c.font = '600 44px "DM Sans Variable", system-ui, sans-serif'
  c.fillText(titulo.toUpperCase(), 48, A - 92)
  c.font = '400 30px "DM Sans Variable", system-ui, sans-serif'
  c.fillStyle = 'rgba(243,240,231,.7)'
  c.fillText('Style Up', 48, A - 44)

  const blob = await new Promise<Blob | null>((ok) => tela.toBlob(ok, 'image/png'))
  if (!blob) throw new Error('Não foi possível gerar a imagem.')
  return blob
}
