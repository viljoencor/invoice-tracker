import { computed } from 'vue'

/**
 * Single application-facing auth state abstraction.
 * The token cookie is the source of truth; this composable is the only
 * interface the application should use to read or clear auth state.
 *
 * NOTE (Phase 8): this will be replaced by an HTTP-only cookie + BFF proxy.
 */
export function useAuth() {
  const token = useCookie<string | null>('token', { sameSite: 'lax' })

  /** True when a non-empty token is stored in the session cookie. */
  const isAuthenticated = computed(() => !!(token.value ?? '').trim())

  /** Clear the session token and redirect to the login page. */
  async function logout() {
    token.value = null
    await navigateTo('/login')
  }

  return { token, isAuthenticated, logout }
}
