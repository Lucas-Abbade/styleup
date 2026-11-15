/** Preparo da foto no aparelho, antes de enviar para análise. */

const LADO_MAXIMO = 1280 // o servidor reduz para 1024; mais que isso é só tráfego
const QUALIDADE = 0.85

/**
 * Reduz e recomprime a foto. Uma foto de 12 MP (4–8 MB) vira ~250 KB, o que
 * corta segundos de envio em rede móvel. `createImageBitmap` já aplica a
 * orientação do EXIF e redimensiona na decodificação, sem estourar o limite de
 * área de canvas do Safari do iOS.
 */
export async function prepararFoto(arquivo: Blob): Promise<Blob> {
  try {
    const original = await createImageBitmap(arquivo)
    const escala = Math.min(1, LADO_MAXIMO / Math.max(original.width, original.height))
    const largura = Math.round(original.width * escala)
    const altura = Math.round(original.height * escala)
    const tela = document.createElement('canvas')
    tela.width = largura
    tela.height = altura
    tela.getContext('2d')!.drawImage(original, 0, 0, largura, altura)
    original.close()
    const blob = await new Promise<Blob | null>((ok) => tela.toBlob(ok, 'image/jpeg', QUALIDADE))
    return blob && blob.size < arquivo.size ? blob : arquivo
  } catch {
    return arquivo // formato que o navegador não decodifica: o servidor decide
  }
}

export async function dataUrlParaBlob(dataUrl: string): Promise<Blob> {
  return (await fetch(dataUrl)).blob()
}
