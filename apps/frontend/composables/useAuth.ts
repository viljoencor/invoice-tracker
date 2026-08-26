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
    // Hard navigation so stale useCookie state doesn't keep isAuthenticated true.
    window.location.href = '/login'
  }

  return { isAuthenticated, logout }
}
