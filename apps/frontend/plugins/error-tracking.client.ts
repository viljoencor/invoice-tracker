/**
 * Client-side error tracking plugin.
 *
 * Captures unhandled Vue errors and forwards them to an error tracking service.
 * Configure via NUXT_PUBLIC_ERROR_TRACKING_DSN (or integrate your preferred SDK).
 *
 * To wire up Sentry (example):
 *   1. npm install @sentry/vue
 *   2. import * as Sentry from '@sentry/vue'
 *   3. Replace the console.error calls below with Sentry.captureException(error)
 *   4. Set NUXT_PUBLIC_ERROR_TRACKING_DSN in your environment
 */
export default defineNuxtPlugin((nuxtApp) => {
  const config = useRuntimeConfig()
  const dsn = config.public.errorTrackingDsn as string | undefined

  if (!dsn) {
    // No DSN configured — log a reminder in development only
    if (import.meta.env.DEV) {
      console.warn('[error-tracking] NUXT_PUBLIC_ERROR_TRACKING_DSN is not set; errors will not be reported.')
    }
    return
  }

  // Global Vue error handler — catches errors from any component tree
  nuxtApp.vueApp.config.errorHandler = (error, instance, info) => {
    reportError(error, { info, component: instance?.$options?.name })
  }

  // Nuxt-level error hook — catches errors thrown during route navigation or SSR
  nuxtApp.hook('app:error', (error) => {
    reportError(error, { source: 'app:error' })
  })

  function reportError(error: unknown, context?: Record<string, unknown>) {
    // Replace with your SDK call, e.g. Sentry.captureException(error, { extra: context })
    console.error('[error-tracking]', error, context)
  }
})
