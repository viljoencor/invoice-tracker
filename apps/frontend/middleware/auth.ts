// apps/frontend/middleware/auth.ts
export default defineNuxtRouteMiddleware((to) => {
  // `session` is the non-httpOnly auth indicator set by the BFF on login.
  const session = useCookie<string | null>('session')

  if (to.path === '/login') {
    if (session.value === '1') return navigateTo('/')
    return
  }

  if (session.value !== '1') return navigateTo('/login')
})
