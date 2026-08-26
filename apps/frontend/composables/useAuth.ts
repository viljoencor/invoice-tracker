import { computed } from 'vue'

export function useAuth() {
  // Read directly from document.cookie; useCookie() useState can hold a stale value
  // when the BFF sets the session cookie via a Set-Cookie header mid-session.
  const hasSession = () =>
    typeof document !== 'undefined' &&
    document.cookie.split(';').some(c => c.trim().startsWith('session=1'))

  const isAuthenticated = computed(hasSession)

  async function logout() {
    try {
      await $fetch('/api/auth/logout', { method: 'POST', credentials: 'include' })
    } catch { /* ignore — BFF-side cookies are cleared regardless */ }
    // navigateTo is safe here: logout clears the session cookie, so the middleware
    // sees no cookie and allows /login without a stale-state redirect.
    await navigateTo('/login')
  }

  return { isAuthenticated, logout }
}
