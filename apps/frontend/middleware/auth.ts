// apps/frontend/middleware/auth.ts
export default defineNuxtRouteMiddleware((to) => {
  // Route guard: keeps unauthenticated users off protected pages and authenticated users off the login page.
  // Step 1: Read non-httpOnly session indicator; 
  // Step 2: Redirect authenticated users away from /login;
  // Step 3: Redirect unauthenticated users to /login for all other routes.
  const session = useCookie<string | null>('session')

  if (to.path === '/login') {
    if (session.value === '1') return navigateTo('/')
    return
  }

  if (session.value !== '1') return navigateTo('/login')
})
