import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'
import { VitePWA } from 'vite-plugin-pwa'

// O PWA é o que atende ao RNF06 (instalável no celular) e ao RNF09 (consulta ao
// guarda-roupa a partir de cache local). O cache de rede cobre justamente a
// listagem de peças; recomendação e upload continuam exigindo conexão.
export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      manifest: {
        name: 'StyleUp',
        short_name: 'StyleUp',
        description: 'Seu guarda-roupa catalogado por foto, com sugestões de look.',
        theme_color: '#1c1917',
        background_color: '#fafaf9',
        display: 'standalone',
        start_url: '/',
        icons: [
          { src: 'icone-192.png', sizes: '192x192', type: 'image/png' },
          { src: 'icone-512.png', sizes: '512x512', type: 'image/png' },
          { src: 'icone-512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
        ],
      },
      workbox: {
        runtimeCaching: [
          {
            // guarda-roupa disponível offline
            urlPattern: ({ url }) => url.pathname.startsWith('/pecas'),
            handler: 'NetworkFirst',
            options: {
              cacheName: 'guarda-roupa',
              networkTimeoutSeconds: 3,
              expiration: { maxEntries: 200, maxAgeSeconds: 60 * 60 * 24 * 7 },
            },
          },
          {
            urlPattern: ({ url }) => url.pathname.includes('/storage/v1/object'),
            handler: 'CacheFirst',
            options: {
              cacheName: 'fotos-pecas',
              expiration: { maxEntries: 300, maxAgeSeconds: 60 * 60 * 24 * 30 },
            },
          },
        ],
      },
    }),
  ],
  server: { port: 5173 },
})
