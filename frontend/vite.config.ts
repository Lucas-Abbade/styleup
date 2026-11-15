import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'
import { VitePWA } from 'vite-plugin-pwa'

// O PWA é o que atende ao RNF06 (instalável no celular) e ao RNF09 (consulta ao
// guarda-roupa a partir de cache local).
export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      // "prompt", não "autoUpdate": uma atualização automática recarrega a aba
      // e descarta o formulário de cadastro que o usuário estiver preenchendo.
      registerType: 'prompt',
      includeAssets: ['favicon.svg', 'icone-192.png', 'icone-512.png'],
      manifest: {
        name: 'Style Up',
        short_name: 'Style Up',
        description: 'Seu guarda-roupa catalogado por foto, com sugestões de look.',
        lang: 'pt-BR',
        theme_color: '#f3f0e7',
        background_color: '#f3f0e7',
        display: 'standalone',
        start_url: '/',
        icons: [
          { src: 'icone-192.png', sizes: '192x192', type: 'image/png' },
          { src: 'icone-512.png', sizes: '512x512', type: 'image/png' },
          { src: 'icone-512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
        ],
      },
      workbox: {
        navigateFallbackDenylist: [/^\/demo\//],
        runtimeCaching: [
          {
            // Fotos das peças. A URL assinada do Supabase muda a cada assinatura
            // (o token vai na query); sem normalizar a chave, o cache nunca
            // acerta. A chave passa a ser só o caminho do arquivo.
            urlPattern: ({ url }) =>
              url.pathname.includes('/storage/v1/object/sign/') ||
              url.pathname.startsWith('/demo/fotos/'),
            handler: 'CacheFirst',
            options: {
              cacheName: 'fotos-pecas',
              expiration: { maxEntries: 400, maxAgeSeconds: 60 * 60 * 24 * 30 },
              cacheableResponse: { statuses: [200] },
              plugins: [
                {
                  cacheKeyWillBeUsed: async ({ request }) => {
                    const url = new URL(request.url)
                    return url.origin + url.pathname
                  },
                },
              ],
            },
          },
          {
            // Catálogos públicos (categorias, cores, inspirações): mudam raramente.
            urlPattern: ({ url }) =>
              ['/pecas/taxonomia', '/pecas/cores', '/inspiracoes', '/eventos'].includes(
                url.pathname,
              ),
            handler: 'StaleWhileRevalidate',
            options: { cacheName: 'catalogos' },
          },
          // As respostas com dados do usuário NÃO passam pelo service worker: num
          // aparelho compartilhado, o cache de um usuário apareceria para outro.
          // O guarda-roupa offline (RNF09) fica no armazenamento por usuário
          // (src/lib/cache.ts), apagado ao sair.
        ],
      },
    }),
  ],
  server: { port: 5173 },
  build: { target: 'es2022', sourcemap: false },
})
