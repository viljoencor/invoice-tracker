// apps/frontend/middleware/auth.ts
export default defineNuxtRouteMiddleware((to) => {
  const token = useCookie<string | null>('token')

  if (to.path === '/login') {
    if (token.value) return navigateTo('/dashboard')
    return
  }

  if (!token.value) return navigateTo('/login')
})
