// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  // ⚠️  DEPLOYMENT REQUIREMENT — this app requires a running Nitro server.
  // The BFF proxy, CSRF middleware, and security headers all live in the
  // Nitro layer. Deploying as pure static files (nuxt generate / S3 / CDN)
  // disables every server-side security control. Always deploy with:
  //   nuxt build && node .output/server/index.mjs
  ssr: false,
  nitro: {
    compressPublicAssets: true,
  },
  devtools: { enabled: true },
  modules: ['@pinia/nuxt', 'nuxt-security'],
  security: {
    headers: {
      contentSecurityPolicy: {
        'default-src': ["'self'"],
        'script-src': ["'self'"],
        // 'unsafe-inline' is required for Tailwind JIT and Vue SFC styles.
        'style-src': ["'self'", "'unsafe-inline'", 'https://rsms.me'],
        'font-src': ["'self'", 'data:', 'https://rsms.me'],
        'img-src': ["'self'", 'data:', 'blob:'],
        'connect-src': ["'self'"],
        'frame-ancestors': ["'none'"],
        'object-src': ["'none'"],
        'base-uri': ["'self'"],
        'form-action': ["'self'"],
      },
      xFrameOptions: 'DENY',
      xContentTypeOptions: 'nosniff',
      referrerPolicy: 'strict-origin-when-cross-origin',
      permissionsPolicy: { camera: [], geolocation: [], microphone: [] },
      // External font CDN (rsms.me) requires cross-origin loading.
      crossOriginEmbedderPolicy: false,
      crossOriginOpenerPolicy: false,
      crossOriginResourcePolicy: false,
      strictTransportSecurity: false,
    },
    // ssr: false means assets are pre-rendered. nuxt-security's SSG plugin
    // computes SHA-256 hashes for each script chunk at build time and appends
    // them to script-src automatically — no stale hardcoded hashes.
    ssg: {
      hashScripts: true,
      hashStyles: false, // styles rely on 'unsafe-inline' above
    },
    rateLimiter: false,              // rate-limiting handled by the backend
    xssValidator: false,             // not needed for this API-driven SPA
    corsHandler: false,              // same-origin only; no CORS needed
    allowedMethodsRestricter: false,
    csrf: false,                     // custom CSRF in server/middleware/csrf.ts
    nonce: false,                    // nonces require SSR; this app uses ssr: false
  },
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
