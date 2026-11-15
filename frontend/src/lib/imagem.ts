// Preparo da foto no aparelho, antes de enviar.

const LADO_MAXIMO = 1280

/**
 * Reduz a foto para no máximo 1280 px e converte para JPEG.
 *
 * A câmera de um celular entrega 12 a 48 megapixels; o modelo de classificação
 * trabalha em 224 px. Enviar o original só gasta dados do usuário e tempo de
 * upload — que entra na conta dos 5 segundos da catalogação. De quebra, o
 * formato HEIC do iPhone vira JPEG, que o servidor sabe abrir.
 */
export async function prepararFoto(arquivo: Blob): Promise<Blob> {
  try {
    // `createImageBitmap` já aplica a rotação do EXIF por padrão
    const original = await createImageBitmap(arquivo)
    const escala = Math.min(1, LADO_MAXIMO / Math.max(original.width, original.height))
    const largura = Math.round(original.width * escala)
    const altura = Math.round(original.height * escala)
    const tela = document.createElement('canvas')
    tela.width = largura
    tela.height = altura
    const contexto = tela.getContext('2d')
    if (!contexto) return arquivo
    contexto.fillStyle = '#ffffff'
    contexto.fillRect(0, 0, largura, altura)
    contexto.drawImage(original, 0, 0, largura, altura)
    original.close()
    const reduzida = await new Promise<Blob | null>((ok) => tela.toBlob(ok, 'image/jpeg', 0.85))
    return reduzida ?? arquivo
  } catch {
    return arquivo // formato que o navegador não abre: o servidor decide
  }
}

export async function dataUrlParaBlob(dataUrl: string): Promise<Blob> {
  return (await fetch(dataUrl)).blob()
}

export function baixar(blob: Blob, nome: string): void {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = nome
  link.click()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}
