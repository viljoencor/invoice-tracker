// apps/frontend/middleware/auth.ts
export default defineNuxtRouteMiddleware((to) => {
  // On the server (initial request with ssr:false), skip — client will run this after hydration.
  if (process.server) return

  // Read directly from document.cookie; useCookie() is backed by Nuxt useState which can
  // hold a stale null from before the session cookie was set by the BFF login response.
  const hasSession = document.cookie.split(';').some(c => c.trim().startsWith('session=1'))

  if (to.path === '/login' || to.path === '/register') {
    if (hasSession) return navigateTo('/')
    return
  }

  if (!hasSession) return navigateTo('/login')
})
