/**
 * Silhuetas das peças, desenhadas em SVG e tingidas com a cor da peça.
 *
 * Aparecem quando a peça não tem foto (cadastro manual, modo demonstração, foto
 * que não carregou) e na exportação do look como imagem. Como é só uma string
 * de SVG, a mesma função serve ao `<img>` da tela e ao canvas da exportação.
 */
import type { Papel } from './api'

/** c = corpo (cor da peça) · s = sombra · l = luz · t = traço · b = borracha clara (sola) */
type Parte = ['c' | 's' | 'l' | 't' | 'b', string]

const MANGA_LONGA =
  'M42 16 L22 24 L7 92 L23 97 L34 54 L34 106 L86 106 L86 54 L97 97 L113 92 L98 24 L78 16 C72 26 48 26 42 16 Z'

const FORMAS: Record<string, Parte[]> = {
  camiseta: [
    ['c', 'M42 18 L24 26 L7 47 L22 60 L33 49 L33 104 L87 104 L87 49 L98 60 L113 47 L96 26 L78 18 C73 29 47 29 42 18 Z'],
    ['s', 'M42 18 C47 29 73 29 78 18 L74 17 C70 25 50 25 46 17 Z'],
  ],
  regata: [
    ['c', 'M45 14 L37 14 C37 34 29 40 27 47 L27 106 L93 106 L93 47 C91 40 83 34 83 14 L75 14 C73 31 47 31 45 14 Z'],
    ['s', 'M45 14 C47 31 73 31 75 14 L72 14 C70 27 50 27 48 14 Z'],
  ],
  polo: [
    ['c', 'M42 18 L24 26 L7 47 L22 60 L33 49 L33 104 L87 104 L87 49 L98 60 L113 47 L96 26 L78 18 L60 30 Z'],
    ['s', 'M42 18 L50 12 L60 24 L70 12 L78 18 L62 36 L60 30 L58 36 Z'],
    ['t', 'M60 30 L60 56'],
  ],
  camisa: [
    ['c', MANGA_LONGA],
    ['s', 'M42 16 L50 10 L60 22 L70 10 L78 16 L63 34 L60 28 L57 34 Z'],
    ['t', 'M60 28 L60 106 M56 48 h.1 M56 64 h.1 M56 80 h.1 M56 96 h.1'],
    ['s', 'M7 92 L23 97 L22 101 L6 96 Z M113 92 L97 97 L98 101 L114 96 Z'],
  ],
  moletom: [
    ['c', 'M40 24 L20 32 L6 94 L22 99 L32 58 L32 106 L88 106 L88 58 L98 99 L114 94 L100 32 L80 24 C80 6 40 6 40 24 Z'],
    ['s', 'M45 25 C48 13 72 13 75 25 C69 37 51 37 45 25 Z'],
    ['s', 'M44 80 L76 80 L81 99 L39 99 Z'],
    ['s', 'M32 100 L88 100 L88 106 L32 106 Z'],
    ['t', 'M55 34 L54 50 M65 34 L66 50'],
  ],
  sueter: [
    ['c', 'M42 18 L22 26 L7 92 L23 97 L34 54 L34 106 L86 106 L86 54 L97 97 L113 92 L98 26 L78 18 C73 28 47 28 42 18 Z'],
    ['s', 'M42 18 C47 28 73 28 78 18 L75 16 C70 24 50 24 45 16 Z'],
    ['s', 'M34 98 L86 98 L86 106 L34 106 Z M7 92 L23 97 L21 103 L5 98 Z M113 92 L97 97 L99 103 L115 98 Z'],
  ],
  bermuda: [
    ['c', 'M30 22 L90 22 L99 96 L66 96 L60 52 L54 96 L21 96 Z'],
    ['s', 'M30 22 L90 22 L91 31 L29 31 Z'],
    ['t', 'M60 31 L60 52 M36 38 C38 46 36 50 32 52 M84 38 C82 46 84 50 88 52'],
  ],
  calca: [
    ['c', 'M34 10 L86 10 L95 110 L69 110 L60 42 L51 110 L25 110 Z'],
    ['s', 'M34 10 L86 10 L87 19 L33 19 Z'],
    ['t', 'M60 19 L60 42 M39 24 C41 31 39 35 35 37 M81 24 C79 31 81 35 85 37'],
  ],
  tenis: [
    ['c', 'M10 86 C10 70 22 66 31 53 L47 49 C55 62 71 68 93 71 C105 73 111 79 111 89 L111 92 L10 92 Z'],
    ['b', 'M8 92 L112 92 L112 100 C112 103 110 105 107 105 L13 105 C10 105 8 103 8 100 Z'],
    ['s', 'M10 86 C10 76 16 72 22 66 L28 78 C24 84 22 88 22 92 L10 92 Z'],
    ['t', 'M44 60 L56 54 M51 66 L63 60 M58 71 L70 66'],
  ],
  sapato: [
    ['c', 'M10 84 C10 72 24 70 34 59 L49 57 C59 68 79 72 97 75 C107 77 112 82 112 90 L10 90 Z'],
    ['s', 'M8 90 L112 90 L112 97 L62 97 L58 94 L8 94 Z'],
    ['t', 'M40 64 C52 66 58 72 62 78'],
  ],
  bota: [
    ['c', 'M30 16 L62 16 L62 60 C70 70 96 72 104 82 C108 88 108 93 108 96 L28 96 Z'],
    ['s', 'M26 96 L110 96 L110 104 L66 104 L62 100 L26 100 Z'],
    ['s', 'M30 16 L62 16 L62 24 L30 24 Z'],
    ['t', 'M62 60 C56 64 50 64 46 60'],
  ],
  chinelo: [
    ['c', 'M40 14 C57 8 77 20 79 45 C81 66 74 97 62 107 C50 113 38 104 36 84 C34 60 30 24 40 14 Z'],
    ['t', 'M41 52 C50 36 60 34 60 22 M60 22 C62 36 70 40 76 54'],
  ],
  jaqueta: [
    ['c', MANGA_LONGA],
    ['s', 'M42 16 L50 9 L60 24 L70 9 L78 16 L64 36 L60 30 L56 36 Z'],
    ['s', 'M34 98 L86 98 L86 106 L34 106 Z'],
    ['t', 'M60 30 L60 98 M40 62 L52 62 M68 62 L80 62'],
  ],
  blazer: [
    ['c', 'M42 14 L22 22 L8 96 L24 100 L33 56 L32 110 L88 110 L87 56 L96 100 L112 96 L98 22 L78 14 L60 22 Z'],
    ['s', 'M42 14 L60 22 L78 14 L84 24 L72 34 L78 40 L60 70 L42 40 L48 34 L36 24 Z'],
    ['l', 'M50 16 L60 22 L70 16 L60 60 Z'],
    ['t', 'M60 70 L60 110 M56 80 h.1 M56 92 h.1 M38 84 L50 84 M70 84 L82 84'],
  ],
  casaco: [
    ['c', 'M42 10 L22 18 L8 92 L24 96 L33 52 L30 114 L90 114 L87 52 L96 96 L112 92 L98 18 L78 10 L60 20 Z'],
    ['s', 'M42 10 L60 20 L78 10 L84 22 L72 32 L77 38 L60 62 L43 38 L48 32 L36 22 Z'],
    ['t', 'M60 62 L60 114 M56 72 h.1 M56 86 h.1 M56 100 h.1 M36 80 L48 82 M72 82 L84 80'],
  ],
  bone: [
    ['c', 'M18 72 C16 42 40 26 63 28 C86 30 99 46 99 68 L99 76 L18 78 Z'],
    ['s', 'M99 66 L117 73 C117 82 104 84 96 80 L18 80 L18 74 L99 72 Z'],
    ['t', 'M62 28 C54 44 52 60 52 76 M63 28 C76 42 80 58 80 74'],
    ['s', 'M58 24 h9 v5 h-9 Z'],
  ],
  gorro: [
    ['c', 'M24 88 C22 44 40 20 60 20 C80 20 98 44 96 88 Z'],
    ['s', 'M20 84 L100 84 L100 101 L20 101 Z'],
    ['t', 'M34 86 v13 M47 86 v13 M60 86 v13 M73 86 v13 M86 86 v13'],
    ['c', 'M53 12 a7 7 0 1 0 14 0 a7 7 0 1 0 -14 0 Z'],
  ],
  cinto: [
    ['c', 'M60 22 C84 22 100 36 100 58 C100 82 82 98 60 98 C38 98 20 82 20 58 C20 36 36 22 60 22 Z M60 38 C46 38 36 46 36 58 C36 72 46 82 60 82 C74 82 84 72 84 58 C84 46 74 38 60 38 Z'],
    ['b', 'M50 84 h22 v18 h-22 Z'],
    ['t', 'M56 90 h10 v6 h-10 Z'],
  ],
  relogio: [
    ['c', 'M48 8 h24 l3 30 h-30 Z M45 82 h30 l-3 30 h-24 Z'],
    ['s', 'M60 34 a26 26 0 1 0 .1 0 Z'],
    ['b', 'M60 41 a19 19 0 1 0 .1 0 Z'],
    ['t', 'M60 48 L60 60 L69 65'],
  ],
  oculos: [
    ['c', 'M10 50 h42 c0 20 -8 28 -21 28 c-13 0 -21 -8 -21 -28 Z M68 50 h42 c0 20 -8 28 -21 28 c-13 0 -21 -8 -21 -28 Z'],
    ['t', 'M52 54 C56 50 64 50 68 54 M10 50 L4 46 M110 50 L116 46'],
  ],
  cachecol: [
    ['c', 'M30 30 C30 14 90 14 90 30 C90 46 30 46 30 30 Z M50 42 L44 104 L60 104 L64 44 Z M68 44 L72 92 L86 92 L80 42 Z'],
    ['s', 'M42 30 C42 24 78 24 78 30 C78 36 42 36 42 30 Z'],
    ['t', 'M44 98 h16 M72 86 h14'],
  ],
  mochila: [
    ['c', 'M34 32 C34 18 86 18 86 32 L92 100 C92 106 88 110 82 110 L38 110 C32 110 28 106 28 100 Z'],
    ['s', 'M40 66 h40 a4 4 0 0 1 4 4 v26 a4 4 0 0 1 -4 4 h-40 a4 4 0 0 1 -4 -4 v-26 a4 4 0 0 1 4 -4 Z'],
    ['t', 'M48 22 C48 6 72 6 72 22 M36 54 h48 M52 78 h16'],
  ],
}

const FORMA_DA_CATEGORIA: Record<string, string> = {
  camiseta: 'camiseta', regata: 'regata', polo: 'polo',
  'camisa-casual': 'camisa', 'camisa-social': 'camisa',
  moletom: 'moletom', sueter: 'sueter',
  bermuda: 'bermuda', 'calca-jeans': 'calca', 'calca-sarja': 'calca',
  'calca-social': 'calca', 'calca-moletom': 'calca',
  tenis: 'tenis', 'tenis-casual': 'tenis', 'sapato-social': 'sapato', mocassim: 'sapato',
  bota: 'bota', chinelo: 'chinelo', sandalia: 'chinelo',
  'jaqueta-jeans': 'jaqueta', 'jaqueta-couro': 'jaqueta', 'corta-vento': 'jaqueta',
  blazer: 'blazer', casaco: 'casaco',
  bone: 'bone', gorro: 'gorro', cinto: 'cinto', relogio: 'relogio',
  oculos: 'oculos', cachecol: 'cachecol', mochila: 'mochila',
}

const FORMA_DO_PAPEL: Record<Papel, string> = {
  superior: 'camiseta', inferior: 'calca', calcado: 'tenis',
  sobreposicao: 'jaqueta', acessorio: 'mochila',
}

function rgb(hex: string): [number, number, number] {
  const limpo = /^#?[0-9a-f]{6}$/i.test(hex) ? hex.replace('#', '') : '8c8c8c'
  const n = parseInt(limpo, 16)
  return [n >> 16, (n >> 8) & 255, n & 255]
}

function misturar(hex: string, alvo: number, quanto: number): string {
  const [r, g, b] = rgb(hex).map((c) => Math.round(c + (alvo - c) * quanto))
  return `rgb(${r},${g},${b})`
}

/** Luminância relativa (WCAG), para decidir a cor do contorno. */
function luminancia(hex: string): number {
  const [r, g, b] = rgb(hex).map((c) => {
    const v = c / 255
    return v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4
  })
  return 0.2126 * r + 0.7152 * g + 0.0722 * b
}

/** SVG completo da silhueta de uma peça, na cor dela. */
export function svgDaPeca(categoria: string, papel: Papel, corHex: string): string {
  const forma = FORMAS[FORMA_DA_CATEGORIA[categoria] ?? FORMA_DO_PAPEL[papel]] ?? FORMAS.camiseta
  const escura = luminancia(corHex) < 0.08
  // peça escura: a "sombra" clareia, senão some; o contorno acompanha
  const sombra = escura ? misturar(corHex, 255, 0.16) : misturar(corHex, 0, 0.2)
  const luz = misturar(corHex, 255, 0.3)
  const traco = escura ? 'rgba(255,255,255,.34)' : 'rgba(0,0,0,.3)'
  const contorno = escura ? 'rgba(255,255,255,.2)' : 'rgba(0,0,0,.2)'
  const partes = forma
    .map(([tipo, d]) => {
      if (tipo === 't')
        return `<path d="${d}" fill="none" stroke="${traco}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>`
      const cor = tipo === 'c' ? corHex : tipo === 's' ? sombra : tipo === 'l' ? luz : '#f1efe9'
      const borda = tipo === 'c' || tipo === 'b' ? ` stroke="${contorno}" stroke-width="1.2"` : ''
      return `<path d="${d}" fill="${cor}" fill-rule="evenodd" stroke-linejoin="round"${borda}/>`
    })
    .join('')
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120" width="480" height="480">${partes}</svg>`
}

export function silhuetaComoUrl(categoria: string, papel: Papel, corHex: string): string {
  return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svgDaPeca(categoria, papel, corHex))}`
}
