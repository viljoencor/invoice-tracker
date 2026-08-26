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
        // 'strict-dynamic' lets scripts loaded by a nonce-trusted script run.
        'script-src': ["'self'", "'strict-dynamic'"],
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
    ssg: {
      hashScripts: true,
      hashStyles: false, // styles use 'unsafe-inline'
    },
    rateLimiter: false,              // rate-limiting handled by the backend
    xssValidator: false,             // not needed for this API-driven SPA
    corsHandler: false,              // same-origin only; no CORS needed
    allowedMethodsRestricter: false,
    csrf: false,                     // custom CSRF in server/middleware/csrf.ts
    nonce: false,                    // nonces require SSR; route middleware runs client-side with ssr: false
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
      // Set NUXT_PUBLIC_ERROR_TRACKING_DSN to enable client-side error reporting.
      // See plugins/error-tracking.client.ts for integration instructions.
      errorTrackingDsn: process.env.NUXT_PUBLIC_ERROR_TRACKING_DSN || '',
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

  // Vite HMR and inline scripts are incompatible with strict-dynamic + nonces.
  $development: {
    security: {
      headers: {
        contentSecurityPolicy: false,
      },
    },
  },
})
