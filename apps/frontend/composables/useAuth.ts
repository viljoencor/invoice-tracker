import { computed } from 'vue'

/**
 * Single application-facing auth state abstraction.
 *
 * Architecture (Phase 8):
 * - Access and refresh tokens live in httpOnly cookies managed by the Nitro BFF.
 * - Client JS only reads the `session` indicator cookie (not httpOnly) to know
 *   whether a session exists without touching the actual tokens.
 * - logout() calls the BFF which revokes the refresh token and clears all cookies.
 */
export function useAuth() {
  // Non-httpOnly indicator set by the BFF on login; cleared on logout.
  const session = useCookie<string | null>('session', { sameSite: 'lax' })

  /** True when the BFF has established an authenticated session. */
  const isAuthenticated = computed(() => session.value === '1')

  /** Revoke the server-side session and redirect to the login page. */
  async function logout() {
    try {
      await $fetch('/api/auth/logout', { method: 'POST', credentials: 'include' })
    } catch { /* ignore — BFF-side cookies are cleared regardless */ }
    await navigateTo('/login')
  }

  return { isAuthenticated, logout }
}
