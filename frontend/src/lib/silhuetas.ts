// Silhuetas das peças, desenhadas em SVG e tingidas com a cor da peça.
//
// Aparecem quando a peça não tem foto (cadastro manual, modo demonstração) e
// quando a foto não carrega. São geradas como texto SVG para servirem tanto a
// um <img> na tela quanto ao canvas que exporta o look como imagem.

type Forma = { d: string; tipo?: 'corpo' | 'sombra' | 'luz' | 'traco' }

const MANGA_CURTA =
  'M42 18 24 26 8 46l14 12 10-10v56h56V48l10 10 14-12-16-20-18-8c-4 10-32 10-36 0Z'
const MANGA_LONGA =
  'M42 16 22 24 8 92l16 4 10-44v54h52V52l10 44 16-4-14-68-20-8c-4 10-32 10-36 0Z'
const CALCA = 'M34 10h52l8 100H68L60 40l-8 70H26Z'

const FORMAS: Record<string, Forma[]> = {
  camiseta: [
    { d: MANGA_CURTA },
    { d: 'M42 18c4 10 32 10 36 0', tipo: 'traco' },
  ],
  regata: [
    { d: 'M44 14h-8c0 20-8 26-10 32v60h68V46c-2-6-10-12-10-32h-8c-2 16-30 16-32 0Z' },
    { d: 'M44 14c2 16 30 16 32 0', tipo: 'traco' },
  ],
  polo: [
    { d: MANGA_CURTA },
    { d: 'M42 18 60 34 78 18l-8-4-10 10-10-10Z', tipo: 'sombra' },
    { d: 'M60 34v22', tipo: 'traco' },
  ],
  camisa: [
    { d: MANGA_LONGA },
    { d: 'M42 16 60 32 78 16l-8-4-10 10-10-10Z', tipo: 'sombra' },
    { d: 'M60 32v74M60 46h.1M60 60h.1M60 74h.1M60 88h.1', tipo: 'traco' },
  ],
  moletom: [
    { d: 'M40 22 20 32 6 94l16 4 10-40v48h56V58l10 40 16-4-14-62-20-10C78 8 42 8 40 22Z' },
    { d: 'M46 24c4-10 24-10 28 0-6 10-22 10-28 0Z', tipo: 'sombra' },
    { d: 'M44 80h32l4 18H40Z', tipo: 'sombra' },
    { d: 'M54 32v14M66 32v14', tipo: 'traco' },
  ],
  sueter: [
    { d: MANGA_LONGA },
    { d: 'M42 16c4 12 32 12 36 0l-6-2c-4 8-20 8-24 0Z', tipo: 'sombra' },
    { d: 'M34 98h52', tipo: 'traco' },
  ],
  bermuda: [
    { d: 'M30 20h60l8 76H66L60 50l-6 46H22Z' },
    { d: 'M30 20h60l1 10H29Z', tipo: 'sombra' },
    { d: 'M60 30v20', tipo: 'traco' },
  ],
  calca: [
    { d: CALCA },
    { d: 'M34 10h52l1 10H33Z', tipo: 'sombra' },
    { d: 'M60 20v20', tipo: 'traco' },
  ],
  tenis: [
    { d: 'M10 84c0-14 12-18 20-30l16-4c8 12 24 18 46 20 12 2 18 8 18 18v4H10Z' },
    { d: 'M8 92h104v8c0 2-2 4-4 4H12c-2 0-4-2-4-4Z', tipo: 'luz' },
    { d: 'M40 56l10 12M48 53l10 13M57 60l8 10', tipo: 'traco' },
  ],
  sapato: [
    { d: 'M10 86c0-12 14-14 24-24l14-2c10 10 30 14 48 16 10 2 16 8 16 16H10Z' },
    { d: 'M8 92h104v6H60l-4-3H8Z', tipo: 'sombra' },
    { d: 'M46 62c4 8 12 12 22 14', tipo: 'traco' },
  ],
  bota: [
    { d: 'M30 16h32v44c8 10 34 12 42 22 4 6 4 12 4 14H28Z' },
    { d: 'M26 96h84v8H26Z', tipo: 'sombra' },
    { d: 'M30 28h32M62 60c-10 2-22 2-32 0', tipo: 'traco' },
  ],
  chinelo: [
    { d: 'M40 14c16-6 36 6 38 30 2 20-4 52-16 62-12 6-24-2-26-22-2-24-6-60 4-70Z' },
    { d: 'M42 52c10-14 20-14 30 2M56 42v-14', tipo: 'traco' },
  ],
  jaqueta: [
    { d: MANGA_LONGA },
    { d: 'M42 16 54 34 60 26l6 8 12-18-8-4-10 8-10-8Z', tipo: 'sombra' },
    { d: 'M60 26v80M34 96h52M42 62h10M68 62h10', tipo: 'traco' },
  ],
  blazer: [
    { d: 'M42 14 22 24 8 96l16 4 8-44v54h56V56l8 44 16-4-14-72-20-10-18 26Z' },
    { d: 'M42 14 60 62 52 40l-8-4 6-6ZM78 14 60 62l8-22 8-4-6-6Z', tipo: 'sombra' },
    { d: 'M60 62v48M60 74h.1M60 88h.1M38 84h12M70 84h12', tipo: 'traco' },
  ],
  bone: [
    { d: 'M18 72c0-30 24-46 46-44s34 18 34 38l20 8c-2 8-14 8-22 4H18Z' },
    { d: 'M98 66l20 8c-2 8-14 8-22 4Z', tipo: 'sombra' },
    { d: 'M60 28c-10 12-12 30-10 50M60 28c10 12 16 26 18 42', tipo: 'traco' },
  ],
  gorro: [
    { d: 'M24 88c-2-44 16-68 36-68s38 24 36 68Z' },
    { d: 'M20 84h80v16H20Z', tipo: 'sombra' },
    { d: 'M36 84v16M52 84v16M68 84v16M84 84v16', tipo: 'traco' },
  ],
  cinto: [
    { d: 'M60 26a34 34 0 1 0 .1 0Zm0 12a22 22 0 1 1-.1 0Z' },
    { d: 'M84 52h24v16H84Z', tipo: 'sombra' },
    { d: 'M90 56h12v8H90Z', tipo: 'luz' },
  ],
  relogio: [
    { d: 'M48 8h24l4 30H44ZM44 82h32l-4 30H48Z' },
    { d: 'M60 34a26 26 0 1 0 .1 0Z', tipo: 'sombra' },
    { d: 'M60 42a18 18 0 1 0 .1 0Z', tipo: 'luz' },
    { d: 'M60 50v10l8 6', tipo: 'traco' },
  ],
  oculos: [
    { d: 'M8 46h44v10c0 14-8 22-20 22S10 70 8 56ZM68 46h44l-2 10c-2 14-10 22-22 22s-20-8-20-22Z' },
    { d: 'M52 50c4-4 12-4 16 0', tipo: 'traco' },
  ],
  cachecol: [
    { d: 'M26 30c20-16 48-16 68 0 10 10 4 26-14 30l6 44H62l-4-36c-16 2-34-2-38-14-2-10 0-18 6-24Z' },
    { d: 'M62 104h24M26 44c18 12 50 12 68 0M64 92h22', tipo: 'traco' },
  ],
  mochila: [
    { d: 'M34 30c0-12 10-20 26-20s26 8 26 20v8c8 4 10 12 10 22v44c0 4-4 8-8 8H32c-4 0-8-4-8-8V60c0-10 2-18 10-22Zm10 2h32c0-6-6-12-16-12s-16 6-16 12Z' },
    { d: 'M38 70h44v28c0 2-2 4-4 4H42c-2 0-4-2-4-4Z', tipo: 'sombra' },
    { d: 'M38 56h44', tipo: 'traco' },
  ],
}

const POR_CATEGORIA: Record<string, string> = {
  camiseta: 'camiseta', regata: 'regata', polo: 'polo',
  'camisa-casual': 'camisa', 'camisa-social': 'camisa',
  moletom: 'moletom', sueter: 'sueter',
  bermuda: 'bermuda', 'calca-jeans': 'calca', 'calca-sarja': 'calca',
  'calca-social': 'calca', 'calca-moletom': 'calca',
  tenis: 'tenis', 'tenis-casual': 'tenis', 'sapato-social': 'sapato', mocassim: 'sapato',
  bota: 'bota', chinelo: 'chinelo', sandalia: 'chinelo',
  'jaqueta-jeans': 'jaqueta', 'jaqueta-couro': 'jaqueta', 'corta-vento': 'jaqueta',
  blazer: 'blazer', casaco: 'blazer',
  bone: 'bone', gorro: 'gorro', cinto: 'cinto', relogio: 'relogio',
  oculos: 'oculos', cachecol: 'cachecol', mochila: 'mochila',
}

const POR_PAPEL: Record<string, string> = {
  superior: 'camiseta', inferior: 'calca', calcado: 'tenis',
  sobreposicao: 'jaqueta', acessorio: 'bone',
}

function claridade(hex: string): number {
  const n = parseInt(hex.replace('#', ''), 16)
  return (0.2126 * (n >> 16) + 0.7152 * ((n >> 8) & 255) + 0.0722 * (n & 255)) / 255
}

/** Texto SVG da silhueta de uma peça, na cor dela. */
export function svgDaPeca(categoria: string, papel: string, corHex: string): string {
  const cor = /^#[0-9a-f]{6}$/i.test(corHex) ? corHex : '#8c8c8c'
  const formas = FORMAS[POR_CATEGORIA[categoria] ?? POR_PAPEL[papel] ?? 'camiseta']
  const escura = claridade(cor) < 0.35
  // sombra e traço mudam de lado conforme a cor: numa peça preta, o detalhe
  // precisa ser mais claro para aparecer
  const sombra = escura ? 'rgba(255,255,255,.16)' : 'rgba(0,0,0,.14)'
  const traco = escura ? 'rgba(255,255,255,.34)' : 'rgba(0,0,0,.28)'
  const contorno = escura ? 'rgba(255,255,255,.10)' : 'rgba(0,0,0,.22)'
  const partes = formas.map(({ d, tipo = 'corpo' }) => {
    if (tipo === 'traco') {
      return `<path d="${d}" fill="none" stroke="${traco}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>`
    }
    if (tipo === 'sombra') return `<path d="${d}" fill="${sombra}"/>`
    if (tipo === 'luz') return `<path d="${d}" fill="rgba(255,255,255,.82)" stroke="${contorno}" stroke-width="1"/>`
    return `<path d="${d}" fill="${cor}" stroke="${contorno}" stroke-width="1.4" stroke-linejoin="round" fill-rule="evenodd"/>`
  })
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120">${partes.join('')}</svg>`
}

export function silhuetaComoUrl(categoria: string, papel: string, corHex: string): string {
  return `data:image/svg+xml;utf8,${encodeURIComponent(svgDaPeca(categoria, papel, corHex))}`
}
