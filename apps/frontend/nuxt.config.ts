// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  ssr: false,
  nitro: {
    compressPublicAssets: true,
  },
  devtools: { enabled: true },
  modules: ['@pinia/nuxt'],
  css: ['~/assets/tailwind.css'],
  postcss: {
    plugins: {
      tailwindcss: {},
      autoprefixer: {},
    },
  },

  runtimeConfig: {
    // PRIVATE — only accessible in Nitro server routes (BFF proxy).
    // Never exposed to browser JavaScript.
    apiBase: process.env.NUXT_API_BASE || 'http://127.0.0.1:8000/api/v1',
    public: {
      // All API traffic flows through the BFF proxy (/api/proxy/*) so no
      // backend URL needs to be public.
    },
  },
  app: {
    head: {
      title: 'Invoice Tracker',
      meta: [
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
      ],
      link: [
        {
          rel: 'stylesheet',
          href: 'https://rsms.me/inter/inter.css',
        },
      ],
    },
  },
  typescript: {
    strict: true,
    typeCheck: true,
  },
  imports: {
    dirs: ['stores'],
  },
})
